from dataclasses import dataclass
from typing import Mapping

from core.foundation import WorldId


@dataclass(frozen=True)
class WorldDomainState:
    """Canonical, runtime-free World identity, metadata and bounds contract."""

    world_id: WorldId
    name: str
    width: int | None
    height: int | None

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId.")
        if not isinstance(self.name, str):
            raise TypeError("World name must be a string.")
        if not self.name.strip():
            raise ValueError("World name cannot be empty.")
        self._validate_bound(self.width, "width")
        self._validate_bound(self.height, "height")

    @staticmethod
    def _validate_bound(value: int | None, name: str) -> None:
        if value is None:
            return
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError(f"World {name} must be a positive integer or None.")
        if value <= 0:
            raise ValueError(f"World {name} must be greater than zero.")

    def to_dict(self) -> dict[str, object]:
        return {
            "world_id": str(self.world_id),
            "name": self.name,
            "width": self.width,
            "height": self.height,
        }

    def to_persistence(self) -> dict[str, object]:
        return self.to_dict()

    @classmethod
    def from_persistence(cls, data: Mapping[str, object]) -> "WorldDomainState":
        if not isinstance(data, Mapping):
            raise TypeError("WorldDomainState data must be a mapping.")
        required = {"world_id", "name", "width", "height"}
        if not required.issubset(data):
            raise ValueError("WorldDomainState is missing required identity or bounds fields.")
        return cls(WorldId(data["world_id"]), data["name"], data["width"], data["height"])
