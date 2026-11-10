from dataclasses import dataclass
from typing import Callable


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

    Bir process_until çağrısı başladığında hazır olan olaylar FIFO
    sırasıyla işlenir. Callback içinden eklenen olaylar bir sonraki
    process_until çağrısında çalışır.
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
                if event.cancelled:
                    return False
                event.cancelled = True
                return True
        return False

    def process_until(self, current_tick: int):
        """
        Başlangıçta hazır olan olayları FIFO sırasıyla çalıştırır.

        Her olay callback çağrısından önce kuyruktan çıkarılır. Böylece
        callback hata verirse daha önce çalışmış olaylar tekrar çalışmaz;
        henüz çalışmamış olaylar sonraki çağrıya kalır. Callback içinden
        eklenen olaylar da mevcut çağrının hazır kümesine dahil edilmez.
        """
        ready = [
            event
            for event in self._events
            if not event.cancelled and event.trigger_tick <= current_tick
        ]
        processed = []

        for event in ready:
            if event.cancelled:
                self._events.remove(event)
                continue

            self._events.remove(event)
            event.callback()
            processed.append(event)

        self._events = [
            event for event in self._events if not event.cancelled
        ]
        return processed

    @property
    def pending_count(self):
        return sum(not event.cancelled for event in self._events)

    def clear(self):
        self._events.clear()
