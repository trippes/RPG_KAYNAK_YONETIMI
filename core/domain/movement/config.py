"""Validated, content-supplied continuous movement tuning."""
from dataclasses import dataclass
import math
from numbers import Real

from .mode import MovementMode


@dataclass(frozen=True, slots=True)
class MovementConfig:
    """Movement speeds use world units per second; no balance defaults are assumed."""

    max_speed: float
    running_speed_multiplier: float = 1.5
    stealth_speed_multiplier: float = 0.5

    def __post_init__(self) -> None:
        self._validate_number("max_speed", self.max_speed)
        if self.max_speed < 0:
            raise ValueError("max_speed must not be negative.")
        self._validate_number("running_speed_multiplier", self.running_speed_multiplier)
        self._validate_number("stealth_speed_multiplier", self.stealth_speed_multiplier)
        if self.running_speed_multiplier < 0 or self.stealth_speed_multiplier < 0:
            raise ValueError("Movement speed multipliers must not be negative.")
        object.__setattr__(self, "max_speed", float(self.max_speed))
        object.__setattr__(self, "running_speed_multiplier", float(self.running_speed_multiplier))
        object.__setattr__(self, "stealth_speed_multiplier", float(self.stealth_speed_multiplier))

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
