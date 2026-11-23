"""Square-grid click-to-move route intent; continuous physics remains authoritative."""
from __future__ import annotations

import math
from dataclasses import dataclass

from application.square_grid_cache import SquareGridChunkCache
from application.square_grid_pathfinding import (
    SquareGridNavigationProfile, SquareGridPathfinder, make_physics_edge_validator,
)
from core.domain.movement import MovementIntent, MovementMode, MovementTarget
from core.domain.physics import Vector2
from core.domain.spatial import (
    LocalHexPosition, SquareGridCoord, WorldPoint, square_grid_to_world_point,
    world_point_to_hex, world_point_to_square_grid,
)


@dataclass(slots=True)
class _Route:
    runtime: object
    actor_id: str
    map_id: str
    goal: WorldPoint
    snapshot: object
    body: object
    cells: tuple[SquareGridCoord, ...]
    waypoints: tuple[WorldPoint, ...]
    blocked: frozenset[SquareGridCoord]
    cursor: int = 0


class SquareGridClickMoveRouteController:
    """Plan a square-grid route and expose one continuous world-space target."""

    ARRIVAL_TOLERANCE = 0.5

    def __init__(self, cache: SquareGridChunkCache, *, cell_size: float) -> None:
        if not isinstance(cache, SquareGridChunkCache):
            raise TypeError("cache must be a SquareGridChunkCache.")
        if isinstance(cell_size, bool) or not isinstance(cell_size, (int, float)):
            raise TypeError("cell_size must be a finite positive number.")
        if not math.isfinite(cell_size) or cell_size <= 0:
            raise ValueError("cell_size must be finite and positive.")
        self._cache = cache
        self._cell_size = float(cell_size)
        self._route: _Route | None = None
        self._target: MovementTarget | None = None
        self._status = "idle"
        self._metrics = {
            "player_square_grid_path_queries": 0,
            "player_square_grid_route_replans": 0,
            "player_square_grid_route_failures": 0,
            "player_square_grid_route_arrivals": 0,
        }

    @property
    def active(self) -> bool:
        return self._route is not None

    @property
    def status(self) -> str:
        return self._status

    def consume_movement_target(self) -> MovementTarget | None:
        target, self._target = self._target, None
        return target

    def cancel(self, reason: str = "cancelled") -> None:
        self._route = None
        self._target = None
        self._status = reason

    def metrics_snapshot(self) -> dict[str, int]:
        return dict(self._metrics)

    def intent(
        self, runtime, actor_id: str, goal: WorldPoint, physics_snapshot, body,
        *, mode: MovementMode = MovementMode.NORMAL,
    ) -> MovementIntent:
        self._target = None
        if runtime is None or physics_snapshot is None or body is None:
            self.cancel("navigation_unavailable")
            return MovementIntent()
        if not isinstance(goal, WorldPoint) or not isinstance(mode, MovementMode):
            raise TypeError("goal and mode must be WorldPoint and MovementMode.")

        try:
            entity = runtime.entity(actor_id)
            current = runtime.continuous_position(actor_id).point
            map_id = entity.position.map_id
            if physics_snapshot.map_id != map_id:
                self.cancel("physics_map_mismatch")
                return MovementIntent()
            definition = runtime.map_definition(map_id)
            target_hex = LocalHexPosition.from_hex_coord(world_point_to_hex(
                goal, physics_snapshot.hex_size, origin=physics_snapshot.origin,
            ))
            if not definition.has_cell(target_hex):
                self.cancel("target_outside_map")
                return MovementIntent()
            blocked = self._blocked_cells(runtime, map_id, actor_id, physics_snapshot)
            start_cell = world_point_to_square_grid(
                current, self._cell_size, origin=physics_snapshot.origin,
            )
            goal_cell = world_point_to_square_grid(
                goal, self._cell_size, origin=physics_snapshot.origin,
            )
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            self.cancel("navigation_context_invalid")
            return MovementIntent()

        route = self._route
        replan = (
            route is None or route.runtime is not runtime
            or route.actor_id != actor_id or route.map_id != map_id
            or route.goal != goal or route.snapshot is not physics_snapshot
            or route.body != body or route.blocked != blocked
            or start_cell not in route.cells[max(0, route.cursor):]
        )
        if replan:
            self._metrics["player_square_grid_route_replans"] += int(route is not None)
            route = self._plan(
                runtime, actor_id, map_id, current, goal, start_cell, goal_cell,
                blocked, physics_snapshot, body, entity.profile,
            )
            if route is None:
                return MovementIntent()
            self._route = route

        while route.cursor < len(route.waypoints):
            waypoint = route.waypoints[route.cursor]
            dx, dy = waypoint.x - current.x, waypoint.y - current.y
            if math.hypot(dx, dy) > self.ARRIVAL_TOLERANCE:
                self._target = MovementTarget(waypoint, self.ARRIVAL_TOLERANCE)
                self._status = "following"
                return MovementIntent(Vector2(dx, dy), mode)
            route.cursor += 1

        self._target = MovementTarget(goal, self.ARRIVAL_TOLERANCE)
        self._route = None
        self._status = "arrived"
        self._metrics["player_square_grid_route_arrivals"] += 1
        return MovementIntent()

    def _blocked_cells(self, runtime, map_id, actor_id, snapshot):
        blocked = set()
        for occupant in runtime.occupancy.snapshot():
            if occupant.entity_id == actor_id or occupant.position.map_id != map_id:
                continue
            if not (occupant.blocks_movement or occupant.blocks_occupancy):
                continue
            if runtime.entity(occupant.entity_id).profile.ignores_occupancy:
                continue
            point = runtime.continuous_position(occupant.entity_id).point
            blocked.add(world_point_to_square_grid(
                point, self._cell_size, origin=snapshot.origin,
            ))
        return frozenset(blocked)

    def _plan(
        self, runtime, actor_id, map_id, current, goal, start_cell, goal_cell,
        blocked, snapshot, body, movement_profile,
    ):
        try:
            coverage = self._cache.get_coverage_map(
                snapshot.map_definition,
                cell_size=self._cell_size,
                hex_size=snapshot.hex_size,
                grid_origin=snapshot.origin,
                hex_origin=snapshot.origin,
            )
            profile = SquareGridNavigationProfile(
                movement=movement_profile, collider_radius=body.collider.radius,
            )
            physics_edge = make_physics_edge_validator(snapshot, body)
            start_center = square_grid_to_world_point(
                start_cell, self._cell_size, origin=coverage.grid_origin,
            )

            def validate_edge(source, target):
                return physics_edge(current if source == start_center else source, target)

            self._metrics["player_square_grid_path_queries"] += 1
            cells = SquareGridPathfinder.find_path(
                coverage, start_cell, goal_cell, profile=profile,
                blocked_cells=blocked, edge_validator=validate_edge,
            )
            if not cells:
                self._fail("no_safe_route")
                return None
            waypoints = [
                square_grid_to_world_point(
                    cell, self._cell_size, origin=coverage.grid_origin,
                )
                for cell in cells[1:]
            ]
            last = waypoints[-1] if waypoints else current
            if math.hypot(goal.x - last.x, goal.y - last.y) > 1e-9:
                if not physics_edge(last, goal):
                    self._fail("goal_segment_blocked")
                    return None
                waypoints.append(goal)
            elif not waypoints:
                if not physics_edge(current, goal):
                    self._fail("goal_segment_blocked")
                    return None
                waypoints.append(goal)
            return _Route(
                runtime, actor_id, map_id, goal, snapshot, body,
                tuple(cells), tuple(waypoints), blocked,
            )
        except (AttributeError, KeyError, RuntimeError, TypeError, ValueError):
            self._fail("route_planning_error")
            return None

    def _fail(self, reason):
        self._route = None
        self._target = None
        self._status = reason
        self._metrics["player_square_grid_route_failures"] += 1


__all__ = ["SquareGridClickMoveRouteController"]
