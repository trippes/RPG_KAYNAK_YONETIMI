"""Runtime-free resource domain value objects."""

from dataclasses import dataclass
from enum import Enum

from core.foundation import Identifier


@dataclass(frozen=True, order=True)
class ResourceType(Identifier):
    """Stable resource kind identity.

    Display names, quantities and runtime ownership are deliberately outside
    this value object. The canonical identity is the inherited ``value``.
    """


class ResourceUnit(str, Enum):
    """Supported measurement units for resource quantities."""

    ITEM = "item"
    KG = "kg"
    LITER = "liter"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_code(cls, code: str) -> "ResourceUnit":
        if not isinstance(code, str):
            raise TypeError("Resource unit code must be a string.")
        try:
            return cls(code)
        except ValueError as error:
            raise ValueError(f"Unsupported resource unit: {code!r}") from error


@dataclass(frozen=True, order=True)
class Quantity:
    """Non-negative integer amount paired with an explicit resource unit."""

    value: int
    unit: ResourceUnit

    def __post_init__(self) -> None:
        if isinstance(self.value, bool) or not isinstance(self.value, int):
            raise TypeError("Quantity value must be an integer.")
        if self.value < 0:
            raise ValueError("Quantity value cannot be negative.")
        if not isinstance(self.unit, ResourceUnit):
            raise TypeError("Quantity unit must be a ResourceUnit.")
