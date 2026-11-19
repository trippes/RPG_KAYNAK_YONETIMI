"""Immutable interaction capabilities and tags."""
from dataclasses import dataclass
import math
@dataclass(frozen=True, slots=True)
class InteractionProfile:
    targetable: bool = True
    interaction_radius: float = 24.0
    interaction_tags: frozenset[str] = frozenset({"inspect"})
    selection_priority: int = 0
    def __post_init__(self) -> None:
        if not isinstance(self.targetable, bool): raise TypeError("targetable must be a bool")
        if isinstance(self.interaction_radius, bool) or not isinstance(self.interaction_radius, (int, float)):
            raise TypeError("interaction_radius must be a real number")
        if not math.isfinite(self.interaction_radius) or self.interaction_radius <= 0:
            raise ValueError("interaction_radius must be finite and greater than zero")
        if not isinstance(self.interaction_tags, frozenset): raise TypeError("interaction_tags must be a frozenset")
        if any(not isinstance(tag, str) or not tag.strip() for tag in self.interaction_tags):
            raise ValueError("interaction tags must be non-empty strings")
        if isinstance(self.selection_priority, bool) or not isinstance(self.selection_priority, int):
            raise TypeError("selection_priority must be an integer")
