"""Immutable finite vector in Eldoria's canonical y-down world plane."""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real


@dataclass(frozen=True, slots=True)
class Vector2:
    x: float
    y: float

    def __post_init__(self) -> None:
        for name, value in (("x", self.x), ("y", self.y)):
            if isinstance(value, bool) or not isinstance(value, Real):
                raise TypeError(f"{name} must be a finite real number.")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite.")
            object.__setattr__(self, name, float(value))

    @property
    def length_squared(self) -> float:
        return self.x * self.x + self.y * self.y

    @property
    def length(self) -> float:
        return math.hypot(self.x, self.y)

    def normalized(self) -> "Vector2":
        magnitude = self.length
        if magnitude == 0.0:
            return Vector2(0.0, 0.0)
        return Vector2(self.x / magnitude, self.y / magnitude)

    def dot(self, other: "Vector2") -> float:
        if not isinstance(other, Vector2):
            raise TypeError("other must be a Vector2.")
        return self.x * other.x + self.y * other.y

    def perpendicular(self) -> "Vector2":
        return Vector2(-self.y, self.x)

    def __add__(self, other: object) -> "Vector2":
        if not isinstance(other, Vector2):
            return NotImplemented
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: object) -> "Vector2":
        if not isinstance(other, Vector2):
            return NotImplemented
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> "Vector2":
        if isinstance(scalar, bool) or not isinstance(scalar, Real):
            raise TypeError("scalar must be a finite real number.")
        if not math.isfinite(scalar):
            raise ValueError("scalar must be finite.")
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> "Vector2":
        return self * scalar
