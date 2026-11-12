"""Immutable world-map placement model and cross-map hex transition validation."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping

from core.domain.spatial import HexDirection, WorldHexPosition


class WorldMapDefinitionError(ValueError):
    """Raised when a world-map definition or its map links are invalid."""


@dataclass(frozen=True, slots=True)
class WorldMapPlacement:
    map_id: str
    position: WorldHexPosition

    def __post_init__(self) -> None:
        if not isinstance(self.map_id, str) or not self.map_id.strip():
            raise WorldMapDefinitionError("placement.map_id must be a non-empty string.")
        if not isinstance(self.position, WorldHexPosition):
            raise TypeError("placement.position must be a WorldHexPosition.")


@dataclass(frozen=True, slots=True)
class WorldMapDefinition:
    schema_version: int
    world_map_id: str
    name: str
    placements: tuple[WorldMapPlacement, ...]
    metadata: Mapping[str, object] = field(compare=False, hash=False)
    _placements_by_map_id: Mapping[str, WorldMapPlacement] = field(init=False, repr=False, compare=False, hash=False)
    _placements_by_position: Mapping[WorldHexPosition, WorldMapPlacement] = field(init=False, repr=False, compare=False, hash=False)

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise WorldMapDefinitionError("Unsupported world map schema_version; expected 1.")
        for field, value in (("id", self.world_map_id), ("name", self.name)):
            if not isinstance(value, str) or not value.strip():
                raise WorldMapDefinitionError(f"world map {field} must be a non-empty string.")
        placements = tuple(self.placements)
        if any(not isinstance(item, WorldMapPlacement) for item in placements):
            raise TypeError("placements must contain WorldMapPlacement values.")
        map_ids = [item.map_id for item in placements]
        positions = [item.position for item in placements]
        if len(map_ids) != len(set(map_ids)):
            raise WorldMapDefinitionError("World map contains duplicate map_id placements.")
        if len(positions) != len(set(positions)):
            raise WorldMapDefinitionError("World map contains duplicate axial coordinates.")
        if not isinstance(self.metadata, Mapping):
            raise TypeError("world map metadata must be a mapping.")
        object.__setattr__(self, "placements", placements)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        object.__setattr__(self, "_placements_by_map_id", MappingProxyType({item.map_id: item for item in placements}))
        object.__setattr__(self, "_placements_by_position", MappingProxyType({item.position: item for item in placements}))

    @property
    def placements_by_map_id(self) -> Mapping[str, WorldMapPlacement]:
        return self._placements_by_map_id

    @property
    def placements_by_position(self) -> Mapping[WorldHexPosition, WorldMapPlacement]:
        return self._placements_by_position

    def get_placement(self, map_id: str) -> WorldMapPlacement | None:
        return self.placements_by_map_id.get(map_id)

    def neighbor(self, map_id: str, direction: HexDirection) -> WorldMapPlacement | None:
        placement = self.get_placement(map_id)
        if placement is None:
            raise KeyError(f"World map '{self.world_map_id}' has no placement for '{map_id}'.")
        return self.placements_by_position.get(placement.position.neighbor(direction))


def _non_empty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise WorldMapDefinitionError(f"{field} must be a non-empty string.")
    return value


def _strict_object(value: object, field: str, allowed: set[str]) -> dict:
    if not isinstance(value, dict):
        raise WorldMapDefinitionError(f"{field} must be an object.")
    unknown = sorted(set(value) - allowed)
    if unknown:
        raise WorldMapDefinitionError(f"{field} has unsupported fields: {', '.join(unknown)}")
    return value


def parse_world_map(data: object) -> WorldMapDefinition:
    """Parse schema-v1 world JSON; map contents remain owned by local map files."""
    root = _strict_object(data, "world map", {"schema_version", "id", "name", "maps", "metadata"})
    if type(root.get("schema_version")) is not int or root["schema_version"] != 1:
        raise WorldMapDefinitionError("Unsupported world map schema_version; expected 1.")
    if "id" not in root or "name" not in root or "maps" not in root:
        missing = sorted({"id", "name", "maps"} - set(root))
        raise WorldMapDefinitionError("world map missing fields: " + ", ".join(missing))
    records = root["maps"]
    if not isinstance(records, list):
        raise WorldMapDefinitionError("world map maps must be a list.")
    placements = []
    for index, raw in enumerate(records):
        item = _strict_object(raw, f"maps[{index}]", {"map_id", "position"})
        if "map_id" not in item or "position" not in item:
            raise WorldMapDefinitionError(f"maps[{index}] requires map_id and position.")
        position = _strict_object(item["position"], f"maps[{index}].position", {"q", "r"})
        if set(position) != {"q", "r"}:
            raise WorldMapDefinitionError(f"maps[{index}].position requires q and r.")
        q, r = position["q"], position["r"]
        if type(q) is not int or type(r) is not int:
            raise WorldMapDefinitionError(f"maps[{index}].position q and r must be integers.")
        placements.append(WorldMapPlacement(
            _non_empty_text(item["map_id"], f"maps[{index}].map_id"),
            WorldHexPosition(q, r),
        ))
    metadata = root.get("metadata", {})
    if not isinstance(metadata, dict):
        raise WorldMapDefinitionError("world map metadata must be an object.")
    return WorldMapDefinition(
        1,
        _non_empty_text(root["id"], "id"),
        _non_empty_text(root["name"], "name"),
        tuple(placements),
        metadata,
    )


def validate_world_map(
    world_map: WorldMapDefinition,
    hex_map_definitions: Mapping[str, object],
) -> None:
    """Validate placement coverage and active local exits against world topology.

    Inactive transitions are editorial placeholders, not traversable links, so
    they may refer to a not-yet-created map. Active links must be fully resolved.
    The local HexMapTransition remains the sole source of transition data.
    """
    if not isinstance(world_map, WorldMapDefinition):
        raise TypeError("world_map must be a WorldMapDefinition.")
    placements = world_map.placements_by_map_id
    known_ids = set(hex_map_definitions)
    unknown = sorted(set(placements) - known_ids)
    if unknown:
        raise WorldMapDefinitionError(
            f"World map '{world_map.world_map_id}' references unknown hex maps: {', '.join(unknown)}."
        )
    unplaced = sorted(known_ids - set(placements))
    if unplaced:
        raise WorldMapDefinitionError(
            f"World map '{world_map.world_map_id}' has unplaced hex maps: {', '.join(unplaced)}."
        )

    for source_map_id, source_definition in hex_map_definitions.items():
        source_placement = placements[source_map_id]
        for transition in source_definition.transitions:
            if not transition.active:
                continue
            transition_label = f"map '{source_map_id}' transition '{transition.transition_id}'"
            target_map_id = transition.target_map_id
            target_definition = hex_map_definitions.get(target_map_id)
            if target_definition is None or target_map_id not in placements:
                raise WorldMapDefinitionError(
                    f"{transition_label} references missing target hex map '{target_map_id}'."
                )
            if not transition.target_cells:
                raise WorldMapDefinitionError(
                    f"{transition_label} must define target_cells for an active transition."
                )
            for cell in transition.source_cells:
                if cell not in source_definition.valid_cells:
                    raise WorldMapDefinitionError(
                        f"{transition_label} source cell ({cell.q}, {cell.r}) is outside valid_cells."
                    )
            for cell in transition.target_cells:
                if cell not in target_definition.valid_cells:
                    raise WorldMapDefinitionError(
                        f"{transition_label} target cell ({cell.q}, {cell.r}) is outside "
                        f"target map '{target_map_id}' valid_cells."
                    )
            target_placement = placements[target_map_id]
            expected_position = source_placement.position.neighbor(transition.exit_direction)
            if target_placement.position != expected_position:
                raise WorldMapDefinitionError(
                    f"{transition_label} direction {transition.exit_direction.name} does not "
                    f"lead to adjacent target map '{target_map_id}'."
                )
            if transition.target_entry_direction != transition.exit_direction.opposite:
                raise WorldMapDefinitionError(
                    f"{transition_label} target_entry_direction must be "
                    f"{transition.exit_direction.opposite.name}."
                )
            if transition.traversal_mode == "bidirectional":
                reciprocal = any(
                    candidate.active
                    and candidate.traversal_mode == "bidirectional"
                    and candidate.target_map_id == source_map_id
                    and candidate.exit_direction == transition.target_entry_direction
                    and candidate.target_entry_direction == transition.exit_direction
                    and set(candidate.source_cells) == set(transition.target_cells)
                    and set(candidate.target_cells) == set(transition.source_cells)
                    for candidate in target_definition.transitions
                )
                if not reciprocal:
                    raise WorldMapDefinitionError(
                        f"{transition_label} requires a reciprocal bidirectional transition "
                        f"in map '{target_map_id}' with reversed cells and directions."
                    )


__all__ = [
    "WorldMapDefinitionError",
    "WorldMapPlacement",
    "WorldMapDefinition",
    "parse_world_map",
    "validate_world_map",
]
