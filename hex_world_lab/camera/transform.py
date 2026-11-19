"""Pure world-to-screen and screen-to-world camera transformations."""

from __future__ import annotations

from dataclasses import dataclass
import math

from hex_world_lab.geometry import WorldPoint

from .coordinates import ScreenPoint, Viewport


@dataclass(frozen=True, slots=True)
class WorldScreenTransform:
    """Immutable transform for one camera center, zoom, and viewport snapshot."""

    viewport: Viewport
    center: WorldPoint
    zoom: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        if not isinstance(self.center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        if isinstance(self.zoom, bool) or not isinstance(self.zoom, (int, float)):
            raise TypeError("zoom must be a real number")
        if not math.isfinite(self.zoom) or self.zoom <= 0.0:
            raise ValueError("zoom must be finite and greater than zero")
        object.__setattr__(self, "zoom", float(self.zoom))

    def world_to_screen(self, point: WorldPoint) -> ScreenPoint:
        """Map a world point to viewport pixels, flipping the y axis once."""
        if not isinstance(point, WorldPoint):
            raise TypeError("point must be a WorldPoint")
        return ScreenPoint(
            self.viewport.width / 2.0
            + (point.x - self.center.x) * self.zoom,
            self.viewport.height / 2.0
            - (point.y - self.center.y) * self.zoom,
        )

    def screen_to_world(self, point: ScreenPoint) -> WorldPoint:
        """Map viewport pixels back to mathematical world coordinates."""
        if not isinstance(point, ScreenPoint):
            raise TypeError("point must be a ScreenPoint")
        return WorldPoint(
            self.center.x
            + (point.x - self.viewport.width / 2.0) / self.zoom,
            self.center.y
            - (point.y - self.viewport.height / 2.0) / self.zoom,
        )
