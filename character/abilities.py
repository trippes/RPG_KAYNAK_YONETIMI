"""Abilities granted by a character's race and class."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Ability:
    ability_id: str
    name: str
    description: str = ""

    def __post_init__(self):
        if not self.ability_id.strip() or not self.name.strip():
            raise ValueError("Ability id and name are required.")

