from enum import Enum
from types import MappingProxyType
from typing import Mapping

from core.foundation import ActionId, Identifier
from core.time import Tick


class ActionState(Enum):
    CREATED = "created"
    SCHEDULED = "scheduled"
    STARTED = "started"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Action:
    """Canonical deterministic action with guarded lifecycle transitions."""

    def __init__(
        self,
        action_id: ActionId,
        owner_id: Identifier,
        created_tick: Tick,
        duration: Tick,
        context: Mapping[str, object] | None = None,
    ) -> None:
        if not isinstance(action_id, ActionId):
            raise TypeError("action_id must be ActionId.")
        if not isinstance(owner_id, Identifier):
            raise TypeError("owner_id must be Identifier.")
        if not isinstance(created_tick, Tick) or not isinstance(duration, Tick):
            raise TypeError("created_tick and duration must be Tick.")
        self._action_id = action_id
        self._owner_id = owner_id
        self._created_tick = created_tick
        self._duration = duration
        self._context = MappingProxyType(dict(context or {}))
        self._state = ActionState.CREATED
        self._scheduled_tick = None
        self._started_tick = None
        self._completed_tick = None
        self._result = None
        self._failure = None
        self._cancellation = None

    @property
    def action_id(self) -> ActionId:
        return self._action_id

    @property
    def owner_id(self) -> Identifier:
        return self._owner_id

    @property
    def created_tick(self) -> Tick:
        return self._created_tick

    @property
    def duration(self) -> Tick:
        return self._duration

    @property
    def context(self) -> Mapping[str, object]:
        return self._context

    @property
    def state(self) -> ActionState:
        return self._state

    @property
    def scheduled_tick(self) -> Tick | None:
        return self._scheduled_tick

    @property
    def started_tick(self) -> Tick | None:
        return self._started_tick

    @property
    def completed_tick(self) -> Tick | None:
        return self._completed_tick

    @property
    def completion_tick(self) -> Tick | None:
        if self._started_tick is None:
            return None
        return self._started_tick + self._duration

    @property
    def result(self):
        return self._result

    @property
    def failure(self):
        return self._failure

    @property
    def cancellation(self):
        return self._cancellation

    def schedule(self, tick: Tick) -> None:
        self._require_state(ActionState.CREATED)
        self._require_not_before(tick, self._created_tick)
        self._scheduled_tick = tick
        self._state = ActionState.SCHEDULED

    def start(self, tick: Tick) -> None:
        self._require_state(ActionState.SCHEDULED)
        self._require_not_before(tick, self._scheduled_tick)
        self._started_tick = tick
        self._state = ActionState.STARTED

    def complete(self, tick: Tick, result=None) -> None:
        self._require_state(ActionState.STARTED)
        self._require_not_before(tick, self.completion_tick)
        self._completed_tick = tick
        self._result = result
        self._state = ActionState.COMPLETED

    def fail(self, tick: Tick, failure) -> None:
        self._require_state(ActionState.STARTED)
        self._require_not_before(tick, self._started_tick)
        self._failure = failure
        self._state = ActionState.FAILED

    def cancel(self, tick: Tick, cancellation) -> None:
        if self._state not in {
            ActionState.CREATED,
            ActionState.SCHEDULED,
            ActionState.STARTED,
        }:
            raise ValueError("Action cannot be cancelled in its current state.")
        self._require_not_before(tick, self._created_tick)
        self._cancellation = cancellation
        self._state = ActionState.CANCELLED

    def to_dict(self) -> dict[str, object]:
        return {
            "action_id": str(self._action_id),
            "owner_id": str(self._owner_id),
            "created_tick": self._created_tick.value,
            "duration": self._duration.value,
            "state": self._state.value,
            "scheduled_tick": self._scheduled_tick.value if self._scheduled_tick else None,
            "started_tick": self._started_tick.value if self._started_tick else None,
            "completed_tick": self._completed_tick.value if self._completed_tick else None,
            "context": dict(self._context),
            "result": self._result,
            "failure": self._failure,
            "cancellation": self._cancellation,
        }

    def _require_state(self, expected: ActionState) -> None:
        if self._state != expected:
            raise ValueError(f"Expected state {expected.value}, got {self._state.value}.")

    @staticmethod
    def _require_not_before(tick: Tick, minimum: Tick | None) -> None:
        if not isinstance(tick, Tick):
            raise TypeError("Action transition time must be Tick.")
        if minimum is not None and tick < minimum:
            raise ValueError("Action transition cannot move simulation time backwards.")
