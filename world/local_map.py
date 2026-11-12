"""Immutable local tile-map dimensions for a world location."""
from dataclasses import dataclass

@dataclass(frozen=True)
class LocalMapDefinition:
    world_id: str
    location_id: str
    width: int
    height: int

    def __post_init__(self):
        for name in ("world_id", "location_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        for name in ("width", "height"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer.")
