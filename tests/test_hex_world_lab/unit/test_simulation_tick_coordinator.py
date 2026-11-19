import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import MovementIntent, MovementState
from hex_world_lab.simulation.tick_coordinator import SimulationTickCoordinator


class FakeMovementSystem:
    def __init__(self, events=None):
        self.next_tick_number = 0
        self.calls = []
        self.events = events

    def step(self, tick_number, intent):
        self.calls.append((tick_number, intent))
        if self.events is not None:
            self.events.append(("movement", tick_number))
        state = MovementState(WorldPoint(float(tick_number + 1), 0.0))
        self.next_tick_number += 1
        return state


class FakeCellTracker:
    def __init__(self, events):
        self.events = events
        self.fail_once = False
        self.calls = []

    def update(self, position):
        self.events.append(("cell", position))
        self.calls.append(position)
        if self.fail_once:
            self.fail_once = False
            raise RuntimeError("cell tracking failed")


def make_coordinator(*, sync=None, cell_tracker=None):
    events = []
    movement = FakeMovementSystem()
    tracker = cell_tracker or FakeCellTracker(events)
    intents = []
    def read_intent():
        events.append(("input", None))
        intent = MovementIntent()
        intents.append(intent)
        return intent
    coordinator = SimulationTickCoordinator(movement, read_intent, tracker, sync)
    return coordinator, movement, tracker, events, intents


def test_tick_runs_input_movement_cell_and_entity_sync_in_order():
    events = []
    movement = FakeMovementSystem(events)
    tracker = FakeCellTracker(events)
    def read_intent():
        events.append(("input", None))
        return MovementIntent()
    def sync(position):
        events.append(("entity", position))
    coordinator = SimulationTickCoordinator(movement, read_intent, tracker, sync)

    result = coordinator.advance_tick(0)

    assert result.position == WorldPoint(1.0, 0.0)
    assert [event[0] for event in events] == ["input", "movement", "cell", "entity"]
    assert movement.next_tick_number == 1
    assert coordinator.next_tick_number == 1
    assert coordinator.last_completed_tick_number == 0
    assert not coordinator.has_pending_tick


def test_input_is_sampled_once_when_a_later_stage_fails_and_tick_retries():
    coordinator, movement, tracker, events, intents = make_coordinator()
    tracker.fail_once = True

    with pytest.raises(RuntimeError, match="cell tracking failed"):
        coordinator.advance_tick(0)

    assert coordinator.has_pending_tick
    assert len(intents) == 1
    assert len(movement.calls) == 1

    result = coordinator.advance_tick(0)

    assert result.position == WorldPoint(1.0, 0.0)
    assert len(intents) == 1
    assert len(movement.calls) == 1
    assert tracker.calls == [WorldPoint(1.0, 0.0), WorldPoint(1.0, 0.0)]
    assert coordinator.last_completed_tick_number == 0


def test_entity_sync_failure_retries_without_repeating_movement_or_cell_tracking():
    events = []
    movement = FakeMovementSystem()
    tracker = FakeCellTracker(events)
    sync_calls = []
    def sync(position):
        sync_calls.append(position)
        if len(sync_calls) == 1:
            raise RuntimeError("entity sync failed")
    coordinator = SimulationTickCoordinator(
        movement, lambda: MovementIntent(), tracker, sync
    )

    with pytest.raises(RuntimeError, match="entity sync failed"):
        coordinator.advance_tick(0)

    coordinator.advance_tick(0)

    assert len(movement.calls) == 1
    assert tracker.calls == [WorldPoint(1.0, 0.0)]
    assert sync_calls == [WorldPoint(1.0, 0.0), WorldPoint(1.0, 0.0)]
    assert coordinator.next_tick_number == 1


def test_pending_tick_rejects_a_different_tick_number():
    coordinator, _, tracker, _, _ = make_coordinator()
    tracker.fail_once = True
    with pytest.raises(RuntimeError):
        coordinator.advance_tick(0)
    with pytest.raises(ValueError, match="is pending"):
        coordinator.advance_tick(1)
    coordinator.advance_tick(0)


def test_wrong_or_repeated_tick_is_rejected():
    coordinator, _, _, _, _ = make_coordinator()
    with pytest.raises(ValueError, match="expected tick 0"):
        coordinator.advance_tick(1)
    coordinator.advance_tick(0)
    with pytest.raises(ValueError, match="expected tick 1"):
        coordinator.advance_tick(0)


def test_entity_sync_callback_can_only_be_bound_before_first_tick():
    coordinator, _, _, _, _ = make_coordinator()
    calls = []
    coordinator.bind_entity_sync_callback(calls.append)
    coordinator.advance_tick(0)
    with pytest.raises(RuntimeError, match="before the first tick"):
        coordinator.bind_entity_sync_callback(calls.append)
    assert calls == [WorldPoint(1.0, 0.0)]


def test_entity_sync_is_optional_for_movement_only_demo():
    coordinator, _, _, _, _ = make_coordinator()
    result = coordinator.advance_tick(0)
    assert result.position == WorldPoint(1.0, 0.0)


@pytest.mark.parametrize("invalid", [True, -1, 1.5, "0"])
def test_invalid_tick_number_is_rejected(invalid):
    coordinator, _, _, _, _ = make_coordinator()
    with pytest.raises((TypeError, ValueError)):
        coordinator.advance_tick(invalid)
