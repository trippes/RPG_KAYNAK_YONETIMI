"""Stateless physics projection from Eldoria hex maps into Hex World physics."""

from __future__ import annotations

import math
from collections.abc import Iterable

from application.hex_map_definition import HexMapDefinition
from core.domain.spatial import LocalHexPosition
from core.foundation import WorldId
from hex_world_lab.geometry import HexLayout, HexOrientation
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics import (
    ActorBodyTransform,
    BodyDefinition,
    BoundaryPolicy,
    CircleShape,
    ContinuousCollisionResolution,
    HexMapCollisionGeometry,
    ObstacleDefinition,
    ObstacleSpatialIndex,
    build_hex_map_collision_geometry,
    resolve_continuous_motion,
)
from hex_world_lab.world import HexWorld
from hex_world_lab.world.cell import HexCellData
from hex_world_lab.world.map_definition import HexMapDefinition as LabHexMapDefinition

from .hex_world_geometry_bridge import (
    local_position_to_lab_axial,
    local_position_to_world_point,
    to_lab_map_id,
    to_lab_world_id,
)


class HexPhysicsSnapshot:
    """Immutable map/geometry snapshot with a private static-obstacle index.

    The snapshot is derived from Eldoria's canonical HexMapDefinition. The
    temporary HexWorld used to build it is discarded; no second map registry,
    content owner, actor registry, or movement state survives the build.
    """

    __slots__ = (
        "_world_id",
        "_map_definition",
        "_layout",
        "_geometry",
        "_obstacle_index",
    )

    def __init__(
        self,
        world_id: WorldId,
        map_definition: HexMapDefinition,
        layout: HexLayout,
        geometry: HexMapCollisionGeometry,
        *,
        cell_size: float = 128.0,
    ) -> None:
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId")
        if not isinstance(map_definition, HexMapDefinition):
            raise TypeError("map_definition must be an Eldoria HexMapDefinition")
        _require_pointy_top(layout)
        if not isinstance(geometry, HexMapCollisionGeometry):
            raise TypeError("geometry must be a HexMapCollisionGeometry")
        if geometry.map_id.value != map_definition.map_id:
            raise ValueError("collision geometry belongs to a different map")
        self._world_id = world_id
        self._map_definition = map_definition
        self._layout = layout
        self._geometry = geometry
        self._obstacle_index = ObstacleSpatialIndex(
            geometry.collision_obstacles,
            cell_size=cell_size,
        )

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def map_id(self) -> str:
        return self._map_definition.map_id

    @property
    def geometry(self) -> HexMapCollisionGeometry:
        return self._geometry

    @property
    def collision_obstacles(self) -> tuple[ObstacleDefinition, ...]:
        return self._geometry.collision_obstacles

    def resolve_cell_step(
        self,
        source: LocalHexPosition,
        target: LocalHexPosition,
        body: BodyDefinition,
    ) -> ContinuousCollisionResolution:
        """Resolve a center-to-center cell step without changing gameplay state."""
        if not isinstance(source, LocalHexPosition):
            raise TypeError("source must be a LocalHexPosition")
        if not isinstance(target, LocalHexPosition):
            raise TypeError("target must be a LocalHexPosition")
        if not isinstance(body, BodyDefinition):
            raise TypeError("body must be a BodyDefinition")
        if not isinstance(body.collider, CircleShape):
            raise TypeError("continuous hex-step validation currently requires a circle body")
        if not self._map_definition.has_cell(source):
            raise ValueError("source cell is outside the canonical map mask")
        if not self._map_definition.has_cell(target):
            raise ValueError("target cell is outside the canonical map mask")

        start = local_position_to_world_point(source, self._layout)
        finish = local_position_to_world_point(target, self._layout)
        displacement = Vector2(finish.x - start.x, finish.y - start.y)
        moving_circle = ActorBodyTransform(start).transform_shape(body)
        if not isinstance(moving_circle, CircleShape):
            raise TypeError("continuous hex-step validation requires a circle collider")

        obstacles = self.collision_obstacles if body.enabled else ()
        provider = self._obstacle_index if body.enabled else None
        return resolve_continuous_motion(
            moving_circle,
            displacement,
            obstacles,
            candidate_provider=provider,
        )

    def can_reach_cell(
        self,
        source: LocalHexPosition,
        target: LocalHexPosition,
        body: BodyDefinition,
        *,
        tolerance: float = 1e-6,
    ) -> bool:
        """Whether physics permits reaching the target cell center completely."""
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            raise TypeError("tolerance must be a real number")
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and non-negative")
        resolution = self.resolve_cell_step(source, target, body)
        start = local_position_to_world_point(source, self._layout)
        finish = local_position_to_world_point(target, self._layout)
        desired_x = finish.x - start.x
        desired_y = finish.y - start.y
        return (
            resolution.unresolved_penetration <= tolerance
            and math.isclose(
                resolution.applied_displacement.x,
                desired_x,
                rel_tol=0.0,
                abs_tol=tolerance,
            )
            and math.isclose(
                resolution.applied_displacement.y,
                desired_y,
                rel_tol=0.0,
                abs_tol=tolerance,
            )
        )


def build_hex_physics_snapshot(
    world_id: WorldId,
    map_definition: HexMapDefinition,
    layout: HexLayout,
    *,
    boundary_policy: BoundaryPolicy = BoundaryPolicy.BLOCKED,
    object_obstacles: Iterable[ObstacleDefinition] = (),
    cell_size: float = 128.0,
) -> HexPhysicsSnapshot:
    """Project one Eldoria map into a disposable lab world and build collision data."""
    if not isinstance(world_id, WorldId):
        raise TypeError("world_id must be a canonical WorldId")
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be an Eldoria HexMapDefinition")
    _require_pointy_top(layout)
    if not isinstance(boundary_policy, BoundaryPolicy):
        raise TypeError("boundary_policy must be a BoundaryPolicy")

    lab_world_id = to_lab_world_id(world_id)
    lab_map_id = to_lab_map_id(map_definition.map_id)
    blocked_landmarks = {
        landmark.position
        for landmark in map_definition.landmarks
        if not landmark.walkable
    }

    lab_cells = {}
    for position, cell in map_definition.cells.items():
        blocked = cell.blocked or position in blocked_landmarks
        lab_cells[local_position_to_lab_axial(position)] = HexCellData(
            terrain_id=cell.terrain_id,
            is_walkable=not blocked,
            has_obstacle=blocked,
        )

    projected_definition = LabHexMapDefinition(
        world_id=lab_world_id,
        map_id=lab_map_id,
        name=map_definition.name,
        layout=layout,
        cells=lab_cells,
    )
    projected_world = HexWorld(lab_world_id)
    projected_world.register_map(lab_map_id, map_definition.name)
    projected_world.load_map(projected_definition)

    geometry = build_hex_map_collision_geometry(
        projected_world.view,
        projected_world.runtime,
        lab_map_id,
        boundary_policy=boundary_policy,
        object_obstacles=tuple(object_obstacles),
    )
    return HexPhysicsSnapshot(
        world_id,
        map_definition,
        layout,
        geometry,
        cell_size=cell_size,
    )


def _require_pointy_top(layout: HexLayout) -> None:
    if not isinstance(layout, HexLayout):
        raise TypeError("layout must be a HexLayout")
    if layout.orientation is not HexOrientation.POINTY_TOP:
        raise ValueError("Eldoria physics currently supports pointy-top geometry only")


__all__ = ["HexPhysicsSnapshot", "build_hex_physics_snapshot"]
