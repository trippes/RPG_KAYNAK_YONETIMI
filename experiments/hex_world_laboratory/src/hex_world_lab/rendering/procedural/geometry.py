"""Pure local 2D geometry primitives for procedural rendering.

This module deliberately has no Pygame or world-domain dependency.
"""
from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass


def _finite_number(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


@dataclass(frozen=True, slots=True)
class Point2D:
    """An immutable point in an object's local 2D coordinate space."""

    x: float
    y: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", _finite_number(self.x, "x"))
        object.__setattr__(self, "y", _finite_number(self.y, "y"))


@dataclass(frozen=True, slots=True)
class Bounds2D:
    """An axis-aligned local-space rectangle, including its boundary."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        for name in ("min_x", "min_y", "max_x", "max_y"):
            object.__setattr__(self, name, _finite_number(getattr(self, name), name))
        if self.max_x < self.min_x or self.max_y < self.min_y:
            raise ValueError("bounds maximums must not be smaller than minimums")

    @property
    def width(self) -> float:
        return self.max_x - self.min_x

    @property
    def height(self) -> float:
        return self.max_y - self.min_y

    def contains(self, point: Point2D) -> bool:
        if not isinstance(point, Point2D):
            raise TypeError("point must be a Point2D")
        return (
            self.min_x <= point.x <= self.max_x
            and self.min_y <= point.y <= self.max_y
        )

    def union(self, other: Bounds2D) -> Bounds2D:
        if not isinstance(other, Bounds2D):
            raise TypeError("other must be a Bounds2D")
        return Bounds2D(
            min(self.min_x, other.min_x),
            min(self.min_y, other.min_y),
            max(self.max_x, other.max_x),
            max(self.max_y, other.max_y),
        )

    @classmethod
    def from_points(cls, points: Iterable[Point2D]) -> Bounds2D:
        materialized = tuple(points)
        if not materialized:
            raise ValueError("at least one point is required")
        if any(not isinstance(point, Point2D) for point in materialized):
            raise TypeError("all points must be Point2D instances")
        return cls(
            min(point.x for point in materialized),
            min(point.y for point in materialized),
            max(point.x for point in materialized),
            max(point.y for point in materialized),
        )


@dataclass(frozen=True, slots=True)
class Transform2D:
    """Scale, rotate, then translate a point in local 2D space."""

    translate_x: float = 0.0
    translate_y: float = 0.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    rotation_radians: float = 0.0

    def __post_init__(self) -> None:
        for name in (
            "translate_x", "translate_y", "scale_x", "scale_y", "rotation_radians"
        ):
            object.__setattr__(self, name, _finite_number(getattr(self, name), name))
        if self.scale_x == 0 or self.scale_y == 0:
            raise ValueError("transform scale must not be zero")

    def apply(self, point: Point2D) -> Point2D:
        if not isinstance(point, Point2D):
            raise TypeError("point must be a Point2D")
        scaled_x = point.x * self.scale_x
        scaled_y = point.y * self.scale_y
        cosine = math.cos(self.rotation_radians)
        sine = math.sin(self.rotation_radians)
        return Point2D(
            scaled_x * cosine - scaled_y * sine + self.translate_x,
            scaled_x * sine + scaled_y * cosine + self.translate_y,
        )
