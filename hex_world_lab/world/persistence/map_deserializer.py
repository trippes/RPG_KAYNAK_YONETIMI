"""Conversion from validated schema-v1 JSON data to immutable map models."""

from __future__ import annotations

from typing import Any

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from .map_validator import validate_map_payload


def deserialize_map_payload(payload: Any) -> HexMapDefinition:
    """Validate a complete payload, then construct exactly one immutable map."""
    data = validate_map_payload(payload)
    layout_data = data["layout"]
    origin_data = layout_data["origin"]
    layout = HexLayout(
        orientation=HexOrientation(layout_data["orientation"]),
        radius=float(layout_data["radius"]),
        origin=WorldPoint(float(origin_data["x"]), float(origin_data["y"])),
    )
    cells = {}
    for item in data["cells"]:
        coord = AxialCoord(item["q"], item["r"])
        cell = HexCellData(
            terrain_id=item["terrain_id"],
            is_walkable=item["is_walkable"],
            has_obstacle=item["has_obstacle"],
            metadata=item["metadata"],
        )
        cells[coord] = cell
    return HexMapDefinition(
        world_id=WorldId(data["world_id"]),
        map_id=MapId(data["map_id"]),
        name=data["name"],
        layout=layout,
        cells=cells,
    )
