"""Exact overlap tests for native circles and strictly convex polygons."""
from __future__ import annotations

import math

from core.domain.spatial import WorldPoint
from .contacts import Contact
from .shapes import CircleShape, ConvexPolygonShape
from .vector2 import Vector2

_EPSILON = 1e-10
Shape = CircleShape | ConvexPolygonShape


def _dot(a: Vector2, b: Vector2) -> float:
    return a.x * b.x + a.y * b.y


def _centroid(shape: ConvexPolygonShape) -> Vector2:
    count = len(shape.vertices)
    return Vector2(
        sum(point.x for point in shape.vertices) / count,
        sum(point.y for point in shape.vertices) / count,
    )


def _axes(shape: ConvexPolygonShape) -> tuple[Vector2, ...]:
    result = []
    for index, start in enumerate(shape.vertices):
        end = shape.vertices[(index + 1) % len(shape.vertices)]
        edge = Vector2(end.x - start.x, end.y - start.y)
        result.append(Vector2(-edge.y, edge.x).normalized())
    return tuple(result)


def _project_polygon(shape: ConvexPolygonShape, axis: Vector2) -> tuple[float, float]:
    values = tuple(point.x * axis.x + point.y * axis.y for point in shape.vertices)
    return min(values), max(values)


def _project_circle(shape: CircleShape, axis: Vector2) -> tuple[float, float]:
    center = shape.center.x * axis.x + shape.center.y * axis.y
    return center - shape.radius, center + shape.radius


def _minimum_overlap(first: tuple[float, float], second: tuple[float, float]) -> float | None:
    if first[1] < second[0] - _EPSILON or second[1] < first[0] - _EPSILON:
        return None
    return max(0.0, min(first[1] - second[0], second[1] - first[0]))


def _orient_axis(axis: Vector2, direction: Vector2) -> Vector2:
    projection = _dot(axis, direction)
    if projection < -_EPSILON:
        return Vector2(-axis.x, -axis.y)
    if abs(projection) <= _EPSILON and (
        axis.x < -_EPSILON or (abs(axis.x) <= _EPSILON and axis.y < 0)
    ):
        return Vector2(-axis.x, -axis.y)
    return axis


def _closest_on_segment(point: WorldPoint, start: WorldPoint, end: WorldPoint) -> WorldPoint:
    edge = Vector2(end.x - start.x, end.y - start.y)
    relative = Vector2(point.x - start.x, point.y - start.y)
    length_squared = _dot(edge, edge)
    if length_squared == 0:
        return start
    amount = max(0.0, min(1.0, _dot(relative, edge) / length_squared))
    return WorldPoint(start.x + edge.x * amount, start.y + edge.y * amount)


def _closest_polygon_point(point: WorldPoint, polygon: ConvexPolygonShape) -> WorldPoint:
    candidates = tuple(
        _closest_on_segment(
            point, polygon.vertices[index],
            polygon.vertices[(index + 1) % len(polygon.vertices)],
        )
        for index in range(len(polygon.vertices))
    )
    return min(candidates, key=lambda candidate: (
        (candidate.x - point.x) ** 2 + (candidate.y - point.y) ** 2,
        candidate.x, candidate.y,
    ))


def _circle_circle(first: CircleShape, second: CircleShape, obstacle_id: str) -> Contact | None:
    delta = Vector2(first.center.x - second.center.x, first.center.y - second.center.y)
    distance = delta.length
    total_radius = first.radius + second.radius
    if distance > total_radius + _EPSILON:
        return None
    normal = delta.normalized() if distance > _EPSILON else Vector2(1.0, 0.0)
    point = WorldPoint(
        first.center.x - normal.x * first.radius,
        first.center.y - normal.y * first.radius,
    )
    return Contact(obstacle_id, point, normal, max(0.0, total_radius - distance))


def _circle_polygon(circle: CircleShape, polygon: ConvexPolygonShape, obstacle_id: str) -> Contact | None:
    closest = _closest_polygon_point(circle.center, polygon)
    boundary_axis = Vector2(circle.center.x - closest.x, circle.center.y - closest.y)
    axes = list(_axes(polygon))
    if boundary_axis.length > _EPSILON:
        axes.append(boundary_axis.normalized())
    center = _centroid(polygon)
    direction = Vector2(circle.center.x - center.x, circle.center.y - center.y)
    best_depth = math.inf
    best_axis = None
    for axis in axes:
        overlap = _minimum_overlap(_project_circle(circle, axis), _project_polygon(polygon, axis))
        if overlap is None:
            return None
        if overlap < best_depth:
            best_depth, best_axis = overlap, _orient_axis(axis, direction)
    if best_axis is None:
        return None
    point = _closest_polygon_point(circle.center, polygon)
    return Contact(obstacle_id, point, best_axis, best_depth)


def _polygon_polygon(first: ConvexPolygonShape, second: ConvexPolygonShape, obstacle_id: str) -> Contact | None:
    first_center, second_center = _centroid(first), _centroid(second)
    direction = Vector2(first_center.x - second_center.x, first_center.y - second_center.y)
    best_depth = math.inf
    best_axis = None
    for axis in _axes(first) + _axes(second):
        overlap = _minimum_overlap(_project_polygon(first, axis), _project_polygon(second, axis))
        if overlap is None:
            return None
        if overlap < best_depth:
            best_depth, best_axis = overlap, _orient_axis(axis, direction)
    if best_axis is None:
        return None
    first_support = min(first.vertices, key=lambda point: point.x * best_axis.x + point.y * best_axis.y)
    second_support = max(second.vertices, key=lambda point: point.x * best_axis.x + point.y * best_axis.y)
    point = WorldPoint(
        (first_support.x + second_support.x) / 2.0,
        (first_support.y + second_support.y) / 2.0,
    )
    return Contact(obstacle_id, point, best_axis, best_depth)


def collide_shapes(first: Shape, second: Shape, obstacle_id: str) -> Contact | None:
    """Return overlap contact; normal points from second shape toward first."""
    if not isinstance(first, (CircleShape, ConvexPolygonShape)):
        raise TypeError("first must be a supported collider shape.")
    if not isinstance(second, (CircleShape, ConvexPolygonShape)):
        raise TypeError("second must be a supported collider shape.")
    if not isinstance(obstacle_id, str) or not obstacle_id.strip():
        raise ValueError("obstacle_id must be a non-empty string.")
    if isinstance(first, CircleShape) and isinstance(second, CircleShape):
        return _circle_circle(first, second, obstacle_id)
    if isinstance(first, CircleShape) and isinstance(second, ConvexPolygonShape):
        return _circle_polygon(first, second, obstacle_id)
    if isinstance(first, ConvexPolygonShape) and isinstance(second, CircleShape):
        contact = _circle_polygon(second, first, obstacle_id)
        if contact is None:
            return None
        return Contact(contact.obstacle_id, contact.point, Vector2(-contact.normal.x, -contact.normal.y), contact.penetration_depth)
    return _polygon_polygon(first, second, obstacle_id)
