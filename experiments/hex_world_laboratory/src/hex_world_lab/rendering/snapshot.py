"""Immutable render-only snapshots with no simulation or Pygame dependencies."""

from __future__ import annotations

from dataclasses import dataclass

from hex_world_lab.geometry import AxialCoord, WorldPoint


@dataclass(frozen=True, slots=True)
class CellVisual:
    coord: AxialCoord
    has_obstacle: bool = False
    is_active: bool = False


@dataclass(frozen=True, slots=True)
class CircleVisual:
    center: WorldPoint
    radius: float


@dataclass(frozen=True, slots=True)
class PolygonVisual:
    vertices: tuple[WorldPoint, ...]
    is_cell_obstacle: bool = False


@dataclass(frozen=True, slots=True)
class LineVisual:
    start: WorldPoint
    end: WorldPoint
    kind: str = "boundary"
    width: int = 2


@dataclass(frozen=True, slots=True)
class WorldRenderSnapshot:
    """All world-space visual data required for one read-only render pass."""

    cells: tuple[CellVisual, ...]
    circles: tuple[CircleVisual, ...]
    polygons: tuple[PolygonVisual, ...]
    boundaries: tuple[LineVisual, ...]
    house_lines: tuple[LineVisual, ...]
    actor_position: WorldPoint
    actor_radius: float
    selected_cell: AxialCoord | None = None
