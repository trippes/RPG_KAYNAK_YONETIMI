"""Immutable map definitions and explicit cell-boundary queries."""

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from hex_world_lab.geometry import AxialCoord, HexLayout
from hex_world_lab.world.cell import HexCellData
from hex_world_lab.world.identity import MapId, WorldId


class UnknownCellError(LookupError):
    """Raised when a strict query addresses a cell absent from a map."""

    def __init__(self, world_id: WorldId, map_id: MapId, coord: AxialCoord) -> None:
        self.world_id = world_id
        self.map_id = map_id
        self.coord = coord
        super().__init__(
            f"cell ({coord.q}, {coord.r}) does not exist in "
            f"map '{map_id.value}' of world '{world_id.value}'"
        )


@dataclass(frozen=True, slots=True)
class HexMapDefinition:
    """Immutable definition of one map and its explicitly existing hex cells.

    The map owns its coordinate context, so cell queries use AxialCoord rather
    than requiring callers to repeat the world's and map's identifiers.
    An empty cell mapping is valid and represents an empty map.
    """

    world_id: WorldId
    map_id: MapId
    name: str
    layout: HexLayout
    cells: Mapping[AxialCoord, HexCellData]

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace-only")
        if not isinstance(self.layout, HexLayout):
            raise TypeError("layout must be a HexLayout")
        if not isinstance(self.cells, Mapping):
            raise TypeError("cells must be a mapping of AxialCoord to HexCellData")

        copied_cells: dict[AxialCoord, HexCellData] = {}
        for coord, cell_data in self.cells.items():
            if not isinstance(coord, AxialCoord):
                raise TypeError("cell keys must be AxialCoord instances")
            if not isinstance(cell_data, HexCellData):
                raise TypeError("cell values must be HexCellData instances")
            copied_cells[coord] = cell_data

        object.__setattr__(self, "cells", MappingProxyType(copied_cells))

    def get_cell_data(self, coord: AxialCoord) -> HexCellData | None:
        """Return cell data, or None when the coordinate is outside this map."""
        self._validate_coord(coord)
        return self.cells.get(coord)

    def require_cell_data(self, coord: AxialCoord) -> HexCellData:
        """Return cell data or raise UnknownCellError when the cell is absent."""
        self._validate_coord(coord)
        try:
            return self.cells[coord]
        except KeyError:
            raise UnknownCellError(self.world_id, self.map_id, coord) from None

    @staticmethod
    def _validate_coord(coord: AxialCoord) -> None:
        if not isinstance(coord, AxialCoord):
            raise TypeError("coord must be an AxialCoord")
