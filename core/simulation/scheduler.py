from dataclasses import dataclass
from typing import Mapping

from core.time import Tick


@dataclass(frozen=True, order=True)
class ScheduledWork:
    """Callback-free work item ordered by tick and insertion sequence."""

    trigger_tick: Tick
    sequence: int
    work_id: str
    work_type: str
    payload: Mapping[str, object]
    cancelled: bool = False


class CanonicalScheduler:
    """Deterministic simulation scheduler that emits work, never callbacks."""

    def __init__(self, start_tick: Tick | int = Tick(0)) -> None:
        self._current_tick = self._coerce_tick(start_tick)
        self._next_sequence = 1
        self._next_work_id = 1
        self._pending: dict[str, ScheduledWork] = {}

    @property
    def current_tick(self) -> Tick:
        return self._current_tick

    @property
    def pending_count(self) -> int:
        return sum(not work.cancelled for work in self._pending.values())

    @property
    def next_scheduled_tick(self) -> Tick | None:
        """Return the next live work tick without changing scheduler state."""
        ticks = [
            work.trigger_tick
            for work in self._pending.values()
            if not work.cancelled
        ]
        return min(ticks) if ticks else None

    def schedule(
        self,
        trigger_tick: Tick | int,
        work_type: str,
        payload: Mapping[str, object] | None = None,
    ) -> ScheduledWork:
        trigger = self._coerce_tick(trigger_tick)
        if trigger < self._current_tick:
            raise ValueError("Cannot schedule work in the past.")
        if not isinstance(work_type, str) or not work_type.strip():
            raise ValueError("work_type cannot be empty.")

        work = ScheduledWork(
            trigger_tick=trigger,
            sequence=self._next_sequence,
            work_id=f"schedule_{self._next_work_id:06d}",
            work_type=work_type,
            payload=dict(payload or {}),
        )
        self._pending[work.work_id] = work
        self._next_sequence += 1
        self._next_work_id += 1
        return work

    def cancel(self, work_id: str) -> bool:
        work = self._pending.get(work_id)
        if work is None or work.cancelled:
            return False
        self._pending[work_id] = ScheduledWork(
            trigger_tick=work.trigger_tick,
            sequence=work.sequence,
            work_id=work.work_id,
            work_type=work.work_type,
            payload=work.payload,
            cancelled=True,
        )
        return True

    def advance_to(self, target_tick: Tick | int) -> Tick:
        target = self._coerce_tick(target_tick)
        if target < self._current_tick:
            raise ValueError("Simulation time cannot move backwards.")
        self._current_tick = target
        return self._current_tick

    def pop_ready(self) -> tuple[ScheduledWork, ...]:
        ready = sorted(
            (
                work
                for work in self._pending.values()
                if not work.cancelled and work.trigger_tick <= self._current_tick
            ),
            key=lambda work: (work.trigger_tick, work.sequence),
        )
        for work in ready:
            self._pending.pop(work.work_id, None)
        self._pending = {
            work_id: work
            for work_id, work in self._pending.items()
            if not work.cancelled
        }
        return tuple(ready)

    def clear(self) -> None:
        self._pending.clear()

    @staticmethod
    def _coerce_tick(value: Tick | int) -> Tick:
        if isinstance(value, Tick):
            return value
        if isinstance(value, int) and not isinstance(value, bool):
            return Tick(value)
        raise TypeError("Tick value must be Tick or int.")
