"""Canonical deterministic event transport for Core 2.0.

The transport is deliberately a queue, not a subscriber bus.  Consumers can
dequeue immutable event envelopes; dispatch policy remains an application
concern.
"""

from dataclasses import replace
from typing import Iterable

from core.foundation import EventId, Identifier
from core.time import Tick

from .events import SimulationEvent
from .event_types import canonical_event_type


class CanonicalEventTransport:
    """FIFO transport ordered by ``(simulation_tick, insertion_sequence)``."""

    def __init__(self) -> None:
        self._events: list[SimulationEvent] = []
        self._next_sequence = 0
        self._next_event_id = 1
        self._known_ids: set[EventId] = set()

    def enqueue(self, event: SimulationEvent) -> SimulationEvent:
        if not isinstance(event, SimulationEvent):
            raise TypeError("Canonical transport accepts SimulationEvent only.")
        if event.event_id is not None and event.event_id in self._known_ids:
            raise ValueError(f"Duplicate event identity: {event.event_id}")
        event_id = event.event_id or EventId(f"event_{self._next_event_id:06d}")
        canonical = replace(
            event,
            event_id=event_id,
            insertion_sequence=self._next_sequence,
        )
        self._events.append(canonical)
        self._events.sort(key=lambda item: (item.simulation_tick, item.insertion_sequence))
        self._known_ids.add(event_id)
        self._next_sequence += 1
        self._next_event_id += 1
        return canonical

    publish = enqueue

    def dequeue(self) -> SimulationEvent | None:
        return self._events.pop(0) if self._events else None

    def peek(self) -> SimulationEvent | None:
        return self._events[0] if self._events else None

    def empty(self) -> bool:
        return not self._events

    def count(self) -> int:
        return len(self._events)

    def drain(self) -> tuple[SimulationEvent, ...]:
        result = tuple(self._events)
        self._events.clear()
        return result

    def clear(self) -> None:
        self._events.clear()

    def __len__(self) -> int:
        return self.count()


# Naming aliases make the contract discoverable without introducing a second
# event package that would collide with the 1.x ``core.events`` module.
CanonicalEventQueue = CanonicalEventTransport
EventTransport = CanonicalEventTransport


class LegacyEventAdapter:
    """Translate a 1.x ``Event`` into the canonical transport."""

    def __init__(self, transport: CanonicalEventTransport) -> None:
        if not isinstance(transport, CanonicalEventTransport):
            raise TypeError("transport must be CanonicalEventTransport.")
        self.transport = transport

    def enqueue(
        self,
        event,
        simulation_tick: Tick | int = Tick(0),
        source_id: Identifier | None = None,
        metadata: dict[str, object] | None = None,
    ) -> SimulationEvent:
        if not hasattr(event, "tur") or not hasattr(event, "veri"):
            raise TypeError("Legacy adapter accepts an Event-shaped object only.")
        tick = simulation_tick if isinstance(simulation_tick, Tick) else Tick(simulation_tick)
        return self.transport.enqueue(
            SimulationEvent(
                event_type=canonical_event_type(event.tur),
                simulation_tick=tick,
                source_id=source_id,
                target_id=None,
                action_id=None,
                payload=event.veri,
                metadata=metadata or {"legacy": True},
            )
        )

    def enqueue_many(self, events: Iterable[object], simulation_tick: Tick | int = Tick(0)) -> tuple[SimulationEvent, ...]:
        return tuple(self.enqueue(event, simulation_tick) for event in events)
