"""Consumer boundary for canonical simulation events."""

from dataclasses import dataclass
from typing import Iterable

from .events import SimulationEvent
from .transport import CanonicalEventTransport


class EventConsumer:
    """Minimal consumer contract: implement ``consume(event)``."""

    def consume(self, event: SimulationEvent) -> None:  # pragma: no cover - interface
        raise NotImplementedError


@dataclass(frozen=True)
class _Registration:
    consumer: object
    event_types: frozenset[str] | None


class CanonicalEventDispatcher:
    """Dispatch transport events in queue order and registration order.

    A dispatch cycle snapshots the number of pending events. Events enqueued
    by a consumer are deferred to the next cycle. Calling ``dispatch_pending``
    recursively is rejected, making re-entrant behavior explicit and safe.
    """

    def __init__(self, transport: CanonicalEventTransport) -> None:
        if not isinstance(transport, CanonicalEventTransport):
            raise TypeError("transport must be CanonicalEventTransport.")
        self.transport = transport
        self._registrations: list[_Registration] = []
        self._dispatching = False

    def register(self, consumer: EventConsumer, event_types: Iterable[str] | None = None) -> None:
        if not callable(getattr(consumer, "consume", None)):
            raise TypeError("consumer must implement consume(event).")
        if any(item.consumer is consumer for item in self._registrations):
            raise ValueError("consumer is already registered.")
        types = None if event_types is None else frozenset(event_types)
        self._registrations.append(_Registration(consumer, types))

    def unregister(self, consumer: EventConsumer) -> bool:
        for index, item in enumerate(self._registrations):
            if item.consumer is consumer:
                del self._registrations[index]
                return True
        return False

    def consumer_count(self) -> int:
        return len(self._registrations)

    def registration_snapshot(self) -> tuple[tuple[object, frozenset[str] | None], ...]:
        """Return registrations so an application runtime can be replaced safely."""
        return tuple((item.consumer, item.event_types) for item in self._registrations)

    def dispatch(self, event: SimulationEvent) -> int:
        if not isinstance(event, SimulationEvent):
            raise TypeError("dispatcher accepts SimulationEvent only.")
        if self._dispatching:
            raise RuntimeError("Re-entrant event dispatch is not allowed.")
        self._dispatching = True
        try:
            handled = 0
            for registration in tuple(self._registrations):
                if registration.event_types is None or event.event_type in registration.event_types:
                    registration.consumer.consume(event)
                    handled += 1
            return handled
        finally:
            self._dispatching = False

    def dispatch_pending(self) -> int:
        if self._dispatching:
            raise RuntimeError("Re-entrant event dispatch is not allowed.")
        cycle_size = self.transport.count()
        dispatched = 0
        self._dispatching = True
        try:
            for _ in range(cycle_size):
                event = self.transport.peek()
                if event is None:
                    break
                for registration in tuple(self._registrations):
                    if registration.event_types is None or event.event_type in registration.event_types:
                        registration.consumer.consume(event)
                self.transport.dequeue()
                dispatched += 1
            return dispatched
        finally:
            self._dispatching = False


EventDispatcher = CanonicalEventDispatcher
