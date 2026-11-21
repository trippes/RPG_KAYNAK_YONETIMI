"""Validated, content-supplied continuous movement tuning."""
from dataclasses import dataclass
import math
from numbers import Real

from .mode import MovementMode


@dataclass(frozen=True, slots=True)
class MovementConfig:
    """Movement speeds and acceleration use world units and seconds."""

    max_speed: float
    running_speed_multiplier: float = 1.5
    stealth_speed_multiplier: float = 0.5
    acceleration: float = 180.0
    deceleration: float = 240.0
    braking_deceleration: float = 360.0

    def __post_init__(self) -> None:
        for name in (
            "max_speed",
            "running_speed_multiplier",
            "stealth_speed_multiplier",
            "acceleration",
            "deceleration",
            "braking_deceleration",
        ):
            value = getattr(self, name)
            self._validate_number(name, value)
            if value < 0:
                raise ValueError(f"{name} must not be negative.")
            object.__setattr__(self, name, float(value))

    @staticmethod
    def _validate_number(name: str, value: Real) -> None:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a real number.")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")

    def speed_multiplier_for(self, mode: MovementMode) -> float:
        if not isinstance(mode, MovementMode):
            raise TypeError("mode must be a MovementMode.")
        if mode is MovementMode.NORMAL:
            return 1.0
        if mode is MovementMode.RUNNING:
            return self.running_speed_multiplier
        if mode is MovementMode.STEALTH:
            return self.stealth_speed_multiplier
        raise ValueError(f"Unsupported movement mode: {mode!r}")
