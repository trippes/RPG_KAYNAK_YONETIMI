"""Immutable render-only snapshots with no simulation or Pygame dependencies."""
from __future__ import annotations
from dataclasses import dataclass
from hex_world_lab.geometry import AxialCoord, WorldPoint
from .visibility import VisibleRegion


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
class SpriteVisual:
    """A sprite placed by its world-space ground-contact point."""
    visual_id: str
    asset_key: str
    ground_anchor: WorldPoint
    depth_anchor_y: float
    layer_priority: int = 0
    normalized_anchor: tuple[float, float] | None = None


@dataclass(frozen=True, slots=True)
class EnvironmentDebugVisual:
    """World-space anchor and bounds metadata for an environment instance."""
    instance_id: str
    ground_anchor: WorldPoint
    depth_anchor: WorldPoint
    visual_bounds: tuple[WorldPoint, WorldPoint]
    canopy_bounds: tuple[WorldPoint, WorldPoint] | None = None


@dataclass(frozen=True, slots=True)
class ColliderVisual:
    """A read-only physical shape for a debug overlay."""
    owner_id: str
    shape: CircleVisual | PolygonVisual
    category: str = "obstacle"


@dataclass(frozen=True, slots=True)
class RenderDebugOptions:
    show_hex_edges: bool = True
    show_cell_centers: bool = False
    show_coordinate_labels: bool = False
    show_collider_debug: bool = False
    show_culling_debug: bool = False
    show_environment_debug: bool = False


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
    sprites: tuple[SpriteVisual, ...] = ()
    colliders: tuple[ColliderVisual, ...] = ()
    debug_options: RenderDebugOptions = RenderDebugOptions()
    visible_region: VisibleRegion | None = None
    environment_debug: tuple[EnvironmentDebugVisual, ...] = ()
