"""Internal immutable bounds value used by spatial tree nodes."""
from dataclasses import dataclass
import math


@dataclass(frozen=True, slots=True)
class Bounds:
    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self):
        values = (self.min_x, self.min_y, self.max_x, self.max_y)
        if any(not math.isfinite(value) for value in values):
            raise ValueError("bounds must be finite")
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError("invalid bounds")

    def intersects(self, other):
        return not (self.max_x < other.min_x or other.max_x < self.min_x
                    or self.max_y < other.min_y or other.max_y < self.min_y)
