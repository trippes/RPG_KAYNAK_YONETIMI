"""Input-device-independent continuous movement intent."""
from dataclasses import dataclass, field

from core.domain.physics import Vector2

from .mode import MovementMode


@dataclass(frozen=True, slots=True)
class MovementIntent:
    """Desired direction and movement mode; zero direction means idle."""

    direction: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    mode: MovementMode = MovementMode.NORMAL

    def __post_init__(self) -> None:
        if not isinstance(self.direction, Vector2):
            raise TypeError("direction must be a Vector2.")
        if not isinstance(self.mode, MovementMode):
            raise TypeError("mode must be a MovementMode.")

    @property
    def is_moving(self) -> bool:
        return self.direction.length_squared > 0.0
