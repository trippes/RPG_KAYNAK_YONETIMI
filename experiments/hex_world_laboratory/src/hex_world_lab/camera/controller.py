"""Pygame-independent camera controller and bounded zoom policy."""

from __future__ import annotations

import math

from hex_world_lab.geometry import WorldPoint

from .coordinates import Viewport
from .state import CameraState
from .transform import WorldScreenTransform


class CameraController:
    """Own camera state while exposing immutable snapshots to consumers."""

    __slots__ = ("_center", "_viewport", "_zoom", "_min_zoom", "_max_zoom", "_zoom_factor")

    def __init__(
        self,
        viewport: Viewport,
        center: WorldPoint = WorldPoint(0.0, 0.0),
        *,
        zoom: float = 1.0,
        min_zoom: float = 0.5,
        max_zoom: float = 3.0,
        zoom_factor: float = 1.1,
    ) -> None:
        if not isinstance(viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        if not isinstance(center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        for name, value in (
            ("min_zoom", min_zoom),
            ("max_zoom", max_zoom),
            ("zoom_factor", zoom_factor),
            ("zoom", zoom),
        ):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise TypeError(f"{name} must be a real number")
            if not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if min_zoom <= 0.0:
            raise ValueError("min_zoom must be greater than zero")
        if max_zoom < min_zoom:
            raise ValueError("max_zoom must be greater than or equal to min_zoom")
        if zoom_factor <= 1.0:
            raise ValueError("zoom_factor must be greater than one")

        self._viewport = viewport
        self._center = center
        self._min_zoom = float(min_zoom)
        self._max_zoom = float(max_zoom)
        self._zoom_factor = float(zoom_factor)
        self._zoom = self._clamp_zoom(float(zoom))

    @property
    def state(self) -> CameraState:
        """Return an immutable snapshot of the current camera."""
        return CameraState(self._center, self._viewport, self._zoom)

    @property
    def transform(self) -> WorldScreenTransform:
        """Return the world/screen transform for the current snapshot."""
        state = self.state
        return WorldScreenTransform(state.viewport, state.center, state.zoom)

    @property
    def min_zoom(self) -> float:
        return self._min_zoom

    @property
    def max_zoom(self) -> float:
        return self._max_zoom

    def set_zoom(self, zoom: float) -> float:
        """Set zoom, clamping it to the configured inclusive limits."""
        if isinstance(zoom, bool) or not isinstance(zoom, (int, float)):
            raise TypeError("zoom must be a real number")
        if not math.isfinite(zoom):
            raise ValueError("zoom must be finite")
        self._zoom = self._clamp_zoom(float(zoom))
        return self._zoom

    def zoom_by_steps(self, steps: int) -> float:
        """Apply discrete wheel steps; positive values zoom in."""
        if isinstance(steps, bool) or not isinstance(steps, int):
            raise TypeError("steps must be an integer")
        return self.set_zoom(self._zoom * self._zoom_factor ** steps)

    def set_viewport(self, viewport: Viewport) -> None:
        """Update drawable dimensions without changing world center or zoom."""
        if not isinstance(viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        self._viewport = viewport

    def set_center(self, center: WorldPoint) -> None:
        """Set the camera center in authoritative world coordinates."""
        if not isinstance(center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        self._center = center

    def _clamp_zoom(self, zoom: float) -> float:
        return min(self._max_zoom, max(self._min_zoom, zoom))
