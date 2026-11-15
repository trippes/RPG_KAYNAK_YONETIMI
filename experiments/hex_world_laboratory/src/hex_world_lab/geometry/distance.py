"""Hex-grid distance calculations."""
from .coordinates import AxialCoord

def hex_distance(first: AxialCoord, second: AxialCoord) -> int:
    """Return the shortest number of hex edges between two axial cells."""
    dq, dr = first.q-second.q, first.r-second.r
    return max(abs(dq), abs(dr), abs(-dq-dr))
