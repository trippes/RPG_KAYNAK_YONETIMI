import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementConfig, MovementIntent, MovementState, Vector2
from hex_world_lab.simulation import MovementSystem
from hex_world_lab.simulation.movement_system import TICK_DELTA_SECONDS


def make_system(*, first_tick_number=0):
    initial = MovementState(WorldPoint(0.0, 0.0))
    return MovementSystem(
        initial,
        MovementConfig(max_speed=60.0),
        first_tick_number=first_tick_number,
    )


def test_system_accepts_default_first_tick_and_advances_once():
    system = make_system()
    result = system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    assert result.position == WorldPoint(1.0, 0.0)
    assert system.state is result
    assert system.next_tick_number == 1


def test_system_supports_explicit_first_tick_number():
    system = make_system(first_tick_number=41)
    result = system.step(41, MovementIntent(Vector2(0.0, 1.0)))
    assert result.position == WorldPoint(0.0, 1.0)
    assert system.next_tick_number == 42


def test_each_consecutive_tick_advances_exactly_one_fixed_step():
    system = make_system()
    for tick in range(60):
        system.step(tick, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state.position.x == pytest.approx(60.0)
    assert system.next_tick_number == 60
    assert TICK_DELTA_SECONDS == 1.0 / 60.0


@pytest.mark.parametrize("tick", [True, 0.0, "0", None])
def test_system_rejects_non_integer_tick_numbers(tick):
    system = make_system()
    with pytest.raises(TypeError):
        system.step(tick, MovementIntent())
    assert system.next_tick_number == 0
    assert system.state.position == WorldPoint(0.0, 0.0)


def test_system_rejects_negative_tick_number():
    system = make_system()
    with pytest.raises(ValueError):
        system.step(-1, MovementIntent())
    assert system.next_tick_number == 0


@pytest.mark.parametrize("tick", [1, 2, 10])
def test_system_rejects_skipped_or_future_tick(tick):
    system = make_system()
    with pytest.raises(ValueError, match="expected tick 0"):
        system.step(tick, MovementIntent())
    assert system.next_tick_number == 0


def test_system_rejects_duplicate_tick():
    system = make_system()
    system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    state = system.state
    with pytest.raises(ValueError, match="expected tick 1"):
        system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state is state
    assert system.next_tick_number == 1


def test_system_rejects_backwards_tick():
    system = make_system()
    system.step(0, MovementIntent())
    system.step(1, MovementIntent())
    with pytest.raises(ValueError, match="expected tick 2"):
        system.step(0, MovementIntent())
    assert system.next_tick_number == 2


def test_system_rejects_invalid_intent_without_mutating_state_or_tick():
    system = make_system()
    state = system.state
    with pytest.raises(TypeError):
        system.step(0, object())
    assert system.state is state
    assert system.next_tick_number == 0


def test_system_commits_state_and_tick_only_after_successful_integration():
    system = make_system()
    state = system.state
    # A finite direction with a huge magnitude still normalizes safely for ordinary inputs.
    system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state is not state
    assert system.next_tick_number == 1


def test_system_has_no_clock_or_accumulator_responsibility():
    system = make_system()
    assert not hasattr(system, "clock")
    assert not hasattr(system, "accumulator")


def test_failed_integration_does_not_commit_state_or_tick():
    initial = MovementState(WorldPoint(1.79e308, 0.0))
    system = MovementSystem(
        initial,
        MovementConfig(max_speed=1.7976931348623157e308),
    )
    with pytest.raises(ValueError):
        system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state is initial
    assert system.next_tick_number == 0
