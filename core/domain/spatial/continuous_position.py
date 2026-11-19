"""Map-scoped continuous entity position value object."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

from .world_point import WorldPoint


@dataclass(frozen=True, slots=True)
class ContinuousEntityPosition:
    """Authoritative continuous location scoped to one local hex map."""

    map_id: str
    point: WorldPoint

    def __post_init__(self) -> None:
        if not isinstance(self.map_id, str) or not self.map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        if not isinstance(self.point, WorldPoint):
            raise TypeError("point must be a WorldPoint.")

    @classmethod
    def from_xy(cls, map_id: str, x: Real, y: Real) -> "ContinuousEntityPosition":
        return cls(map_id, WorldPoint(x, y))

    @property
    def x(self) -> float:
        return self.point.x

    @property
    def y(self) -> float:
        return self.point.y

    def to_dict(self) -> dict[str, str | float]:
        return {"map_id": self.map_id, "x": self.x, "y": self.y}
