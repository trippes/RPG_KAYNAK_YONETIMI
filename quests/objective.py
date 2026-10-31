"""Quest objectives and progress."""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum

class ObjectiveType(Enum): KILL="kill"; COLLECT="collect"; TALK="talk"; REACH="reach"; CUSTOM="custom"

@dataclass
class Objective:
    objective_id: str
    description: str
    objective_type: ObjectiveType
    target_id: str | None = None
    required: int = 1
    progress: int = 0
    optional: bool = False
    def __post_init__(self):
        if not self.objective_id or not self.description: raise ValueError("Objective ID and description are required.")
        self.objective_type = ObjectiveType(self.objective_type)
        if isinstance(self.required, bool) or self.required < 1: raise ValueError("required must be positive.")
        self.progress = max(0, min(self.required, self.progress))
    @property
    def completed(self): return self.progress >= self.required
    def advance(self, amount=1):
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0: raise ValueError("amount must be non-negative.")
        self.progress = min(self.required, self.progress + amount); return self.completed

__all__ = ["Objective", "ObjectiveType"]
