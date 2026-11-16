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
        for _ in range(24):
            clock.advance(1.0 / 60.0)
            demo.pump()

        assert demo.state.position.x > 224.0
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


def test_movement_modes_flow_through_demo_ticks_without_position_snapping() -> None:
    from hex_world_lab.movement import MovementMode

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
        assert demo.state.position.x == 1.0
        assert demo.state.mode is MovementMode.NORMAL

        keys.add(pygame.K_LSHIFT)
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position.x == 2.5
        assert demo.state.mode is MovementMode.RUNNING
        assert demo.state.velocity.x == 90.0

        keys.add(pygame.K_LALT)
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position.x == 3.0
        assert demo.state.mode is MovementMode.STEALTH
        assert demo.state.velocity.x == 30.0

        keys.clear()
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position.x == 3.0
        assert demo.state.mode is MovementMode.STEALTH
        assert demo.state.velocity.x == 0.0

        keys.add(pygame.K_LALT)
        clock.advance(1.0 / 60.0)
        demo.pump()
        assert demo.state.position.x == 3.0
        assert demo.state.mode is MovementMode.NORMAL
        assert demo.state.velocity.x == 0.0
        assert demo.current_resolution is not None
        assert demo.current_resolution.coord is not None
    finally:
        pygame.quit()



def test_cell_boundary_crossing_remains_continuous_across_movement_modes() -> None:
    from hex_world_lab.movement import MovementMode

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

        positions: list[float] = []
        cells: list[AxialCoord] = []

        def tick() -> None:
            clock.advance(1.0 / 60.0)
            demo.pump()
            positions.append(demo.state.position.x)
            assert demo.current_resolution is not None
            cells.append(demo.current_resolution.coord)

        # Ten normal ticks move to x=10, safely inside the starting cell.
        for _ in range(10):
            tick()
        assert demo.state.mode is MovementMode.NORMAL
        assert cells[-1] == AxialCoord(0, 0)

        # Ten running ticks move from x=10 to x=25, across the
        # shared boundary at x=24 into axial cell (1, 0).
        keys.add(pygame.K_LSHIFT)
        for _ in range(10):
            tick()
        assert demo.state.mode is MovementMode.RUNNING
        assert cells[-1] == AxialCoord(1, 0)

        # Stealth changes speed only; it must not snap the physical position.
        keys.add(pygame.K_LALT)
        for _ in range(2):
            tick()
        assert demo.state.mode is MovementMode.STEALTH
        assert cells[-1] == AxialCoord(1, 0)

        assert positions[:10] == [float(value) for value in range(1, 11)]
        assert positions[10:20] == [
            10.0 + 1.5 * value for value in range(1, 11)
        ]
        assert positions[20:] == [25.5, 26.0]
        assert all(
            later > earlier
            for earlier, later in zip(positions, positions[1:])
        )
        assert demo.state.position == WorldPoint(26.0, 0.0)
    finally:
        pygame.quit()


def test_shift_and_alt_toggle_interaction_flows_through_demo_ticks() -> None:
    from hex_world_lab.movement import MovementMode

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

        def tick() -> None:
            clock.advance(1.0 / 60.0)
            demo.pump()

        tick()
        assert demo.state.mode is MovementMode.NORMAL
        assert demo.state.position.x == 1.0

        keys.add(pygame.K_LSHIFT)
        tick()
        assert demo.state.mode is MovementMode.RUNNING
        assert demo.state.velocity.x == 90.0
        assert demo.state.position.x == 2.5

        keys.add(pygame.K_LALT)
        tick()
        assert demo.state.mode is MovementMode.STEALTH
        assert demo.state.velocity.x == 30.0
        assert demo.state.position.x == 3.0

        # Releasing Alt does not turn stealth off; Shift remains held.
        keys.remove(pygame.K_LALT)
        tick()
        assert demo.state.mode is MovementMode.STEALTH
        assert demo.state.velocity.x == 30.0
        assert demo.state.position.x == 3.5

        # A second Alt press toggles stealth off; held Shift resumes running.
        keys.add(pygame.K_LALT)
        tick()
        assert demo.state.mode is MovementMode.RUNNING
        assert demo.state.velocity.x == 90.0
        assert demo.state.position.x == 5.0

        keys.remove(pygame.K_LALT)
        keys.remove(pygame.K_LSHIFT)
        tick()
        assert demo.state.mode is MovementMode.NORMAL
        assert demo.state.velocity.x == 60.0
        assert demo.state.position.x == 6.0
    finally:
        pygame.quit()


def test_focus_loss_and_regain_do_not_fake_toggle_held_alt_in_demo() -> None:
    from hex_world_lab.movement import MovementMode

    pygame.init()
    try:
        clock = FakeClock()
        keys = {pygame.K_d, pygame.K_LALT}
        demo = MovementDemo(
            movement_speed=60.0,
            key_state_provider=lambda: _PressedKeys(keys),
            clock=clock,
        )
        demo.start()

        def tick() -> None:
            clock.advance(1.0 / 60.0)
            demo.pump()

        tick()
        assert demo.state.mode is MovementMode.STEALTH
        assert demo.state.position == WorldPoint(0.5, 0.0)

        demo.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        tick()
        assert demo.state.mode is MovementMode.NORMAL
        assert demo.state.velocity.x == 0.0
        assert demo.state.position == WorldPoint(0.5, 0.0)

        # Alt is still physically held, but remove movement before focus returns.
        keys.remove(pygame.K_d)
        demo.handle_event(pygame.event.Event(pygame.WINDOWFOCUSGAINED))
        tick()
        assert demo.state.mode is MovementMode.NORMAL
        assert demo.state.velocity.x == 0.0
        assert demo.state.position == WorldPoint(0.5, 0.0)

        # A release followed by a fresh press is a genuine new Alt edge.
        keys.remove(pygame.K_LALT)
        tick()
        assert demo.state.mode is MovementMode.NORMAL

        keys.add(pygame.K_d)
        keys.add(pygame.K_LALT)
        tick()
        assert demo.state.mode is MovementMode.STEALTH
        assert demo.state.velocity.x == 30.0
        assert demo.state.position == WorldPoint(1.0, 0.0)
    finally:
        pygame.quit()
