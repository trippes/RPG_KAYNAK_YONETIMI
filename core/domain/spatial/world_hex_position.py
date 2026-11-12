"""World-level axial coordinates, distinct from map-local positions."""

from __future__ import annotations

from dataclasses import dataclass

from .hex_coord import HexCoord
from .hex_direction import HexDirection


@dataclass(frozen=True, order=True, slots=True)
class WorldHexPosition:
    """An immutable axial coordinate locating a map in the world topology."""

    q: int
    r: int

    def __post_init__(self) -> None:
        if type(self.q) is not int or type(self.r) is not int:
            raise TypeError("WorldHexPosition q and r must be integers.")

    @classmethod
    def from_hex_coord(cls, coord: HexCoord) -> "WorldHexPosition":
        if not isinstance(coord, HexCoord):
            raise TypeError("coord must be a HexCoord.")
        return cls(coord.q, coord.r)

    def to_hex_coord(self) -> HexCoord:
        return HexCoord(self.q, self.r)

    def neighbor(self, direction: HexDirection) -> "WorldHexPosition":
        return WorldHexPosition.from_hex_coord(self.to_hex_coord().neighbor(direction))

    def distance_to(self, other: "WorldHexPosition") -> int:
        if not isinstance(other, WorldHexPosition):
            raise TypeError("other must be a WorldHexPosition.")
        return self.to_hex_coord().distance_to(other.to_hex_coord())
