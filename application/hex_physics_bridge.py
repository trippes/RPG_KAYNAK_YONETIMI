"""Stateless native physics projection from Eldoria hex maps."""
from __future__ import annotations

import math
from collections.abc import Iterable

from application.hex_map_definition import HexMapDefinition
from application.hex_map_physics import build_hex_map_collision_geometry
from core.domain.physics import (
    BoundaryPolicy,
    CircleShape,
    ContinuousCollisionResolution,
    PhysicsBodyDefinition,
    StaticObstacle,
    StaticObstacleIndex,
    Vector2,
    ActorBodyTransform,
    resolve_continuous_motion,
)
from core.domain.spatial import LocalHexPosition, WorldPoint, axial_to_world_point
from core.foundation import WorldId


class HexPhysicsSnapshot:
    """Immutable map/geometry snapshot with a private native static-obstacle index."""

    __slots__ = (
        "_world_id",
        "_map_definition",
        "_hex_size",
        "_origin",
        "_geometry",
        "_obstacle_index",
    )

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("HexPhysicsSnapshot is immutable")

    def __init__(
        self,
        world_id: WorldId,
        map_definition: HexMapDefinition,
        hex_size: float,
        origin: WorldPoint,
        geometry,
        *,
        cell_size: float = 128.0,
    ) -> None:
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a canonical WorldId")
        if not isinstance(map_definition, HexMapDefinition):
            raise TypeError("map_definition must be an Eldoria HexMapDefinition")
        if isinstance(hex_size, bool) or not isinstance(hex_size, (int, float)):
            raise TypeError("hex_size must be a real number")
        if not math.isfinite(hex_size) or hex_size <= 0:
            raise ValueError("hex_size must be finite and positive")
        if not isinstance(origin, WorldPoint):
            raise TypeError("origin must be a WorldPoint")
        from core.domain.physics import HexMapCollisionGeometry
        if not isinstance(geometry, HexMapCollisionGeometry):
            raise TypeError("geometry must be a native HexMapCollisionGeometry")
        if geometry.map_id != map_definition.map_id:
            raise ValueError("collision geometry belongs to a different map")
        obstacles = geometry.collision_obstacles
        object.__setattr__(self, "_world_id", world_id)
        object.__setattr__(self, "_map_definition", map_definition)
        object.__setattr__(self, "_hex_size", float(hex_size))
        object.__setattr__(self, "_origin", origin)
        object.__setattr__(self, "_geometry", geometry)
        object.__setattr__(
            self, "_obstacle_index",
            StaticObstacleIndex(obstacles, cell_size=cell_size),
        )

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def map_id(self) -> str:
        return self._map_definition.map_id

    @property
    def map_definition(self) -> HexMapDefinition:
        """Return the immutable canonical map used to build this snapshot."""
        return self._map_definition

    @property
    def hex_size(self) -> float:
        """Return the canonical hex geometry scale in world units."""
        return self._hex_size

    @property
    def origin(self) -> WorldPoint:
        """Return the canonical world-space origin shared with map physics."""
        return self._origin

    @property
    def geometry(self):
        return self._geometry

    @property
    def collision_obstacles(self) -> tuple[StaticObstacle, ...]:
        return self._geometry.collision_obstacles

    def cell_center(self, position: LocalHexPosition) -> WorldPoint:
        if not isinstance(position, LocalHexPosition):
            raise TypeError("position must be a LocalHexPosition")
        return axial_to_world_point(position.to_hex_coord(), self._hex_size, self._origin)

    def resolve_motion(
        self,
        start: WorldPoint,
        displacement: Vector2,
        body: PhysicsBodyDefinition,
    ) -> ContinuousCollisionResolution:
        """Resolve one continuous body displacement against this map's indexed obstacles."""
        if not isinstance(start, WorldPoint):
            raise TypeError("start must be a WorldPoint")
        if not isinstance(displacement, Vector2):
            raise TypeError("displacement must be a Vector2")
        if not isinstance(body, PhysicsBodyDefinition):
            raise TypeError("body must be a PhysicsBodyDefinition")
        if not isinstance(body.collider, CircleShape):
            raise TypeError("continuous movement currently requires a circle body")
        moving_circle = ActorBodyTransform(start).transform_shape(body)
        if not isinstance(moving_circle, CircleShape):
            raise TypeError("continuous movement currently requires a circle collider")
        return resolve_continuous_motion(
            moving_circle,
            displacement,
            self.collision_obstacles if body.enabled else (),
            map_id=self.map_id,
            candidate_provider=self._obstacle_index if body.enabled else None,
        )

    def resolve_cell_step(
        self,
        source: LocalHexPosition,
        target: LocalHexPosition,
        body: PhysicsBodyDefinition,
    ) -> ContinuousCollisionResolution:
        """Resolve a center-to-center cell step without changing gameplay state."""
        if not isinstance(source, LocalHexPosition):
            raise TypeError("source must be a LocalHexPosition")
        if not isinstance(target, LocalHexPosition):
            raise TypeError("target must be a LocalHexPosition")
        if not isinstance(body, PhysicsBodyDefinition):
            raise TypeError("body must be a PhysicsBodyDefinition")
        if not isinstance(body.collider, CircleShape):
            raise TypeError("continuous hex-step validation currently requires a circle body")
        if not self._map_definition.has_cell(source):
            raise ValueError("source cell is outside the canonical map mask")
        if not self._map_definition.has_cell(target):
            raise ValueError("target cell is outside the canonical map mask")

        start = self.cell_center(source)
        finish = self.cell_center(target)
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
            map_id=self.map_id,
            candidate_provider=provider,
        )

    def can_reach_cell(
        self,
        source: LocalHexPosition,
        target: LocalHexPosition,
        body: PhysicsBodyDefinition,
        *,
        tolerance: float = 1e-6,
    ) -> bool:
        if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
            raise TypeError("tolerance must be a real number")
        if not math.isfinite(tolerance) or tolerance < 0:
            raise ValueError("tolerance must be finite and non-negative")
        resolution = self.resolve_cell_step(source, target, body)
        start = self.cell_center(source)
        finish = self.cell_center(target)
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
    hex_size: float = 32.0,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
    boundary_policy: BoundaryPolicy = BoundaryPolicy.BLOCKED,
    object_obstacles: Iterable[StaticObstacle] = (),
    cell_size: float = 128.0,
) -> HexPhysicsSnapshot:
    """Build a native physics snapshot directly from Eldoria's canonical map."""
    if not isinstance(world_id, WorldId):
        raise TypeError("world_id must be a canonical WorldId")
    if not isinstance(map_definition, HexMapDefinition):
        raise TypeError("map_definition must be an Eldoria HexMapDefinition")
    if isinstance(hex_size, bool) or not isinstance(hex_size, (int, float)):
        raise TypeError("hex_size must be a real number")
    if not math.isfinite(hex_size) or hex_size <= 0:
        raise ValueError("hex_size must be finite and positive")
    if not isinstance(origin, WorldPoint):
        raise TypeError("origin must be a WorldPoint")
    if not isinstance(boundary_policy, BoundaryPolicy):
        raise TypeError("boundary_policy must be a BoundaryPolicy")
    supplied_obstacles = tuple(object_obstacles)
    if any(not isinstance(item, StaticObstacle) for item in supplied_obstacles):
        raise TypeError("object_obstacles must contain native StaticObstacle values")

    geometry = build_hex_map_collision_geometry(
        map_definition,
        float(hex_size),
        origin=origin,
        boundary_policy=boundary_policy,
        object_obstacles=supplied_obstacles,
    )
    return HexPhysicsSnapshot(
        world_id,
        map_definition,
        float(hex_size),
        origin,
        geometry,
        cell_size=cell_size,
    )


__all__ = ["HexPhysicsSnapshot", "build_hex_physics_snapshot"]
