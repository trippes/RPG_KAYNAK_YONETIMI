"""Immutable coordinate value objects for hex-grid geometry."""
from dataclasses import dataclass
import math

@dataclass(frozen=True, slots=True)
class AxialCoord:
    """Integer axial hex coordinate (q, r)."""
    q: int
    r: int
    def __post_init__(self):
        for name, value in (("q", self.q), ("r", self.r)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")

@dataclass(frozen=True, slots=True)
class CubeCoord:
    """Integer cube coordinate (q, r, s), constrained by q + r + s = 0."""
    q: int
    r: int
    s: int
    def __post_init__(self):
        for name, value in (("q", self.q), ("r", self.r), ("s", self.s)):
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError(f"{name} must be an integer")
        if self.q + self.r + self.s != 0:
            raise ValueError("cube coordinates must satisfy q + r + s == 0")

@dataclass(frozen=True, slots=True)
class WorldPoint:
    """Continuous point in mathematical world coordinates (x right, y up)."""
    x: float
    y: float
    def __post_init__(self):
        if not math.isfinite(self.x) or not math.isfinite(self.y):
            raise ValueError("world point coordinates must be finite")
