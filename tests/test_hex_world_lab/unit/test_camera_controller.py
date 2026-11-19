"""Unit tests for camera state, zoom policy, and viewport updates."""

import math

import pytest

from hex_world_lab.camera import CameraController, CameraState, Viewport
from hex_world_lab.geometry import WorldPoint


def make_camera(**kwargs):
    return CameraController(Viewport(960, 640), **kwargs)


def test_camera_uses_documented_default_zoom_and_limits():
    camera = make_camera()
    assert camera.state.zoom == 1.0
    assert camera.min_zoom == 0.5
    assert camera.max_zoom == 3.0


@pytest.mark.parametrize(("requested", "expected"), [(0.1, 0.5), (0.5, 0.5), (1.75, 1.75), (3.0, 3.0), (8.0, 3.0)])
def test_set_zoom_clamps_to_inclusive_limits(requested, expected):
    camera = make_camera()
    assert camera.set_zoom(requested) == expected
    assert camera.state.zoom == expected


def test_zoom_wheel_steps_use_multiplicative_factor():
    camera = make_camera()
    assert camera.zoom_by_steps(1) == pytest.approx(1.1)
    assert camera.zoom_by_steps(1) == pytest.approx(1.21)
    assert camera.zoom_by_steps(-2) == pytest.approx(1.0)


def test_zoom_steps_stop_at_limits():
    camera = make_camera()
    assert camera.zoom_by_steps(100) == 3.0
    assert camera.zoom_by_steps(-100) == 0.5


@pytest.mark.parametrize("value", [True, "2", None])
def test_set_zoom_rejects_non_numeric_values(value):
    camera = make_camera()
    with pytest.raises(TypeError):
        camera.set_zoom(value)


@pytest.mark.parametrize("value", [math.inf, -math.inf, math.nan])
def test_set_zoom_rejects_non_finite_values(value):
    camera = make_camera()
    with pytest.raises(ValueError):
        camera.set_zoom(value)


@pytest.mark.parametrize("steps", [True, 1.5, "1"])
def test_zoom_steps_reject_non_integer_values(steps):
    camera = make_camera()
    with pytest.raises(TypeError):
        camera.zoom_by_steps(steps)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"min_zoom": 0.0},
        {"min_zoom": -1.0},
        {"min_zoom": 2.0, "max_zoom": 1.0},
        {"zoom_factor": 1.0},
        {"zoom_factor": 0.9},
        {"zoom_factor": math.inf},
    ],
)
def test_camera_rejects_invalid_zoom_configuration(kwargs):
    with pytest.raises(ValueError):
        make_camera(**kwargs)


def test_initial_zoom_is_clamped_to_configured_limits():
    camera = make_camera(zoom=9.0, min_zoom=0.75, max_zoom=2.0)
    assert camera.state.zoom == 2.0


def test_viewport_resize_preserves_world_center_and_zoom():
    center = WorldPoint(12.5, -8.25)
    camera = make_camera(center=center, zoom=1.75)
    camera.set_viewport(Viewport(1280, 720))
    assert camera.state.viewport == Viewport(1280, 720)
    assert camera.state.center == center
    assert camera.state.zoom == 1.75


def test_center_can_be_updated_without_changing_zoom_or_viewport():
    camera = make_camera(zoom=2.0)
    camera.set_center(WorldPoint(-4.0, 9.0))
    assert camera.state.center == WorldPoint(-4.0, 9.0)
    assert camera.state.zoom == 2.0
    assert camera.state.viewport == Viewport(960, 640)


def test_state_is_an_immutable_snapshot():
    camera = make_camera()
    snapshot = camera.state
    camera.set_zoom(2.0)
    assert snapshot.zoom == 1.0
    with pytest.raises(AttributeError):
        snapshot.zoom = 3.0


def test_transform_tracks_current_camera_state():
    camera = make_camera(center=WorldPoint(4.0, 5.0), zoom=2.0)
    transform = camera.transform
    assert transform.center == WorldPoint(4.0, 5.0)
    assert transform.zoom == 2.0
    camera.set_zoom(1.5)
    assert camera.transform.zoom == 1.5


def test_camera_rejects_invalid_viewport_and_center_updates():
    camera = make_camera()
    with pytest.raises(TypeError):
        camera.set_viewport((800, 600))
    with pytest.raises(TypeError):
        camera.set_center((1.0, 2.0))


def test_camera_state_rejects_invalid_components():
    with pytest.raises(TypeError):
        CameraState((0.0, 0.0), Viewport(800, 600))
    with pytest.raises(TypeError):
        CameraState(WorldPoint(0.0, 0.0), (800, 600))
