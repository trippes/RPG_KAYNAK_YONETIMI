"""Tests for exact convex narrowphase contact queries."""

import pytest

from hex_world_lab.geometry import (
    AxialCoord, HexLayout, HexOrientation, WorldPoint, hex_polygon,
)
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics.contacts import Contact, ContactManifold
from hex_world_lab.physics.narrowphase import collide_shapes
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape


def square(half=1.0):
    return ConvexPolygonShape((
        Vector2(-half, -half), Vector2(half, -half),
        Vector2(half, half), Vector2(-half, half),
    ))


def test_circle_circle_overlap_reports_normal_point_and_depth():
    contact = collide_shapes(CircleShape(1, Vector2(1.5, 0)), CircleShape(1), "rock")
    assert contact is not None
    assert contact.normal == Vector2(1, 0)
    assert contact.point == WorldPoint(0.5, 0)
    assert contact.penetration_depth == pytest.approx(0.5)


def test_circle_circle_separation_and_tangent_cases():
    assert collide_shapes(CircleShape(1, Vector2(2.01, 0)), CircleShape(1), "rock") is None
    tangent = collide_shapes(CircleShape(1, Vector2(2, 0)), CircleShape(1), "rock")
    assert tangent is not None and tangent.penetration_depth == 0


def test_circle_polygon_face_contact_points_from_polygon_to_circle():
    contact = collide_shapes(CircleShape(0.5, Vector2(1.2, 0)), square(), "wall")
    assert contact is not None
    assert contact.normal.x == pytest.approx(1)
    assert contact.normal.y == pytest.approx(0)
    assert contact.point == WorldPoint(1, 0)
    assert contact.penetration_depth == pytest.approx(0.3)


def test_circle_inside_polygon_gets_exit_depth_not_interval_intersection_length():
    contact = collide_shapes(CircleShape(0.5), square(), "wall")
    assert contact is not None
    assert contact.penetration_depth == pytest.approx(1.5)


def test_circle_polygon_vertex_contact_is_detected():
    contact = collide_shapes(CircleShape(0.5, Vector2(1.3, 1.3)), square(), "corner")
    assert contact is not None
    assert contact.normal.x == pytest.approx(2 ** -0.5)
    assert contact.normal.y == pytest.approx(2 ** -0.5)


def test_polygon_circle_reverses_contact_normal():
    circle = CircleShape(0.5, Vector2(1.2, 0))
    forward = collide_shapes(circle, square(), "wall")
    reverse = collide_shapes(square(), circle, "wall")
    assert forward is not None and reverse is not None
    assert reverse.normal == Vector2(-forward.normal.x, -forward.normal.y)
    assert reverse.penetration_depth == forward.penetration_depth


def test_polygon_polygon_sat_detects_overlap_and_separation():
    shifted = ConvexPolygonShape(tuple(
        Vector2(point.x + 1.5, point.y) for point in square().vertices
    ))
    overlap = collide_shapes(square(), shifted, "block")
    assert overlap is not None
    assert overlap.penetration_depth == pytest.approx(0.5)

    first = ConvexPolygonShape((Vector2(0, 0), Vector2(2, 0), Vector2(0, 2)))
    second = ConvexPolygonShape((
        Vector2(1.5, 1.5), Vector2(2.5, 1.5), Vector2(1.5, 2.5),
    ))
    assert collide_shapes(first, second, "triangle") is None


@pytest.mark.parametrize("orientation", [HexOrientation.FLAT_TOP, HexOrientation.POINTY_TOP])
def test_circle_contact_against_real_hex_polygon_in_both_layouts(orientation):
    layout = HexLayout(orientation, radius=2.0, origin=WorldPoint(0, 0))
    vertices = hex_polygon(AxialCoord(0, 0), layout)
    polygon = ConvexPolygonShape(tuple(Vector2(point.x, point.y) for point in vertices))
    contact = collide_shapes(CircleShape(0.5), polygon, "hex")
    assert contact is not None
    assert contact.penetration_depth > 0
    assert contact.normal.length == pytest.approx(1.0)


def test_contact_and_manifold_validate_and_sort_deterministically():
    a = Contact("b", WorldPoint(1, 0), Vector2(1, 0), 0.1)
    b = Contact("a", WorldPoint(0, 0), Vector2(0, 1), 0.2)
    assert ContactManifold((a, b)).contacts == (b, a)
    with pytest.raises(ValueError, match="normalized"):
        Contact("bad", WorldPoint(0, 0), Vector2(2, 0), 0.1)
    with pytest.raises(ValueError, match="non-negative"):
        Contact("bad", WorldPoint(0, 0), Vector2(1, 0), -0.1)


def test_invalid_shape_inputs_are_rejected():
    with pytest.raises(TypeError):
        collide_shapes("circle", square(), "wall")
    with pytest.raises(ValueError):
        collide_shapes(CircleShape(1), square(), "")
