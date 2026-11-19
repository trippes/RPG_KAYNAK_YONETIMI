"""Application-owned fixed-step clock for continuous gameplay movement."""

import math
from numbers import Real


class FixedStepAccumulator:
    """Convert frame elapsed time into deterministic fixed movement-step counts.

    This clock is deliberately separate from canonical world-time Tick.
    It does not advance the calendar, own actors, or execute movement itself.
    The caller decides when gameplay is active and consumes the returned steps.
    """

    __slots__ = ("_step_seconds", "_accumulated_seconds")

    def __init__(self, step_seconds: Real = 1.0 / 60.0) -> None:
        self._validate_seconds("step_seconds", step_seconds)
        if step_seconds <= 0:
            raise ValueError("step_seconds must be greater than zero.")
        self._step_seconds = float(step_seconds)
        self._accumulated_seconds = 0.0

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
    def accumulated_seconds(self) -> float:
        return self._accumulated_seconds

    def reset(self) -> None:
        """Discard partial elapsed time, for example when gameplay is paused."""
        self._accumulated_seconds = 0.0

    def advance(self, elapsed_seconds: Real, *, active: bool = True) -> int:
        """Return the number of fixed steps ready to execute.

        Inactive gameplay discards accumulated time, preventing a burst of
        movement when play resumes. No world-time Tick is created or advanced.
        """
        self._validate_seconds("elapsed_seconds", elapsed_seconds)
        if not isinstance(active, bool):
            raise TypeError("active must be a bool.")
        if not active:
            self.reset()
            return 0

        self._accumulated_seconds += float(elapsed_seconds)
        tolerance = self._step_seconds * 1e-12
        steps = int((self._accumulated_seconds + tolerance) // self._step_seconds)
        if steps:
            self._accumulated_seconds -= steps * self._step_seconds
            if abs(self._accumulated_seconds) <= tolerance:
                self._accumulated_seconds = 0.0
        return steps
