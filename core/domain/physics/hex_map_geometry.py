"""Native collision geometry derived directly from Eldoria HexMapDefinition."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math

from application.hex_map_definition import HexMapDefinition
from core.domain.spatial import HexCoord, LocalHexPosition, WorldPoint, axial_to_world_point
from .obstacle import StaticObstacle
from .shapes import ConvexPolygonShape


_BOUNDARY_WALL_THICKNESS = 1e-4
_NEIGHBOR_DELTAS = (
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1),
)


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


def _hex_vertices(center: WorldPoint, hex_size: float) -> tuple[WorldPoint, ...]:
    return tuple(
        WorldPoint(
            center.x + math.cos(math.radians(-90.0 + index * 60.0)) * hex_size,
            center.y + math.sin(math.radians(-90.0 + index * 60.0)) * hex_size,
        )
        for index in range(6)
    )


def _cell_center(position: LocalHexPosition, hex_size: float) -> WorldPoint:
    return axial_to_world_point(HexCoord(position.q, position.r), hex_size)


def _boundary_edges(
    map_id: str,
    cells: frozenset[LocalHexPosition],
    hex_size: float,
) -> tuple[HexBoundaryEdge, ...]:
    edges: list[HexBoundaryEdge] = []
    for cell in sorted(cells, key=lambda item: (item.q, item.r)):
        center = _cell_center(cell, hex_size)
        vertices = _hex_vertices(center, hex_size)
        for edge_index in range(6):
            start, end = vertices[edge_index], vertices[(edge_index + 1) % 6]
            midpoint = WorldPoint((start.x + end.x) / 2.0, (start.y + end.y) / 2.0)
            outward_x, outward_y = midpoint.x - center.x, midpoint.y - center.y
            neighbor = max(
                _NEIGHBOR_DELTAS,
                key=lambda delta: (
                    (delta[0] * math.sqrt(3.0) * hex_size
                     + delta[1] * math.sqrt(3.0) * hex_size / 2.0) * outward_x
                    + (delta[1] * 1.5 * hex_size) * outward_y
                ),
            )
            adjacent = LocalHexPosition(cell.q + neighbor[0], cell.r + neighbor[1])
            if adjacent not in cells:
                edges.append(HexBoundaryEdge(
                    f"boundary:{cell.q}:{cell.r}:{edge_index}",
                    map_id, cell, start, end,
                ))
    return tuple(edges)


def build_hex_map_collision_geometry(
    map_definition: HexMapDefinition,
    hex_size: int | float,
    *,
    boundary_policy: BoundaryPolicy = BoundaryPolicy.BLOCKED,
    object_obstacles: tuple[StaticObstacle, ...] = (),
) -> HexMapCollisionGeometry:
    """Build collision shapes from Eldoria's map mask and blocked content."""
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be an Eldoria HexMapDefinition.")
    if isinstance(hex_size, bool) or not isinstance(hex_size, (int, float)):
        raise TypeError("hex_size must be a real number.")
    if not math.isfinite(hex_size) or hex_size <= 0:
        raise ValueError("hex_size must be finite and positive.")
    if not isinstance(boundary_policy, BoundaryPolicy):
        raise TypeError("boundary_policy must be a BoundaryPolicy.")

    obstacles: list[StaticObstacle] = []
    for cell in sorted(map_definition.valid_cells, key=lambda item: (item.q, item.r)):
        record = map_definition.get_cell(cell)
        if record is not None and record.blocked:
            center = _cell_center(cell, float(hex_size))
            local_vertices = tuple(
                WorldPoint(point.x - center.x, point.y - center.y)
                for point in _hex_vertices(center, float(hex_size))
            )
            obstacles.append(StaticObstacle(
                f"cell:{cell.q}:{cell.r}", map_definition.map_id,
                ConvexPolygonShape(local_vertices), center,
            ))

    for landmark in sorted(map_definition.landmarks, key=lambda item: item.landmark_id):
        if not landmark.walkable:
            center = _cell_center(landmark.position, float(hex_size))
            local_vertices = tuple(
                WorldPoint(point.x - center.x, point.y - center.y)
                for point in _hex_vertices(center, float(hex_size))
            )
            obstacles.append(StaticObstacle(
                f"landmark:{landmark.landmark_id}", map_definition.map_id,
                ConvexPolygonShape(local_vertices), center,
            ))

    supplied = tuple(object_obstacles)
    if any(not isinstance(item, StaticObstacle) for item in supplied):
        raise TypeError("object_obstacles must contain StaticObstacle values.")
    if any(item.map_id != map_definition.map_id for item in supplied):
        raise ValueError("object obstacles must belong to the map definition.")
    obstacles.extend(supplied)

    boundaries = (
        _boundary_edges(map_definition.map_id, map_definition.valid_cells, float(hex_size))
        if boundary_policy is BoundaryPolicy.BLOCKED else ()
    )
    return HexMapCollisionGeometry(
        map_definition.map_id, tuple(obstacles), boundaries, boundary_policy,
    )
