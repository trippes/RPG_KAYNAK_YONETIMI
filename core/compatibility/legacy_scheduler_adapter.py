"""Legacy callback API backed by the canonical typed-work scheduler.

The adapter preserves the 1.x callback contract while keeping callback objects
outside the canonical scheduler. Canonical work records carry only stable IDs;
the compatibility boundary owns the callable registry and execution policy.
"""

from dataclasses import dataclass
from typing import Callable

from core.simulation.scheduler import CanonicalScheduler, ScheduledWork
from core.time import Tick


@dataclass
class LegacyScheduledEvent:
    event_id: int
    trigger_tick: int
    callback: Callable
    description: str = ""
    cancelled: bool = False


class LegacyCallbackSchedulerAdapter:
    """Expose the legacy Scheduler API over CanonicalScheduler."""

    def __init__(self, start_tick: int = 0) -> None:
        self._scheduler = CanonicalScheduler(start_tick)
        self._callbacks: dict[str, LegacyScheduledEvent] = {}
        self._work_ids: dict[int, str] = {}
        self._next_event_id = 1

    @property
    def canonical_scheduler(self) -> CanonicalScheduler:
        return self._scheduler

    @property
    def pending_count(self) -> int:
        return self._scheduler.pending_count

    def schedule(self, trigger_tick: int, callback: Callable, description: str = "") -> int:
        if isinstance(trigger_tick, bool) or not isinstance(trigger_tick, int):
            raise TypeError("trigger_tick tam sayı olmalıdır.")
        if trigger_tick < 0:
            raise ValueError("Olay zamanı negatif olamaz.")
        if not callable(callback):
            raise TypeError("callback çağrılabilir olmalıdır.")

        event_id = self._next_event_id
        self._next_event_id += 1
        # The legacy API accepts already-due work. CanonicalScheduler rejects
        # scheduling in the past, so due work is represented at its current tick.
        canonical_tick = max(trigger_tick, self._scheduler.current_tick.value)
        work = self._scheduler.schedule(
            Tick(canonical_tick),
            "legacy.callback",
            {"event_id": event_id},
        )
        event = LegacyScheduledEvent(event_id, trigger_tick, callback, description)
        self._callbacks[work.work_id] = event
        self._work_ids[event_id] = work.work_id
        return event_id

    def cancel(self, event_id: int) -> bool:
        work_id = self._work_ids.get(event_id)
        if work_id is None or not self._scheduler.cancel(work_id):
            return False
        event = self._callbacks.get(work_id)
        if event is not None:
            event.cancelled = True
        return True

    def process_until(self, current_tick: int):
        if isinstance(current_tick, bool) or not isinstance(current_tick, int):
            raise TypeError("current_tick tam sayı olmalıdır.")
        self._scheduler.advance_to(Tick(current_tick))
        # Snapshotting IDs preserves the old rule: work added by a callback
        # waits until the next process_until call.
        ready = self._scheduler.ready_snapshot()
        processed = []
        for scheduled in ready:
            work = self._scheduler.pop_work(scheduled.work_id)
            if work is None:
                continue
            event = self._callbacks.pop(work.work_id)
            self._work_ids.pop(event.event_id, None)
            event.callback()
            processed.append(event)
        return processed

    def clear(self) -> None:
        self._scheduler.clear()
        self._callbacks.clear()
        self._work_ids.clear()
