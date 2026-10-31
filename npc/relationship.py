"""Directed NPC relationships."""
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class Relationship:
    source_id: str
    target_id: str
    value: int = 0
    trust: int = 0

    def __post_init__(self):
        for value, name in ((self.source_id, "source_id"), (self.target_id, "target_id")):
            if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must be non-empty.")
        self.value = self._bounded(self.value); self.trust = self._bounded(self.trust)

    @staticmethod
    def _bounded(value):
        if isinstance(value, bool) or not isinstance(value, int): raise TypeError("relationship values must be integers.")
        return max(-100, min(100, value))

    def change(self, value=0, trust=0):
        self.value = self._bounded(self.value + value); self.trust = self._bounded(self.trust + trust)


class RelationshipGraph:
    def __init__(self): self._items: dict[tuple[str, str], Relationship] = {}
    def get(self, source_id, target_id): return self._items.get((source_id, target_id))
    def ensure(self, source_id, target_id):
        return self._items.setdefault((source_id, target_id), Relationship(source_id, target_id))
    def set(self, relationship):
        if not isinstance(relationship, Relationship): raise TypeError("relationship must be Relationship.")
        self._items[(relationship.source_id, relationship.target_id)] = relationship
    def all(self): return tuple(self._items[key] for key in sorted(self._items))

__all__ = ["Relationship", "RelationshipGraph"]
