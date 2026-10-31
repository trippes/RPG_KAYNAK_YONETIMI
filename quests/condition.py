"""Composable quest conditions."""
from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Condition:
    kind: str
    key: str
    expected: object = True
    def evaluate(self, context) -> bool:
        if self.kind == "flag": return context.get("flags", {}).get(self.key, False) == self.expected
        if self.kind == "reputation": return context.get("reputation", {}).get(self.key, 0) >= self.expected
        if self.kind == "item": return context.get("items", {}).get(self.key, 0) >= self.expected
        if self.kind == "objective": return context.get("objectives", {}).get(self.key, 0) >= self.expected
        raise ValueError(f"Unknown condition kind: {self.kind}")

class AllConditions:
    def __init__(self, conditions=()): self.conditions = tuple(conditions)
    def evaluate(self, context): return all(c.evaluate(context) for c in self.conditions)

__all__ = ["Condition", "AllConditions"]
