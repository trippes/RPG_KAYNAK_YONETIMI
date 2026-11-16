"""Deterministic conversion from immutable map models to JSON text."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from hex_world_lab.world.map_definition import HexMapDefinition
from .errors import MapValidationError


def _json_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _json_value(item) for key, item in sorted(value.items())}
    if isinstance(value, tuple):
        return [_json_value(item) for item in value]
    return value


def map_to_payload(map_definition: HexMapDefinition) -> dict[str, Any]:
    """Return a fresh schema-v1 JSON-compatible mapping."""
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition")
    cells = []
    for coord, data in sorted(
        map_definition.cells.items(), key=lambda item: (item[0].q, item[0].r)
    ):
        cells.append(
            {
                "q": coord.q,
                "r": coord.r,
                "terrain_id": data.terrain_id,
                "is_walkable": data.is_walkable,
                "has_obstacle": data.has_obstacle,
                "metadata": None if data.metadata is None else _json_value(data.metadata),
            }
        )
    return {
        "schema_version": 1,
        "world_id": map_definition.world_id.value,
        "map_id": map_definition.map_id.value,
        "name": map_definition.name,
        "layout": {
            "orientation": map_definition.layout.orientation.value,
            "radius": map_definition.layout.radius,
            "origin": {
                "x": map_definition.layout.origin.x,
                "y": map_definition.layout.origin.y,
            },
        },
        "cells": cells,
    }


def serialize_map(map_definition: HexMapDefinition) -> str:
    """Serialize a map to stable, UTF-8-compatible JSON text with a final newline."""
    try:
        return json.dumps(
            map_to_payload(map_definition),
            ensure_ascii=False,
            allow_nan=False,
            indent=2,
            sort_keys=True,
        ) + "\n"
    except (TypeError, ValueError) as exc:
        raise MapValidationError(f"map cannot be represented as schema v1: {exc}") from exc
