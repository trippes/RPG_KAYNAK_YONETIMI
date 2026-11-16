"""Headless rendering tests for the movement demo."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from hex_world_lab.application.movement_demo import MovementDemo


def test_render_draws_scene_without_mutating_simulation_state() -> None:
    pygame.init()
    try:
        demo = MovementDemo()
        surface = pygame.Surface((960, 640))
        state_before = demo.state
        tracker_before = demo.current_resolution
        tick_before = demo.tick_pump.diagnostics

        demo.render(surface, 60.0)

        assert demo.state == state_before
        assert demo.current_resolution == tracker_before
        assert demo.tick_pump.diagnostics == tick_before
        assert surface.get_at((480, 328))[:3] != (21, 25, 34)
    finally:
        pygame.quit()
