"""Race definitions."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping
from .abilities import Ability
from .attributes import Attribute


@dataclass(frozen=True)
class Race:
    race_id: str
    name: str
    attribute_modifiers: Mapping[Attribute | str, int] = field(default_factory=dict)
    abilities: tuple[Ability, ...] = ()

    def __post_init__(self):
        if not self.race_id.strip() or not self.name.strip():
            raise ValueError("Race id and name are required.")
        object.__setattr__(self, "attribute_modifiers", {Attribute(k): v for k, v in self.attribute_modifiers.items()})
        if any(not isinstance(a, Ability) for a in self.abilities):
            raise TypeError("Race abilities must be Ability instances.")

