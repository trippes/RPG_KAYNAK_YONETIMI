"""Immutable spatial records."""
from dataclasses import dataclass

from .protocols import Bounds2D


@dataclass(frozen=True, slots=True)
class SpatialEntry:
    item_id: str
    bounds: Bounds2D

    def __post_init__(self) -> None:
        if not isinstance(self.item_id, str) or not self.item_id.strip():
            raise ValueError("item_id must be a non-empty string")
        _validate_bounds(self.bounds)


def _validate_bounds(bounds: Bounds2D) -> None:
    values = (bounds.min_x, bounds.min_y, bounds.max_x, bounds.max_y)
    if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
        raise TypeError("bounds coordinates must be real numbers")
    import math
    if any(not math.isfinite(value) for value in values):
        raise ValueError("bounds coordinates must be finite")
    if bounds.min_x > bounds.max_x or bounds.min_y > bounds.max_y:
        raise ValueError("bounds minimums must not exceed maximums")
    if not callable(getattr(bounds, "intersects", None)):
        raise TypeError("bounds must provide intersects(other)")
