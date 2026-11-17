"""Axial neighbor directions and neighbor lookup."""
from .coordinates import AxialCoord

AXIAL_DIRECTIONS = (
    AxialCoord(1, 0), AxialCoord(1, -1), AxialCoord(0, -1),
    AxialCoord(-1, 0), AxialCoord(-1, 1), AxialCoord(0, 1),
)

def hex_neighbors(coord: AxialCoord) -> tuple[AxialCoord, ...]:
    return tuple(AxialCoord(coord.q+d.q, coord.r+d.r) for d in AXIAL_DIRECTIONS)


def hex_radius_cells(coord: AxialCoord, radius: int) -> tuple[AxialCoord, ...]:
    """Return the complete axial disk in deterministic (q, r) order."""
    if not isinstance(coord, AxialCoord):
        raise TypeError("coord must be an AxialCoord")
    if isinstance(radius, bool) or not isinstance(radius, int):
        raise TypeError("radius must be an integer")
    if radius < 0:
        raise ValueError("radius must be non-negative")
    cells = []
    for dq in range(-radius, radius + 1):
        r_min = max(-radius, -dq - radius)
        r_max = min(radius, -dq + radius)
        for dr in range(r_min, r_max + 1):
            cells.append(AxialCoord(coord.q + dq, coord.r + dr))
    return tuple(cells)
