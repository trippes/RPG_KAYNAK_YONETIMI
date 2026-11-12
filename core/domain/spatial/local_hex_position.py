"""Map-local axial coordinates, distinct from geometry-only HexCoord."""
from dataclasses import dataclass
from .hex_coord import HexCoord

@dataclass(frozen=True, order=True, slots=True)
class LocalHexPosition:
    q: int
    r: int

    def __post_init__(self):
        if type(self.q) is not int or type(self.r) is not int:
            raise TypeError("q and r must be integers (bool is not allowed).")

    @classmethod
    def from_hex_coord(cls, coord):
        if not isinstance(coord, HexCoord):
            raise TypeError("coord must be a HexCoord.")
        return cls(coord.q, coord.r)

    def to_hex_coord(self):
        return HexCoord(self.q, self.r)
