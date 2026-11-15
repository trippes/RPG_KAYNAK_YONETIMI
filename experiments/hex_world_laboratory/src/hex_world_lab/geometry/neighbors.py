"""Axial neighbor directions and neighbor lookup."""
from .coordinates import AxialCoord

AXIAL_DIRECTIONS = (
    AxialCoord(1, 0), AxialCoord(1, -1), AxialCoord(0, -1),
    AxialCoord(-1, 0), AxialCoord(-1, 1), AxialCoord(0, 1),
)

def hex_neighbors(coord: AxialCoord) -> tuple[AxialCoord, ...]:
    return tuple(AxialCoord(coord.q+d.q, coord.r+d.r) for d in AXIAL_DIRECTIONS)
