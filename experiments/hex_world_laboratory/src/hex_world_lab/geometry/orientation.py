"""Supported regular-hexagon orientations."""
from enum import Enum

class HexOrientation(str, Enum):
    """Hex orientation; coordinates use a mathematical y-up world axis."""
    FLAT_TOP = "flat_top"
    POINTY_TOP = "pointy_top"
