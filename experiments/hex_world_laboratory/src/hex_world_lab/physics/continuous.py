"""Swept collision detection for continuous kinematic circle movement."""

from dataclasses import dataclass
import math
from typing import Iterable

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2

from .broadphase import AABB, gather_candidates
from .contacts import Contact, ContactManifold
from .narrowphase import collide_shapes
from .obstacle import ObstacleDefinition
from .shapes import CircleShape, ConvexPolygonShape
from .solver import resolve_kinematic_motion

_EPSILON = 1e-10
_DEFAULT_SKIN = 1e-8
Shape = CircleShape | ConvexPolygonShape


@dataclass(frozen=True, slots=True)
class SweepHit:
    """Earliest normalized time of impact for a swept circle query."""

    obstacle_id: str
    time_of_impact: float
    point: WorldPoint
    normal: Vector2

    def __post_init__(self) -> None:
        if not isinstance(self.obstacle_id, str) or not self.obstacle_id.strip():
            raise ValueError("obstacle_id must be a non-empty string")
        if not math.isfinite(self.time_of_impact) or not 0.0 <= self.time_of_impact <= 1.0:
            raise ValueError("time_of_impact must be finite and in [0, 1]")
        if not isinstance(self.point, WorldPoint) or not isinstance(self.normal, Vector2):
            raise TypeError("point and normal must be WorldPoint and Vector2")
        if not math.isclose(self.normal.length, 1.0, rel_tol=1e-7, abs_tol=1e-7):
            raise ValueError("normal must be normalized")


@dataclass(frozen=True, slots=True)
class ContinuousCollisionResolution:
    """Resolved circle movement and the ordered impacts encountered."""

    final_shape: CircleShape
    applied_displacement: Vector2
    impacts: tuple[SweepHit, ...]
    contacts: ContactManifold
    iterations: int
    unresolved_penetration: float

    def __post_init__(self) -> None:
        if not isinstance(self.final_shape, CircleShape):
            raise TypeError("final_shape must be a CircleShape")
        if not isinstance(self.applied_displacement, Vector2):
            raise TypeError("applied_displacement must be a Vector2")
        if any(not isinstance(hit, SweepHit) for hit in self.impacts):
            raise TypeError("impacts must contain SweepHit values")
        if not isinstance(self.contacts, ContactManifold):
            raise TypeError("contacts must be a ContactManifold")
        if self.iterations < 0 or not math.isfinite(self.unresolved_penetration) or self.unresolved_penetration < 0:
            raise ValueError("invalid resolution diagnostics")


def _dot(a: Vector2, b: Vector2) -> float:
    return a.x * b.x + a.y * b.y


def _point_on_segment(point: Vector2, start: Vector2, end: Vector2) -> bool:
    edge = end - start
    length_squared = edge.length_squared
    if length_squared <= _EPSILON:
        return False
    amount = _dot(point - start, edge) / length_squared
    return -_EPSILON <= amount <= 1.0 + _EPSILON


def _quadratic_first_root(position: Vector2, displacement: Vector2, radius: float) -> float | None:
    a = displacement.length_squared
    if a <= _EPSILON:
        return None
    b = 2.0 * _dot(position, displacement)
    c = position.length_squared - radius * radius
    discriminant = b * b - 4.0 * a * c
    if discriminant < -_EPSILON:
        return None
    root = math.sqrt(max(0.0, discriminant))
    values = sorted(((-b - root) / (2.0 * a), (-b + root) / (2.0 * a)))
    for value in values:
        if -_EPSILON <= value <= 1.0 + _EPSILON:
            t = max(0.0, min(1.0, value))
            normal = (position + displacement * t).normalized()
            if _dot(displacement, normal) < -_EPSILON:
                return t
    return None


