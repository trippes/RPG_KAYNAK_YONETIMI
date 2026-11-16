"""Pure world-to-screen and screen-to-world camera transformations."""

from __future__ import annotations

import math

from hex_world_lab.geometry import WorldPoint

from .coordinates import ScreenPoint, Viewport


class WorldScreenTransform:
    """Immutable transform for one camera center, zoom, and viewport snapshot."""

    __slots__ = ("_viewport", "_center", "_zoom")

    def __init__(
        self,
        viewport: Viewport,
        center: WorldPoint,
        zoom: float = 1.0,
    ) -> None:
        if not isinstance(viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        if not isinstance(center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        if isinstance(zoom, bool) or not isinstance(zoom, (int, float)):
            raise TypeError("zoom must be a real number")
        if not math.isfinite(zoom) or zoom <= 0.0:
            raise ValueError("zoom must be finite and greater than zero")
        self._viewport = viewport
        self._center = center
        self._zoom = float(zoom)

    @property
    def viewport(self) -> Viewport:
        return self._viewport

    @property
    def center(self) -> WorldPoint:
        return self._center

    @property
    def zoom(self) -> float:
        return self._zoom

    def world_to_screen(self, point: WorldPoint) -> ScreenPoint:
        """Map a world point to viewport pixels, flipping the y axis once."""
        if not isinstance(point, WorldPoint):
            raise TypeError("point must be a WorldPoint")
        return ScreenPoint(
            self._viewport.width / 2.0
            + (point.x - self._center.x) * self._zoom,
            self._viewport.height / 2.0
            - (point.y - self._center.y) * self._zoom,
        )

    def screen_to_world(self, point: ScreenPoint) -> WorldPoint:
        """Map viewport pixels back to mathematical world coordinates."""
        if not isinstance(point, ScreenPoint):
            raise TypeError("point must be a ScreenPoint")
        return WorldPoint(
            self._center.x
            + (point.x - self._viewport.width / 2.0) / self._zoom,
            self._center.y
            - (point.y - self._viewport.height / 2.0) / self._zoom,
        )
