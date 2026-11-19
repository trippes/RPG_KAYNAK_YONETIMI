"""Application factory projecting canonical map data into native physics geometry."""
from __future__ import annotations

import math

from application.hex_map_definition import HexMapDefinition
from core.domain.physics import (
    BoundaryPolicy,
    HexBoundaryEdge,
    HexMapCollisionGeometry,
    StaticObstacle,
)
from core.domain.physics.shapes import ConvexPolygonShape
from core.domain.spatial import HexCoord, LocalHexPosition, WorldPoint, axial_to_world_point


_NEIGHBOR_DELTAS = (
    (1, 0), (1, -1), (0, -1),
    (-1, 0), (-1, 1), (0, 1),
)


def _hex_vertices(center: WorldPoint, hex_size: float) -> tuple[WorldPoint, ...]:
    return tuple(
        WorldPoint(
            center.x + math.cos(math.radians(-90.0 + index * 60.0)) * hex_size,
            center.y + math.sin(math.radians(-90.0 + index * 60.0)) * hex_size,
        )
        for index in range(6)
    )


def _cell_center(
    position: LocalHexPosition,
    hex_size: float,
    origin: WorldPoint,
) -> WorldPoint:
    return axial_to_world_point(HexCoord(position.q, position.r), hex_size, origin)


def _boundary_edges(
    map_id: str,
    cells: frozenset[LocalHexPosition],
    hex_size: float,
    origin: WorldPoint,
) -> tuple[HexBoundaryEdge, ...]:
    edges: list[HexBoundaryEdge] = []
    for cell in sorted(cells, key=lambda item: (item.q, item.r)):
        center = _cell_center(cell, hex_size, origin)
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
    origin: WorldPoint = WorldPoint(0.0, 0.0),
    boundary_policy: BoundaryPolicy = BoundaryPolicy.BLOCKED,
    object_obstacles: tuple[StaticObstacle, ...] = (),
) -> HexMapCollisionGeometry:
    """Build native collision geometry in Eldoria's canonical y-down world frame.

    Origin is the world-space center of axial cell (0, 0).
    """
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be an Eldoria HexMapDefinition.")
    if isinstance(hex_size, bool) or not isinstance(hex_size, (int, float)):
        raise TypeError("hex_size must be a real number.")
    if not math.isfinite(hex_size) or hex_size <= 0:
        raise ValueError("hex_size must be finite and positive.")
    if not isinstance(origin, WorldPoint):
        raise TypeError("origin must be a WorldPoint.")
    if not isinstance(boundary_policy, BoundaryPolicy):
        raise TypeError("boundary_policy must be a BoundaryPolicy.")

    size = float(hex_size)
    obstacles: list[StaticObstacle] = []
    for cell in sorted(map_definition.valid_cells, key=lambda item: (item.q, item.r)):
        record = map_definition.get_cell(cell)
        if record is not None and record.blocked:
            center = _cell_center(cell, size, origin)
            local_vertices = tuple(
                WorldPoint(point.x - center.x, point.y - center.y)
                for point in _hex_vertices(center, size)
            )
            obstacles.append(StaticObstacle(
                f"cell:{cell.q}:{cell.r}", map_definition.map_id,
                ConvexPolygonShape(local_vertices), center,
            ))

    for landmark in sorted(map_definition.landmarks, key=lambda item: item.landmark_id):
        if not landmark.walkable:
            center = _cell_center(landmark.position, size, origin)
            local_vertices = tuple(
                WorldPoint(point.x - center.x, point.y - center.y)
                for point in _hex_vertices(center, size)
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
        _boundary_edges(map_definition.map_id, map_definition.valid_cells, size, origin)
        if boundary_policy is BoundaryPolicy.BLOCKED else ()
    )
    return HexMapCollisionGeometry(
        map_definition.map_id, tuple(obstacles), boundaries, boundary_policy,
    )
