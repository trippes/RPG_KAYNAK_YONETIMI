from typing import Mapping

from core.foundation import ActionId, Identifier
from core.simulation.action import Action, ActionState
from core.simulation.events import SimulationEvent
from core.simulation.scheduler import CanonicalScheduler
from core.time import Tick
from core.simulation.transport import CanonicalEventTransport
from core.simulation.event_types import CanonicalEventType


class ActionProcessor:
    """Runtime service for canonical Action lifecycle processing."""

    def __init__(self, scheduler=None, start_tick: Tick | int = Tick(0), event_transport=None) -> None:
        self._scheduler = scheduler or CanonicalScheduler(start_tick)
        self._event_transport = (
            event_transport if event_transport is not None else CanonicalEventTransport()
        )
        self._actions: dict[ActionId, Action] = {}
        self._scheduled_work: dict[ActionId, set[str]] = {}
        self._next_action_id = 1
        self._events: list[SimulationEvent] = []
        self._source_id = Identifier("action_processor")

    @property
    def scheduler(self) -> CanonicalScheduler:
        return self._scheduler

    @property
    def current_tick(self) -> Tick:
        return self._scheduler.current_tick

    @property
    def event_transport(self) -> CanonicalEventTransport:
        return self._event_transport

    def create(
        self,
        owner_id: Identifier,
        duration: Tick | int,
        context: Mapping[str, object] | None = None,
        action_id: ActionId | None = None,
    ) -> Action:
        duration = self._coerce_tick(duration)
        action_id = action_id or ActionId(f"action_{self._next_action_id:06d}")
        if action_id in self._actions:
            raise ValueError(f"Action ID already exists: {action_id}")
        action = Action(
            action_id=action_id,
            owner_id=owner_id,
            created_tick=self.current_tick,
            duration=duration,
            context=context,
        )
        self._actions[action_id] = action
        self._next_action_id += 1
        self._emit(CanonicalEventType.ACTION_CREATED, action)
        return action

    def get(self, action_id: ActionId) -> Action | None:
        return self._actions.get(action_id)

    def schedule(self, action_id: ActionId, scheduled_tick: Tick | int | None = None) -> Action:
        action = self._require(action_id)
        tick = self.current_tick if scheduled_tick is None else self._coerce_tick(scheduled_tick)
        if tick < self.current_tick:
            raise ValueError("Cannot schedule an action in the past.")
        action.schedule(tick)
        try:
            work = self._scheduler.schedule(
                trigger_tick=tick,
                work_type="action.start",
                payload={"action_id": str(action_id)},
            )
            self._scheduled_work.setdefault(action_id, set()).add(work.work_id)
        except Exception:
            # Keep action and scheduler state atomic if scheduling fails.
            action._state = ActionState.CREATED
            action._scheduled_tick = None
            raise
        self._emit(CanonicalEventType.ACTION_SCHEDULED, action)
        return action

    def cancel(self, action_id: ActionId, cancellation="cancelled") -> Action:
        action = self._require(action_id)
        action.cancel(self.current_tick, cancellation)
        self._cancel_pending_work(action_id)
        self._emit(CanonicalEventType.ACTION_CANCELLED, action)
        return action

    def fail(self, action_id: ActionId, failure) -> Action:
        action = self._require(action_id)
        action.fail(self.current_tick, failure)
        self._cancel_pending_work(action_id)
        self._emit(CanonicalEventType.ACTION_FAILED, action)
        return action

    def advance_to(self, target_tick: Tick | int) -> tuple[SimulationEvent, ...]:
        target = self._coerce_tick(target_tick)
        while True:
            next_tick = self._scheduler.next_scheduled_tick
            if next_tick is None or next_tick > target:
                self._scheduler.advance_to(target)
                break
            self._scheduler.advance_to(next_tick)
            ready = self._scheduler.pop_ready()
            if not ready:
                continue
            for work in ready:
                self._scheduled_work.get(ActionId(work.payload["action_id"]), set()).discard(work.work_id)
                action_id = ActionId(work.payload["action_id"])
                action = self._require(action_id)
                if work.work_type == "action.start":
                    if action.state != ActionState.SCHEDULED:
                        continue
                    action.start(work.trigger_tick)
                    self._emit(CanonicalEventType.ACTION_STARTED, action)
                    completion = self._scheduler.schedule(
                        trigger_tick=action.completion_tick,
                        work_type="action.complete",
                        payload={"action_id": str(action.action_id)},
                    )
                    self._scheduled_work.setdefault(action_id, set()).add(completion.work_id)
                elif work.work_type == "action.complete":
                    if action.state != ActionState.STARTED:
                        continue
                    action.complete(work.trigger_tick)
                    self._emit(CanonicalEventType.ACTION_COMPLETED, action)
            # Newly scheduled completion work at the current tick is handled
            # in the next deterministic pass, including zero-duration actions.
        return self.drain_events()

    def drain_events(self) -> tuple[SimulationEvent, ...]:
        events = tuple(self._events)
        self._events.clear()
        return events

    def _emit(self, event_type: str, action: Action) -> None:
        if event_type == CanonicalEventType.ACTION_STARTED:
            tick = action.started_tick
        elif event_type == CanonicalEventType.ACTION_COMPLETED:
            tick = action.completed_tick
        else:
            tick = self.current_tick
        event = SimulationEvent(
                event_type=event_type,
                simulation_tick=tick or self.current_tick,
                source_id=self._source_id,
                target_id=action.owner_id,
                action_id=action.action_id,
                payload={"state": action.state.value},
                metadata={},
            )
        self._events.append(self._event_transport.enqueue(event))

    def _require(self, action_id: ActionId) -> Action:
        action = self._actions.get(action_id)
        if action is None:
            raise KeyError(f"Action not found: {action_id}")
        return action

    def _cancel_pending_work(self, action_id: ActionId) -> None:
        for work_id in self._scheduled_work.pop(action_id, set()):
            self._scheduler.cancel(work_id)

    @staticmethod
    def _coerce_tick(value: Tick | int) -> Tick:
        if isinstance(value, Tick):
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return Tick(value)
        raise TypeError("Tick value must be Tick or int.")
