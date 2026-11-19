"""Strict validation for runtime snapshot JSON schema version 1."""

from __future__ import annotations

import hashlib
import re
from typing import Any

from hex_world_lab.geometry import AxialCoord
from hex_world_lab.world.map_definition import HexMapDefinition
from .map_serializer import serialize_map
from .runtime_errors import (
    RuntimeBaseMapMismatchError,
    RuntimeMapMismatchError,
    RuntimeSchemaVersionError,
    RuntimeValidationError,
    RuntimeWorldMismatchError,
)

_TOP = {"schema_version", "kind", "world_id", "map_id", "base_map_sha256", "overrides"}
_OVERRIDE = {"q", "r", "terrain_id", "is_walkable", "has_obstacle"}
_HASH = re.compile(r"^[0-9a-f]{64}$")


def base_map_sha256(map_definition: HexMapDefinition) -> str:
    """Hash the canonical Stage 3.6 UTF-8 map serialization."""
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition")
    return hashlib.sha256(serialize_map(map_definition).encode("utf-8")).hexdigest()


def _object(value: Any, allowed: set[str], required: set[str], path: str) -> dict:
    if not isinstance(value, dict):
        raise RuntimeValidationError("must be an object", path)
    unknown = set(value) - allowed
    missing = required - set(value)
    if unknown:
        key = sorted(unknown)[0]
        raise RuntimeValidationError(f"unknown field {key!r}", f"{path}.{key}")
    if missing:
        key = sorted(missing)[0]
        raise RuntimeValidationError("required field is missing", f"{path}.{key}")
    return value


def validate_runtime_payload(payload: Any, map_definition: HexMapDefinition) -> dict:
    """Validate schema, target identity, base fingerprint, and all cell overrides."""
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition")
    data = _object(payload, _TOP, _TOP, "$")
    version = data["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise RuntimeValidationError("must be an integer", "$.schema_version")
    if version != 1:
        raise RuntimeSchemaVersionError(f"unsupported runtime schema version {version}", "$.schema_version")
    if data["kind"] != "hex_world_runtime_snapshot":
        raise RuntimeValidationError("invalid runtime snapshot kind", "$.kind")
    for key in ("world_id", "map_id"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise RuntimeValidationError("must be a non-empty string", f"$.{key}")
    if data["world_id"] != map_definition.world_id.value:
        raise RuntimeWorldMismatchError("snapshot WorldId does not match target map", "$.world_id")
    if data["map_id"] != map_definition.map_id.value:
        raise RuntimeMapMismatchError("snapshot MapId does not match target map", "$.map_id")
    fingerprint = data["base_map_sha256"]
    if not isinstance(fingerprint, str) or not _HASH.fullmatch(fingerprint):
        raise RuntimeValidationError("must be 64 lowercase hexadecimal characters", "$.base_map_sha256")
    if fingerprint != base_map_sha256(map_definition):
        raise RuntimeBaseMapMismatchError("base map SHA-256 does not match", "$.base_map_sha256")

    raw_overrides = data["overrides"]
    if not isinstance(raw_overrides, list):
        raise RuntimeValidationError("must be an array", "$.overrides")
    seen: set[tuple[int, int]] = set()
    for index, raw in enumerate(raw_overrides):
        path = f"$.overrides[{index}]"
        item = _object(raw, _OVERRIDE, {"q", "r"}, path)
        for axis in ("q", "r"):
            value = item[axis]
            if isinstance(value, bool) or not isinstance(value, int):
                raise RuntimeValidationError("must be an integer (not boolean)", f"{path}.{axis}")
        coord_key = (item["q"], item["r"])
        if coord_key in seen:
            raise RuntimeValidationError("duplicate axial coordinate", path)
        seen.add(coord_key)
        coord = AxialCoord(*coord_key)
        base = map_definition.get_cell_data(coord)
        if base is None:
            raise RuntimeValidationError("cell does not exist in base map", path)
        fields = set(item) - {"q", "r"}
        if not fields:
            raise RuntimeValidationError("at least one override field is required", path)
        for field in fields:
            value = item[field]
            if value is None:
                raise RuntimeValidationError("null is not allowed", f"{path}.{field}")
            if field == "terrain_id":
                if not isinstance(value, str) or not value.strip():
                    raise RuntimeValidationError("must be a non-empty string", f"{path}.{field}")
                if value == base.terrain_id:
                    raise RuntimeValidationError("redundant base-equal override", f"{path}.{field}")
            else:
                if not isinstance(value, bool):
                    raise RuntimeValidationError("must be a boolean", f"{path}.{field}")
                base_value = base.is_walkable if field == "is_walkable" else base.has_obstacle
                if value == base_value:
                    raise RuntimeValidationError("redundant base-equal override", f"{path}.{field}")
    return data
