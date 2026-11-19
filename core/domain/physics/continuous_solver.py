"""Swept collision detection for Eldoria-native continuous circle movement."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from core.domain.spatial import AABB, WorldPoint
from .contacts import Contact, ContactManifold
from .kinematic_solver import resolve_kinematic_motion
from .narrowphase import collide_shapes
from .obstacle import StaticObstacle
from .obstacle_index import StaticObstacleIndex, obstacle_bounds
from .shapes import CircleShape, ConvexPolygonShape
from .vector2 import Vector2

_EPSILON = 1e-10
_DEFAULT_SKIN = 1e-8


@dataclass(frozen=True, slots=True)
class SweepHit:
    obstacle_id: str
    time_of_impact: float
    point: WorldPoint
    normal: Vector2

    def __post_init__(self) -> None:
        if not isinstance(self.obstacle_id, str) or not self.obstacle_id.strip():
            raise ValueError("obstacle_id must be a non-empty string.")
        if isinstance(self.time_of_impact, bool) or not isinstance(self.time_of_impact, (int, float)):
            raise TypeError("time_of_impact must be a real number.")
        if not math.isfinite(self.time_of_impact) or not 0.0 <= self.time_of_impact <= 1.0:
            raise ValueError("time_of_impact must be finite and in [0, 1].")
        if not isinstance(self.point, WorldPoint) or not isinstance(self.normal, Vector2):
            raise TypeError("point and normal must be WorldPoint and Vector2.")
        if not math.isclose(self.normal.length, 1.0, rel_tol=1e-7, abs_tol=1e-7):
            raise ValueError("normal must be normalized.")


@dataclass(frozen=True, slots=True)
class ContinuousCollisionResolution:
    final_shape: CircleShape
    applied_displacement: Vector2
    impacts: tuple[SweepHit, ...]
    contacts: ContactManifold
    iterations: int
    unresolved_penetration: float

    def __post_init__(self) -> None:
        if not isinstance(self.final_shape, CircleShape):
            raise TypeError("final_shape must be a CircleShape.")
        if not isinstance(self.applied_displacement, Vector2):
            raise TypeError("applied_displacement must be a Vector2.")
        impacts = tuple(self.impacts)
        if any(not isinstance(item, SweepHit) for item in impacts):
            raise TypeError("impacts must contain SweepHit values.")
        if not isinstance(self.contacts, ContactManifold):
            raise TypeError("contacts must be a ContactManifold.")
        if isinstance(self.iterations, bool) or not isinstance(self.iterations, int) or self.iterations < 0:
            raise ValueError("iterations must be a non-negative integer.")
        if isinstance(self.unresolved_penetration, bool) or not isinstance(self.unresolved_penetration, (int, float)):
            raise TypeError("unresolved_penetration must be a real number.")
        if not math.isfinite(self.unresolved_penetration) or self.unresolved_penetration < 0:
            raise ValueError("unresolved_penetration must be finite and non-negative.")
        object.__setattr__(self, "impacts", impacts)


def _dot(first: Vector2, second: Vector2) -> float:
    return first.x * second.x + first.y * second.y


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
    for value in sorted(((-b - root) / (2.0 * a), (-b + root) / (2.0 * a))):
        if -_EPSILON <= value <= 1.0 + _EPSILON:
            t = max(0.0, min(1.0, value))
            normal = (position + displacement * t).normalized()
            if _dot(displacement, normal) < -_EPSILON:
                return t
    return None


def _closest_world_point_on_segment(point: WorldPoint, start: WorldPoint, end: WorldPoint) -> WorldPoint:
    edge = Vector2(end.x - start.x, end.y - start.y)
    relative = Vector2(point.x - start.x, point.y - start.y)
    length_squared = edge.length_squared
    if length_squared <= _EPSILON:
        return start
    amount = max(0.0, min(1.0, _dot(relative, edge) / length_squared))
    return WorldPoint(start.x + edge.x * amount, start.y + edge.y * amount)


def sweep_circle_polygon(
    circle: CircleShape,
    displacement: Vector2,
    polygon: ConvexPolygonShape,
    obstacle_id: str,
) -> SweepHit | None:
    """Return the earliest edge/vertex impact for a swept circle and convex polygon."""
    if not isinstance(circle, CircleShape) or not isinstance(polygon, ConvexPolygonShape):
        raise TypeError("sweep_circle_polygon requires a circle and convex polygon.")
    if not isinstance(displacement, Vector2):
        raise TypeError("displacement must be a Vector2.")
    if not isinstance(obstacle_id, str) or not obstacle_id.strip():
        raise ValueError("obstacle_id must be a non-empty string.")

    initial = collide_shapes(circle, polygon, obstacle_id)
    if initial is not None and initial.penetration_depth > _EPSILON:
        return SweepHit(obstacle_id, 0.0, initial.point, initial.normal)

    vertices = polygon.vertices
    signed_area = sum(
        vertices[index].x * vertices[(index + 1) % len(vertices)].y
        - vertices[(index + 1) % len(vertices)].x * vertices[index].y
        for index in range(len(vertices))
    )
    counter_clockwise = signed_area > 0.0
    candidates: list[SweepHit] = []

    for index, start_point in enumerate(vertices):
        end_point = vertices[(index + 1) % len(vertices)]
        start = Vector2(start_point.x, start_point.y)
        end = Vector2(end_point.x, end_point.y)
        edge = end - start
        outward = (
            Vector2(edge.y, -edge.x).normalized()
            if counter_clockwise
            else Vector2(-edge.y, edge.x).normalized()
        )
        center = Vector2(circle.center.x, circle.center.y)
        distance = _dot(center - start, outward)
        approach_speed = _dot(displacement, outward)
        if approach_speed < -_EPSILON:
            time = (circle.radius - distance) / approach_speed
            if -_EPSILON <= time <= 1.0 + _EPSILON:
                time = max(0.0, min(1.0, time))
                center_at_hit = center + displacement * time
                contact = center_at_hit - outward * circle.radius
                if _point_on_segment(contact, start, end):
                    candidates.append(SweepHit(
                        obstacle_id, time,
                        WorldPoint(contact.x, contact.y), outward,
                    ))

        relative = center - start
        vertex_time = _quadratic_first_root(relative, displacement, circle.radius)
        if vertex_time is not None:
            center_at_hit = center + displacement * vertex_time
            radial = (center_at_hit - start).normalized()
            previous_point = vertices[index - 1]
            previous = Vector2(previous_point.x, previous_point.y)
            following = Vector2(end_point.x, end_point.y)
            toward_previous = previous - start
            toward_following = following - start
            offset = center_at_hit - start
            if (
                radial.length > _EPSILON
                and _dot(displacement, radial) < -_EPSILON
                and _dot(offset, toward_previous) <= _EPSILON
                and _dot(offset, toward_following) <= _EPSILON
            ):
                candidates.append(SweepHit(
                    obstacle_id, vertex_time,
                    WorldPoint(start.x, start.y), radial,
                ))

    if not candidates:
        return None
    return min(candidates, key=lambda hit: (
        hit.time_of_impact, hit.obstacle_id, hit.point.x, hit.point.y,
    ))


def _sweep_circle_circle(
    circle: CircleShape,
    displacement: Vector2,
    obstacle: CircleShape,
    obstacle_id: str,
) -> SweepHit | None:
    relative = Vector2(
        circle.center.x - obstacle.center.x,
        circle.center.y - obstacle.center.y,
    )
    combined_radius = circle.radius + obstacle.radius
    if relative.length < combined_radius - _EPSILON:
        contact = collide_shapes(circle, obstacle, obstacle_id)
        if contact is not None:
            return SweepHit(obstacle_id, 0.0, contact.point, contact.normal)
    time = _quadratic_first_root(relative, displacement, combined_radius)
    if time is None:
        return None
    center = Vector2(circle.center.x, circle.center.y) + displacement * time
    normal = Vector2(center.x - obstacle.center.x, center.y - obstacle.center.y).normalized()
    point = WorldPoint(
        obstacle.center.x + normal.x * obstacle.radius,
        obstacle.center.y + normal.y * obstacle.radius,
    )
    return SweepHit(obstacle_id, time, point, normal)


def _translated(circle: CircleShape, displacement: Vector2) -> CircleShape:
    return CircleShape(
        circle.radius,
        WorldPoint(circle.center.x + displacement.x, circle.center.y + displacement.y),
    )


def _remove_inward(displacement: Vector2, normal: Vector2) -> Vector2:
    inward = _dot(displacement, normal)
    return displacement - normal * inward if inward < 0.0 else displacement


def _swept_circle_bounds(circle: CircleShape, displacement: Vector2) -> AABB:
    return AABB(
        min(circle.center.x - circle.radius, circle.center.x + displacement.x - circle.radius),
        min(circle.center.y - circle.radius, circle.center.y + displacement.y - circle.radius),
        max(circle.center.x + circle.radius, circle.center.x + displacement.x + circle.radius),
        max(circle.center.y + circle.radius, circle.center.y + displacement.y + circle.radius),
    )


def resolve_continuous_motion(
    moving_circle: CircleShape,
    desired_displacement: Vector2,
    obstacles: Iterable[StaticObstacle],
    *,
    max_impacts: int = 6,
    collision_skin: float = _DEFAULT_SKIN,
    penetration_slop: float = 1e-7,
    map_id: str | None = None,
    candidate_provider: StaticObstacleIndex | None = None,
) -> ContinuousCollisionResolution:
    """Sweep a circle against static map obstacles and slide along contacts."""
    if not isinstance(moving_circle, CircleShape):
        raise TypeError("moving_circle must be a CircleShape.")
    if not isinstance(desired_displacement, Vector2):
        raise TypeError("desired_displacement must be a Vector2.")
    if isinstance(max_impacts, bool) or not isinstance(max_impacts, int) or max_impacts < 1:
        raise ValueError("max_impacts must be a positive integer.")
    if isinstance(collision_skin, bool) or not isinstance(collision_skin, (int, float)):
        raise TypeError("collision_skin must be a real number.")
    if not math.isfinite(collision_skin) or collision_skin < 0:
        raise ValueError("collision_skin must be finite and non-negative.")
    if isinstance(penetration_slop, bool) or not isinstance(penetration_slop, (int, float)):
        raise TypeError("penetration_slop must be a real number.")
    if not math.isfinite(penetration_slop) or penetration_slop < 0:
        raise ValueError("penetration_slop must be finite and non-negative.")

    values = tuple(obstacles)
    if any(not isinstance(item, StaticObstacle) for item in values):
        raise TypeError("obstacles must contain StaticObstacle values.")
    ids = tuple(item.obstacle_id for item in values)
    if len(ids) != len(set(ids)):
        raise ValueError("obstacle IDs must be unique.")
    if map_id is None:
        maps = {item.map_id for item in values}
        if len(maps) > 1:
            raise ValueError("map_id is required when obstacles span multiple maps.")
        map_id = next(iter(maps), "")
    if any(item.map_id != map_id for item in values):
        raise ValueError("all obstacles must belong to map_id.")
    if candidate_provider is not None and not isinstance(candidate_provider, StaticObstacleIndex):
        raise TypeError("candidate_provider must be a StaticObstacleIndex.")

    depenetrated = resolve_kinematic_motion(
        moving_circle, Vector2(0.0, 0.0), values,
        max_iterations=max_impacts, penetration_slop=penetration_slop,
        map_id=map_id, candidate_provider=candidate_provider,
    )
    current = depenetrated.final_shape
    remaining = desired_displacement
    impacts: list[SweepHit] = []
    contacts = list(depenetrated.contacts.contacts)
    iterations = 0
    unresolved = depenetrated.unresolved_penetration

    while remaining.length > _EPSILON and iterations < max_impacts:
        bounds = _swept_circle_bounds(current, remaining)
        candidates = (
            tuple(candidate_provider.query(map_id, bounds))
            if candidate_provider is not None
            else tuple(item for item in values if bounds.intersects(obstacle_bounds(item)))
        )
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
        safe_time = max(0.0, hit.time_of_impact - backoff)
        traveled = remaining * safe_time
        current = _translated(current, traveled)
        remaining = remaining * (1.0 - safe_time)
        projected = _remove_inward(remaining, hit.normal)
        contacts.append(Contact(hit.obstacle_id, hit.point, hit.normal, 0.0))
        if (projected - remaining).length <= _EPSILON and safe_time <= _EPSILON:
            break
        remaining = projected

    applied = Vector2(
        current.center.x - moving_circle.center.x,
        current.center.y - moving_circle.center.y,
    )
    return ContinuousCollisionResolution(
        current, applied, tuple(impacts), ContactManifold(tuple(contacts)),
        iterations, unresolved,
    )
