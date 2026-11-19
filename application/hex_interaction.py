"""Application-level target lookup for world-space NPC interactions."""

from __future__ import annotations

from core.domain.spatial import (
    AABB,
    LocalHexPosition,
    WorldPoint,
    axial_to_world_point,
    world_point_to_hex,
)
from .hex_world_runtime import HexWorldRuntime


class HexInteractionService:
    """Resolve world-space interaction targets without putting rules in the view."""

    def __init__(self, runtime: HexWorldRuntime) -> None:
        if not isinstance(runtime, HexWorldRuntime):
            raise TypeError("runtime must be a HexWorldRuntime.")
        self._runtime = runtime

    def npc_at_world_point(self, map_id: str, point: WorldPoint) -> str | None:
        """Return the stable ID of an NPC in the clicked hex, if one exists.

        The spatial hash supplies candidates; map-cell resolution and entity
        kind/map checks remain exact. Stable actor ID is the final tie-break.
        """
        if not isinstance(map_id, str) or not map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        if not isinstance(point, WorldPoint):
            raise TypeError("point must be a WorldPoint.")
        map_definition = self._runtime.map_definition(map_id)
        cell_coord = world_point_to_hex(point, self._runtime.HEX_SIZE)
        cell = LocalHexPosition.from_hex_coord(cell_coord)
        if not map_definition.has_cell(cell):
            return None

        center = axial_to_world_point(cell_coord, self._runtime.HEX_SIZE)
        candidates = self._runtime.query_spatial_candidates(
            map_id,
            AABB.around_point(center, self._runtime.HEX_SIZE),
        )
        for entity_id in candidates:
            entity = self._runtime.entity(entity_id)
            if (
                entity.kind == "npc"
                and entity.position.map_id == map_id
                and entity.position.cell == cell
            ):
                return entity_id
        return None


__all__ = ["HexInteractionService"]
