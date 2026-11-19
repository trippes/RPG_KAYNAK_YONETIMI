"""Build deterministic collision geometry for one loaded hex map."""

from dataclasses import dataclass
from enum import Enum

from hex_world_lab.geometry import (
    AxialCoord,
    WorldPoint,
    axial_to_world,
    hex_edges,
    hex_neighbors,
    hex_polygon,
)
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.world.identity import CellAddress, MapId
from hex_world_lab.world.runtime import HexWorldRuntime
from hex_world_lab.world.world_view import HexWorldView

from .obstacle import ObstacleDefinition
from .shapes import ConvexPolygonShape


_BOUNDARY_WALL_THICKNESS = 1e-4


class BoundaryPolicy(Enum):
    """Whether the perimeter of a finite map blocks movement."""

    BLOCKED = "blocked"
    OPEN = "open"


@dataclass(frozen=True, slots=True)
class HexBoundaryEdge:
    """One exposed map edge, oriented by its source cell's polygon."""

    edge_id: str
    map_id: MapId
    source_cell: AxialCoord
    start: WorldPoint
    end: WorldPoint

    def __post_init__(self) -> None:
        if not isinstance(self.edge_id, str) or not self.edge_id.strip():
            raise ValueError("edge_id must be a non-empty string")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.source_cell, AxialCoord):
            raise TypeError("source_cell must be an AxialCoord")
        if not isinstance(self.start, WorldPoint) or not isinstance(self.end, WorldPoint):
            raise TypeError("boundary endpoints must be WorldPoint values")
        if self.start == self.end:
            raise ValueError("boundary edge endpoints must differ")

    def as_obstacle(self) -> ObstacleDefinition:
        """Represent this perimeter edge as a thin, two-sided convex wall.

        The wall is centered on the exact hex edge. Its thickness is only a
        numerical collision tolerance; the swept circle still determines the
        effective clearance from the map perimeter.
        """
        dx = self.end.x - self.start.x
        dy = self.end.y - self.start.y
        length = (dx * dx + dy * dy) ** 0.5
        half = _BOUNDARY_WALL_THICKNESS / 2.0
        nx = -dy / length * half
        ny = dx / length * half
        vertices = (
            Vector2(self.start.x + nx, self.start.y + ny),
            Vector2(self.end.x + nx, self.end.y + ny),
            Vector2(self.end.x - nx, self.end.y - ny),
            Vector2(self.start.x - nx, self.start.y - ny),
        )
        return ObstacleDefinition(
            obstacle_id=self.edge_id,
            map_id=self.map_id,
            shape=ConvexPolygonShape(vertices),
            position=WorldPoint(0.0, 0.0),
        )


@dataclass(frozen=True, slots=True)
class HexMapCollisionGeometry:
    """Immutable collision snapshot for the currently loaded map."""

    map_id: MapId
    obstacles: tuple[ObstacleDefinition, ...]
    boundary_edges: tuple[HexBoundaryEdge, ...]
    boundary_policy: BoundaryPolicy

    def __post_init__(self) -> None:
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.boundary_policy, BoundaryPolicy):
            raise TypeError("boundary_policy must be a BoundaryPolicy")
        obstacles = tuple(self.obstacles)
        boundaries = tuple(self.boundary_edges)
        if any(not isinstance(item, ObstacleDefinition) for item in obstacles):
            raise TypeError("obstacles must contain ObstacleDefinition values")
        if any(not isinstance(item, HexBoundaryEdge) for item in boundaries):
            raise TypeError("boundary_edges must contain HexBoundaryEdge values")
        ids = [item.obstacle_id for item in obstacles]
        if len(ids) != len(set(ids)):
            raise ValueError("obstacle IDs must be unique within a map")
        if any(item.map_id != self.map_id for item in obstacles):
            raise ValueError("all obstacles must belong to the collision map")
        if any(item.map_id != self.map_id for item in boundaries):
            raise ValueError("all boundary edges must belong to the collision map")
        if self.boundary_policy is BoundaryPolicy.OPEN and boundaries:
            raise ValueError("OPEN boundary policy must not expose blocking boundary edges")
        object.__setattr__(
            self, "obstacles", tuple(sorted(obstacles, key=lambda item: item.obstacle_id))
        )
        object.__setattr__(
            self, "boundary_edges", tuple(sorted(boundaries, key=lambda item: item.edge_id))
        )

    @property
    def collision_obstacles(self) -> tuple[ObstacleDefinition, ...]:
        """Return object/cell obstacles plus physical walls for blocked edges."""
        if self.boundary_policy is BoundaryPolicy.OPEN:
            return self.obstacles
        combined = self.obstacles + tuple(edge.as_obstacle() for edge in self.boundary_edges)
        ids = [item.obstacle_id for item in combined]
        if len(ids) != len(set(ids)):
            raise ValueError("boundary and object obstacle IDs must be unique")
        return tuple(sorted(combined, key=lambda item: item.obstacle_id))


