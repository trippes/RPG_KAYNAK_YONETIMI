"""World-space map bounds and viewport-aware camera clamping."""

from __future__ import annotations

from dataclasses import dataclass
import math
from collections.abc import Iterable

from hex_world_lab.geometry import AxialCoord, HexLayout, WorldPoint, hex_polygon

from .coordinates import Viewport


@dataclass(frozen=True, slots=True)
class WorldBounds:
    """Axis-aligned world-space bounds enclosing a collection of geometry."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def __post_init__(self) -> None:
        values = (self.min_x, self.min_y, self.max_x, self.max_y)
        if any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in values):
            raise TypeError("world bounds coordinates must be real numbers")
        if not all(math.isfinite(value) for value in values):
            raise ValueError("world bounds coordinates must be finite")
        if self.min_x > self.max_x or self.min_y > self.max_y:
            raise ValueError("world bounds minimums must not exceed maximums")

    @property
    def center(self) -> WorldPoint:
        return WorldPoint(
            (self.min_x + self.max_x) / 2.0,
            (self.min_y + self.max_y) / 2.0,
        )


def bounds_from_hex_cells(
    cells: Iterable[AxialCoord],
    layout: HexLayout,
) -> WorldBounds | None:
    """Build an AABB from actual hex polygon vertices; return None for no cells."""
    if not isinstance(layout, HexLayout):
        raise TypeError("layout must be a HexLayout")
    if cells is None:
        raise TypeError("cells must be an iterable of AxialCoord values")

    min_x = min_y = math.inf
    max_x = max_y = -math.inf
    found = False
    for coord in cells:
        if not isinstance(coord, AxialCoord):
            raise TypeError("cells must contain only AxialCoord values")
        found = True
        for point in hex_polygon(coord, layout):
            min_x = min(min_x, point.x)
            min_y = min(min_y, point.y)
            max_x = max(max_x, point.x)
            max_y = max(max_y, point.y)

    if not found:
        return None
    return WorldBounds(min_x, min_y, max_x, max_y)


def clamp_camera_center(
    center: WorldPoint,
    bounds: WorldBounds,
    viewport: Viewport,
    zoom: float,
) -> WorldPoint:
    """Clamp camera center so its visible world rectangle stays within bounds.

    If the viewport spans more world units than the map on an axis, that axis
    is centered on the map rather than applying an inverted clamp interval.
    """
    if not isinstance(center, WorldPoint):
        raise TypeError("center must be a WorldPoint")
    if not isinstance(bounds, WorldBounds):
        raise TypeError("bounds must be a WorldBounds")
    if not isinstance(viewport, Viewport):
        raise TypeError("viewport must be a Viewport")
    if isinstance(zoom, bool) or not isinstance(zoom, (int, float)):
        raise TypeError("zoom must be a real number")
    if not math.isfinite(zoom) or zoom <= 0.0:
        raise ValueError("zoom must be finite and greater than zero")

    half_width = viewport.width / (2.0 * zoom)
    half_height = viewport.height / (2.0 * zoom)

    def clamp_axis(value: float, minimum: float, maximum: float, half_extent: float) -> float:
        low = minimum + half_extent
        high = maximum - half_extent
        if low > high:
            return (minimum + maximum) / 2.0
        return min(high, max(low, value))

    return WorldPoint(
        clamp_axis(center.x, bounds.min_x, bounds.max_x, half_width),
        clamp_axis(center.y, bounds.min_y, bounds.max_y, half_height),
    )
