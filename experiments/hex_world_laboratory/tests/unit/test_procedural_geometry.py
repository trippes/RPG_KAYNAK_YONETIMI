import math

import pytest

from hex_world_lab.rendering.procedural.geometry import Bounds2D, Point2D, Transform2D


def test_point_rejects_non_finite_and_boolean_coordinates():
    with pytest.raises(ValueError):
        Point2D(float("nan"), 0)
    with pytest.raises(ValueError):
        Point2D(0, float("inf"))
    with pytest.raises(TypeError):
        Point2D(True, 0)


def test_bounds_contains_boundary_and_unions_bounds():
    bounds = Bounds2D(-2, -1, 3, 4)
    assert bounds.width == 5
    assert bounds.height == 5
    assert bounds.contains(Point2D(-2, 4))
    assert not bounds.contains(Point2D(3.01, 0))
    assert bounds.union(Bounds2D(2, -5, 8, 1)) == Bounds2D(-2, -5, 8, 4)


def test_bounds_can_be_built_from_points_and_rejects_empty_input():
    assert Bounds2D.from_points((Point2D(3, 4), Point2D(-1, 2))) == Bounds2D(-1, 2, 3, 4)
    with pytest.raises(ValueError):
        Bounds2D.from_points(())


def test_transform_scales_then_rotates_then_translates():
    transform = Transform2D(translate_x=10, translate_y=20, scale_x=2, scale_y=3,
                            rotation_radians=math.pi / 2)
    result = transform.apply(Point2D(1, 2))
    assert result.x == pytest.approx(4)
    assert result.y == pytest.approx(22)


def test_transform_rejects_zero_scale_and_non_finite_rotation():
    with pytest.raises(ValueError):
        Transform2D(scale_x=0)
    with pytest.raises(ValueError):
        Transform2D(rotation_radians=float("nan"))
