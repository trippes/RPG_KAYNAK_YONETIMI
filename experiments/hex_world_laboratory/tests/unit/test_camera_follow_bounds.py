"""Unit tests for camera follow, map bounds, and clamp policies."""

import math

import pytest

from hex_world_lab.camera import (
    CameraBoundsPolicy,
    CameraController,
    CameraFollowController,
    Viewport,
    WorldBounds,
    bounds_from_hex_cells,
    clamp_camera_center,
)
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
)


@pytest.mark.parametrize(
    ("orientation", "expected_x", "expected_y"),
    [
        (HexOrientation.FLAT_TOP, 10.0, 10.0 * math.sqrt(3.0) / 2.0),
        (HexOrientation.POINTY_TOP, 10.0 * math.sqrt(3.0) / 2.0, 10.0),
    ],
)
def test_single_hex_bounds_come_from_polygon_vertices(
    orientation, expected_x, expected_y
):
    layout = HexLayout(orientation, radius=10.0)
    bounds = bounds_from_hex_cells([AxialCoord(0, 0)], layout)
    assert bounds is not None
    assert bounds.min_x == pytest.approx(-expected_x)
    assert bounds.max_x == pytest.approx(expected_x)
    assert bounds.min_y == pytest.approx(-expected_y)
    assert bounds.max_y == pytest.approx(expected_y)


def test_bounds_cover_all_vertices_of_irregular_cell_collection():
    layout = HexLayout(HexOrientation.FLAT_TOP, radius=5.0)
    coords = [AxialCoord(-3, 1), AxialCoord(0, 0), AxialCoord(2, -2)]
    bounds = bounds_from_hex_cells(coords, layout)
    assert bounds is not None
    assert bounds.min_x == pytest.approx(-27.5)
    assert bounds.max_x == pytest.approx(20.0)
    assert bounds.min_y == pytest.approx(-12.9903810568)
    assert bounds.max_y == pytest.approx(4.3301270189)


def test_empty_hex_collection_has_no_bounds():
    assert bounds_from_hex_cells([], HexLayout(HexOrientation.FLAT_TOP)) is None


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_x": 2.0, "min_y": 0.0, "max_x": 1.0, "max_y": 1.0},
        {"min_x": 0.0, "min_y": 2.0, "max_x": 1.0, "max_y": 1.0},
        {"min_x": math.nan, "min_y": 0.0, "max_x": 1.0, "max_y": 1.0},
    ],
)
def test_world_bounds_reject_invalid_ranges(kwargs):
    with pytest.raises(ValueError):
        WorldBounds(**kwargs)


def test_world_bounds_center_is_midpoint():
    bounds = WorldBounds(-10.0, -4.0, 30.0, 8.0)
    assert bounds.center == WorldPoint(10.0, 2.0)


def test_camera_clamp_respects_viewport_world_extent():
    bounds = WorldBounds(-100.0, -50.0, 100.0, 50.0)
    center = clamp_camera_center(
        WorldPoint(100.0, -100.0), bounds, Viewport(100, 50), zoom=1.0
    )
    assert center == WorldPoint(50.0, -25.0)


def test_camera_clamp_uses_zoom_when_calculating_visible_extent():
    bounds = WorldBounds(-100.0, -100.0, 100.0, 100.0)
    center = clamp_camera_center(
        WorldPoint(100.0, 100.0), bounds, Viewport(200, 100), zoom=2.0
    )
    assert center == WorldPoint(50.0, 75.0)


def test_camera_clamp_centers_map_when_viewport_is_larger():
    bounds = WorldBounds(0.0, 0.0, 40.0, 20.0)
    center = clamp_camera_center(
        WorldPoint(100.0, -100.0), bounds, Viewport(100, 80), zoom=1.0
    )
    assert center == WorldPoint(20.0, 10.0)


def test_follow_moves_toward_target_using_exponential_damping():
    follow = CameraFollowController(smoothing=8.0)
    result = follow.update(WorldPoint(0.0, 0.0), WorldPoint(10.0, 20.0), 0.1)
    alpha = 1.0 - math.exp(-0.8)
    assert result.x == pytest.approx(10.0 * alpha)
    assert result.y == pytest.approx(20.0 * alpha)


