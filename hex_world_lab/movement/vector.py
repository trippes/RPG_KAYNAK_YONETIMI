"""Immutable two-dimensional vectors used by movement systems."""

from dataclasses import dataclass
import math


def _validate_component(value: object, name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a real number")
    if not math.isfinite(value):
        raise ValueError(f"{name} must be finite")


@dataclass(frozen=True, slots=True)
class Vector2:
    """A finite vector in mathematical world coordinates (x right, y up)."""

    x: float
    y: float

    def __post_init__(self) -> None:
        _validate_component(self.x, "x")
        _validate_component(self.y, "y")

    @property
    def length_squared(self) -> float:
        """Return the squared vector magnitude without a square root."""
        return self.x * self.x + self.y * self.y

    @property
    def length(self) -> float:
        """Return the vector magnitude."""
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vector2":
        """Return a unit vector; the zero vector remains zero."""
        magnitude = self.length
        if magnitude == 0.0:
            return Vector2(0.0, 0.0)
        return Vector2(self.x / magnitude, self.y / magnitude)

    def __add__(self, other: object) -> "Vector2":
        if not isinstance(other, Vector2):
            return NotImplemented
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: object) -> "Vector2":
        if not isinstance(other, Vector2):
            return NotImplemented
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2":
        _validate_component(scalar, "scalar")
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2":
        return self * scalar
