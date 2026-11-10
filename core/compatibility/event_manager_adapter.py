"""Canonical transport-backed implementation of the legacy EventManager API.

The queue is owned by CanonicalEventTransport. Event objects and EventBus
handlers remain at the compatibility edge so existing public consumers retain
object identity, FIFO, re-entrant dispatch, and exception-consumption behavior.
"""

from core.compatibility.usage import record_usage
from core.event_bus import EventBus
from core.event_manager import EventManager
from core.events import Event
from core.simulation.events import SimulationEvent
from core.simulation.transport import CanonicalEventTransport
from core.simulation.event_types import canonical_event_type
from core.time import Tick


class CanonicalEventQueueView:
    """Legacy EventQueue-shaped view over the canonical event transport."""

    def __init__(self, transport: CanonicalEventTransport) -> None:
        self._transport = transport
        self._legacy_events: dict[str, Event] = {}

    def ekle(self, event: Event) -> None:
        if not isinstance(event, Event):
            raise TypeError("Kuyruğa yalnızca Event nesnesi eklenebilir.")
        canonical = self._transport.enqueue(
            SimulationEvent(
                event_type=canonical_event_type(event.tur),
                simulation_tick=Tick(0),
                source_id=None,
                target_id=None,
                action_id=None,
                payload=event.veri,
                metadata={"legacy_event": True},
            )
        )
        self._legacy_events[str(canonical.event_id)] = event

    def al(self) -> Event | None:
        canonical = self._transport.dequeue()
        if canonical is None:
            return None
        return self._legacy_events.pop(str(canonical.event_id), None)

    def bekleyen_sayi(self) -> int:
        return self._transport.count()

    def bos_mu(self) -> bool:
        return self._transport.empty()

    def temizle(self) -> None:
        self._transport.clear()
        self._legacy_events.clear()

    def listele(self) -> list[Event]:
        return [
            self._legacy_events[str(event.event_id)]
            for event in self._transport.snapshot()
        ]


class CanonicalEventManagerAdapter(EventManager):
    """Preserve EventManager's API while moving queue ownership to Core 2.x."""

    def __init__(self, event_bus: EventBus | None = None) -> None:
        if event_bus is not None and not isinstance(event_bus, EventBus):
            raise TypeError("event_bus yalnızca EventBus nesnesi veya None olabilir.")
        record_usage("core.event_manager.EventManager")
        self.event_bus = event_bus if event_bus is not None else EventBus()
        self._transport = CanonicalEventTransport()
        self.event_queue = CanonicalEventQueueView(self._transport)

    @property
    def event_transport(self) -> CanonicalEventTransport:
        return self._transport

    def olustur(self, tur, veri=None):
        return Event(tur=tur, veri=veri)

    def ekle(self, tur, veri=None):
        event = self.olustur(tur=tur, veri=veri)
        self.event_queue.ekle(event)
        return event

    def yayinla(self, event):
        if not isinstance(event, Event):
            raise TypeError("Yalnızca Event nesneleri yayınlanabilir.")
        return self.event_bus.publish(event)

    def islet(self):
        processed_events = 0
        processed_handlers = 0
        while not self.event_queue.bos_mu():
            event = self.event_queue.al()
            if event is None:
                break
            processed_handlers += self.event_bus.publish(event)
            processed_events += 1
        return processed_events, processed_handlers

    def bekleyen_sayi(self):
        return self.event_queue.bekleyen_sayi()

    def temizle(self):
        self.event_queue.temizle()
