"""Character attributes and immutable stat values."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class Attribute(str, Enum):
    STRENGTH = "strength"
    DEXTERITY = "dexterity"
    CONSTITUTION = "constitution"
    INTELLIGENCE = "intelligence"
    WISDOM = "wisdom"
    CHARISMA = "charisma"


@dataclass(frozen=True)
class Attributes:
    """The six base attributes. Values are bounded to a sensible RPG range."""
    values: Mapping[Attribute, int] = field(default_factory=dict)

    def __post_init__(self):
        normalized = {Attribute(key): _score(value) for key, value in self.values.items()}
        for attribute in Attribute:
            normalized.setdefault(attribute, 10)
        object.__setattr__(self, "values", MappingProxyType(normalized))

    def get(self, attribute: Attribute | str) -> int:
        return self.values[Attribute(attribute)]

    def modifier(self, attribute: Attribute | str) -> int:
        """Return the classic RPG modifier for an attribute score."""
        return (self.get(attribute) - 10) // 2

    def with_modifiers(self, modifiers: Mapping[Attribute | str, int]) -> "Attributes":
        result = dict(self.values)
        for key, value in modifiers.items():
            attribute = Attribute(key)
            result[attribute] = _score(result[attribute] + value)
        return Attributes(result)

    def to_dict(self) -> dict[str, int]:
        return {attribute.value: value for attribute, value in self.values.items()}


def _score(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 30:
        raise ValueError("Attribute scores must be integers between 1 and 30.")
    return value
