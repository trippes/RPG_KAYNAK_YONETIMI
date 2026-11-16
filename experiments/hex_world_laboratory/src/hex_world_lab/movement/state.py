"""Immutable runtime state for one continuously moving actor."""

from dataclasses import dataclass, field

from hex_world_lab.geometry import WorldPoint

from .vector import Vector2


@dataclass(frozen=True, slots=True)
class MovementState:
    """Current continuous position and velocity of an actor."""

    position: WorldPoint
    velocity: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))

    def __post_init__(self) -> None:
        if not isinstance(self.position, WorldPoint):
            raise TypeError("position must be a WorldPoint")
        if not isinstance(self.velocity, Vector2):
            raise TypeError("velocity must be a Vector2")
