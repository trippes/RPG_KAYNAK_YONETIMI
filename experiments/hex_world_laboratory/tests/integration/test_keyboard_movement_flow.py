"""Integration tests for keyboard input flowing through simulation ticks."""

import pygame
import pytest

from hex_world_lab.application import DemoTickPump
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.input import PygameKeyboardAdapter
from hex_world_lab.movement import MovementConfig, MovementState
from hex_world_lab.simulation import MovementSystem


class FakeClock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


class FakeKeys:
    def __init__(self):
        self.pressed = set()

    def __getitem__(self, key):
        return key in self.pressed


def test_tick_pump_samples_keyboard_and_advances_movement_each_tick():
    clock = FakeClock()
    keys = FakeKeys()
    adapter = PygameKeyboardAdapter(lambda: keys)
    movement = MovementSystem(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementConfig(max_speed=60.0),
    )

    def on_tick(tick_number):
        if tick_number < 3:
            keys.pressed = {pygame.K_d}
        else:
            keys.pressed = set()
        movement.step(tick_number, adapter.read_intent())

    pump = DemoTickPump(on_tick, clock=clock)
    pump.start()
    clock.advance(1.0 / 10.0)

    while pump.diagnostics.pending_full_ticks or pump.diagnostics.total_ticks < 6:
        pump.pump()

    assert pump.diagnostics.total_ticks == 6
    assert movement.next_tick_number == 6
    assert movement.state.position.x == pytest.approx(3.0)
    assert movement.state.position.y == pytest.approx(0.0)
    assert movement.state.velocity.x == 0.0
    assert movement.state.velocity.y == 0.0


def test_focus_loss_stops_movement_on_next_simulation_tick():
    clock = FakeClock()
    keys = FakeKeys()
    keys.pressed = {pygame.K_w}
    adapter = PygameKeyboardAdapter(lambda: keys)
    movement = MovementSystem(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementConfig(max_speed=60.0),
    )

    def on_tick(tick_number):
        if tick_number == 1:
            adapter.handle_event(pygame.event.Event(pygame.WINDOWFOCUSLOST))
        movement.step(tick_number, adapter.read_intent())

    pump = DemoTickPump(on_tick, clock=clock)
    pump.start()
    clock.advance(3.0 / 60.0)
    pump.pump()

    assert movement.state.position.y == pytest.approx(1.0)
    assert movement.state.velocity == movement.state.velocity.__class__(0.0, 0.0)
