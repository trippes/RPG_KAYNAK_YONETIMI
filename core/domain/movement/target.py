"""Immutable world-space movement target and arrival tolerance."""
from dataclasses import dataclass
import math
from numbers import Real

from core.domain.spatial import WorldPoint


@dataclass(frozen=True, slots=True)
class MovementTarget:
    """A target point; it carries no route, actor, or runtime reference."""

    position: WorldPoint
    arrival_tolerance: float = 0.5

    def __post_init__(self) -> None:
        if not isinstance(self.position, WorldPoint):
            raise TypeError("position must be a WorldPoint.")
        value = self.arrival_tolerance
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("arrival_tolerance must be a real number.")
        if not math.isfinite(value):
            raise ValueError("arrival_tolerance must be finite.")
        if value < 0:
            raise ValueError("arrival_tolerance must not be negative.")
        object.__setattr__(self, "arrival_tolerance", float(value))
