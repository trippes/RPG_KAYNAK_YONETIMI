"""Immutable continuous point in Eldoria's canonical y-down world plane."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real


@dataclass(frozen=True, slots=True)
class WorldPoint:
    """World-space point measured in world units; +x is right and +y is down."""

    x: float
    y: float

    def __post_init__(self) -> None:
        for name, value in (("x", self.x), ("y", self.y)):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a finite real number.")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")

    def translated(self, dx: float = 0.0, dy: float = 0.0) -> "WorldPoint":
        return WorldPoint(self.x + dx, self.y + dy)

    def distance_to(self, other: "WorldPoint") -> float:
        if not isinstance(other, WorldPoint):
            raise TypeError("other must be a WorldPoint.")
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_dict(self) -> dict[str, float]:
        return {"x": self.x, "y": self.y}
