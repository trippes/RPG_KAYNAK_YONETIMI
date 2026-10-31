"""Serialization-ready value and document contracts without persistence I/O."""

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Type

from core.domain.spatial import Position
from core.foundation import ActionId, EntityId, EventId, Identifier, WorldId
from core.time import Tick

CANONICAL_PERSISTENCE_SCHEMA = "rpg-core"
PERSISTENCE_SCHEMA_VERSION = 1
PERSISTENCE_EXCLUSIONS = (
    "Entity.world_id", "World._entities", "Legacy EventBus", "Legacy EventQueue",
    "GameClock", "time_system.Scheduler", "ActionManager", "legacy Position",
    "legacy Tick", "callback/runtime implementation details", "dispatcher consumers",
    "transient runtime objects",
)


class PersistenceSchemaError(ValueError):
    """Malformed persistence contract data."""


class UnsupportedPersistenceSchemaError(PersistenceSchemaError):
    """A structurally valid but unsupported persistence schema version."""


def serialize_identifier(identifier: Identifier) -> str:
    if not isinstance(identifier, Identifier):
        raise TypeError("identifier must be a canonical Identifier.")
    return str(identifier)


def deserialize_identifier(value: object, identifier_type: Type[Identifier]) -> Identifier:
    if not isinstance(identifier_type, type) or not issubclass(identifier_type, Identifier):
        raise TypeError("identifier_type must be an Identifier subclass.")
    if not isinstance(value, str):
        raise PersistenceSchemaError("Identifier representation must be a string.")
    return identifier_type(value)


def serialize_position(position: Position) -> dict[str, int | float]:
    if not isinstance(position, Position):
        raise TypeError("position must be canonical Position.")
    return {"x": position.x, "y": position.y}


def deserialize_position(data: object) -> Position:
    if not isinstance(data, Mapping):
        raise PersistenceSchemaError("Position representation must be an object.")
    if set(data) != {"x", "y"}:
        raise PersistenceSchemaError("Position requires exactly x and y fields.")
    return Position(data["x"], data["y"])


def serialize_tick(tick: Tick) -> int:
    if not isinstance(tick, Tick):
        raise TypeError("tick must be canonical Tick.")
    return tick.value


def deserialize_tick(value: object) -> Tick:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PersistenceSchemaError("Tick representation must be a non-negative integer.")
    return Tick(value)


@dataclass(frozen=True)
class PersistenceDocument:
    """Snapshot envelope; filesystem access is delegated to the file adapter."""

    state: Mapping[str, object]
    simulation_tick: Tick
    schema: str = CANONICAL_PERSISTENCE_SCHEMA
    schema_version: int = PERSISTENCE_SCHEMA_VERSION
    core_version: str = "2.0"
    snapshot_id: str | None = None

    def __post_init__(self) -> None:
        if self.schema != CANONICAL_PERSISTENCE_SCHEMA:
            raise PersistenceSchemaError("Unknown persistence schema identifier.")
        if isinstance(self.schema_version, bool) or not isinstance(self.schema_version, int) or self.schema_version < 1:
            raise PersistenceSchemaError("schema_version must be a positive integer.")
        if self.schema_version > PERSISTENCE_SCHEMA_VERSION:
            raise UnsupportedPersistenceSchemaError("Future persistence schema requires migration.")
        if not isinstance(self.core_version, str) or not self.core_version.strip():
            raise PersistenceSchemaError("core_version must be non-empty.")
        if not isinstance(self.simulation_tick, Tick):
            raise PersistenceSchemaError("simulation_tick must be Tick.")
        if not isinstance(self.state, Mapping):
            raise PersistenceSchemaError("state must be an object mapping.")
        object.__setattr__(self, "state", MappingProxyType(deepcopy(dict(self.state))))

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "core_version": self.core_version,
            "snapshot_id": self.snapshot_id,
            "simulation_tick": serialize_tick(self.simulation_tick),
            "state": deepcopy(dict(self.state)),
        }

    @classmethod
    def from_state(
        cls,
        state,
        *,
        core_version: str = "2.0",
        snapshot_id: str | None = None,
    ) -> "PersistenceDocument":
        """Wrap a canonical session state in the persistence envelope."""
        from .state import CanonicalSessionState

        if not isinstance(state, CanonicalSessionState):
            raise TypeError("state must be CanonicalSessionState.")
        return cls(
            state=state.to_dict(),
            simulation_tick=Tick(state.simulation_tick),
            core_version=core_version,
            snapshot_id=snapshot_id,
        )

    def to_state(self):
        """Reconstruct canonical session state after envelope validation."""
        from .state import CanonicalSessionState

        state = CanonicalSessionState.from_dict(self.state)
        if state.simulation_tick != self.simulation_tick.value:
            raise PersistenceSchemaError("document/state Tick mismatch")
        return state

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "PersistenceDocument":
        if not isinstance(data, Mapping):
            raise PersistenceSchemaError("Persistence document must be an object.")
        required = {"schema", "schema_version", "core_version", "simulation_tick", "state"}
        missing = required - set(data)
        if missing:
            raise PersistenceSchemaError(f"Missing required fields: {sorted(missing)}")
        # Unknown fields are intentionally tolerated for forward compatibility.
        return cls(
            state=data["state"],
            simulation_tick=deserialize_tick(data["simulation_tick"]),
            schema=data["schema"],
            schema_version=data["schema_version"],
            core_version=data["core_version"],
            snapshot_id=data.get("snapshot_id"),
        )
