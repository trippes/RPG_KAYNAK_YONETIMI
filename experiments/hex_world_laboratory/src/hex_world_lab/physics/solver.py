"""Deterministic kinematic collision resolution with wall sliding."""

from dataclasses import dataclass
import math
from typing import Iterable

from hex_world_lab.movement.vector import Vector2

from .broadphase import AABB, gather_candidates
from .contacts import Contact, ContactManifold
from .narrowphase import collide_shapes
from .obstacle import ObstacleDefinition
from .shapes import CircleShape, ConvexPolygonShape

Shape = CircleShape | ConvexPolygonShape
_EPSILON = 1e-10


@dataclass(frozen=True, slots=True)
class CollisionResolution:
    """Resolved world-space shape and diagnostics for one requested movement."""

    final_shape: Shape
    applied_displacement: Vector2
    contacts: ContactManifold
    iterations: int
    unresolved_penetration: float

    def __post_init__(self) -> None:
        if not isinstance(self.final_shape, (CircleShape, ConvexPolygonShape)):
            raise TypeError("final_shape must be a supported collider shape")
        if not isinstance(self.applied_displacement, Vector2):
            raise TypeError("applied_displacement must be a Vector2")
        if not isinstance(self.contacts, ContactManifold):
            raise TypeError("contacts must be a ContactManifold")
        if isinstance(self.iterations, bool) or not isinstance(self.iterations, int) or self.iterations < 0:
            raise ValueError("iterations must be a non-negative integer")
        if not math.isfinite(self.unresolved_penetration) or self.unresolved_penetration < 0:
            raise ValueError("unresolved_penetration must be finite and non-negative")


def _reference_point(shape: Shape) -> Vector2:
    if isinstance(shape, CircleShape):
        return shape.center
    count = len(shape.vertices)
    return Vector2(
        sum(point.x for point in shape.vertices) / count,
        sum(point.y for point in shape.vertices) / count,
    )


def _translated(shape: Shape, delta: Vector2) -> Shape:
    if isinstance(shape, CircleShape):
        return CircleShape(
            shape.radius,
            Vector2(shape.center.x + delta.x, shape.center.y + delta.y),
        )
    return ConvexPolygonShape(tuple(
        Vector2(point.x + delta.x, point.y + delta.y)
        for point in shape.vertices
    ))


def _swept_bounds(shape: Shape, displacement: Vector2) -> AABB:
    start = AABB.from_shape(shape)
    end = AABB.from_shape(_translated(shape, displacement))
    return AABB(
        min(start.min_x, end.min_x),
        min(start.min_y, end.min_y),
        max(start.max_x, end.max_x),
        max(start.max_y, end.max_y),
    )


def _contacts(shape: Shape, obstacles: tuple[ObstacleDefinition, ...]) -> ContactManifold:
    values: list[Contact] = []
    for obstacle in obstacles:
        contact = collide_shapes(shape, obstacle.world_shape(), obstacle.obstacle_id)
        if contact is not None:
            values.append(contact)
    return ContactManifold(tuple(values))


def _depenetrate(
    shape: Shape,
    obstacles: tuple[ObstacleDefinition, ...],
    *,
    max_iterations: int,
    slop: float,
) -> tuple[Shape, tuple[Contact, ...], int, float]:
    current = shape
    encountered: list[Contact] = []
    iterations = 0
    for _ in range(max_iterations):
        manifold = _contacts(current, obstacles)
        penetrating = tuple(
            item for item in manifold
            if item.penetration_depth > slop
        )
        if not penetrating:
            break
        # Resolve the deepest constraint first; ID order breaks equal-depth ties.
        selected = min(
            penetrating,
            key=lambda item: (-item.penetration_depth, item.obstacle_id),
        )
        encountered.append(selected)
        correction = selected.normal * (selected.penetration_depth + slop)
        current = _translated(current, correction)
        iterations += 1

    remaining = _contacts(current, obstacles)
    unresolved = max(
        (item.penetration_depth for item in remaining),
        default=0.0,
    )
    return current, tuple(encountered), iterations, max(0.0, unresolved)


