"""Immutable result of resolving a continuous position against a hex world."""

from dataclasses import dataclass

from hex_world_lab.geometry import AxialCoord
from hex_world_lab.world.cell import HexCellData
from hex_world_lab.world.identity import CellAddress, MapId, WorldId


@dataclass(frozen=True, slots=True)
class MovementCellResolution:
    """The selected hex address and its current cell data, if that cell exists.

    A resolution describes spatial context only. It never changes or snaps the
    actor's authoritative continuous WorldPoint position.
    """

    world_id: WorldId
    map_id: MapId
    coord: AxialCoord
    address: CellAddress
    cell_data: HexCellData | None

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.coord, AxialCoord):
            raise TypeError("coord must be an AxialCoord")
        if not isinstance(self.address, CellAddress):
            raise TypeError("address must be a CellAddress")
        if self.address.world_id != self.world_id:
            raise ValueError("address world_id does not match resolution")
        if self.address.map_id != self.map_id:
            raise ValueError("address map_id does not match resolution")
        if self.address.coord != self.coord:
            raise ValueError("address coord does not match resolution")
        if self.cell_data is not None and not isinstance(self.cell_data, HexCellData):
            raise TypeError("cell_data must be HexCellData or None")
