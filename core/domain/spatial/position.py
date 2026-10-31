from dataclasses import dataclass
import math
from numbers import Real
from typing import Any


@dataclass(frozen=True, order=True)
class Position:
    """Immutable two-dimensional position value object.

    Position validates coordinate shape only. World bounds, collision and
    movement policy belong to the world/application layer.
    """

    x: int | float = 0
    y: int | float = 0

    def __post_init__(self) -> None:
        self._validate_coordinate(self.x, "x")
        self._validate_coordinate(self.y, "y")

    @staticmethod
    def _validate_coordinate(value: Any, name: str) -> None:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be an int or float.")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    def translated(self, dx: int | float = 0, dy: int | float = 0) -> "Position":
        self._validate_coordinate(dx, "dx")
        self._validate_coordinate(dy, "dy")
        return Position(self.x + dx, self.y + dy)

    def distance_to(self, other: "Position") -> float:
        if not isinstance(other, Position):
            raise TypeError("other must be a Position.")
        return math.hypot(self.x - other.x, self.y - other.y)

    def to_dict(self) -> dict[str, int | float]:
        return {"x": self.x, "y": self.y}

    def to_persistence(self) -> dict[str, int | float]:
        return self.to_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Position":
        if not isinstance(data, dict):
            raise TypeError("Position data must be a dictionary.")
        try:
            return cls(x=data["x"], y=data["y"])
        except KeyError as exc:
            raise ValueError(f"Missing position field: {exc.args[0]}") from exc

    @classmethod
    def from_persistence(cls, data: dict[str, Any]) -> "Position":
        return cls.from_dict(data)
