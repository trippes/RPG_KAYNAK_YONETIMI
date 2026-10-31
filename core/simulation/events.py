from dataclasses import dataclass
from copy import deepcopy
from types import MappingProxyType
from typing import Mapping

from core.foundation import ActionId, EventId, Identifier
from core.time import Tick
from .event_types import DEFAULT_SCHEMA_VERSION


@dataclass(frozen=True)
class SimulationEvent:
    """Typed deterministic event envelope for the canonical runtime."""

    event_type: str
    simulation_tick: Tick
    source_id: Identifier | None
    target_id: Identifier | None
    action_id: ActionId | None
    payload: Mapping[str, object]
    metadata: Mapping[str, object]
    # Assigned by CanonicalEventTransport.  Keeping it optional preserves the
    # Phase 3 construction API while making identity explicit in Phase 4.
    event_id: EventId | None = None
    insertion_sequence: int | None = None
    schema_version: int = DEFAULT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("event_type cannot be empty.")
        if not isinstance(self.simulation_tick, Tick):
            raise TypeError("simulation_tick must be Tick.")
        object.__setattr__(self, "payload", MappingProxyType(deepcopy(dict(self.payload))))
        object.__setattr__(self, "metadata", MappingProxyType(deepcopy(dict(self.metadata))))
        if self.event_id is not None and not isinstance(self.event_id, EventId):
            raise TypeError("event_id must be EventId or None.")
        if isinstance(self.schema_version, bool) or not isinstance(self.schema_version, int):
            raise TypeError("schema_version must be an integer.")
        if self.schema_version < 1:
            raise ValueError("schema_version must be positive.")
        if self.insertion_sequence is not None and (
            isinstance(self.insertion_sequence, bool)
            or not isinstance(self.insertion_sequence, int)
            or self.insertion_sequence < 0
        ):
            raise ValueError("insertion_sequence must be a non-negative integer or None.")

    def to_dict(self) -> dict[str, object]:
        return {
            "event_type": self.event_type,
            "simulation_tick": self.simulation_tick.value,
            "source_id": str(self.source_id) if self.source_id else None,
            "target_id": str(self.target_id) if self.target_id else None,
            "action_id": str(self.action_id) if self.action_id else None,
            "payload": dict(self.payload),
            "metadata": dict(self.metadata),
            "event_id": str(self.event_id) if self.event_id else None,
            "insertion_sequence": self.insertion_sequence,
            "schema_version": self.schema_version,
        }
