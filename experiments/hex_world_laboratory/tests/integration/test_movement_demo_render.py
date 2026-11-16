"""Headless rendering and diagnostics tests for the movement demo."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.movement import MovementIntent, MovementMode, Vector2


class RecordingFont:
    def __init__(self):
        self.rendered = []

    def size(self, text):
        return (len(text) * 7, 12)

    def render(self, text, antialias, color):
        self.rendered.append(text)
        return pygame.Surface((1, 1), pygame.SRCALPHA)


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


@pytest.mark.parametrize(
    ("mode", "expected_mode", "expected_multiplier", "expected_speed"),
    [
        (MovementMode.NORMAL, "Mode: NORMAL", "Multiplier: 1.00x", "Mode speed: 40.0"),
        (MovementMode.RUNNING, "Mode: RUNNING", "Multiplier: 1.50x", "Mode speed: 60.0"),
        (MovementMode.STEALTH, "Mode: STEALTH", "Multiplier: 0.50x", "Mode speed: 20.0"),
    ],
)
def test_diagnostics_show_mode_multiplier_and_configured_speed(
    mode, expected_mode, expected_multiplier, expected_speed
):
    pygame.init()
    try:
        demo = MovementDemo(movement_speed=40.0)
        demo.movement_system.step(0, MovementIntent(mode=mode))
        recorder = RecordingFont()
        demo._font = recorder
        demo._small_font = recorder

        demo._draw_diagnostics(pygame.Surface((960, 640)), 60.0)

        assert expected_mode in recorder.rendered
        assert any(expected_multiplier in line for line in recorder.rendered)
        assert any(expected_speed in line for line in recorder.rendered)
        velocity_line = next(line for line in recorder.rendered if line.startswith("Velocity:"))
        assert "speed=0.00" in velocity_line
    finally:
        pygame.quit()


def test_diagnostics_keep_actual_velocity_separate_from_mode_speed():
    pygame.init()
    try:
        demo = MovementDemo(movement_speed=40.0)
        demo.movement_system.step(
            0,
            MovementIntent(
                direction=Vector2(1.0, 0.0),
                mode=MovementMode.RUNNING,
            ),
        )
        recorder = RecordingFont()
        demo._font = recorder
        demo._small_font = recorder

        demo._draw_diagnostics(pygame.Surface((960, 640)), 60.0)

        velocity_line = next(line for line in recorder.rendered if line.startswith("Velocity:"))
        mode_line = next(line for line in recorder.rendered if line.startswith("Multiplier:"))
        assert "speed=60.00" in velocity_line
        assert "Mode speed: 60.0" in mode_line
    finally:
        pygame.quit()
