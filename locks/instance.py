"""Runtime state for one lock capability attached to a Core entity."""
from dataclasses import dataclass


@dataclass
class LockInstance:
    lock_id: str
    entity_id: str
    definition_id: str
    locked: bool = True
    jammed: bool = False
    broken: bool = False

    def __post_init__(self):
        for field in ("lock_id", "entity_id", "definition_id"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field} must be a non-empty string.")
        for field in ("locked", "jammed", "broken"):
            if not isinstance(getattr(self, field), bool):
                raise TypeError(f"{field} must be boolean.")
        if self.broken and self.jammed:
            raise ValueError("A lock cannot be both broken and jammed.")
        if (self.broken or self.jammed) and self.locked:
            raise ValueError("A broken or jammed lock cannot remain locked.")
