"""Headless end-to-end tests for the movement acceptance demo."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.geometry import AxialCoord, WorldPoint


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def key_provider(*pressed: int):
    active = set(pressed)
    return lambda: _PressedKeys(active)


class _PressedKeys:
    def __init__(self, active: set[int]) -> None:
        self.active = active

    def __getitem__(self, key: int) -> bool:
        return key in self.active


def test_keyboard_tick_movement_and_cell_tracking_are_connected() -> None:
    pygame.init()
    try:
        clock = FakeClock()
        keys = {pygame.K_d}
        demo = MovementDemo(
            movement_speed=60.0,
            key_state_provider=lambda: _PressedKeys(keys),
            clock=clock,
        )
        demo.start()
        clock.advance(1.0 / 60.0)
        diagnostics = demo.pump()

        assert diagnostics.total_ticks == 1
        assert demo.state.position.x == 1.0
        assert demo.state.position.y == 0.0
        assert demo.current_resolution is not None
        assert demo.current_resolution.coord == AxialCoord(0, 0)
        assert demo.current_resolution.cell_data is not None

        keys.clear()
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position.x == 1.0
        assert demo.state.velocity.x == 0.0
    finally:
        pygame.quit()


def test_focus_loss_produces_neutral_intent_for_following_tick() -> None:
    pygame.init()
    try:
        clock = FakeClock()
        keys = {pygame.K_d}
        demo = MovementDemo(
            movement_speed=60.0,
            key_state_provider=lambda: _PressedKeys(keys),
            clock=clock,
        )
        demo.start()
        clock.advance(1.0 / 60.0)
        demo.pump()
        before = demo.state.position

        demo.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position == before
        assert demo.state.velocity.x == 0.0
    finally:
        pygame.quit()


def test_movement_can_continue_beyond_the_explicit_map_cell_set() -> None:
    pygame.init()
    try:
        clock = FakeClock()
        demo = MovementDemo(
            movement_speed=600.0,
            key_state_provider=lambda: _PressedKeys({pygame.K_d}),
            clock=clock,
        )
        demo.start()
        for _ in range(7):
            clock.advance(1.0 / 60.0)
            demo.pump()

        assert demo.state.position.x > 128.0
        assert demo.current_resolution is not None
        assert demo.current_resolution.cell_data is None
    finally:
        pygame.quit()


def test_cell_tracker_does_not_snap_physical_position() -> None:
    pygame.init()
    try:
        clock = FakeClock()
        demo = MovementDemo(
            movement_speed=60.0,
            key_state_provider=lambda: _PressedKeys({pygame.K_d}),
            clock=clock,
        )
        demo.start()
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position == WorldPoint(1.0, 0.0)
    finally:
        pygame.quit()
