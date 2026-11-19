"""Axis-aligned bounds for continuous world-space queries."""

from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

from .world_point import WorldPoint


@dataclass(frozen=True, slots=True)
class AABB:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        values = (self.min_x, self.min_y, self.max_x, self.max_y)
        for value in values:
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError("AABB coordinates must be finite real numbers.")
            if not math.isfinite(value):
                raise ValueError("AABB coordinates must be finite.")
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError("AABB minimums must not exceed maximums.")
        for name, value in zip(("min_x", "min_y", "max_x", "max_y"), values):
            object.__setattr__(self, name, float(value))

    @classmethod
    def at_point(cls, point: WorldPoint) -> "AABB":
        if not isinstance(point, WorldPoint):
            raise TypeError("point must be a WorldPoint.")
        return cls(point.x, point.y, point.x, point.y)

    @classmethod
    def around_point(
        cls,
        point: WorldPoint,
        half_width: float,
        half_height: float | None = None,
    ) -> "AABB":
        if not isinstance(point, WorldPoint):
            raise TypeError("point must be a WorldPoint.")
        if half_height is None:
            half_height = half_width
        for value in (half_width, half_height):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError("AABB half extents must be real numbers.")
            if not math.isfinite(value) or value < 0:
                raise ValueError("AABB half extents must be finite and non-negative.")
        return cls(
            point.x - half_width,
            point.y - half_height,
            point.x + half_width,
            point.y + half_height,
        )

    def intersects(self, other: "AABB") -> bool:
        if not isinstance(other, AABB):
            raise TypeError("other must be an AABB.")
        return not (
            self.max_x < other.min_x
            or other.max_x < self.min_x
            or self.max_y < other.min_y
            or other.max_y < self.min_y
        )