def _remove_inward_components(
    displacement: Vector2,
    normals: tuple[Vector2, ...],
) -> Vector2:
    result = displacement
    # Repeated projection handles independent corner constraints without
    # depending on obstacle insertion order.
    for _ in range(max(1, len(normals))):
        changed = False
        for normal in normals:
            inward = result.x * normal.x + result.y * normal.y
            if inward < -_EPSILON:
                result = result - normal * inward
                changed = True
        if not changed:
            break
    return result


def resolve_kinematic_motion(
    moving_shape: Shape,
    desired_displacement: Vector2,
    obstacles: Iterable[ObstacleDefinition],
    *,
    max_iterations: int = 6,
    penetration_slop: float = 1e-7,
) -> CollisionResolution:
    """Resolve a kinematic move, removing inward motion and preserving sliding.

    The moving shape and obstacle shapes must already be in world coordinates.
    Broadphase is conservative; all final decisions come from narrowphase.
    This discrete solver does not prevent tunneling; swept collision is handled
    by the next continuous-collision stage.
    """
    if not isinstance(moving_shape, (CircleShape, ConvexPolygonShape)):
        raise TypeError("moving_shape must be a supported collider shape")
    if not isinstance(desired_displacement, Vector2):
        raise TypeError("desired_displacement must be a Vector2")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise TypeError("max_iterations must be an integer")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least one")
    if isinstance(penetration_slop, bool) or not isinstance(penetration_slop, (int, float)):
        raise TypeError("penetration_slop must be a real number")
    if not math.isfinite(penetration_slop) or penetration_slop < 0:
        raise ValueError("penetration_slop must be finite and non-negative")

    obstacle_values = tuple(obstacles)
    if any(not isinstance(item, ObstacleDefinition) for item in obstacle_values):
        raise TypeError("obstacles must contain ObstacleDefinition values")
    ids = tuple(item.obstacle_id for item in obstacle_values)
    if len(ids) != len(set(ids)):
        raise ValueError("obstacle IDs must be unique")

    candidates = gather_candidates(
        _swept_bounds(moving_shape, desired_displacement),
        obstacle_values,
    )
    current, initial_contacts, used, unresolved = _depenetrate(
        moving_shape,
        candidates,
        max_iterations=max_iterations,
        slop=penetration_slop,
    )
    all_contacts = list(initial_contacts)
    if unresolved > penetration_slop:
        return CollisionResolution(
            current,
            Vector2(
                _reference_point(current).x - _reference_point(moving_shape).x,
                _reference_point(current).y - _reference_point(moving_shape).y,
            ),
            ContactManifold(tuple(all_contacts)),
            used,
            unresolved,
        )

    movement_origin = _reference_point(current)
    remaining = desired_displacement
    for _ in range(max_iterations - used):
        if remaining.length <= _EPSILON:
            break
        proposed = _translated(current, remaining)
        manifold = _contacts(proposed, candidates)
        if not manifold.contacts:
            current = proposed
            remaining = Vector2(0.0, 0.0)
            used += 1
            break

        all_contacts.extend(manifold.contacts)
        corrected, corrections, correction_iterations, unresolved = _depenetrate(
            proposed,
            candidates,
            max_iterations=max(1, max_iterations - used),
            slop=penetration_slop,
        )
        all_contacts.extend(corrections)
        used += 1 + correction_iterations

        before = _reference_point(current)
        after = _reference_point(corrected)
        step = Vector2(after.x - before.x, after.y - before.y)
        current = corrected
        remaining = remaining - step
        normals = tuple(item.normal for item in manifold.contacts + ContactManifold(corrections).contacts)
        remaining = _remove_inward_components(remaining, normals)

        if unresolved > penetration_slop:
            break
        if step.length <= _EPSILON and remaining.length > _EPSILON:
            # No safe progress is possible within the current contact set.
            break

    final_reference = _reference_point(current)
    applied = Vector2(
        final_reference.x - movement_origin.x,
        final_reference.y - movement_origin.y,
    )
    return CollisionResolution(
        current,
        applied,
        ContactManifold(tuple(all_contacts)),
        used,
        unresolved,
    )
