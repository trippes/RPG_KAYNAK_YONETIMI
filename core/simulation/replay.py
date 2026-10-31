"""Small, serialization-ready replay contract for canonical simulation events."""

from collections.abc import Iterable, Mapping

from .events import SimulationEvent


class SimulationReplay:
    """Capture and verify canonical event streams without owning runtime state."""

    def __init__(self, events: Iterable[SimulationEvent] = ()) -> None:
        self._events = tuple(self._validate(event) for event in events)

    @property
    def events(self) -> tuple[SimulationEvent, ...]:
        return self._events

    def to_dict(self) -> dict[str, object]:
        return {"events": [event.to_dict() for event in self._events]}

    @classmethod
    def from_events(cls, events: Iterable[SimulationEvent]) -> "SimulationReplay":
        return cls(events)

    def assert_matches(self, events: Iterable[SimulationEvent]) -> None:
        actual = tuple(self._validate(event).to_dict() for event in events)
        expected = tuple(event.to_dict() for event in self._events)
        if actual != expected:
            raise AssertionError("Canonical replay mismatch: event stream differs.")

    @staticmethod
    def _validate(event: SimulationEvent) -> SimulationEvent:
        if not isinstance(event, SimulationEvent):
            raise TypeError("Replay accepts SimulationEvent values only.")
        return event

    @staticmethod
    def from_dict(data: Mapping[str, object]) -> "SimulationReplay":
        if not isinstance(data, Mapping) or not isinstance(data.get("events"), list):
            raise ValueError("Replay document must contain an events list.")
        if data["events"]:
            raise ValueError("Replay event decoding requires a typed event adapter.")
        return SimulationReplay()