def sweep_circle_polygon(
    circle: CircleShape,
    displacement: Vector2,
    polygon: ConvexPolygonShape,
    obstacle_id: str,
) -> SweepHit | None:
    """Return the earliest exact edge/vertex impact for a moving circle.

    The polygon is convex and its vertices may be clockwise or counter-clockwise.
    """
    if not isinstance(circle, CircleShape) or not isinstance(polygon, ConvexPolygonShape):
        raise TypeError("sweep_circle_polygon requires a circle and convex polygon")
    if not isinstance(displacement, Vector2):
        raise TypeError("displacement must be a Vector2")
    if not isinstance(obstacle_id, str) or not obstacle_id.strip():
        raise ValueError("obstacle_id must be a non-empty string")

    initial = collide_shapes(circle, polygon, obstacle_id)
    if initial is not None and initial.penetration_depth > _EPSILON:
        return SweepHit(obstacle_id, 0.0, initial.point, initial.normal)

    vertices = polygon.vertices
    signed_area = sum(
        vertices[i].x * vertices[(i + 1) % len(vertices)].y
        - vertices[(i + 1) % len(vertices)].x * vertices[i].y
        for i in range(len(vertices))
    )
    ccw = signed_area > 0.0
    candidates: list[SweepHit] = []

    for index, start_point in enumerate(vertices):
        end_point = vertices[(index + 1) % len(vertices)]
        start = Vector2(start_point.x, start_point.y)
        end = Vector2(end_point.x, end_point.y)
        edge = end - start
        outward = Vector2(edge.y, -edge.x).normalized() if ccw else Vector2(-edge.y, edge.x).normalized()
        distance = _dot(circle.center - start, outward)
        approach_speed = _dot(displacement, outward)
        if approach_speed < -_EPSILON:
            t = (circle.radius - distance) / approach_speed
            if -_EPSILON <= t <= 1.0 + _EPSILON:
                t = max(0.0, min(1.0, t))
                center_at_hit = circle.center + displacement * t
                contact_point = center_at_hit - outward * circle.radius
                if _point_on_segment(contact_point, start, end):
                    candidates.append(SweepHit(
                        obstacle_id, t,
                        WorldPoint(contact_point.x, contact_point.y), outward,
                    ))

        relative = circle.center - start
        vertex_t = _quadratic_first_root(relative, displacement, circle.radius)
        if vertex_t is not None:
            center_at_hit = circle.center + displacement * vertex_t
            radial = (center_at_hit - start).normalized()
            if radial.length > _EPSILON and _dot(displacement, radial) < -_EPSILON:
                # A vertex is active only in its Voronoi region, outside both adjacent edges.
                previous = Vector2(
                    vertices[index - 1].x, vertices[index - 1].y
                )
                following = Vector2(end_point.x, end_point.y)
                toward_previous = previous - start
                toward_following = following - start
                if _dot(center_at_hit - start, toward_previous) <= _EPSILON and _dot(
                    center_at_hit - start, toward_following
                ) <= _EPSILON:
                    candidates.append(SweepHit(
                        obstacle_id, vertex_t, WorldPoint(start.x, start.y), radial,
                    ))

    if not candidates:
        return None
    return min(candidates, key=lambda hit: (hit.time_of_impact, hit.obstacle_id, hit.point.x, hit.point.y))


def _sweep_circle_circle(
    circle: CircleShape, displacement: Vector2, obstacle: CircleShape, obstacle_id: str
) -> SweepHit | None:
    relative = circle.center - obstacle.center
    combined = circle.radius + obstacle.radius
    initial_distance = relative.length
    if initial_distance < combined - _EPSILON:
        contact = collide_shapes(circle, obstacle, obstacle_id)
        assert contact is not None
        return SweepHit(obstacle_id, 0.0, contact.point, contact.normal)
    t = _quadratic_first_root(relative, displacement, combined)
    if t is None:
        return None
    center = circle.center + displacement * t
    normal = (center - obstacle.center).normalized()
    point = obstacle.center + normal * obstacle.radius
    return SweepHit(obstacle_id, t, WorldPoint(point.x, point.y), normal)


def _translated(circle: CircleShape, delta: Vector2) -> CircleShape:
    return CircleShape(circle.radius, circle.center + delta)


