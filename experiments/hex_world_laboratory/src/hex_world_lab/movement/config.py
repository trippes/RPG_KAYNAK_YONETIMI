"""Validated configuration for continuous movement."""

from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class MovementConfig:
    """Movement tuning values; speed uses world units per second."""

    max_speed: float

    def __post_init__(self) -> None:
        if isinstance(self.max_speed, bool) or not isinstance(self.max_speed, (int, float)):
            raise TypeError("max_speed must be a real number")
        if not math.isfinite(self.max_speed):
            raise ValueError("max_speed must be finite")
        if self.max_speed < 0.0:
            raise ValueError("max_speed must not be negative")
