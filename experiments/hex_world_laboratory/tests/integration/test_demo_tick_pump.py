import pytest

from hex_world_lab.application import DemoTickPump
from hex_world_lab.application.demo_tick_pump import (
    MAX_TICKS_PER_PUMP,
    TICK_DURATION_SECONDS,
)


class FakeClock:
    def __init__(self, value=0.0):
        self.value = value

    def __call__(self):
        return self.value

    def advance(self, seconds):
        self.value += seconds


def test_pump_requires_start_and_rejects_second_start():
    clock = FakeClock()
    pump = DemoTickPump(lambda tick: None, clock=clock)
    with pytest.raises(RuntimeError):
        pump.pump()
    pump.start()
    with pytest.raises(RuntimeError):
        pump.start()


def test_one_second_creates_sixty_ticks_but_processes_only_eight_per_call():
    clock = FakeClock()
    seen = []
    pump = DemoTickPump(seen.append, clock=clock)
    pump.start()
    clock.advance(1.0)

    diagnostics = pump.pump()
    assert seen == list(range(8))
    assert diagnostics.total_ticks == 8
    assert diagnostics.next_tick_number == 8
    assert diagnostics.last_frame_tick_count == MAX_TICKS_PER_PUMP
    assert diagnostics.pending_full_ticks == 52
    assert diagnostics.time_debt_seconds == pytest.approx(52 / 60)

    while pump.diagnostics.pending_full_ticks:
        diagnostics = pump.pump()
    assert seen == list(range(60))
    assert diagnostics.total_ticks == 60
    assert diagnostics.next_tick_number == 60
    assert diagnostics.pending_full_ticks == 0
    assert diagnostics.time_debt_seconds == pytest.approx(0.0, abs=1e-12)


def test_pending_debt_is_processed_without_new_elapsed_time():
    clock = FakeClock()
    seen = []
    pump = DemoTickPump(seen.append, clock=clock)
    pump.start()
    clock.advance(0.5)
    first = pump.pump()
    assert first.total_ticks == 8
    assert first.pending_full_ticks == 22
    second = pump.pump()
    assert second.total_ticks == 16
    assert second.pending_full_ticks == 14


def test_fractional_time_is_preserved_until_a_full_tick_exists():
    clock = FakeClock()
    seen = []
    pump = DemoTickPump(seen.append, clock=clock)
    pump.start()
    clock.advance(TICK_DURATION_SECONDS * 0.5)
    first = pump.pump()
    assert seen == []
    assert first.pending_full_ticks == 0
    assert first.time_debt_seconds == pytest.approx(TICK_DURATION_SECONDS * 0.5)

    clock.advance(TICK_DURATION_SECONDS * 0.5)
    second = pump.pump()
    assert seen == [0]
    assert second.total_ticks == 1


def test_fragmented_elapsed_time_accumulates_correctly():
    clock = FakeClock()
    seen = []
    pump = DemoTickPump(seen.append, clock=clock)
    pump.start()
    for _ in range(120):
        clock.advance(1 / 120)
        pump.pump()
    assert seen == list(range(60))


def test_callback_failure_does_not_consume_failed_tick_or_time_debt():
    clock = FakeClock()
    seen = []

    def callback(tick):
        seen.append(tick)
        if tick == 2:
            raise RuntimeError("simulated callback failure")

    pump = DemoTickPump(callback, clock=clock)
    pump.start()
    clock.advance(0.1)
    with pytest.raises(RuntimeError, match="simulated"):
        pump.pump()

    assert seen == [0, 1, 2]
    assert pump.diagnostics.total_ticks == 2
    assert pump.diagnostics.next_tick_number == 2
    assert pump.diagnostics.pending_full_ticks == 4

    # Remove the failure and retry the still-pending tick.
    pump._callback = lambda tick: seen.append(tick)
    diagnostics = pump.pump()
    assert diagnostics.total_ticks == 8
    assert diagnostics.next_tick_number == 8
    assert seen[-1] == 7


def test_pump_rejects_clock_moving_backwards_without_corrupting_state():
    clock = FakeClock(10.0)
    pump = DemoTickPump(lambda tick: None, clock=clock)
    pump.start()
    clock.value = 9.0
    with pytest.raises(ValueError, match="monotonic"):
        pump.pump()
    assert pump.diagnostics.total_ticks == 0
    clock.value = 10.0 + TICK_DURATION_SECONDS
    assert pump.pump().total_ticks == 1


@pytest.mark.parametrize("invalid", [True, "1.0", None, float("nan"), float("inf")])
def test_pump_rejects_invalid_clock_values(invalid):
    clock = FakeClock()
    pump = DemoTickPump(lambda tick: None, clock=clock)
    pump.start()
    clock.value = invalid
    with pytest.raises((TypeError, ValueError)):
        pump.pump()
    assert pump.diagnostics.total_ticks == 0


def test_pump_rejects_invalid_initial_clock_value():
    clock = FakeClock(float("nan"))
    pump = DemoTickPump(lambda tick: None, clock=clock)
    with pytest.raises(ValueError):
        pump.start()


def test_pump_supports_custom_first_tick_number():
    clock = FakeClock()
    seen = []
    pump = DemoTickPump(seen.append, clock=clock, first_tick_number=17)
    pump.start()
    clock.advance(TICK_DURATION_SECONDS)
    pump.pump()
    assert seen == [17]
    assert pump.diagnostics.next_tick_number == 18
