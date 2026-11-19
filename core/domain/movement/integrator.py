"""Pure continuous movement integration; the caller owns elapsed-time policy."""
import math
from numbers import Real

from core.domain.physics import Vector2
from core.domain.spatial import WorldPoint

from .config import MovementConfig
from .intent import MovementIntent
from .state import MovementState


class MovementIntegrator:
    """Calculate movement without owning a clock, tick counter, or world runtime."""

    __slots__ = ("_config",)

    def __init__(self, config: MovementConfig) -> None:
        if not isinstance(config, MovementConfig):
            raise TypeError("config must be a MovementConfig.")
        self._config = config

    @property
    def config(self) -> MovementConfig:
        return self._config

    def step(
        self,
        state: MovementState,
        intent: MovementIntent,
        delta_seconds: Real,
    ) -> MovementState:
        if not isinstance(state, MovementState):
            raise TypeError("state must be a MovementState.")
        if not isinstance(intent, MovementIntent):
            raise TypeError("intent must be a MovementIntent.")
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, Real):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds):
            raise ValueError("delta_seconds must be finite.")
        if delta_seconds < 0:
            raise ValueError("delta_seconds must not be negative.")

        speed = self._config.max_speed * self._config.speed_multiplier_for(intent.mode)
        velocity = (
            intent.direction.normalized() * speed
            if intent.is_moving and speed > 0
            else Vector2(0.0, 0.0)
        )
        elapsed = float(delta_seconds)
        position = WorldPoint(
            state.position.x + velocity.x * elapsed,
            state.position.y + velocity.y * elapsed,
        )
        return MovementState(position, velocity, intent.mode)
