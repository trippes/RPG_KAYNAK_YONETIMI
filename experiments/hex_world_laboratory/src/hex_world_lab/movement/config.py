"""Validated configuration for continuous movement."""

from dataclasses import dataclass
import math

from .mode import MovementMode


@dataclass(frozen=True, slots=True)
class MovementConfig:
    """Movement tuning values; speed uses world units per second."""

    max_speed: float
    running_speed_multiplier: float = 1.5
    stealth_speed_multiplier: float = 0.5

    def __post_init__(self) -> None:
        if isinstance(self.max_speed, bool) or not isinstance(self.max_speed, (int, float)):
            raise TypeError("max_speed must be a real number")
        if not math.isfinite(self.max_speed):
            raise ValueError("max_speed must be finite")
        if self.max_speed < 0.0:
            raise ValueError("max_speed must not be negative")

        self._validate_multiplier("running_speed_multiplier", self.running_speed_multiplier)
        self._validate_multiplier("stealth_speed_multiplier", self.stealth_speed_multiplier)

    @staticmethod
    def _validate_multiplier(name: str, value: float) -> None:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a real number")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")
        if value < 0.0:
            raise ValueError(f"{name} must not be negative")

    def speed_multiplier_for(self, mode: MovementMode) -> float:
        """Return the configured speed multiplier for a movement mode."""
        if not isinstance(mode, MovementMode):
            raise TypeError("mode must be a MovementMode")
        if mode is MovementMode.NORMAL:
            return 1.0
        if mode is MovementMode.RUNNING:
            return float(self.running_speed_multiplier)
        if mode is MovementMode.STEALTH:
            return float(self.stealth_speed_multiplier)
        raise ValueError(f"unsupported movement mode: {mode!r}")
