"""Conservative viewport-to-axial visibility queries for hex maps."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from hex_world_lab.camera import ScreenPoint, WorldScreenTransform
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    WorldPoint,
    world_to_fractional_axial,
)


@dataclass(frozen=True, slots=True)
class VisibleRegion:
    """Conservative world-space axis-aligned viewport bounds."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float

    def intersects_aabb(self, min_x: float, min_y: float, max_x: float, max_y: float) -> bool:
        return not (
            max_x < self.min_x or min_x > self.max_x
            or max_y < self.min_y or min_y > self.max_y
        )



MIN_CULLING_CELL_COUNT = 257


def should_use_culling(cell_count: int) -> bool:
    """Return whether measurements justify viewport culling for this map size."""
    if isinstance(cell_count, bool) or not isinstance(cell_count, int):
        raise TypeError("cell_count must be an integer")
    if cell_count < 0:
        raise ValueError("cell_count must not be negative")
    return cell_count >= MIN_CULLING_CELL_COUNT


class VisibleAreaCuller:
    """Return a conservative superset of existing cells touching the viewport.

    False positives are acceptable; false negatives are not.
    """

    def visible_region(self, transform: WorldScreenTransform, layout: HexLayout) -> VisibleRegion:
        if not isinstance(transform, WorldScreenTransform):
            raise TypeError("transform must be a WorldScreenTransform")
        if not isinstance(layout, HexLayout):
            raise TypeError("layout must be a HexLayout")
        viewport = transform.viewport
        corners = (
            transform.screen_to_world(ScreenPoint(0.0, 0.0)),
            transform.screen_to_world(ScreenPoint(float(viewport.width), 0.0)),
            transform.screen_to_world(ScreenPoint(0.0, float(viewport.height))),
            transform.screen_to_world(ScreenPoint(float(viewport.width), float(viewport.height))),
        )
        margin = layout.radius
        return VisibleRegion(
            min(point.x for point in corners) - margin,
            min(point.y for point in corners) - margin,
            max(point.x for point in corners) + margin,
            max(point.y for point in corners) + margin,
        )

    def visible_cells(self, cells: Mapping[AxialCoord, object], layout: HexLayout,
                      transform: WorldScreenTransform) -> tuple[AxialCoord, ...]:
        if not isinstance(cells, Mapping):
            raise TypeError("cells must be a mapping")
        region = self.visible_region(transform, layout)
        corners = (
            WorldPoint(region.min_x, region.min_y), WorldPoint(region.min_x, region.max_y),
            WorldPoint(region.max_x, region.min_y), WorldPoint(region.max_x, region.max_y),
        )
        fractional = tuple(world_to_fractional_axial(point, layout) for point in corners)
        q_min = math.floor(min(value[0] for value in fractional)) - 1
        q_max = math.ceil(max(value[0] for value in fractional)) + 1
        r_min = math.floor(min(value[1] for value in fractional)) - 1
        r_max = math.ceil(max(value[1] for value in fractional)) + 1
        visible = [
            AxialCoord(q, r)
            for q in range(q_min, q_max + 1)
            for r in range(r_min, r_max + 1)
            if AxialCoord(q, r) in cells
        ]
        return tuple(sorted(visible, key=lambda coord: (coord.q, coord.r)))
