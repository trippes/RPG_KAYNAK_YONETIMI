"""Square movement-grid coordinate geometry, independent of Pygame."""

from __future__ import annotations

import math
from dataclasses import dataclass
from numbers import Real

from .world_point import WorldPoint


def _validate_cell_size(cell_size: object) -> float:
    if isinstance(cell_size, bool) or not isinstance(cell_size, Real):
        raise TypeError("cell_size must be a finite real number.")
    result = float(cell_size)
    if not math.isfinite(result):
        raise ValueError("cell_size must be finite.")
    if result <= 0.0:
        raise ValueError("cell_size must be greater than zero.")
    return result


def _validate_origin(origin: object) -> WorldPoint:
    if not isinstance(origin, WorldPoint):
        raise TypeError("origin must be a WorldPoint.")
    return origin


@dataclass(frozen=True, order=True, slots=True)
class SquareGridCoord:
    """Integer coordinate of a square-grid cell; x increases right, y increases down."""

    x: int
    y: int

    def __post_init__(self) -> None:
        if type(self.x) is not int or type(self.y) is not int:
            raise TypeError("square-grid coordinates must be integers (bool is not allowed).")


def world_point_to_square_grid(
    point: WorldPoint,
    cell_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> SquareGridCoord:
    """Return the square cell containing point.

    origin is the world-space center of cell (0, 0), not its top-left corner.
    Cell boundaries belong to the cell on their right/bottom. This half-open
    convention is deterministic for positive and negative world coordinates.
    """
    if not isinstance(point, WorldPoint):
        raise TypeError("point must be a WorldPoint.")
    size = _validate_cell_size(cell_size)
    grid_origin = _validate_origin(origin)
    grid_x = math.floor((point.x - grid_origin.x) / size + 0.5)
    grid_y = math.floor((point.y - grid_origin.y) / size + 0.5)
    return SquareGridCoord(grid_x, grid_y)


def square_grid_to_world_point(
    coord: SquareGridCoord,
    cell_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> WorldPoint:
    """Return the center of a square-grid cell in canonical world coordinates."""
    if not isinstance(coord, SquareGridCoord):
        raise TypeError("coord must be a SquareGridCoord.")
    size = _validate_cell_size(cell_size)
    grid_origin = _validate_origin(origin)
    return WorldPoint(
        grid_origin.x + coord.x * size,
        grid_origin.y + coord.y * size,
    )


def square_grid_cell_bounds(
    coord: SquareGridCoord,
    cell_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> tuple[float, float, float, float]:
    """Return (left, top, right, bottom) bounds for one square cell."""
    center = square_grid_to_world_point(coord, cell_size, origin=origin)
    half = _validate_cell_size(cell_size) / 2.0
    return center.x - half, center.y - half, center.x + half, center.y + half


def square_grid_cell_corners(
    coord: SquareGridCoord,
    cell_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> tuple[WorldPoint, WorldPoint, WorldPoint, WorldPoint]:
    """Return the cell corners clockwise, starting at top-left."""
    left, top, right, bottom = square_grid_cell_bounds(
        coord, cell_size, origin=origin,
    )
    return (
        WorldPoint(left, top),
        WorldPoint(right, top),
        WorldPoint(right, bottom),
        WorldPoint(left, bottom),
    )


__all__ = [
    "SquareGridCoord",
    "world_point_to_square_grid",
    "square_grid_to_world_point",
    "square_grid_cell_bounds",
    "square_grid_cell_corners",
]
