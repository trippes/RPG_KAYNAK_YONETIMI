"""Authoritative foundation-support evidence derived from map terrain metadata."""
from __future__ import annotations

from core.domain.spatial import HexCoord, LocalHexPosition
from application.hex_map_definition import HexMapDefinition


class ConstructionSupportService:
    """Resolve ground-foundation support from explicit terrain capabilities.

    Walkability and collision flags are deliberately ignored: a blocked rock
    cell may be load-bearing, while a walkable marsh need not be. Unknown
    terrain capabilities are unsupported (fail closed).
    """

    def supported_foundation_cells(
        self, map_definition: HexMapDefinition
    ) -> frozenset[HexCoord]:
        if not isinstance(map_definition, HexMapDefinition):
            raise TypeError("map_definition must be a HexMapDefinition.")
        supported_terrain = map_definition.foundation_supporting_terrain_ids
        return frozenset(
            cell.position.to_hex_coord()
            for cell in map_definition.cells.values()
            if cell.terrain_id in supported_terrain
        )


__all__ = ["ConstructionSupportService"]
