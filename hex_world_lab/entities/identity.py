"""Stable entity identifiers."""
from dataclasses import dataclass
@dataclass(frozen=True, slots=True, order=True)
class EntityId:
    value: str
    def __post_init__(self) -> None:
        if not isinstance(self.value, str): raise TypeError("entity id must be a string")
        if not self.value.strip(): raise ValueError("entity id must not be empty or whitespace-only")
