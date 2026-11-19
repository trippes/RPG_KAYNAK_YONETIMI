"""Immutable continuous movement state in Eldoria world coordinates."""
from dataclasses import dataclass, field

from core.domain.physics import Vector2
from core.domain.spatial import WorldPoint

from .mode import MovementMode


@dataclass(frozen=True, slots=True)
class MovementState:
    position: WorldPoint
    velocity: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    mode: MovementMode = MovementMode.NORMAL

    def __post_init__(self) -> None:
        if not isinstance(self.position, WorldPoint):
            raise TypeError("position must be a WorldPoint.")
        if not isinstance(self.velocity, Vector2):
            raise TypeError("velocity must be a Vector2.")
        if not isinstance(self.mode, MovementMode):
            raise TypeError("mode must be a MovementMode.")
