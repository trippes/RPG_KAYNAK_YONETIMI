"""Unit tests for camera coordinate values and world/screen transforms."""

import math

import pytest

from hex_world_lab.camera import ScreenPoint, Viewport, WorldScreenTransform
from hex_world_lab.geometry import WorldPoint


@pytest.mark.parametrize(
    ("width", "height"),
    [(1, 1), (960, 640), (1280, 720)],
)
def test_viewport_accepts_positive_integer_dimensions(width, height):
    assert Viewport(width, height) == Viewport(width, height)


@pytest.mark.parametrize(
    ("width", "height"),
    [(0, 10), (10, 0), (-1, 10), (10, -1)],
)
def test_viewport_rejects_non_positive_dimensions(width, height):
    with pytest.raises(ValueError):
        Viewport(width, height)


@pytest.mark.parametrize("value", [True, 1.5, "10"])
def test_viewport_rejects_non_integer_dimensions(value):
    with pytest.raises(TypeError):
        Viewport(value, 10)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_screen_point_rejects_non_finite_coordinates(value):
    with pytest.raises(ValueError):
        ScreenPoint(value, 0.0)


def test_screen_point_rejects_boolean_coordinates():
    with pytest.raises(TypeError):
        ScreenPoint(True, 0.0)


def test_camera_center_maps_to_viewport_center():
    transform = WorldScreenTransform(
        Viewport(960, 640), WorldPoint(12.0, -8.0), zoom=2.0
    )
    assert transform.world_to_screen(WorldPoint(12.0, -8.0)) == ScreenPoint(
        480.0, 320.0
    )


def test_positive_world_y_maps_toward_smaller_screen_y():
    transform = WorldScreenTransform(
        Viewport(800, 600), WorldPoint(0.0, 0.0), zoom=1.0
    )
    assert transform.world_to_screen(WorldPoint(0.0, 10.0)).y == 290.0
    assert transform.world_to_screen(WorldPoint(0.0, -10.0)).y == 310.0


@pytest.mark.parametrize("zoom", [0.5, 1.0, 3.0])
@pytest.mark.parametrize("viewport", [Viewport(960, 640), Viewport(1280, 720)])
def test_world_screen_round_trip(zoom, viewport):
    transform = WorldScreenTransform(
        viewport, WorldPoint(-13.25, 7.75), zoom=zoom
    )
    for point in (
        WorldPoint(0.0, 0.0),
        WorldPoint(-125.5, 73.125),
        WorldPoint(9.75, -4.5),
    ):
        actual = transform.screen_to_world(transform.world_to_screen(point))
        assert actual.x == pytest.approx(point.x)
        assert actual.y == pytest.approx(point.y)


@pytest.mark.parametrize("zoom", [0.0, -1.0, math.inf, -math.inf, math.nan])
def test_transform_rejects_invalid_zoom(zoom):
    with pytest.raises(ValueError):
        WorldScreenTransform(Viewport(800, 600), WorldPoint(0.0, 0.0), zoom)


def test_transform_rejects_wrong_argument_types():
    with pytest.raises(TypeError):
        WorldScreenTransform((800, 600), WorldPoint(0.0, 0.0))
    transform = WorldScreenTransform(
        Viewport(800, 600), WorldPoint(0.0, 0.0)
    )
    with pytest.raises(TypeError):
        transform.world_to_screen(ScreenPoint(1.0, 2.0))
    with pytest.raises(TypeError):
        transform.screen_to_world(WorldPoint(1.0, 2.0))
