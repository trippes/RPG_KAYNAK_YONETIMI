"""Immutable runtime state for one continuously moving actor."""

from dataclasses import dataclass, field

from hex_world_lab.geometry import WorldPoint

from .mode import MovementMode
from .vector import Vector2


@dataclass(frozen=True, slots=True)
class MovementState:
    """Current continuous position, velocity and selected movement mode."""

    position: WorldPoint
    velocity: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    mode: MovementMode = MovementMode.NORMAL

    def __post_init__(self) -> None:
        if not isinstance(self.position, WorldPoint):
            raise TypeError("position must be a WorldPoint")
        if not isinstance(self.velocity, Vector2):
            raise TypeError("velocity must be a Vector2")
        if not isinstance(self.mode, MovementMode):
            raise TypeError("mode must be a MovementMode")
