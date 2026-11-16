"""Pure fixed-speed integration for continuous movement."""

import math

from hex_world_lab.geometry import WorldPoint

from .config import MovementConfig
from .intent import MovementIntent
from .state import MovementState
from .vector import Vector2


class MovementIntegrator:
    """Calculate one movement step without owning a clock or tick counter."""

    __slots__ = ("_config",)

    def __init__(self, config: MovementConfig) -> None:
        if not isinstance(config, MovementConfig):
            raise TypeError("config must be a MovementConfig")
        self._config = config

    @property
    def config(self) -> MovementConfig:
        """Return the immutable movement configuration."""
        return self._config

    def step(
        self,
        state: MovementState,
        intent: MovementIntent,
        delta_time: float,
    ) -> MovementState:
        """Return a new state after advancing by delta_time seconds."""
        if not isinstance(state, MovementState):
            raise TypeError("state must be a MovementState")
        if not isinstance(intent, MovementIntent):
            raise TypeError("intent must be a MovementIntent")
        if isinstance(delta_time, bool) or not isinstance(delta_time, (int, float)):
            raise TypeError("delta_time must be a real number")
        if not math.isfinite(delta_time):
            raise ValueError("delta_time must be finite")
        if delta_time < 0.0:
            raise ValueError("delta_time must not be negative")

        multiplier = self._config.speed_multiplier_for(intent.mode)
        effective_speed = self._config.max_speed * multiplier
        if not intent.is_moving or effective_speed == 0.0:
            velocity = Vector2(0.0, 0.0)
        else:
            velocity = intent.direction.normalized() * effective_speed

        position = WorldPoint(
            state.position.x + velocity.x * delta_time,
            state.position.y + velocity.y * delta_time,
        )
        return MovementState(
            position=position,
            velocity=velocity,
            mode=intent.mode,
        )
