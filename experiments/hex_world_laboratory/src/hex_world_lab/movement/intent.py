"""Player or AI movement intent, independent of input devices."""

from dataclasses import dataclass, field

from .vector import Vector2


@dataclass(frozen=True, slots=True)
class MovementIntent:
    """Desired movement direction; a zero vector means no movement."""

    direction: Vector2 = field(default_factory=lambda: Vector2(0.0, 0.0))

    def __post_init__(self) -> None:
        if not isinstance(self.direction, Vector2):
            raise TypeError("direction must be a Vector2")

    @property
    def is_moving(self) -> bool:
        """Whether a non-zero movement direction was requested."""
        return self.direction.length_squared > 0.0
