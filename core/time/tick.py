from dataclasses import dataclass


@dataclass(frozen=True, order=True)
class Tick:
    """Non-negative immutable simulation time value."""

    value: int = 0

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError("Tick value must be an integer.")
        if self.value < 0:
            raise ValueError("Tick value cannot be negative.")

    def __int__(self) -> int:
        return self.value

    def __add__(self, other: "Tick | int") -> "Tick":
        if isinstance(other, Tick):
            return Tick(self.value + other.value)
        if isinstance(other, int) and not isinstance(other, bool):
            return Tick(self.value + other)
        return NotImplemented

    def __radd__(self, other: "Tick | int") -> "Tick":
        return self + other

    def __sub__(self, other: "Tick | int") -> "Tick":
        if isinstance(other, Tick):
            return Tick(self.value - other.value)
        if isinstance(other, int) and not isinstance(other, bool):
            return Tick(self.value - other)
        return NotImplemented

    def __mul__(self, other: int) -> "Tick":
        if isinstance(other, int) and not isinstance(other, bool):
            return Tick(self.value * other)
        return NotImplemented

    def __rmul__(self, other: int) -> "Tick":
        return self * other

    def to_dict(self) -> dict[str, int]:
        return {"value": self.value}

    def to_persistence(self) -> int:
        return self.value

    @classmethod
    def from_persistence(cls, value: int) -> "Tick":
        return cls(value)
