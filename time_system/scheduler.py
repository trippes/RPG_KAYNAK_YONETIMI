from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class ScheduledEvent:
    """
    Belirli bir oyun zamanında gerçekleşmesi gereken olay.
    """

    event_id: int
    trigger_tick: int
    callback: Callable
    description: str = ""
    cancelled: bool = False


class Scheduler:
    """
    Oyun zamanına bağlı olay planlayıcısı.

    GameClock zamanı ilerlettiğinde Scheduler,
    hedef zamana ulaşılmış olayları tetikler.
    """

    def __init__(self):
        self._events = []
        self._next_id = 1

    def schedule(
        self,
        trigger_tick: int,
        callback: Callable,
        description: str = "",
    ) -> int:

        if trigger_tick < 0:
            raise ValueError("Olay zamanı negatif olamaz.")

        if not callable(callback):
            raise TypeError("callback çağrılabilir olmalıdır.")

        event = ScheduledEvent(
            event_id=self._next_id,
            trigger_tick=trigger_tick,
            callback=callback,
            description=description,
        )

        self._events.append(event)
        self._events.sort(key=lambda item: item.trigger_tick)

        self._next_id += 1

        return event.event_id

    def cancel(self, event_id: int) -> bool:
        for event in self._events:
            if event.event_id == event_id:
                event.cancelled = True
                return True

        return False

    def process_until(self, current_tick: int):
        """
        current_tick'e kadar gerçekleşmesi gereken tüm olayları çalıştırır.
        """

        ready = []

        for event in self._events:
            if not event.cancelled and event.trigger_tick <= current_tick:
                ready.append(event)

        for event in ready:
            event.callback()

        self._events = [
            event
            for event in self._events
            if event not in ready and not event.cancelled
        ]

        return ready

    @property
    def pending_count(self):
        return len(
            [
                event
                for event in self._events
                if not event.cancelled
            ]
        )

    def clear(self):
        self._events.clear()