def test_follow_is_frame_rate_independent_for_equal_elapsed_time():
    follow = CameraFollowController(smoothing=8.0)
    current_a = WorldPoint(0.0, 0.0)
    current_b = WorldPoint(0.0, 0.0)
    target = WorldPoint(100.0, -40.0)
    for _ in range(10):
        current_a = follow.update(current_a, target, 0.1)
    for _ in range(20):
        current_b = follow.update(current_b, target, 0.05)
    assert current_a.x == pytest.approx(current_b.x)
    assert current_a.y == pytest.approx(current_b.y)


def test_follow_caps_large_frame_delta():
    follow = CameraFollowController(smoothing=8.0, max_delta_seconds=0.25)
    result = follow.update(WorldPoint(0.0, 0.0), WorldPoint(10.0, 0.0), 10.0)
    expected = 10.0 * (1.0 - math.exp(-2.0))
    assert result.x == pytest.approx(expected)


def test_follow_without_target_or_elapsed_time_keeps_center():
    follow = CameraFollowController()
    current = WorldPoint(4.0, -7.0)
    assert follow.update(current, None, 1.0) == current
    assert follow.update(current, WorldPoint(9.0, 3.0), 0.0) == current


@pytest.mark.parametrize("delta", [-0.1, math.inf, math.nan])
def test_follow_rejects_invalid_delta(delta):
    with pytest.raises(ValueError):
        CameraFollowController().update(
            WorldPoint(0.0, 0.0), WorldPoint(1.0, 1.0), delta
        )


def test_controller_follows_target_without_touching_simulation_objects():
    camera = CameraController(Viewport(800, 600))
    target = WorldPoint(20.0, 10.0)
    camera.set_target(target)
    result = camera.update(0.1)
    assert result.center.x > 0.0
    assert result.center.y > 0.0
    assert result.center.x < target.x
    assert result.center.y < target.y


def test_controller_clamps_center_when_bounds_policy_is_enabled():
    bounds = WorldBounds(-100.0, -50.0, 100.0, 50.0)
    camera = CameraController(
        Viewport(100, 50),
        bounds=bounds,
        bounds_policy=CameraBoundsPolicy.CLAMP_TO_MAP,
    )
    camera.set_center(WorldPoint(100.0, 100.0))
    assert camera.state.center == WorldPoint(50.0, 25.0)


def test_controller_reapplies_bounds_after_zoom_and_resize():
    bounds = WorldBounds(-100.0, -100.0, 100.0, 100.0)
    camera = CameraController(
        Viewport(100, 100),
        bounds=bounds,
        bounds_policy=CameraBoundsPolicy.CLAMP_TO_MAP,
    )
    camera.set_center(WorldPoint(100.0, 100.0))
    camera.set_zoom(0.5)
    assert camera.state.center == WorldPoint(0.0, 0.0)
    camera.set_viewport(Viewport(40, 40))
    camera.set_center(WorldPoint(100.0, 100.0))
    assert camera.state.center == WorldPoint(60.0, 60.0)


def test_unbounded_camera_policy_does_not_clamp_world_center():
    bounds = WorldBounds(-10.0, -10.0, 10.0, 10.0)
    camera = CameraController(
        Viewport(800, 600),
        bounds=bounds,
        bounds_policy=CameraBoundsPolicy.UNBOUNDED,
    )
    camera.set_center(WorldPoint(500.0, -300.0))
    assert camera.state.center == WorldPoint(500.0, -300.0)


def test_clamp_policy_requires_bounds():
    with pytest.raises(ValueError):
        CameraController(
            Viewport(800, 600),
            bounds_policy=CameraBoundsPolicy.CLAMP_TO_MAP,
        )


def test_switching_to_unbounded_policy_preserves_requested_center():
    bounds = WorldBounds(-10.0, -10.0, 10.0, 10.0)
    camera = CameraController(
        Viewport(10, 10),
        bounds=bounds,
        bounds_policy=CameraBoundsPolicy.CLAMP_TO_MAP,
    )
    camera.set_bounds(bounds, CameraBoundsPolicy.UNBOUNDED)
    camera.set_center(WorldPoint(500.0, 500.0))
    assert camera.state.center == WorldPoint(500.0, 500.0)
