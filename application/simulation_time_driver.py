"""Wall-clock adapter for the one canonical simulation timeline.

This driver converts real elapsed seconds into canonical simulation ticks. It
does not own a second game clock and does not know which activity caused time
to advance; every time-based gameplay system consumes the same SimulationRuntime.
"""

from __future__ import annotations

import math
from numbers import Real


class SimulationTimeDriver:
    """Convert elapsed real time to canonical ticks without dropping fractions."""

    DEFAULT_TICKS_PER_REAL_SECOND = 3_600

    def __init__(
        self,
        ticks_per_real_second: int = DEFAULT_TICKS_PER_REAL_SECOND,
        *,
        speed_multiplier: Real = 1.0,
    ) -> None:
        self._validate_rate(ticks_per_real_second)
        self._validate_multiplier(speed_multiplier)
        self._ticks_per_real_second = ticks_per_real_second
        self._speed_multiplier = float(speed_multiplier)
        self._fractional_ticks = 0.0

    @staticmethod
    def _validate_rate(value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int):
            raise TypeError("ticks_per_real_second must be an integer.")
        if value <= 0:
            raise ValueError("ticks_per_real_second must be greater than zero.")

    @staticmethod
    def _validate_multiplier(value: Real) -> None:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError("speed_multiplier must be a real number.")
        if not math.isfinite(value) or value <= 0:
            raise ValueError("speed_multiplier must be finite and greater than zero.")

    @property
    def ticks_per_real_second(self) -> int:
        return self._ticks_per_real_second

    @property
    def speed_multiplier(self) -> float:
        return self._speed_multiplier

    @property
    def fractional_ticks(self) -> float:
        return self._fractional_ticks

    def set_speed_multiplier(self, value: Real) -> None:
        """Change the central simulation speed without resetting fractional time."""
        self._validate_multiplier(value)
        self._speed_multiplier = float(value)

    def reset(self) -> None:
        """Discard partial real-time progress when gameplay time is stopped."""
        self._fractional_ticks = 0.0

    def advance(self, elapsed_seconds: Real, *, active: bool = True) -> int:
        """Return whole canonical ticks due for this frame.

        The caller decides whether gameplay time should run (for example, at
        least one actor has a running timed activity and the game is not paused).
        Inactive time is deliberately not accumulated.
        """
        if isinstance(elapsed_seconds, bool) or not isinstance(elapsed_seconds, Real):
            raise TypeError("elapsed_seconds must be a real number.")
        if not math.isfinite(elapsed_seconds) or elapsed_seconds < 0:
            raise ValueError("elapsed_seconds must be finite and non-negative.")
        if not isinstance(active, bool):
            raise TypeError("active must be a boolean.")
        if not active:
            self.reset()
            return 0

        due = (
            self._fractional_ticks
            + float(elapsed_seconds)
            * self._ticks_per_real_second
            * self._speed_multiplier
        )
        whole_ticks = math.floor(due + 1e-10)
        self._fractional_ticks = due - whole_ticks
        if self._fractional_ticks < 0 and self._fractional_ticks > -1e-9:
            self._fractional_ticks = 0.0
        return whole_ticks


__all__ = ["SimulationTimeDriver"]
