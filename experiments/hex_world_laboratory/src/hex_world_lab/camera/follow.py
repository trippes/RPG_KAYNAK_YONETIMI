"""Frame-rate-independent camera target following."""

from __future__ import annotations

import math

from hex_world_lab.geometry import WorldPoint


class CameraFollowController:
    """Smoothly approach a world-space target using exponential damping."""

    __slots__ = ("_smoothing", "_max_delta_seconds")

    def __init__(
        self,
        *,
        smoothing: float = 8.0,
        max_delta_seconds: float = 0.25,
    ) -> None:
        for name, value in (
            ("smoothing", smoothing),
            ("max_delta_seconds", max_delta_seconds),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a real number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if smoothing <= 0.0:
            raise ValueError("smoothing must be greater than zero")
        if max_delta_seconds <= 0.0:
            raise ValueError("max_delta_seconds must be greater than zero")
        self._smoothing = float(smoothing)
        self._max_delta_seconds = float(max_delta_seconds)

    @property
    def smoothing(self) -> float:
        return self._smoothing

    @property
    def max_delta_seconds(self) -> float:
        return self._max_delta_seconds

    def update(
        self,
        current: WorldPoint,
        target: WorldPoint | None,
        delta_seconds: float,
    ) -> WorldPoint:
        """Return the next camera center without mutating either input point."""
        if not isinstance(current, WorldPoint):
            raise TypeError("current must be a WorldPoint")
        if target is not None and not isinstance(target, WorldPoint):
            raise TypeError("target must be a WorldPoint or None")
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, (int, float)):
            raise TypeError("delta_seconds must be a real number")
        if not math.isfinite(delta_seconds) or delta_seconds < 0.0:
            raise ValueError("delta_seconds must be finite and non-negative")
        if target is None or delta_seconds == 0.0:
            return current

        elapsed = min(float(delta_seconds), self._max_delta_seconds)
        alpha = 1.0 - math.exp(-self._smoothing * elapsed)
        return WorldPoint(
            current.x + (target.x - current.x) * alpha,
            current.y + (target.y - current.y) * alpha,
        )
