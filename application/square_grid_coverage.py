"""Derived square-grid coverage over the canonical axial hex world.

This module classifies geometry only. It does not perform pathfinding, mutate
actors, or replace the continuous physics/collision authority.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from numbers import Real
from types import MappingProxyType

from application.hex_map_definition import HexMapDefinition
from core.domain.spatial import (
    LocalHexPosition,
    SquareGridCoord,
    WorldPoint,
    pointy_top_hex_corners,
    square_grid_cell_bounds,
    square_grid_to_world_point,
)


class SquareGridCellStatus(str, Enum):
    OUTSIDE = "outside"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    WALKABLE = "walkable"


@dataclass(frozen=True, slots=True)
class HexCellCoverage:
    position: LocalHexPosition
    terrain_id: str
    blocked: bool
    overlap_area: float


@dataclass(frozen=True, slots=True)
class SquareGridCellCoverage:
    coord: SquareGridCoord
    center: WorldPoint
    hex_cells: tuple[HexCellCoverage, ...]
    covered_area: float
    coverage_ratio: float
    status: SquareGridCellStatus

    @property
    def walkable(self) -> bool:
        return self.status is SquareGridCellStatus.WALKABLE

    @property
    def blocked(self) -> bool:
        return any(cell.blocked for cell in self.hex_cells)

    @property
    def fully_covered(self) -> bool:
        return self.status in {
            SquareGridCellStatus.WALKABLE,
            SquareGridCellStatus.BLOCKED,
        }

    @property
    def terrain_ids(self) -> tuple[str, ...]:
        return tuple(sorted({cell.terrain_id for cell in self.hex_cells}))


@dataclass(frozen=True, slots=True)
class SquareGridCoverageMap:
    map_id: str
    cell_size: float
    grid_origin: WorldPoint
    hex_origin: WorldPoint
    cells: Mapping[SquareGridCoord, SquareGridCellCoverage]

    def __post_init__(self) -> None:
        if not isinstance(self.map_id, str) or not self.map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        normalized = dict(sorted(self.cells.items()))
        object.__setattr__(self, "cells", MappingProxyType(normalized))

    @property
    def walkable_count(self) -> int:
        return sum(cell.walkable for cell in self.cells.values())

    @property
    def blocked_count(self) -> int:
        return sum(cell.status is SquareGridCellStatus.BLOCKED for cell in self.cells.values())

    @property
    def partial_count(self) -> int:
        return sum(cell.status is SquareGridCellStatus.PARTIAL for cell in self.cells.values())

    @property
    def outside_count(self) -> int:
        return sum(cell.status is SquareGridCellStatus.OUTSIDE for cell in self.cells.values())


def _axis_grid_range(
    minimum: float,
    maximum: float,
    *,
    origin: float,
    cell_size: float,
) -> range:
    first = math.floor((minimum - origin) / cell_size + 0.5)
    last = math.floor((maximum - origin) / cell_size + 0.5)
    return range(first, last + 1)


def _clip_polygon_to_boundary(
    polygon: list[tuple[float, float]],
    *,
    axis: int,
    boundary: float,
    keep_greater: bool,
) -> list[tuple[float, float]]:
    if not polygon:
        return []

    result: list[tuple[float, float]] = []
    previous = polygon[-1]
    previous_value = previous[axis]
    previous_inside = (
        previous_value >= boundary if keep_greater else previous_value <= boundary
    )

    for current in polygon:
        current_value = current[axis]
        current_inside = (
            current_value >= boundary if keep_greater else current_value <= boundary
        )
        if current_inside != previous_inside:
            denominator = current_value - previous_value
            if denominator != 0.0:
                fraction = (boundary - previous_value) / denominator
                result.append((
                    previous[0] + (current[0] - previous[0]) * fraction,
                    previous[1] + (current[1] - previous[1]) * fraction,
                ))
        if current_inside:
            result.append(current)
        previous = current
        previous_value = current_value
        previous_inside = current_inside
    return result


def _polygon_area(polygon: list[tuple[float, float]]) -> float:
    if len(polygon) < 3:
        return 0.0
    twice_area = 0.0
    previous = polygon[-1]
    for current in polygon:
        twice_area += previous[0] * current[1] - current[0] * previous[1]
        previous = current
    return abs(twice_area) * 0.5


def _hex_square_intersection_area(
    hex_polygon: tuple[tuple[float, float], ...],
    bounds: tuple[float, float, float, float],
) -> float:
    left, top, right, bottom = bounds
    clipped = list(hex_polygon)
    clipped = _clip_polygon_to_boundary(
        clipped, axis=0, boundary=left, keep_greater=True,
    )
    clipped = _clip_polygon_to_boundary(
        clipped, axis=0, boundary=right, keep_greater=False,
    )
    clipped = _clip_polygon_to_boundary(
        clipped, axis=1, boundary=top, keep_greater=True,
    )
    clipped = _clip_polygon_to_boundary(
        clipped, axis=1, boundary=bottom, keep_greater=False,
    )
    return _polygon_area(clipped)


def build_square_grid_coverage(
    map_definition: HexMapDefinition,
    cell_size: int | float,
    *,
    hex_size: int | float = 32.0,
    grid_origin: WorldPoint = WorldPoint(0.0, 0.0),
    hex_origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> SquareGridCoverageMap:
    """Build a deterministic square-cell coverage map over valid hex polygons.

    A square is walkable only when its complete area is covered by valid map
    hexes and none of the intersected hex area is marked blocked. Partial
    boundary squares and squares outside the valid-hex union are non-walkable.
    The map includes the full grid-aligned rectangle around the hex-map bounds,
    so outside cells remain explicit and testable.
    """
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be a HexMapDefinition.")
    if isinstance(cell_size, bool) or not isinstance(cell_size, Real):
        raise TypeError("cell_size must be a finite real number.")
    size = float(cell_size)
    if not math.isfinite(size) or size <= 0.0:
        raise ValueError("cell_size must be finite and greater than zero.")
    if isinstance(hex_size, bool) or not isinstance(hex_size, Real):
        raise TypeError("hex_size must be a finite real number.")
    radius = float(hex_size)
    if not math.isfinite(radius) or radius <= 0.0:
        raise ValueError("hex_size must be finite and greater than zero.")
    if not isinstance(grid_origin, WorldPoint):
        raise TypeError("grid_origin must be a WorldPoint.")
    if not isinstance(hex_origin, WorldPoint):
        raise TypeError("hex_origin must be a WorldPoint.")

    polygons: list[
        tuple[LocalHexPosition, str, bool, tuple[tuple[float, float], ...]]
    ] = []
    min_x = math.inf
    min_y = math.inf
    max_x = -math.inf
    max_y = -math.inf

    for position in sorted(map_definition.valid_cells):
        corners = pointy_top_hex_corners(
            position.to_hex_coord(), radius, hex_origin,
        )
        polygon = tuple((point.x, point.y) for point in corners)
        min_x = min(min_x, *(point[0] for point in polygon))
        min_y = min(min_y, *(point[1] for point in polygon))
        max_x = max(max_x, *(point[0] for point in polygon))
        max_y = max(max_y, *(point[1] for point in polygon))
        hex_cell = map_definition.get_cell(position)
        polygons.append((position, hex_cell.terrain_id, hex_cell.blocked, polygon))

    grid_x_range = _axis_grid_range(
        min_x, max_x, origin=grid_origin.x, cell_size=size,
    )
    grid_y_range = _axis_grid_range(
        min_y, max_y, origin=grid_origin.y, cell_size=size,
    )

    intersections: dict[SquareGridCoord, list[HexCellCoverage]] = {}
    area_epsilon = max(1e-12, size * size * 1e-12)

    for position, terrain_id, blocked, polygon in polygons:
        hex_min_x = min(point[0] for point in polygon)
        hex_max_x = max(point[0] for point in polygon)
        hex_min_y = min(point[1] for point in polygon)
        hex_max_y = max(point[1] for point in polygon)
        candidate_x = _axis_grid_range(
            hex_min_x, hex_max_x, origin=grid_origin.x, cell_size=size,
        )
        candidate_y = _axis_grid_range(
            hex_min_y, hex_max_y, origin=grid_origin.y, cell_size=size,
        )
        for grid_x in candidate_x:
            for grid_y in candidate_y:
                coord = SquareGridCoord(grid_x, grid_y)
                overlap = _hex_square_intersection_area(
                    polygon,
                    square_grid_cell_bounds(coord, size, origin=grid_origin),
                )
                if overlap > area_epsilon:
                    intersections.setdefault(coord, []).append(
                        HexCellCoverage(position, terrain_id, blocked, overlap)
                    )

    cell_area = size * size
    full_tolerance = max(1e-8, cell_area * 1e-9)
    cells: dict[SquareGridCoord, SquareGridCellCoverage] = {}
    for grid_x in grid_x_range:
        for grid_y in grid_y_range:
            coord = SquareGridCoord(grid_x, grid_y)
            center = square_grid_to_world_point(coord, size, origin=grid_origin)
            hex_cells = tuple(sorted(
                intersections.get(coord, ()),
                key=lambda item: item.position,
            ))
            covered_area = sum(item.overlap_area for item in hex_cells)
            if covered_area <= area_epsilon:
                coverage_ratio = 0.0
                status = SquareGridCellStatus.OUTSIDE
            else:
                coverage_ratio = min(1.0, max(0.0, covered_area / cell_area))
                fully_covered = covered_area >= cell_area - full_tolerance
                if not fully_covered:
                    status = SquareGridCellStatus.PARTIAL
                elif any(item.blocked for item in hex_cells):
                    status = SquareGridCellStatus.BLOCKED
                else:
                    status = SquareGridCellStatus.WALKABLE
            cells[coord] = SquareGridCellCoverage(
                coord=coord,
                center=center,
                hex_cells=hex_cells,
                covered_area=min(cell_area, covered_area),
                coverage_ratio=coverage_ratio,
                status=status,
            )

    return SquareGridCoverageMap(
        map_id=map_definition.map_id,
        cell_size=size,
        grid_origin=grid_origin,
        hex_origin=hex_origin,
        cells=cells,
    )


__all__ = [
    "HexCellCoverage",
    "SquareGridCellStatus",
    "SquareGridCellCoverage",
    "SquareGridCoverageMap",
    "build_square_grid_coverage",
]
