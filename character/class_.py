"""Class definitions (class_ avoids Python's reserved keyword)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping
from .abilities import Ability


@dataclass(frozen=True)
class CharacterClass:
    class_id: str
    name: str
    hit_points: int = 10
    skill_ranks: Mapping[str, int] = field(default_factory=dict)
    abilities: tuple[Ability, ...] = ()

    def __post_init__(self):
        if not self.class_id.strip() or not self.name.strip():
            raise ValueError("Class id and name are required.")
        if isinstance(self.hit_points, bool) or self.hit_points <= 0:
            raise ValueError("hit_points must be positive.")
        object.__setattr__(self, "skill_ranks", dict(self.skill_ranks))
        if any(not isinstance(a, Ability) for a in self.abilities):
            raise TypeError("Class abilities must be Ability instances.")

