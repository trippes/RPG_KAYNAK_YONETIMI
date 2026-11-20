"""Versioned, runtime-independent snapshots for authoritative hex positions."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from core.domain.spatial import (
    AABB, ContinuousEntityPosition, EntityPosition, LocalHexPosition, MovementProfile,
    WorldPoint, axial_to_world_point, world_point_to_hex,
)
from core.domain.physics import CircleShape, PhysicsBodyDefinition
from core.foundation import WorldId

from .hex_world_runtime import HexWorldRuntime


HEX_WORLD_SCHEMA = "rpg-hex-world"
HEX_WORLD_SCHEMA_VERSION = 2


class HexWorldPersistenceError(ValueError):
    """Invalid hex-world snapshot or unsafe restore target."""


def _npc_local_bounds(body: PhysicsBodyDefinition) -> AABB:
    """Rebuild an NPC collider AABB from immutable content after snapshot restore."""
    offset = body.local_offset
    shape = body.collider
    if isinstance(shape, CircleShape):
        center = WorldPoint(offset.x + shape.center.x, offset.y + shape.center.y)
        return AABB.around_point(center, shape.radius)
    points = tuple(
        WorldPoint(offset.x + vertex.x, offset.y + vertex.y)
        for vertex in shape.vertices
    )
    return AABB(
        min(point.x for point in points), min(point.y for point in points),
        max(point.x for point in points), max(point.y for point in points),
    )


@dataclass(frozen=True, slots=True)
class HexWorldEntityRecord:
    entity_id: str
    kind: str
    position: EntityPosition
    profile: MovementProfile
    active: bool
    blocks_movement: bool
    blocks_occupancy: bool
    continuous_position: ContinuousEntityPosition | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise ValueError("entity_id must be a non-empty string.")
        if not isinstance(self.kind, str) or self.kind not in {"player", "npc", "object"}:
            raise ValueError("kind must be player, npc, or object.")
        if not isinstance(self.position, EntityPosition):
            raise TypeError("position must be an EntityPosition.")
        if not isinstance(self.profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")
        if not isinstance(self.active, bool):
            raise TypeError("active must be a boolean.")
        if not isinstance(self.blocks_movement, bool):
            raise TypeError("blocks_movement must be a boolean.")
        if not isinstance(self.blocks_occupancy, bool):
            raise TypeError("blocks_occupancy must be a boolean.")
        continuous = self.continuous_position
        if continuous is None:
            center = axial_to_world_point(
                self.position.cell.to_hex_coord(), HexWorldRuntime.HEX_SIZE
            )
            continuous = ContinuousEntityPosition(self.position.map_id, center)
            object.__setattr__(self, "continuous_position", continuous)
        if not isinstance(continuous, ContinuousEntityPosition):
            raise TypeError("continuous_position must be a ContinuousEntityPosition.")
        if continuous.map_id != self.position.map_id:
            raise ValueError("continuous position belongs to a different map.")
        resolved = LocalHexPosition.from_hex_coord(
            world_point_to_hex(
                continuous.point, HexWorldRuntime.HEX_SIZE,
                previous_cell=self.position.cell.to_hex_coord(),
            )
        )
        if resolved != self.position.cell:
            raise ValueError("continuous position does not resolve to the record cell.")


@dataclass(frozen=True, slots=True)
class HexWorldSnapshot:
    """Serializable position/occupancy state; map geometry remains content-owned."""

    world_id: WorldId
    entities: tuple[HexWorldEntityRecord, ...]
    patrol_indices: tuple[tuple[str, int], ...] = ()
    schema: str = HEX_WORLD_SCHEMA
    schema_version: int = HEX_WORLD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId.")
        if self.schema != HEX_WORLD_SCHEMA:
            raise HexWorldPersistenceError("Unknown hex-world schema identifier.")
        if type(self.schema_version) is not int or self.schema_version != HEX_WORLD_SCHEMA_VERSION:
            raise HexWorldPersistenceError("Unsupported hex-world snapshot version.")
        entities = tuple(self.entities)
        if any(not isinstance(item, HexWorldEntityRecord) for item in entities):
            raise TypeError("entities must contain HexWorldEntityRecord values.")
        entity_ids = [item.entity_id for item in entities]
        if len(entity_ids) != len(set(entity_ids)):
            raise HexWorldPersistenceError("Duplicate entity IDs in hex-world snapshot.")
        object.__setattr__(self, "entities", tuple(sorted(entities, key=lambda item: item.entity_id)))

        patrol = tuple(self.patrol_indices)
        normalized_patrol = []
        for item in patrol:
            if not isinstance(item, tuple) or len(item) != 2:
                raise TypeError("patrol_indices must contain (entity_id, index) pairs.")
            entity_id, index = item
            if not isinstance(entity_id, str) or not entity_id.strip():
                raise ValueError("patrol entity IDs must be non-empty strings.")
            if type(index) is not int or index < 0:
                raise ValueError("patrol indices must be non-negative integers.")
            record = next((value for value in entities if value.entity_id == entity_id), None)
            if record is None or record.kind != "npc":
                raise HexWorldPersistenceError(
                    "Patrol progress must reference an NPC in the same snapshot."
                )
            normalized_patrol.append((entity_id, index))
        if len({entity_id for entity_id, _ in normalized_patrol}) != len(normalized_patrol):
            raise HexWorldPersistenceError("Duplicate NPC patrol progress records.")
        object.__setattr__(
            self,
            "patrol_indices",
            tuple(sorted(normalized_patrol, key=lambda item: item[0])),
        )

    @classmethod
    def from_runtime(cls, runtime: HexWorldRuntime) -> "HexWorldSnapshot":
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime.")
        if runtime.world_id is None:
            raise HexWorldPersistenceError(
                "An unscoped HexWorldRuntime cannot be persisted."
            )
        occupants = {
            occupant.entity_id: occupant
            for occupant in runtime.occupancy.snapshot()
        }
        try:
            runtime_entities = runtime.entities()
        except RuntimeError as error:
            raise HexWorldPersistenceError(
                "Runtime entity and occupancy registries are inconsistent."
            ) from error
        if set(occupants) != {entity.entity_id for entity in runtime_entities}:
            raise HexWorldPersistenceError(
                "Runtime entity and occupancy registries are inconsistent."
            )
        records = []
        for entity in runtime_entities:
            occupant = occupants.get(entity.entity_id)
            if occupant is None:
                raise HexWorldPersistenceError(
                    f"Missing authoritative occupancy for '{entity.entity_id}'."
                )
            if occupant.kind != entity.kind:
                raise HexWorldPersistenceError(
                    f"Entity/occupancy kind mismatch for '{entity.entity_id}'."
                )
            records.append(HexWorldEntityRecord(
                entity.entity_id,
                entity.kind,
                entity.position,
                entity.profile,
                entity.active,
                occupant.blocks_movement,
                occupant.blocks_occupancy,
                entity.continuous_position,
            ))
        return cls(
            runtime.world_id,
            tuple(records),
            tuple(runtime.patrol_indices.items()),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": self.schema,
            "schema_version": self.schema_version,
            "world_id": self.world_id.value,
            "entities": [
                {
                    "entity_id": item.entity_id,
                    "kind": item.kind,
                    "position": {
                        "map_id": item.position.map_id,
                        "q": item.position.cell.q,
                        "r": item.position.cell.r,
                    },
                    "continuous_position": {
                        "x": item.continuous_position.x,
                        "y": item.continuous_position.y,
                    },
                    "profile": {
                        "can_move": item.profile.can_move,
                        "allowed_terrain_ids": (
                            sorted(item.profile.allowed_terrain_ids)
                            if item.profile.allowed_terrain_ids is not None else None
                        ),
                        "can_traverse_blocked_cells": item.profile.can_traverse_blocked_cells,
                        "ignores_occupancy": item.profile.ignores_occupancy,
                    },
                    "active": item.active,
                    "blocks_movement": item.blocks_movement,
                    "blocks_occupancy": item.blocks_occupancy,
                }
                for item in self.entities
            ],
            "patrol_indices": [
                {"entity_id": entity_id, "index": index}
                for entity_id, index in self.patrol_indices
            ],
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "HexWorldSnapshot":
        if not isinstance(data, Mapping):
            raise HexWorldPersistenceError("Hex-world snapshot must be an object.")
        expected = {"schema", "schema_version", "world_id", "entities", "patrol_indices"}
        if set(data) != expected:
            raise HexWorldPersistenceError("Hex-world snapshot has missing or unknown fields.")
        if data.get("schema") != HEX_WORLD_SCHEMA:
            raise HexWorldPersistenceError("Unknown hex-world schema identifier.")
        version = data.get("schema_version")
        if type(version) is not int or version not in {1, HEX_WORLD_SCHEMA_VERSION}:
            raise HexWorldPersistenceError("Unsupported hex-world snapshot version.")
        world_value = data.get("world_id")
        if not isinstance(world_value, str) or not world_value.strip():
            raise HexWorldPersistenceError("world_id must be a non-empty string.")
        raw_entities = data.get("entities")
        raw_patrol = data.get("patrol_indices")
        if not isinstance(raw_entities, list) or not isinstance(raw_patrol, list):
            raise HexWorldPersistenceError("entities and patrol_indices must be lists.")

        records = []
        for raw in raw_entities:
            expected_entity_fields = {
                "entity_id", "kind", "position", "profile", "active",
                "blocks_movement", "blocks_occupancy",
            }
            if version >= 2:
                expected_entity_fields.add("continuous_position")
            if not isinstance(raw, Mapping) or set(raw) != expected_entity_fields:
                raise HexWorldPersistenceError("Malformed hex entity record.")
            position = raw.get("position")
            if not isinstance(position, Mapping) or set(position) != {"map_id", "q", "r"}:
                raise HexWorldPersistenceError("Malformed axial entity position.")
            q, r = position.get("q"), position.get("r")
            if type(q) is not int or type(r) is not int:
                raise HexWorldPersistenceError("Axial q/r coordinates must be integers.")
            profile = raw.get("profile")
            if not isinstance(profile, Mapping) or set(profile) != {
                "can_move", "allowed_terrain_ids",
                "can_traverse_blocked_cells", "ignores_occupancy",
            }:
                raise HexWorldPersistenceError("Malformed movement profile.")
            allowed = profile.get("allowed_terrain_ids")
            if allowed is not None and (
                not isinstance(allowed, list)
                or any(not isinstance(value, str) or not value.strip() for value in allowed)
                or len(allowed) != len(set(allowed))
            ):
                raise HexWorldPersistenceError("Invalid allowed_terrain_ids list.")
            continuous_position = None
            if version >= 2:
                raw_continuous = raw.get("continuous_position")
                if not isinstance(raw_continuous, Mapping) or set(raw_continuous) != {"x", "y"}:
                    raise HexWorldPersistenceError("Malformed continuous entity position.")
                try:
                    continuous_position = ContinuousEntityPosition.from_xy(
                        position["map_id"], raw_continuous["x"], raw_continuous["y"]
                    )
                except (TypeError, ValueError) as error:
                    raise HexWorldPersistenceError("Invalid continuous entity position.") from error
            try:
                records.append(HexWorldEntityRecord(
                    raw["entity_id"],
                    raw["kind"],
                    EntityPosition(position["map_id"], LocalHexPosition(q, r)),
                    MovementProfile(
                        profile["can_move"],
                        frozenset(allowed) if allowed is not None else None,
                        profile["can_traverse_blocked_cells"],
                        profile["ignores_occupancy"],
                    ),
                    raw["active"],
                    raw["blocks_movement"],
                    raw["blocks_occupancy"],
                    continuous_position,
                ))
            except (KeyError, TypeError, ValueError) as error:
                raise HexWorldPersistenceError("Invalid hex entity record.") from error

        patrol_indices = []
        for raw in raw_patrol:
            if not isinstance(raw, Mapping) or set(raw) != {"entity_id", "index"}:
                raise HexWorldPersistenceError("Malformed patrol progress record.")
            patrol_indices.append((raw["entity_id"], raw["index"]))

        try:
            return cls(
                WorldId(world_value),
                tuple(records),
                tuple(patrol_indices),
                schema=data["schema"],
                schema_version=HEX_WORLD_SCHEMA_VERSION,
            )
        except (TypeError, ValueError) as error:
            if isinstance(error, HexWorldPersistenceError):
                raise
            raise HexWorldPersistenceError("Invalid hex-world snapshot.") from error

    def validate_domain_owners(
        self,
        *,
        actors,
        npcs,
        resource_nodes,
        containers,
        membership,
    ) -> None:
        """Reject spatial IDs that do not resolve to a domain owner in this world."""
        world_value = self.world_id.value
        for record in self.entities:
            if record.kind in {"player", "npc"}:
                actor = actors.get(record.entity_id)
                if actor is None:
                    raise HexWorldPersistenceError(
                        f"Spatial actor owner is missing: {record.entity_id}"
                    )
                if actor.world_id != world_value:
                    raise HexWorldPersistenceError(
                        f"Spatial actor belongs to another world: {record.entity_id}"
                    )
                if record.kind == "npc" and npcs.get(record.entity_id) is None:
                    raise HexWorldPersistenceError(
                        f"Spatial NPC domain record is missing: {record.entity_id}"
                    )
                continue

            node = resource_nodes.get(record.entity_id)
            if node is not None:
                if node.world_id != world_value:
                    raise HexWorldPersistenceError(
                        f"Resource node belongs to another world: {record.entity_id}"
                    )
                continue

            container = containers.for_entity(record.entity_id)
            if container is None:
                raise HexWorldPersistenceError(
                    f"Spatial object has no resource/container owner: {record.entity_id}"
                )
            if membership.world_id_for(container.entity_id) != world_value:
                raise HexWorldPersistenceError(
                    f"Container entity is not a member of this world: {record.entity_id}"
                )
            if (
                containers.parent_of(container.container_id) is not None
                or containers.inventory_custody(container.container_id) is not None
            ):
                raise HexWorldPersistenceError(
                    f"Nested or carried container cannot have a world position: {record.entity_id}"
                )

    def restore_into(
        self,
        runtime: HexWorldRuntime,
        *,
        npc_registry=None,
    ) -> HexWorldRuntime:
        """Restore atomically; rebuild NPC collider bounds from content when supplied.

        The snapshot intentionally contains no collider data. Production restore
        callers pass the already-restored NPCRegistry so immutable physics
        definitions reconstruct broadphase bounds without changing schema v2.
        """
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime.")
        if npc_registry is not None and not callable(getattr(npc_registry, "get", None)):
            raise TypeError("npc_registry must provide a callable get method.")
        if runtime.world_id != self.world_id:
            raise HexWorldPersistenceError(
                "Snapshot and runtime belong to different worlds."
            )
        if runtime.entities() or runtime.occupancy.snapshot():
            raise HexWorldPersistenceError("Restore target runtime must be empty.")

        for record in self.entities:
            try:
                definition = runtime.map_definition(record.position.map_id)
            except KeyError as error:
                raise HexWorldPersistenceError(
                    f"Snapshot references unknown map '{record.position.map_id}'."
                ) from error
            if not definition.has_cell(record.position.cell):
                raise HexWorldPersistenceError(
                    f"Snapshot position for '{record.entity_id}' is outside map valid_cells."
                )
            if (
                definition.is_blocked(record.position.cell)
                and not record.profile.can_traverse_blocked_cells
            ):
                raise HexWorldPersistenceError(
                    f"Snapshot places '{record.entity_id}' on a blocked cell."
                )

        if npc_registry is None and any(record.kind == "npc" for record in self.entities):
            raise HexWorldPersistenceError(
                "NPC registry is required to rebuild collider bounds during restore."
            )

        registered = []
        try:
            for record in self.entities:
                local_spatial_bounds = None
                broadphase_enabled = True
                if record.kind == "npc" and npc_registry is not None:
                    npc = npc_registry.get(record.entity_id)
                    if npc is None:
                        raise HexWorldPersistenceError(
                            f"NPC content record is missing during restore: {record.entity_id}"
                        )
                    body = npc.physics_body
                    if not isinstance(body, PhysicsBodyDefinition):
                        raise HexWorldPersistenceError(
                            f"NPC physics definition is missing during restore: {record.entity_id}"
                        )
                    local_spatial_bounds = _npc_local_bounds(body)
                    broadphase_enabled = body.enabled
                runtime.register_entity(
                    record.entity_id,
                    record.kind,
                    record.position,
                    record.profile,
                    active=record.active,
                    blocks_movement=record.blocks_movement,
                    blocks_occupancy=record.blocks_occupancy,
                    continuous_position=record.continuous_position,
                    local_spatial_bounds=local_spatial_bounds,
                    broadphase_enabled=broadphase_enabled,
                )
                registered.append(record.entity_id)
            runtime.restore_patrol_indices(dict(self.patrol_indices))
        except Exception as error:
            for entity_id in reversed(registered):
                runtime.remove_entity(entity_id)
            runtime.restore_patrol_indices({})
            raise HexWorldPersistenceError(
                "Hex-world snapshot could not be restored atomically."
            ) from error
        return runtime


__all__ = [
    "HEX_WORLD_SCHEMA",
    "HEX_WORLD_SCHEMA_VERSION",
    "HexWorldEntityRecord",
    "HexWorldPersistenceError",
    "HexWorldSnapshot",
]