def _remove_inward(displacement: Vector2, normal: Vector2) -> Vector2:
    inward = _dot(displacement, normal)
    return displacement - normal * inward if inward < 0.0 else displacement


def resolve_continuous_motion(
    moving_circle: CircleShape,
    desired_displacement: Vector2,
    obstacles: Iterable[ObstacleDefinition],
    *,
    max_impacts: int = 6,
    collision_skin: float = _DEFAULT_SKIN,
    penetration_slop: float = 1e-7,
) -> ContinuousCollisionResolution:
    """Sweep a circle through static obstacles, sliding after each impact."""
    if not isinstance(moving_circle, CircleShape):
        raise TypeError("moving_circle must be a CircleShape")
    if not isinstance(desired_displacement, Vector2):
        raise TypeError("desired_displacement must be a Vector2")
    if isinstance(max_impacts, bool) or not isinstance(max_impacts, int) or max_impacts < 1:
        raise ValueError("max_impacts must be a positive integer")
    if not math.isfinite(collision_skin) or collision_skin < 0:
        raise ValueError("collision_skin must be finite and non-negative")

    obstacle_values = tuple(obstacles)
    if any(not isinstance(item, ObstacleDefinition) for item in obstacle_values):
        raise TypeError("obstacles must contain ObstacleDefinition values")
    ids = tuple(item.obstacle_id for item in obstacle_values)
    if len(ids) != len(set(ids)):
        raise ValueError("obstacle IDs must be unique")

    # Correct pre-existing overlap before attempting a swept move.
    depenetrated = resolve_kinematic_motion(
        moving_circle, Vector2(0.0, 0.0), obstacle_values,
        max_iterations=max_impacts, penetration_slop=penetration_slop,
    )
    current = depenetrated.final_shape
    remaining = desired_displacement
    impacts: list[SweepHit] = []
    contacts = list(depenetrated.contacts.contacts)
    iterations = 0
    unresolved = depenetrated.unresolved_penetration

    while remaining.length > _EPSILON and iterations < max_impacts:
        bounds = AABB(
            min(current.center.x - current.radius, current.center.x + remaining.x - current.radius),
            min(current.center.y - current.radius, current.center.y + remaining.y - current.radius),
            max(current.center.x + current.radius, current.center.x + remaining.x + current.radius),
            max(current.center.y + current.radius, current.center.y + remaining.y + current.radius),
        )
        candidates = gather_candidates(bounds, obstacle_values)
        hits: list[SweepHit] = []
        for obstacle in candidates:
            world_shape = obstacle.world_shape()
            if isinstance(world_shape, ConvexPolygonShape):
                hit = sweep_circle_polygon(current, remaining, world_shape, obstacle.obstacle_id)
            else:
                hit = _sweep_circle_circle(current, remaining, world_shape, obstacle.obstacle_id)
            if hit is not None:
                hits.append(hit)

        if not hits:
            current = _translated(current, remaining)
            remaining = Vector2(0.0, 0.0)
            break

        hit = min(hits, key=lambda item: (item.time_of_impact, item.obstacle_id))
        impacts.append(hit)
        iterations += 1
        travel_length = remaining.length
        backoff = min(hit.time_of_impact, collision_skin / travel_length) if travel_length else 0.0
        safe_t = max(0.0, hit.time_of_impact - backoff)
        traveled = remaining * safe_t
        current = _translated(current, traveled)
        remaining = remaining * (1.0 - safe_t)
        projected = _remove_inward(remaining, hit.normal)
        contacts.append(Contact(
            hit.obstacle_id, hit.point, hit.normal, 0.0
        ))
        if (projected - remaining).length <= _EPSILON:
            # A zero-time tangential/separating hit cannot make progress.
            if safe_t <= _EPSILON:
                break
        remaining = projected

    final_displacement = current.center - moving_circle.center
    return ContinuousCollisionResolution(
        current, final_displacement, tuple(impacts),
        ContactManifold(tuple(contacts)), iterations, unresolved,
    )
