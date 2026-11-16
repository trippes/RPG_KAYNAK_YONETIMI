"""Validated, immutable runtime snapshot decoding."""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from collections.abc import Mapping
from typing import Any

from hex_world_lab.geometry import AxialCoord
from hex_world_lab.world.identity import MapId, WorldId
from hex_world_lab.world.map_definition import HexMapDefinition
from hex_world_lab.world.runtime import RuntimeCellOverride
from .runtime_validator import validate_runtime_payload


@dataclass(frozen=True, slots=True)
class RuntimeMapSnapshot:
    """Immutable, fully validated snapshot for exactly one map."""

    world_id: WorldId
    map_id: MapId
    base_map_sha256: str
    overrides: Mapping[AxialCoord, RuntimeCellOverride]


def deserialize_runtime_payload(
    payload: Any, map_definition: HexMapDefinition
) -> RuntimeMapSnapshot:
    data = validate_runtime_payload(payload, map_definition)
    overrides = {}
    for item in data["overrides"]:
        coord = AxialCoord(item["q"], item["r"])
        overrides[coord] = RuntimeCellOverride(
            terrain_id=item.get("terrain_id"),
            is_walkable=item.get("is_walkable"),
            has_obstacle=item.get("has_obstacle"),
        )
    return RuntimeMapSnapshot(
        world_id=WorldId(data["world_id"]),
        map_id=MapId(data["map_id"]),
        base_map_sha256=data["base_map_sha256"],
        overrides=MappingProxyType(overrides),
    )
