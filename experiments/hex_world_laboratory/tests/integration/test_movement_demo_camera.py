"""Camera, viewport, rendering, and mouse-picking integration tests."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.camera import ScreenPoint, Viewport
from hex_world_lab.geometry import AxialCoord, WorldPoint, axial_to_world


def test_mouse_wheel_changes_zoom_with_documented_factor():
    pygame.init()
    try:
        demo = MovementDemo()
        demo.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=1, x=0))
        assert demo.camera.state.zoom == pytest.approx(1.1)
        demo.handle_event(pygame.event.Event(pygame.MOUSEWHEEL, y=-2, x=0))
        assert demo.camera.state.zoom == pytest.approx(1.0 / 1.1)
    finally:
        pygame.quit()


def test_mouse_click_picks_cell_using_camera_inverse_transform():
    pygame.init()
    try:
        demo = MovementDemo()
        coord = AxialCoord(1, 0)
        world = axial_to_world(coord, demo._layout)
        screen = demo.camera.transform.world_to_screen(world)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=(round(screen.x), round(screen.y)),
        )
        demo.handle_event(event)
        assert demo.selected_cell == coord
    finally:
        pygame.quit()


def test_mouse_click_outside_loaded_cells_clears_selection():
    pygame.init()
    try:
        demo = MovementDemo()
        demo.selected_cell = AxialCoord(0, 0)
        world = axial_to_world(AxialCoord(20, 0), demo._layout)
        screen = demo.camera.transform.world_to_screen(world)
        event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN,
            button=1,
            pos=(round(screen.x), round(screen.y)),
        )
        demo.handle_event(event)
        assert demo.selected_cell is None
    finally:
        pygame.quit()


def test_viewport_resize_event_updates_camera_transform():
    pygame.init()
    try:
        demo = MovementDemo()
        demo.handle_event(
            pygame.event.Event(
                pygame.VIDEORESIZE,
                size=(1280, 720),
                w=1280,
                h=720,
            )
        )
        assert demo.camera.state.viewport == Viewport(1280, 720)
        assert demo.camera.transform.world_to_screen(WorldPoint(0.0, 0.0)) == ScreenPoint(
            640.0, 360.0
        )
    finally:
        pygame.quit()


def test_camera_follow_tracks_actor_without_advancing_simulation():
    from hex_world_lab.movement import MovementIntent, Vector2

    pygame.init()
    try:
        demo = MovementDemo()
        demo.movement_system.step(
            0,
            MovementIntent(direction=Vector2(1.0, 0.0)),
        )
        actor_position = demo.state.position
        ticks_before = demo.tick_pump.diagnostics
        camera_before = demo.camera.state.center

        demo.update_camera(0.1)

        assert demo.camera.state.center.x > camera_before.x
        assert demo.camera.state.center.x < actor_position.x
        assert demo.state.position == actor_position
        assert demo.tick_pump.diagnostics == ticks_before
    finally:
        pygame.quit()


def test_renderer_uses_camera_transform_for_actor_and_keeps_world_state():
    pygame.init()
    try:
        demo = MovementDemo()
        demo.camera.set_center(WorldPoint(-10.0, 0.0))
        demo.camera.set_zoom(2.0)
        surface = pygame.Surface((960, 640))
        state_before = demo.state
        ticks_before = demo.tick_pump.diagnostics
        transform = demo.camera.transform
        actor_screen = transform.world_to_screen(demo.state.position)

        demo.render(surface, 60.0)

        actor_pixel = (round(actor_screen.x), round(actor_screen.y))
        assert surface.get_at(actor_pixel)[:3] == (231, 93, 83)
        assert demo.state == state_before
        assert demo.tick_pump.diagnostics == ticks_before
    finally:
        pygame.quit()


def test_render_snapshot_contains_world_space_geometry_only():
    pygame.init()
    try:
        demo = MovementDemo()
        snapshot = demo.build_render_snapshot()
        assert len(snapshot.cells) == 61
        # Environment colliders are represented in F3 debug DTOs, not as
        # duplicate visible circles/polygons in the normal scene.
        assert len(snapshot.circles) == 0
        assert len(snapshot.polygons) >= 1
        assert {item.owner_id for item in snapshot.colliders} >= {"object:tree", "object:rock"}
        assert {item.instance_id for item in snapshot.environment_debug} == {"tree", "rock", "bush"}
        assert len(snapshot.house_lines) > 0
        assert snapshot.actor_position == demo.state.position
    finally:
        pygame.quit()
