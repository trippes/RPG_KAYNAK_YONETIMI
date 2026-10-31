"""Canonical state records independent of runtime implementation objects."""

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping

from core.domain import WorldDomainState
from core.domain.spatial import Position
from core.foundation import EntityId, WorldId

from .contracts import deserialize_position, serialize_position


@dataclass(frozen=True)
class CanonicalEntityRecord:
    entity_id: EntityId
    entity_type: str
    state: Mapping[str, object]
    position: Position
    name: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, EntityId):
            raise TypeError("entity_id must be EntityId.")
        if not isinstance(self.entity_type, str) or not self.entity_type.strip():
            raise ValueError("entity_type must be non-empty.")
        if not isinstance(self.name, str):
            raise TypeError("name must be a string.")
        if not isinstance(self.state, Mapping):
            raise TypeError("state must be a mapping.")
        if not isinstance(self.position, Position):
            raise TypeError("position must be canonical Position.")
        object.__setattr__(self, "state", MappingProxyType(deepcopy(dict(self.state))))

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_id": str(self.entity_id),
            "entity_type": self.entity_type,
            "name": self.name,
            "state": deepcopy(dict(self.state)),
            "position": serialize_position(self.position),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CanonicalEntityRecord":
        required = {"entity_id", "entity_type", "state", "position"}
        if not isinstance(data, Mapping) or not required.issubset(data):
            raise ValueError("CanonicalEntityRecord is missing required fields.")
        return cls(
            entity_id=EntityId(data["entity_id"]),
            entity_type=data["entity_type"],
            state=data["state"],
            position=deserialize_position(data["position"]),
            name=data.get("name", ""),
        )


@dataclass(frozen=True)
class EntityRepositoryState:
    records: tuple[CanonicalEntityRecord, ...]

    def __post_init__(self) -> None:
        ordered = tuple(sorted(self.records, key=lambda record: record.entity_id.value))
        if ordered != self.records:
            object.__setattr__(self, "records", ordered)

    @classmethod
    def from_repository(cls, repository) -> "EntityRepositoryState":
        records = []
        for entity in repository.get_all():
            records.append(CanonicalEntityRecord(
                entity_id=EntityId(str(entity.entity_id)),
                entity_type=str(entity.entity_type),
                state=entity.get_state(),
                position=Position(entity.position.x, entity.position.y),
                name=str(entity.name),
            ))
        return cls(tuple(records))

    def to_dict(self) -> dict[str, object]:
        return {"records": [record.to_dict() for record in self.records]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "EntityRepositoryState":
        if not isinstance(data, Mapping) or not isinstance(data.get("records"), (list, tuple)):
            raise ValueError("EntityRepositoryState requires records.")
        return cls(tuple(CanonicalEntityRecord.from_dict(record) for record in data["records"]))


@dataclass(frozen=True, order=True)
class MembershipRecord:
    entity_id: EntityId
    world_id: WorldId

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, EntityId):
            raise TypeError("entity_id must be EntityId.")
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be WorldId.")

    def to_dict(self) -> dict[str, str]:
        return {"entity_id": str(self.entity_id), "world_id": str(self.world_id)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "MembershipRecord":
        required = {"entity_id", "world_id"}
        if not isinstance(data, Mapping) or not required.issubset(data):
            raise ValueError("MembershipRecord is missing required fields.")
        return cls(EntityId(data["entity_id"]), WorldId(data["world_id"]))


@dataclass(frozen=True)
class WorldMembershipState:
    records: tuple[MembershipRecord, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", tuple(sorted(self.records)))

    @classmethod
    def from_service(cls, service) -> "WorldMembershipState":
        records = []
        for world in service.world_registry.get_all():
            for entity_id in service.entity_ids_for(world.world_id):
                records.append(MembershipRecord(EntityId(str(entity_id)), WorldId(str(world.world_id))))
        return cls(tuple(records))

    def to_dict(self) -> dict[str, object]:
        return {"records": [record.to_dict() for record in self.records]}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "WorldMembershipState":
        if not isinstance(data, Mapping) or not isinstance(data.get("records"), (list, tuple)):
            raise ValueError("WorldMembershipState requires records.")
        records = tuple(MembershipRecord.from_dict(item) for item in data["records"])
        return cls(records)


@dataclass(frozen=True)
class CanonicalSessionState:
    worlds: tuple[Mapping[str, object], ...]
    entities: EntityRepositoryState
    memberships: WorldMembershipState
    active_world_id: WorldId | None
    simulation_tick: int

    def __post_init__(self) -> None:
        if isinstance(self.simulation_tick, bool) or not isinstance(self.simulation_tick, int) or self.simulation_tick < 0:
            raise ValueError("simulation_tick must be a non-negative integer.")
        world_records = tuple(MappingProxyType(deepcopy(dict(world))) for world in self.worlds)
        if all("world_id" in world for world in world_records):
            world_records = tuple(sorted(world_records, key=lambda world: world["world_id"]))
        object.__setattr__(self, "worlds", world_records)

    def to_dict(self) -> dict[str, object]:
        return {
            "worlds": [deepcopy(dict(world)) for world in self.worlds],
            "entities": self.entities.to_dict(),
            "memberships": self.memberships.to_dict(),
            "active_world_id": str(self.active_world_id) if self.active_world_id else None,
            "simulation_tick": self.simulation_tick,
        }

    @classmethod
    def from_session(cls, session) -> "CanonicalSessionState":
        worlds = tuple(
            world.domain_state.to_dict()
            for world in sorted(
                session.worlds.get_all(),
                key=lambda item: item.domain_state.world_id,
            )
        )
        active_id = session.worlds.get_active_id()
        return cls(
            worlds=worlds,
            entities=EntityRepositoryState.from_repository(session.entities),
            memberships=WorldMembershipState.from_service(session.membership),
            active_world_id=WorldId(str(active_id)) if active_id else None,
            simulation_tick=session.simulation.current_tick.value,
        )

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "CanonicalSessionState":
        if not isinstance(data, Mapping):
            raise ValueError("CanonicalSessionState must be an object.")
        required = {"worlds", "entities", "memberships", "active_world_id", "simulation_tick"}
        missing = required - set(data)
        if missing:
            raise ValueError(f"CanonicalSessionState is missing required fields: {sorted(missing)}")
        if not isinstance(data["worlds"], (list, tuple)):
            raise ValueError("CanonicalSessionState worlds must be a sequence.")
        worlds = tuple(sorted(
            (
                WorldDomainState.from_persistence(world).to_dict()
                for world in data["worlds"]
            ),
            key=lambda world: world["world_id"],
        ))
        active_id = data.get("active_world_id")
        return cls(
            worlds=worlds,
            entities=EntityRepositoryState.from_dict(data["entities"]),
            memberships=WorldMembershipState.from_dict(data["memberships"]),
            active_world_id=WorldId(active_id) if active_id is not None else None,
            simulation_tick=data["simulation_tick"],
        )
