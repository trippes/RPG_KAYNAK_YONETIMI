"""Strict, side-effect-free validation for map JSON schema version 1."""

from __future__ import annotations

import math
from collections.abc import Mapping
from typing import Any

from .errors import MapValidationError, UnsupportedMapSchemaVersionError

_TOP_LEVEL = {"schema_version", "world_id", "map_id", "name", "layout", "cells"}
_LAYOUT = {"orientation", "radius", "origin"}
_ORIGIN = {"x", "y"}
_CELL = {"q", "r", "terrain_id", "is_walkable", "has_obstacle", "metadata"}
_ORIENTATIONS = {"flat_top", "pointy_top"}


def _object(value: Any, path: str, allowed: set[str], required: set[str] | None = None) -> dict:
    if not isinstance(value, dict):
        raise MapValidationError("must be an object", path)
    if any(not isinstance(key, str) for key in value):
        raise MapValidationError("object field names must be strings", path)
    unknown = set(value) - allowed
    if unknown:
        key = sorted(unknown)[0]
        raise MapValidationError(f"unknown field {key!r}", f"{path}.{key}")
    missing = (required if required is not None else allowed) - set(value)
    if missing:
        key = sorted(missing)[0]
        raise MapValidationError("required field is missing", f"{path}.{key}")
    return value


def _nonempty_string(value: Any, path: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise MapValidationError("must be a non-empty string", path)


def _number(value: Any, path: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MapValidationError("must be a number", path)
    try:
        finite_value = math.isfinite(float(value))
    except (OverflowError, ValueError):
        finite_value = False
    if not finite_value:
        raise MapValidationError("must be finite and representable", path)
    if positive and value <= 0:
        raise MapValidationError("must be greater than zero", path)


def _metadata(value: Any, path: str) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise MapValidationError("metadata numbers must be finite", path)
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _metadata(item, f"{path}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise MapValidationError("metadata object keys must be strings", path)
            _metadata(item, f"{path}.{key}")
        return
    raise MapValidationError("must contain only JSON-compatible values", path)


def validate_map_payload(payload: Any) -> dict:
    """Validate a parsed JSON value and return it unchanged when valid.

    This function never constructs or registers world objects. Callers can
    safely build the immutable model only after the entire payload passes.
    """
    data = _object(payload, "$", _TOP_LEVEL)
    version = data["schema_version"]
    if isinstance(version, bool) or not isinstance(version, int):
        raise MapValidationError("must be an integer", "$.schema_version")
    if version != 1:
        raise UnsupportedMapSchemaVersionError(
            f"unsupported schema version {version}; supported version is 1",
            "$.schema_version",
        )

    _nonempty_string(data["world_id"], "$.world_id")
    _nonempty_string(data["map_id"], "$.map_id")
    _nonempty_string(data["name"], "$.name")

    layout = _object(data["layout"], "$.layout", _LAYOUT)
    if not isinstance(layout["orientation"], str) or layout["orientation"] not in _ORIENTATIONS:
        raise MapValidationError(
            "must be 'flat_top' or 'pointy_top'", "$.layout.orientation"
        )
    _number(layout["radius"], "$.layout.radius", positive=True)
    origin = _object(layout["origin"], "$.layout.origin", _ORIGIN)
    _number(origin["x"], "$.layout.origin.x")
    _number(origin["y"], "$.layout.origin.y")

    cells = data["cells"]
    if not isinstance(cells, list):
        raise MapValidationError("must be an array", "$.cells")
    seen: set[tuple[int, int]] = set()
    for index, raw_cell in enumerate(cells):
        path = f"$.cells[{index}]"
        cell = _object(raw_cell, path, _CELL)
        for axis in ("q", "r"):
            value = cell[axis]
            if isinstance(value, bool) or not isinstance(value, int):
                raise MapValidationError("must be a boolean-free integer", f"{path}.{axis}")
        coord = (cell["q"], cell["r"])
        if coord in seen:
            raise MapValidationError(
                f"duplicate axial coordinate ({coord[0]}, {coord[1]})", path
            )
        seen.add(coord)
        _nonempty_string(cell["terrain_id"], f"{path}.terrain_id")
        if not isinstance(cell["is_walkable"], bool):
            raise MapValidationError("must be a boolean", f"{path}.is_walkable")
        if not isinstance(cell["has_obstacle"], bool):
            raise MapValidationError("must be a boolean", f"{path}.has_obstacle")
        _metadata(cell["metadata"], f"{path}.metadata")
        if cell["metadata"] is not None and not isinstance(cell["metadata"], dict):
            raise MapValidationError("must be null or an object", f"{path}.metadata")
    return data
