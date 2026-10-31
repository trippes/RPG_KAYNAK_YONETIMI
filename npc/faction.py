"""Factions and their stable, serializable relationships."""
from __future__ import annotations

from dataclasses import dataclass, field


def _id(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string.")
    return value


@dataclass
class Faction:
    faction_id: str
    name: str
    description: str = ""
    relations: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _id(self.faction_id, "faction_id"); _id(self.name, "name")
        if not isinstance(self.description, str):
            raise TypeError("description must be a string.")
        for faction_id, value in self.relations.items():
            _id(faction_id, "faction_id")
            if isinstance(value, bool) or not isinstance(value, int):
                raise TypeError("faction relation must be an integer.")
            self.relations[faction_id] = max(-100, min(100, value))

    def set_relation(self, faction_id: str, value: int) -> None:
        _id(faction_id, "faction_id")
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("relation must be an integer.")
        self.relations[faction_id] = max(-100, min(100, value))

    def relation_to(self, faction_id: str) -> int:
        return self.relations.get(faction_id, 0)


class FactionRegistry:
    def __init__(self, factions=()):
        self._factions: dict[str, Faction] = {}
        for faction in factions: self.add(faction)

    def add(self, faction: Faction) -> None:
        if not isinstance(faction, Faction): raise TypeError("faction must be Faction.")
        if faction.faction_id in self._factions: raise ValueError("Duplicate faction ID.")
        self._factions[faction.faction_id] = faction

    def get(self, faction_id: str) -> Faction | None: return self._factions.get(faction_id)
    def all(self) -> tuple[Faction, ...]: return tuple(self._factions[k] for k in sorted(self._factions))
    def __contains__(self, faction_id: str) -> bool: return faction_id in self._factions


__all__ = ["Faction", "FactionRegistry"]
