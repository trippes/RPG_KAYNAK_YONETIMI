import pytest

from hex_world_lab.application import DemoTickPump
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementConfig, MovementIntent, MovementState, Vector2
from hex_world_lab.simulation import MovementSystem


class FakeClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self):
        return self.value


@pytest.mark.parametrize("render_fps", [30, 60, 120])
def test_same_one_second_tick_sequence_is_render_fps_independent(render_fps):
    clock = FakeClock()
    system = MovementSystem(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementConfig(max_speed=120.0),
    )
    received = []
    pump = DemoTickPump(
        lambda tick: (
            received.append(tick),
            system.step(tick, MovementIntent(Vector2(1.0, 0.0))),
        ),
        clock=clock,
    )
    pump.start()

    for _ in range(render_fps):
        clock.value += 1.0 / render_fps
        pump.pump()

    while pump.diagnostics.pending_full_ticks:
        pump.pump()

    assert received == list(range(60))
    assert system.next_tick_number == 60
    assert system.state.position.x == pytest.approx(120.0)
    assert system.state.position.y == pytest.approx(0.0)
    assert pump.diagnostics.total_ticks == 60


def test_pump_and_movement_system_process_each_tick_once():
    clock = FakeClock()
    system = MovementSystem(
        MovementState(WorldPoint(3.0, -2.0)),
        MovementConfig(max_speed=60.0),
    )
    pump = DemoTickPump(
        lambda tick: system.step(tick, MovementIntent(Vector2(0.0, 1.0))),
        clock=clock,
    )
    pump.start()
    clock.value = 1.0
    while pump.diagnostics.pending_full_ticks or pump.diagnostics.total_ticks == 0:
        pump.pump()
    assert system.state.position == WorldPoint(3.0, 58.0)
    assert system.next_tick_number == 60
