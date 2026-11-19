"""Exact convex-shape overlap tests and deterministic contact generation."""

import math

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2

from .contacts import Contact
from .shapes import CircleShape, ConvexPolygonShape


_EPSILON = 1e-10


def _dot(a: Vector2, b: Vector2) -> float:
    return a.x * b.x + a.y * b.y


def _subtract(a: Vector2, b: Vector2) -> Vector2:
    return Vector2(a.x - b.x, a.y - b.y)


def _centroid(shape: ConvexPolygonShape) -> Vector2:
    count = len(shape.vertices)
    return Vector2(
        sum(point.x for point in shape.vertices) / count,
        sum(point.y for point in shape.vertices) / count,
    )


def _axes(shape: ConvexPolygonShape) -> tuple[Vector2, ...]:
    result = []
    vertices = shape.vertices
    for index, start in enumerate(vertices):
        end = vertices[(index + 1) % len(vertices)]
        edge = Vector2(end.x - start.x, end.y - start.y)
        result.append(Vector2(-edge.y, edge.x).normalized())
    return tuple(result)


def _project_polygon(shape: ConvexPolygonShape, axis: Vector2) -> tuple[float, float]:
    values = tuple(_dot(point, axis) for point in shape.vertices)
    return min(values), max(values)


def _project_circle(shape: CircleShape, axis: Vector2) -> tuple[float, float]:
    center = _dot(shape.center, axis)
    return center - shape.radius, center + shape.radius


def _minimum_overlap(
    first: tuple[float, float], second: tuple[float, float]
) -> float | None:
    if first[1] < second[0] - _EPSILON or second[1] < first[0] - _EPSILON:
        return None
    # Correctly handles containment; simple interval intersection length does not.
    return max(0.0, min(first[1] - second[0], second[1] - first[0]))


def _orient_axis(axis: Vector2, from_second_to_first: Vector2) -> Vector2:
    direction = _dot(axis, from_second_to_first)
    if direction < -_EPSILON:
        return Vector2(-axis.x, -axis.y)
    if abs(direction) <= _EPSILON:
        # Stable tie-break for coincident shape centers.
        if axis.x < -_EPSILON or (abs(axis.x) <= _EPSILON and axis.y < 0):
            return Vector2(-axis.x, -axis.y)
    return axis


def _closest_on_segment(point: Vector2, start: Vector2, end: Vector2) -> Vector2:
    edge = _subtract(end, start)
    length_squared = _dot(edge, edge)
    if length_squared == 0:
        return start
    relative = _subtract(point, start)
    amount = max(0.0, min(1.0, _dot(relative, edge) / length_squared))
    return Vector2(start.x + edge.x * amount, start.y + edge.y * amount)


def _closest_polygon_point(
    point: Vector2, polygon: ConvexPolygonShape
) -> Vector2:
    candidates = tuple(
        _closest_on_segment(
            point, polygon.vertices[index],
            polygon.vertices[(index + 1) % len(polygon.vertices)],
        )
        for index in range(len(polygon.vertices))
    )
    return min(
        candidates,
        key=lambda candidate: (
            (candidate.x - point.x) ** 2 + (candidate.y - point.y) ** 2,
            candidate.x, candidate.y,
        ),
    )


def _circle_circle(
    first: CircleShape, second: CircleShape, obstacle_id: str
) -> Contact | None:
    delta = Vector2(first.center.x - second.center.x, first.center.y - second.center.y)
    distance = delta.length
    total_radius = first.radius + second.radius
    if distance > total_radius + _EPSILON:
        return None
    normal = delta.normalized() if distance > _EPSILON else Vector2(1.0, 0.0)
    point = Vector2(
        first.center.x - normal.x * first.radius,
        first.center.y - normal.y * first.radius,
    )
    return Contact(
        obstacle_id, WorldPoint(point.x, point.y), normal,
        max(0.0, total_radius - distance),
    )


def _circle_polygon(
    circle: CircleShape, polygon: ConvexPolygonShape, obstacle_id: str
) -> Contact | None:
    closest_boundary_point = _closest_polygon_point(circle.center, polygon)
    boundary_axis = Vector2(
        circle.center.x - closest_boundary_point.x,
        circle.center.y - closest_boundary_point.y,
    )
    axes = list(_axes(polygon))
    if boundary_axis.length > _EPSILON:
        axes.append(boundary_axis.normalized())

    polygon_center = _centroid(polygon)
    direction = Vector2(
        circle.center.x - polygon_center.x,
        circle.center.y - polygon_center.y,
    )
    best_depth = math.inf
    best_axis: Vector2 | None = None
    for axis in axes:
        overlap = _minimum_overlap(
            _project_circle(circle, axis), _project_polygon(polygon, axis)
        )
        if overlap is None:
            return None
        if overlap < best_depth:
            best_depth = overlap
            best_axis = _orient_axis(axis, direction)

    assert best_axis is not None
    point = _closest_polygon_point(circle.center, polygon)
    return Contact(
        obstacle_id, WorldPoint(point.x, point.y), best_axis, best_depth
    )


def _polygon_polygon(
    first: ConvexPolygonShape, second: ConvexPolygonShape, obstacle_id: str
) -> Contact | None:
    first_center, second_center = _centroid(first), _centroid(second)
    direction = Vector2(
        first_center.x - second_center.x, first_center.y - second_center.y
    )
    best_depth = math.inf
    best_axis: Vector2 | None = None
    for axis in _axes(first) + _axes(second):
        overlap = _minimum_overlap(
            _project_polygon(first, axis), _project_polygon(second, axis)
        )
        if overlap is None:
            return None
        if overlap < best_depth:
            best_depth = overlap
            best_axis = _orient_axis(axis, direction)

    assert best_axis is not None
    first_support = min(
        first.vertices, key=lambda point: _dot(point, best_axis)
    )
    second_support = max(
        second.vertices, key=lambda point: _dot(point, best_axis)
    )
    point = Vector2(
        (first_support.x + second_support.x) / 2.0,
        (first_support.y + second_support.y) / 2.0,
    )
    return Contact(
        obstacle_id, WorldPoint(point.x, point.y), best_axis, best_depth
    )


def collide_shapes(
    first: CircleShape | ConvexPolygonShape,
    second: CircleShape | ConvexPolygonShape,
    obstacle_id: str,
) -> Contact | None:
    """Return one overlap contact; its normal points from second toward first.

    Touching shapes return a zero-depth contact. AABB overlap alone is not enough
    to produce a contact.
    """
    if not isinstance(first, (CircleShape, ConvexPolygonShape)):
        raise TypeError("first must be a supported collider shape")
    if not isinstance(second, (CircleShape, ConvexPolygonShape)):
        raise TypeError("second must be a supported collider shape")
    if not isinstance(obstacle_id, str) or not obstacle_id.strip():
        raise ValueError("obstacle_id must be a non-empty string")
    if isinstance(first, CircleShape) and isinstance(second, CircleShape):
        return _circle_circle(first, second, obstacle_id)
    if isinstance(first, CircleShape) and isinstance(second, ConvexPolygonShape):
        return _circle_polygon(first, second, obstacle_id)
    if isinstance(first, ConvexPolygonShape) and isinstance(second, CircleShape):
        contact = _circle_polygon(second, first, obstacle_id)
        if contact is None:
            return None
        return Contact(
            contact.obstacle_id,
            contact.point,
            Vector2(-contact.normal.x, -contact.normal.y),
            contact.penetration_depth,
        )
    assert isinstance(first, ConvexPolygonShape)
    assert isinstance(second, ConvexPolygonShape)
    return _polygon_polygon(first, second, obstacle_id)
