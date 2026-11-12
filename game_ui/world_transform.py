"""Presentation coordinate transforms for the axial hex world.

The domain remains expressed in axial coordinates. This adapter owns only
world-pixel and viewport-pixel conversion, including camera offset and zoom.
"""
from __future__ import annotations

from dataclasses import dataclass
import math

from core.domain.spatial import HexCoord
from core.domain.spatial.hex_geometry import axial_to_pixel, pixel_to_axial


@dataclass
class WorldTransform:
    """Convert between axial cells, world pixels, and screen pixels."""

    hex_size: float = 32.0
    camera_x: float = 0.0
    camera_y: float = 0.0
    viewport_center: tuple[float, float] = (0.0, 0.0)
    zoom: float = 1.0

    def __post_init__(self) -> None:
        self.configure(
            hex_size=self.hex_size,
            camera_x=self.camera_x,
            camera_y=self.camera_y,
            viewport_center=self.viewport_center,
            zoom=self.zoom,
        )

    @staticmethod
    def _finite(value: float, name: str) -> float:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise TypeError(f"{name} must be a finite number.")
        result = float(value)
        if not math.isfinite(result):
            raise ValueError(f"{name} must be finite.")
        return result

    def configure(
        self,
        *,
        hex_size: float | None = None,
        camera_x: float | None = None,
        camera_y: float | None = None,
        viewport_center: tuple[float, float] | None = None,
        zoom: float | None = None,
    ) -> None:
        if hex_size is not None:
            size = self._finite(hex_size, "hex_size")
            if size <= 0:
                raise ValueError("hex_size must be greater than zero.")
            self.hex_size = size
        if camera_x is not None:
            self.camera_x = self._finite(camera_x, "camera_x")
        if camera_y is not None:
            self.camera_y = self._finite(camera_y, "camera_y")
        if viewport_center is not None:
            if not isinstance(viewport_center, (tuple, list)) or len(viewport_center) != 2:
                raise TypeError("viewport_center must contain two coordinates.")
            self.viewport_center = (
                self._finite(viewport_center[0], "viewport_center.x"),
                self._finite(viewport_center[1], "viewport_center.y"),
            )
        if zoom is not None:
            value = self._finite(zoom, "zoom")
            if value <= 0:
                raise ValueError("zoom must be greater than zero.")
            self.zoom = value

    def axial_to_world(self, coord: HexCoord) -> tuple[float, float]:
        return axial_to_pixel(coord, self.hex_size)

    def world_to_screen(self, x: float, y: float) -> tuple[float, float]:
        return (
            self.viewport_center[0] + (self._finite(x, "world_x") - self.camera_x) * self.zoom,
            self.viewport_center[1] + (self._finite(y, "world_y") - self.camera_y) * self.zoom,
        )

    def screen_to_world(self, x: float, y: float) -> tuple[float, float]:
        return (
            (self._finite(x, "screen_x") - self.viewport_center[0]) / self.zoom + self.camera_x,
            (self._finite(y, "screen_y") - self.viewport_center[1]) / self.zoom + self.camera_y,
        )

    def axial_to_screen(self, coord: HexCoord) -> tuple[float, float]:
        return self.world_to_screen(*self.axial_to_world(coord))

    def screen_to_axial(self, x: float, y: float) -> HexCoord:
        world_x, world_y = self.screen_to_world(x, y)
        return pixel_to_axial(world_x, world_y, self.hex_size)