def _boundary_edges(
    map_id: MapId,
    coords: set[AxialCoord],
    layout,
) -> tuple[HexBoundaryEdge, ...]:
    edges: list[HexBoundaryEdge] = []
    for coord in sorted(coords, key=lambda item: (item.q, item.r)):
        center = axial_to_world(coord, layout)
        neighbors = hex_neighbors(coord)
        for edge_index, (start, end) in enumerate(hex_edges(center, layout)):
            midpoint_x = (start.x + end.x) / 2.0
            midpoint_y = (start.y + end.y) / 2.0
            normal_x = midpoint_x - center.x
            normal_y = midpoint_y - center.y
            neighbor = max(
                neighbors,
                key=lambda candidate: (
                    (axial_to_world(candidate, layout).x - center.x) * normal_x
                    + (axial_to_world(candidate, layout).y - center.y) * normal_y
                ),
            )
            if neighbor not in coords:
                edges.append(
                    HexBoundaryEdge(
                        edge_id=f"boundary:{coord.q}:{coord.r}:{edge_index}",
                        map_id=map_id,
                        source_cell=coord,
                        start=start,
                        end=end,
                    )
                )
    return tuple(edges)


def build_hex_map_collision_geometry(
    world_view: HexWorldView,
    runtime: HexWorldRuntime,
    map_id: MapId,
    *,
    boundary_policy: BoundaryPolicy = BoundaryPolicy.BLOCKED,
    object_obstacles: tuple[ObstacleDefinition, ...] = (),
) -> HexMapCollisionGeometry:
    """Build a stable snapshot without loading maps or reading runtime internals."""
    if not isinstance(world_view, HexWorldView):
        raise TypeError("world_view must be a HexWorldView")
    if not isinstance(runtime, HexWorldRuntime):
        raise TypeError("runtime must be a HexWorldRuntime")
    if not isinstance(map_id, MapId):
        raise TypeError("map_id must be a MapId")
    if not isinstance(boundary_policy, BoundaryPolicy):
        raise TypeError("boundary_policy must be a BoundaryPolicy")
    if world_view.world_id != runtime.world_id:
        raise ValueError("world view and runtime must belong to the same world")

    definition = runtime.require_loaded_map(map_id)
    if definition.world_id != world_view.world_id:
        raise ValueError("map and world view must belong to the same world")

    obstacles: list[ObstacleDefinition] = []
    coords = set(definition.cells)
    for coord in sorted(coords, key=lambda item: (item.q, item.r)):
        address = CellAddress(definition.world_id, map_id, coord)
        cell = world_view.get_cell(address)
        if cell is not None and cell.has_obstacle:
            center = axial_to_world(coord, definition.layout)
            world_vertices = hex_polygon(coord, definition.layout)
            local_vertices = tuple(
                Vector2(point.x - center.x, point.y - center.y)
                for point in world_vertices
            )
            obstacles.append(
                ObstacleDefinition(
                    obstacle_id=f"cell:{coord.q}:{coord.r}",
                    map_id=map_id,
                    shape=ConvexPolygonShape(local_vertices),
                    position=center,
                    source_cell=address,
                )
            )

    supplied_objects = tuple(object_obstacles)
    if any(not isinstance(item, ObstacleDefinition) for item in supplied_objects):
        raise TypeError("object_obstacles must contain ObstacleDefinition values")
    obstacles.extend(supplied_objects)

    boundaries = (
        _boundary_edges(map_id, coords, definition.layout)
        if boundary_policy is BoundaryPolicy.BLOCKED
        else ()
    )
    return HexMapCollisionGeometry(
        map_id=map_id,
        obstacles=tuple(obstacles),
        boundary_edges=boundaries,
        boundary_policy=boundary_policy,
    )
