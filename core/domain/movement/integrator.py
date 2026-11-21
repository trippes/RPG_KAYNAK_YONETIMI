"""Pure continuous movement integration; the caller owns elapsed-time policy."""
import math
from numbers import Real

from core.domain.physics import Vector2
from core.domain.spatial import WorldPoint

from .config import MovementConfig
from .intent import MovementIntent
from .state import MovementState
from .target import MovementTarget


class MovementIntegrator:
    """Calculate acceleration-limited movement without a clock or world runtime."""

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
        *,
        target: MovementTarget | None = None,
    ) -> MovementState:
        if not isinstance(state, MovementState):
            raise TypeError("state must be a MovementState.")
        if not isinstance(intent, MovementIntent):
            raise TypeError("intent must be a MovementIntent.")
        if target is not None and not isinstance(target, MovementTarget):
            raise TypeError("target must be a MovementTarget or None.")
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, Real):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds):
            raise ValueError("delta_seconds must be finite.")
        if delta_seconds < 0:
            raise ValueError("delta_seconds must not be negative.")

        elapsed = float(delta_seconds)
        if elapsed == 0.0:
            return MovementState(state.position, state.velocity, intent.mode)

        multiplier = self._config.speed_multiplier_for(intent.mode)
        mode_max_speed = self._config.max_speed * multiplier
        desired_velocity = (
            intent.direction.normalized() * mode_max_speed
            if intent.is_moving and mode_max_speed > 0.0
            else Vector2(0.0, 0.0)
        )

        remaining = None
        target_direction = None
        if target is not None:
            dx = target.position.x - state.position.x
            dy = target.position.y - state.position.y
            remaining = math.hypot(dx, dy)
            if remaining <= target.arrival_tolerance:
                desired_velocity = Vector2(0.0, 0.0)
            elif remaining > 0.0:
                target_direction = Vector2(dx / remaining, dy / remaining)
                braking_speed = math.sqrt(
                    2.0 * self._config.braking_deceleration
                    * max(0.0, remaining - target.arrival_tolerance)
                )
                target_speed = min(mode_max_speed, braking_speed)
                if intent.is_moving:
                    desired_velocity = target_direction * target_speed

        delta_v = desired_velocity - state.velocity
        delta_length = delta_v.length
        if delta_length <= 1e-12:
            velocity = desired_velocity
        else:
            reducing_speed = (
                desired_velocity.length < state.velocity.length
                or state.velocity.dot(desired_velocity) < 0.0
            )
            rate = (
                self._config.braking_deceleration
                if target is not None and target_direction is not None and reducing_speed
                else self._config.deceleration if not intent.is_moving
                else self._config.acceleration
            )
            max_delta = rate * elapsed
            if max_delta <= 0.0:
                velocity = state.velocity
            elif delta_length <= max_delta:
                velocity = desired_velocity
            else:
                velocity = state.velocity + delta_v * (max_delta / delta_length)

        displacement = velocity * elapsed
        if remaining is not None:
            allowed_distance = max(0.0, remaining - target.arrival_tolerance)
            travel = displacement.length
            if travel > allowed_distance and travel > 0.0:
                displacement = displacement * (allowed_distance / travel)
                velocity = displacement * (1.0 / elapsed)

        position = WorldPoint(
            state.position.x + displacement.x,
            state.position.y + displacement.y,
        )
        return MovementState(position, velocity, intent.mode)
