"""Player or AI movement intent, independent of input devices."""

from dataclasses import dataclass, field

from .mode import MovementMode
from .vector import Vector2


@dataclass(frozen=True, slots=True)
class MovementIntent:
    """Desired direction and speed mode; zero direction means no movement."""

    direction: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))
    mode: MovementMode = MovementMode.NORMAL

    def __post_init__(self) -> None:
        if not isinstance(self.direction, Vector2):
            raise TypeError("direction must be a Vector2")
        if not isinstance(self.mode, MovementMode):
            raise TypeError("mode must be a MovementMode")

    @property
    def is_moving(self) -> bool:
        """Whether a non-zero movement direction was requested."""
        return self.direction.length_squared > 0.0
