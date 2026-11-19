"""Deterministic runtime override snapshot serialization."""

from __future__ import annotations

import json
from typing import Any

from hex_world_lab.world.runtime import HexWorldRuntime
from hex_world_lab.world.map_definition import HexMapDefinition
from .runtime_errors import RuntimeValidationError
from .runtime_validator import base_map_sha256


def runtime_to_payload(runtime: HexWorldRuntime, map_definition: HexMapDefinition) -> dict[str, Any]:
    if not isinstance(runtime, HexWorldRuntime):
        raise TypeError("runtime must be a HexWorldRuntime")
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition")
    if runtime.world_id != map_definition.world_id:
        raise RuntimeValidationError("runtime and map belong to different worlds", "$.world_id")
    loaded = runtime.require_loaded_map(map_definition.map_id)
    if loaded != map_definition:
        raise RuntimeValidationError("provided map definition is not the loaded base map", "$.map_id")

    overrides = []
    for coord, override in runtime.export_map_overrides(map_definition.map_id).items():
        item: dict[str, Any] = {"q": coord.q, "r": coord.r}
        if override.terrain_id is not None:
            item["terrain_id"] = override.terrain_id
        if override.is_walkable is not None:
            item["is_walkable"] = override.is_walkable
        if override.has_obstacle is not None:
            item["has_obstacle"] = override.has_obstacle
        if len(item) > 2:
            overrides.append(item)
    return {
        "schema_version": 1,
        "kind": "hex_world_runtime_snapshot",
        "world_id": map_definition.world_id.value,
        "map_id": map_definition.map_id.value,
        "base_map_sha256": base_map_sha256(map_definition),
        "overrides": overrides,
    }


def serialize_runtime(runtime: HexWorldRuntime, map_definition: HexMapDefinition) -> str:
    try:
        return json.dumps(
            runtime_to_payload(runtime, map_definition),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
    except (TypeError, ValueError) as exc:
        if isinstance(exc, RuntimeValidationError):
            raise
        raise RuntimeValidationError(f"runtime snapshot cannot be serialized: {exc}") from exc
