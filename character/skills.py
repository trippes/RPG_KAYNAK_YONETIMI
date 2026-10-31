"""Character skills."""
from __future__ import annotations
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping


@dataclass(frozen=True)
class Skills:
    values: Mapping[str, int] = field(default_factory=dict)

    def __post_init__(self):
        normalized = {}
        for name, rank in self.values.items():
            if not isinstance(name, str) or not name.strip():
                raise ValueError("Skill names must be non-empty strings.")
            if isinstance(rank, bool) or not isinstance(rank, int) or rank < 0:
                raise ValueError("Skill ranks must be non-negative integers.")
            normalized[name.strip().lower()] = rank
        object.__setattr__(self, "values", MappingProxyType(normalized))

    def get(self, skill: str, default: int = 0) -> int:
        return self.values.get(skill.strip().lower(), default)

    def with_ranks(self, ranks: Mapping[str, int]) -> "Skills":
        result = dict(self.values)
        result.update(ranks)
        return Skills(result)

    def improve(self, skill: str) -> "Skills":
        name = skill.strip().lower()
        if not name:
            raise ValueError("Skill name is required.")
        if name not in self.values:
            raise KeyError(f"Unknown skill: {skill}")
        result = dict(self.values)
        result[name] += 1
        return Skills(result)

    def to_dict(self) -> dict[str, int]:
        return dict(self.values)
