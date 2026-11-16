"""Deterministic contact values shared by narrowphase and collision solving."""

from dataclasses import dataclass
import math

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2


@dataclass(frozen=True, slots=True)
class Contact:
    """A contact whose normal points from the obstacle toward the moving shape."""

    obstacle_id: str
    point: WorldPoint
    normal: Vector2
    penetration_depth: float

    def __post_init__(self) -> None:
        if not isinstance(self.obstacle_id, str) or not self.obstacle_id.strip():
            raise ValueError("obstacle_id must be a non-empty string")
        if not isinstance(self.point, WorldPoint):
            raise TypeError("point must be a WorldPoint")
        if not isinstance(self.normal, Vector2):
            raise TypeError("normal must be a Vector2")
        if not math.isfinite(self.penetration_depth) or self.penetration_depth < 0:
            raise ValueError("penetration_depth must be finite and non-negative")
        if not math.isclose(self.normal.length, 1.0, rel_tol=1e-7, abs_tol=1e-7):
            raise ValueError("contact normal must be normalized")


@dataclass(frozen=True, slots=True)
class ContactManifold:
    """Immutable, stably ordered contacts for one collision query."""

    contacts: tuple[Contact, ...] = ()

    def __post_init__(self) -> None:
        values = tuple(self.contacts)
        if any(not isinstance(item, Contact) for item in values):
            raise TypeError("contacts must contain Contact values")
        object.__setattr__(
            self,
            "contacts",
            tuple(sorted(values, key=lambda item: (
                item.obstacle_id, item.point.x, item.point.y,
                item.normal.x, item.normal.y,
            ))),
        )

    def __len__(self) -> int:
        return len(self.contacts)

    def __iter__(self):
        return iter(self.contacts)
