"""Application-owned bounded fixed-step clock for continuous gameplay movement."""

import math
from numbers import Integral, Real


class FixedStepAccumulator:
    """Convert frame elapsed time into bounded deterministic fixed-step counts.

    Excess whole-step debt is discarded after max_substeps to prevent a
    prolonged frame stall from causing an unbounded catch-up spiral. The
    fractional remainder is retained. This clock never advances canonical
    world-time Tick.
    """

    __slots__ = (
        "_step_seconds", "_accumulated_seconds", "_max_substeps",
        "_last_dropped_seconds", "_total_dropped_seconds",
    )

    def __init__(
        self,
        step_seconds: Real = 1.0 / 60.0,
        *,
        max_substeps: Integral = 8,
    ) -> None:
        self._validate_seconds("step_seconds", step_seconds)
        if step_seconds <= 0:
            raise ValueError("step_seconds must be greater than zero.")
        if isinstance(max_substeps, bool) or not isinstance(max_substeps, Integral):
            raise TypeError("max_substeps must be a positive integer.")
        if max_substeps <= 0:
            raise ValueError("max_substeps must be greater than zero.")
        self._step_seconds = float(step_seconds)
        self._max_substeps = int(max_substeps)
        self._accumulated_seconds = 0.0
        self._last_dropped_seconds = 0.0
        self._total_dropped_seconds = 0.0

    @staticmethod
    def _validate_seconds(name: str, value: Real) -> None:
        if isinstance(value, bool) or not isinstance(value, Real):
            raise TypeError(f"{name} must be a real number.")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite.")
        if value < 0:
            raise ValueError(f"{name} must not be negative.")

    @property
    def step_seconds(self) -> float:
        return self._step_seconds

    @property
    def max_substeps(self) -> int:
        return self._max_substeps

    @property
    def accumulated_seconds(self) -> float:
        return self._accumulated_seconds

    @property
    def last_dropped_seconds(self) -> float:
        return self._last_dropped_seconds

    @property
    def total_dropped_seconds(self) -> float:
        return self._total_dropped_seconds

    def reset(self) -> None:
        """Discard partial elapsed time, for example when gameplay is paused."""
        self._accumulated_seconds = 0.0
        self._last_dropped_seconds = 0.0

    def advance(self, elapsed_seconds: Real, *, active: bool = True) -> int:
        """Return at most max_substeps and account for discarded time debt."""
        self._validate_seconds("elapsed_seconds", elapsed_seconds)
        if not isinstance(active, bool):
            raise TypeError("active must be a bool.")
        self._last_dropped_seconds = 0.0
        if not active:
            self.reset()
            return 0

        self._accumulated_seconds += float(elapsed_seconds)
        tolerance = self._step_seconds * 1e-12
        due_steps = int(
            (self._accumulated_seconds + tolerance) // self._step_seconds
        )
        steps = min(due_steps, self._max_substeps)
        if due_steps > self._max_substeps:
            dropped_steps = due_steps - self._max_substeps
            self._last_dropped_seconds = dropped_steps * self._step_seconds
            self._total_dropped_seconds += self._last_dropped_seconds
        if due_steps:
            self._accumulated_seconds -= due_steps * self._step_seconds
            if abs(self._accumulated_seconds) <= tolerance:
                self._accumulated_seconds = 0.0
        return steps
