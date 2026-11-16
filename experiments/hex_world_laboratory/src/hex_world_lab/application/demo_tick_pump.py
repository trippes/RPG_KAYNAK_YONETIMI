"""Real-time tick pump for demos; deliberately independent of Pygame."""

from dataclasses import dataclass
import math
import time
from typing import Callable

TICK_RATE = 60
TICK_DURATION_SECONDS = 1.0 / TICK_RATE
MAX_TICKS_PER_PUMP = 8
_TIME_EPSILON = 1e-12


@dataclass(frozen=True, slots=True)
class TickPumpDiagnostics:
    """Immutable snapshot of demo tick-pump progress and accumulated debt."""

    total_ticks: int
    next_tick_number: int
    last_frame_tick_count: int
    pending_full_ticks: int
    time_debt_seconds: float


class DemoTickPump:
    """Convert monotonic elapsed time into bounded, lossless fixed ticks."""

    __slots__ = (
        "_callback",
        "_clock",
        "_first_tick_number",
        "_next_tick_number",
        "_last_time",
        "_accumulator",
        "_total_ticks",
        "_last_frame_tick_count",
    )

    def __init__(
        self,
        callback: Callable[[int], object],
        *,
        clock: Callable[[], float] = time.monotonic,
        first_tick_number: int = 0,
    ) -> None:
        if not callable(callback):
            raise TypeError("callback must be callable")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self._validate_tick_number(first_tick_number)
        self._callback = callback
        self._clock = clock
        self._first_tick_number = first_tick_number
        self._next_tick_number = first_tick_number
        self._last_time: float | None = None
        self._accumulator = 0.0
        self._total_ticks = 0
        self._last_frame_tick_count = 0

    @staticmethod
    def _validate_tick_number(tick_number: int) -> None:
        if isinstance(tick_number, bool) or not isinstance(tick_number, int):
            raise TypeError("first_tick_number must be an integer")
        if tick_number < 0:
            raise ValueError("first_tick_number must not be negative")

    @staticmethod
    def _read_valid_time(value: object) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError("clock must return a real number")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError("clock value must be finite")
        return result

    def start(self) -> None:
        """Capture the initial monotonic timestamp exactly once."""
        if self._last_time is not None:
            raise RuntimeError("tick pump has already been started")
        self._last_time = self._read_valid_time(self._clock())

    @property
    def diagnostics(self) -> TickPumpDiagnostics:
        """Return a read-only snapshot of current tick and time debt."""
        pending = int(
            math.floor((self._accumulator + _TIME_EPSILON) / TICK_DURATION_SECONDS)
        )
        return TickPumpDiagnostics(
            total_ticks=self._total_ticks,
            next_tick_number=self._next_tick_number,
            last_frame_tick_count=self._last_frame_tick_count,
            pending_full_ticks=pending,
            time_debt_seconds=self._accumulator,
        )

    def pump(self) -> TickPumpDiagnostics:
        """Accumulate elapsed time and process at most eight successful ticks."""
        if self._last_time is None:
            raise RuntimeError("tick pump must be started before pumping")

        now = self._read_valid_time(self._clock())
        if now < self._last_time:
            raise ValueError("clock must be monotonic and must not move backwards")

        elapsed = now - self._last_time
        new_accumulator = self._accumulator + elapsed
        if not math.isfinite(new_accumulator):
            raise ValueError("accumulated time must remain finite")

        self._last_time = now
        self._accumulator = new_accumulator
        processed = 0

        try:
            while (
                processed < MAX_TICKS_PER_PUMP
                and self._accumulator + _TIME_EPSILON >= TICK_DURATION_SECONDS
            ):
                # A failed callback leaves this tick and its time debt untouched.
                self._callback(self._next_tick_number)
                self._next_tick_number += 1
                self._total_ticks += 1
                self._accumulator -= TICK_DURATION_SECONDS
                if self._accumulator < 0.0 and self._accumulator > -_TIME_EPSILON:
                    self._accumulator = 0.0
                processed += 1
        finally:
            self._last_frame_tick_count = processed

        return self.diagnostics
