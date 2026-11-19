"""Deterministic discrete kinematic collision resolution with wall sliding."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from core.domain.spatial import AABB, WorldPoint
from .contacts import Contact, ContactManifold
from .narrowphase import collide_shapes
from .obstacle import StaticObstacle
from .obstacle_index import StaticObstacleIndex, obstacle_bounds
from .shapes import CircleShape, ColliderShape, ConvexPolygonShape
from .vector2 import Vector2

_EPSILON = 1e-10


@dataclass(frozen=True, slots=True)
class CollisionResolution:
    final_shape: ColliderShape
    applied_displacement: Vector2
    contacts: ContactManifold
    iterations: int
    unresolved_penetration: float

    def __post_init__(self) -> None:
        if not isinstance(self.final_shape, (CircleShape, ConvexPolygonShape)):
            raise TypeError("final_shape must be a supported collider shape.")
        if not isinstance(self.applied_displacement, Vector2):
            raise TypeError("applied_displacement must be a Vector2.")
        if not isinstance(self.contacts, ContactManifold):
            raise TypeError("contacts must be a ContactManifold.")
        if isinstance(self.iterations, bool) or not isinstance(self.iterations, int) or self.iterations < 0:
            raise ValueError("iterations must be a non-negative integer.")
        if isinstance(self.unresolved_penetration, bool) or not isinstance(self.unresolved_penetration, (int, float)):
            raise TypeError("unresolved_penetration must be a real number.")
        if not math.isfinite(self.unresolved_penetration) or self.unresolved_penetration < 0:
            raise ValueError("unresolved_penetration must be finite and non-negative.")


def _reference_point(shape: ColliderShape) -> WorldPoint:
    if isinstance(shape, CircleShape):
        return shape.center
    count = len(shape.vertices)
    return WorldPoint(
        sum(point.x for point in shape.vertices) / count,
        sum(point.y for point in shape.vertices) / count,
    )


def _translated(shape: ColliderShape, delta: Vector2) -> ColliderShape:
    if isinstance(shape, CircleShape):
        return CircleShape(shape.radius, WorldPoint(shape.center.x + delta.x, shape.center.y + delta.y))
    return ConvexPolygonShape(tuple(
        WorldPoint(point.x + delta.x, point.y + delta.y) for point in shape.vertices
    ))


def _shape_bounds(shape: ColliderShape) -> AABB:
    if isinstance(shape, CircleShape):
        return AABB(
            shape.center.x - shape.radius, shape.center.y - shape.radius,
            shape.center.x + shape.radius, shape.center.y + shape.radius,
        )
    xs = tuple(point.x for point in shape.vertices)
    ys = tuple(point.y for point in shape.vertices)
    return AABB(min(xs), min(ys), max(xs), max(ys))


def _swept_bounds(shape: ColliderShape, displacement: Vector2) -> AABB:
    start = _shape_bounds(shape)
    end = _shape_bounds(_translated(shape, displacement))
    return AABB(
        min(start.min_x, end.min_x), min(start.min_y, end.min_y),
        max(start.max_x, end.max_x), max(start.max_y, end.max_y),
    )


def _contacts(shape: ColliderShape, obstacles: tuple[StaticObstacle, ...]) -> ContactManifold:
    values = []
    for obstacle in obstacles:
        contact = collide_shapes(shape, obstacle.world_shape(), obstacle.obstacle_id)
        if contact is not None:
            values.append(contact)
    return ContactManifold(tuple(values))


def _depenetrate(
    shape: ColliderShape,
    obstacles: tuple[StaticObstacle, ...],
    *,
    max_iterations: int,
    slop: float,
) -> tuple[ColliderShape, tuple[Contact, ...], int, float]:
    current = shape
    encountered = []
    iterations = 0
    for _ in range(max_iterations):
        penetrating = tuple(item for item in _contacts(current, obstacles) if item.penetration_depth > slop)
        if not penetrating:
            break
        selected = min(penetrating, key=lambda item: (-item.penetration_depth, item.obstacle_id))
        encountered.append(selected)
        current = _translated(current, selected.normal * (selected.penetration_depth + slop))
        iterations += 1
    remaining = _contacts(current, obstacles)
    unresolved = max((item.penetration_depth for item in remaining), default=0.0)
    return current, tuple(encountered), iterations, max(0.0, unresolved)


def _remove_inward_components(displacement: Vector2, normals: tuple[Vector2, ...]) -> Vector2:
    result = displacement
    for _ in range(max(1, len(normals))):
        changed = False
        for normal in normals:
            inward = result.dot(normal)
            if inward < -_EPSILON:
                result = result - normal * inward
                changed = True
        if not changed:
            break
    return result


def resolve_kinematic_motion(
    moving_shape: ColliderShape,
    desired_displacement: Vector2,
    obstacles: Iterable[StaticObstacle],
    *,
    max_iterations: int = 6,
    penetration_slop: float = 1e-7,
    map_id: str | None = None,
    candidate_provider: StaticObstacleIndex | None = None,
) -> CollisionResolution:
    """Resolve overlap and wall sliding for one discrete move.

    This solver is not continuous collision detection and does not prevent
    tunneling through thin obstacles at large displacements.
    """
    if not isinstance(moving_shape, (CircleShape, ConvexPolygonShape)):
        raise TypeError("moving_shape must be a supported collider shape.")
    if not isinstance(desired_displacement, Vector2):
        raise TypeError("desired_displacement must be a Vector2.")
    if isinstance(max_iterations, bool) or not isinstance(max_iterations, int):
        raise TypeError("max_iterations must be an integer.")
    if max_iterations < 1:
        raise ValueError("max_iterations must be at least one.")
    if isinstance(penetration_slop, bool) or not isinstance(penetration_slop, (int, float)):
        raise TypeError("penetration_slop must be a real number.")
    if not math.isfinite(penetration_slop) or penetration_slop < 0:
        raise ValueError("penetration_slop must be finite and non-negative.")

    obstacle_values = tuple(obstacles)
    if any(not isinstance(item, StaticObstacle) for item in obstacle_values):
        raise TypeError("obstacles must contain StaticObstacle values.")
    ids = tuple(item.obstacle_id for item in obstacle_values)
    if len(ids) != len(set(ids)):
        raise ValueError("obstacle IDs must be unique.")
    if map_id is None:
        maps = {item.map_id for item in obstacle_values}
        if len(maps) > 1:
            raise ValueError("map_id is required when obstacles span multiple maps.")
        map_id = next(iter(maps), "")
    if any(item.map_id != map_id for item in obstacle_values):
        raise ValueError("all obstacles must belong to map_id.")
    if candidate_provider is not None and not isinstance(candidate_provider, StaticObstacleIndex):
        raise TypeError("candidate_provider must be a StaticObstacleIndex.")

    query_bounds = _swept_bounds(moving_shape, desired_displacement)
    candidates = (
        tuple(candidate_provider.query(map_id, query_bounds))
        if candidate_provider is not None
        else tuple(item for item in obstacle_values if query_bounds.intersects(obstacle_bounds(item)))
    )
    candidates = tuple(sorted(candidates, key=lambda item: item.obstacle_id))

    original_reference = _reference_point(moving_shape)
    current, initial_contacts, used, unresolved = _depenetrate(
        moving_shape, candidates, max_iterations=max_iterations, slop=penetration_slop,
    )
    all_contacts = list(initial_contacts)
    if unresolved > penetration_slop:
        final_reference = _reference_point(current)
        return CollisionResolution(
            current,
            Vector2(final_reference.x - original_reference.x, final_reference.y - original_reference.y),
            ContactManifold(tuple(all_contacts)), used, unresolved,
        )

    remaining = desired_displacement
    while used < max_iterations:
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
            proposed, candidates, max_iterations=max(1, max_iterations - used), slop=penetration_slop,
        )
        all_contacts.extend(corrections)
        used += 1 + correction_iterations
        before, after = _reference_point(current), _reference_point(corrected)
        step = Vector2(after.x - before.x, after.y - before.y)
        current = corrected
        remaining = remaining - step
        normals = tuple(item.normal for item in manifold.contacts + ContactManifold(corrections).contacts)
        remaining = _remove_inward_components(remaining, normals)
        if unresolved > penetration_slop:
            break
        if step.length <= _EPSILON and remaining.length > _EPSILON:
            break

    final_reference = _reference_point(current)
    applied = Vector2(final_reference.x - original_reference.x, final_reference.y - original_reference.y)
    return CollisionResolution(current, applied, ContactManifold(tuple(all_contacts)), used, unresolved)
