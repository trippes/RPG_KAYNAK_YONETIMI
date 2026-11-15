"""Hex layout parameters shared by all geometry operations."""
from dataclasses import dataclass
import math
from .coordinates import WorldPoint
from .orientation import HexOrientation

@dataclass(frozen=True, slots=True)
class HexLayout:
    """Regular-hex layout; radius is center-to-vertex circumradius."""
    orientation: HexOrientation
    radius: float = 1.0
    origin: WorldPoint = WorldPoint(0.0, 0.0)
    def __post_init__(self):
        if not isinstance(self.orientation, HexOrientation):
            raise TypeError("orientation must be a HexOrientation")
        if not math.isfinite(self.radius) or self.radius <= 0:
            raise ValueError("radius must be finite and greater than zero")
        if not isinstance(self.origin, WorldPoint):
            raise TypeError("origin must be a WorldPoint")
