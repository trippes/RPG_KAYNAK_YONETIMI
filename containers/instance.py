"""Runtime state for one uniquely identified container entity."""
from dataclasses import dataclass
from math import isfinite


@dataclass
class ContainerInstance:
    container_id: str
    entity_id: str
    definition_id: str
    durability: float | None = None
    broken: bool = False

    def __post_init__(self):
        for field in ("container_id", "entity_id", "definition_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string.")
        if self.durability is not None:
            if isinstance(self.durability, bool) or not isinstance(self.durability, (int, float)) or not isfinite(self.durability) or self.durability < 0:
                raise ValueError("durability must be finite and non-negative or None.")
        if not isinstance(self.broken, bool):
            raise TypeError("broken must be boolean.")
