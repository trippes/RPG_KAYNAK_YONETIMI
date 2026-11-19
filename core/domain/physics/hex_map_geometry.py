"""Native collision geometry derived directly from Eldoria HexMapDefinition."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from core.domain.spatial import LocalHexPosition, WorldPoint
from .obstacle import StaticObstacle
from .shapes import ConvexPolygonShape


_BOUNDARY_WALL_THICKNESS = 1e-4
class BoundaryPolicy(Enum):
    """Whether the perimeter of the finite map blocks physical movement."""
    BLOCKED = "blocked"
    OPEN = "open"


@dataclass(frozen=True, slots=True)
class HexBoundaryEdge:
    """One exposed edge of the union of valid map hexes."""
    edge_id: str
    map_id: str
    source_cell: LocalHexPosition
    start: WorldPoint
    end: WorldPoint

    def __post_init__(self) -> None:
        if not isinstance(self.edge_id, str) or not self.edge_id.strip():
            raise ValueError("edge_id must be a non-empty string.")
        if not isinstance(self.map_id, str) or not self.map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        if not isinstance(self.source_cell, LocalHexPosition):
            raise TypeError("source_cell must be a LocalHexPosition.")
        if not isinstance(self.start, WorldPoint) or not isinstance(self.end, WorldPoint):
            raise TypeError("edge endpoints must be WorldPoint values.")
        if self.start == self.end:
            raise ValueError("boundary edge endpoints must differ.")

    def as_obstacle(self) -> StaticObstacle:
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        length = math.hypot(dx, dy)
        half = _BOUNDARY_WALL_THICKNESS / 2.0
        nx, ny = -dy / length * half, dx / length * half
        vertices = (
            WorldPoint(self.start.x + nx, self.start.y + ny),
            WorldPoint(self.end.x + nx, self.end.y + ny),
            WorldPoint(self.end.x - nx, self.end.y - ny),
            WorldPoint(self.start.x - nx, self.start.y - ny),
        )
        return StaticObstacle(
            self.edge_id, self.map_id, ConvexPolygonShape(vertices),
            WorldPoint(0.0, 0.0),
        )


@dataclass(frozen=True, slots=True)
class HexMapCollisionGeometry:
    """Immutable collision geometry for one canonical Eldoria map."""
    map_id: str
    obstacles: tuple[StaticObstacle, ...]
    boundary_edges: tuple[HexBoundaryEdge, ...]
    boundary_policy: BoundaryPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.map_id, str) or not self.map_id.strip():
            raise ValueError("map_id must be a non-empty string.")
        if not isinstance(self.boundary_policy, BoundaryPolicy):
            raise TypeError("boundary_policy must be a BoundaryPolicy.")
        obstacles, edges = tuple(self.obstacles), tuple(self.boundary_edges)
        if any(not isinstance(item, StaticObstacle) for item in obstacles):
            raise TypeError("obstacles must contain StaticObstacle values.")
        if any(not isinstance(item, HexBoundaryEdge) for item in edges):
            raise TypeError("boundary_edges must contain HexBoundaryEdge values.")
        if any(item.map_id != self.map_id for item in obstacles):
            raise ValueError("all obstacles must belong to this map.")
        if any(item.map_id != self.map_id for item in edges):
            raise ValueError("all boundary edges must belong to this map.")
        ids = [item.obstacle_id for item in obstacles]
        if len(ids) != len(set(ids)):
            raise ValueError("obstacle IDs must be unique.")
        if self.boundary_policy is BoundaryPolicy.OPEN and edges:
            raise ValueError("OPEN boundary policy cannot contain blocking edges.")
        object.__setattr__(self, "obstacles", tuple(sorted(obstacles, key=lambda x: x.obstacle_id)))
        object.__setattr__(self, "boundary_edges", tuple(sorted(edges, key=lambda x: x.edge_id)))

    @property
    def collision_obstacles(self) -> tuple[StaticObstacle, ...]:
        if self.boundary_policy is BoundaryPolicy.OPEN:
            return self.obstacles
        combined = self.obstacles + tuple(edge.as_obstacle() for edge in self.boundary_edges)
        ids = [item.obstacle_id for item in combined]
        if len(ids) != len(set(ids)):
            raise ValueError("boundary and map obstacle IDs must be unique.")
        return tuple(sorted(combined, key=lambda x: x.obstacle_id))
