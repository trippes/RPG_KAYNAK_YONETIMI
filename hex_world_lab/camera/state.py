"""Immutable camera state shared by pure camera controllers and renderers."""

from __future__ import annotations

from dataclasses import dataclass
import math

from hex_world_lab.geometry import WorldPoint

from .coordinates import Viewport


@dataclass(frozen=True, slots=True)
class CameraState:
    """A snapshot of camera center, zoom, and drawable viewport."""

    center: WorldPoint
    viewport: Viewport
    zoom: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.center, WorldPoint):
            raise TypeError("center must be a WorldPoint")
        if not isinstance(self.viewport, Viewport):
            raise TypeError("viewport must be a Viewport")
        if isinstance(self.zoom, bool) or not isinstance(self.zoom, (int, float)):
            raise TypeError("zoom must be a real number")
        if not math.isfinite(self.zoom) or self.zoom <= 0.0:
            raise ValueError("zoom must be finite and greater than zero")
        object.__setattr__(self, "zoom", float(self.zoom))
