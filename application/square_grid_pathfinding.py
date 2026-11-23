"""Deterministic, weighted A* navigation over derived square-grid coverage.

The pathfinder proposes cell-center waypoints only. It never moves actors and
never replaces continuous physics. Gameplay callers should supply an
edge_validator backed by the active physics snapshot.
"""
from __future__ import annotations

import heapq
import math
from collections.abc import Callable, Mapping, Set
from dataclasses import dataclass

from application.hex_physics_bridge import HexPhysicsSnapshot
from application.square_grid_coverage import (
    SquareGridCellCoverage,
    SquareGridCellStatus,
    SquareGridCoverageMap,
)
from core.domain.physics import PhysicsBodyDefinition, Vector2
from core.domain.spatial import (
    MovementProfile,
    SquareGridCoord,
    WorldPoint,
    square_grid_to_world_point,
)


@dataclass(frozen=True, slots=True)
class SquareGridNavigationProfile:
    """Actor-specific conservative grid clearance requirements."""

    movement: MovementProfile = MovementProfile()
    collider_radius: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.movement, MovementProfile):
            raise TypeError("movement must be a MovementProfile.")
        if isinstance(self.collider_radius, bool) or not isinstance(
            self.collider_radius, (int, float)
        ):
            raise TypeError("collider_radius must be a finite real number.")
        radius = float(self.collider_radius)
        if not math.isfinite(radius) or radius < 0.0:
            raise ValueError("collider_radius must be finite and non-negative.")
        object.__setattr__(self, "collider_radius", radius)


EdgeValidator = Callable[[WorldPoint, WorldPoint], bool]


def make_physics_edge_validator(
    snapshot: HexPhysicsSnapshot,
    body: PhysicsBodyDefinition,
    *,
    tolerance: float = 1e-6,
) -> EdgeValidator:
    """Build a side-effect-free edge validator using the active static physics snapshot."""
    if not isinstance(snapshot, HexPhysicsSnapshot):
        raise TypeError("snapshot must be a HexPhysicsSnapshot.")
    if not isinstance(body, PhysicsBodyDefinition):
        raise TypeError("body must be a PhysicsBodyDefinition.")
    if isinstance(tolerance, bool) or not isinstance(tolerance, (int, float)):
        raise TypeError("tolerance must be a finite non-negative real number.")
    if not math.isfinite(tolerance) or tolerance < 0.0:
        raise ValueError("tolerance must be finite and non-negative.")

    def validate(start: WorldPoint, end: WorldPoint) -> bool:
        if not isinstance(start, WorldPoint) or not isinstance(end, WorldPoint):
            raise TypeError("edge endpoints must be WorldPoint values.")
        displacement = Vector2(end.x - start.x, end.y - start.y)
        result = snapshot.resolve_motion(start, displacement, body)
        return (
            result.unresolved_penetration <= tolerance
            and math.isclose(
                result.applied_displacement.x,
                displacement.x,
                rel_tol=0.0,
                abs_tol=tolerance,
            )
            and math.isclose(
                result.applied_displacement.y,
                displacement.y,
                rel_tol=0.0,
                abs_tol=tolerance,
            )
        )

    return validate


def _terrain_multiplier(
    cell: SquareGridCellCoverage,
    terrain_costs: Mapping[str, float],
) -> float:
    terrain_ids = cell.terrain_ids
    if not terrain_ids:
        return 1.0
    return max(
        (terrain_costs.get(terrain_id, 1.0) for terrain_id in terrain_ids),
        default=1.0,
    )


def _validate_terrain_costs(
    terrain_costs: Mapping[str, float] | None,
) -> dict[str, float]:
    if terrain_costs is None:
        return {}
    if not isinstance(terrain_costs, Mapping):
        raise TypeError("terrain_costs must map terrain IDs to positive costs.")
    result: dict[str, float] = {}
    for terrain_id, raw_cost in terrain_costs.items():
        if not isinstance(terrain_id, str) or not terrain_id.strip():
            raise ValueError("terrain cost IDs must be non-empty strings.")
        if isinstance(raw_cost, bool) or not isinstance(raw_cost, (int, float)):
            raise TypeError("terrain costs must be finite positive real numbers.")
        cost = float(raw_cost)
        if not math.isfinite(cost) or cost <= 0.0:
            raise ValueError("terrain costs must be finite and greater than zero.")
        result[terrain_id] = cost
    return result


class SquareGridPathfinder:
    """Find deterministic lowest-cost paths on an eight-neighbour square graph."""

    _NEIGHBOURS = (
        (0, -1, 1.0),
        (-1, 0, 1.0),
        (1, 0, 1.0),
        (0, 1, 1.0),
        (-1, -1, math.sqrt(2.0)),
        (1, -1, math.sqrt(2.0)),
        (-1, 1, math.sqrt(2.0)),
        (1, 1, math.sqrt(2.0)),
    )

    @classmethod
    def find_path(
        cls,
        coverage: SquareGridCoverageMap,
        start: SquareGridCoord,
        goal: SquareGridCoord,
        *,
        profile: SquareGridNavigationProfile | None = None,
        blocked_cells: Set[SquareGridCoord] = frozenset(),
        terrain_costs: Mapping[str, float] | None = None,
        edge_validator: EdgeValidator | None = None,
    ) -> tuple[SquareGridCoord, ...] | None:
        """Return start-to-goal cells, or None when no safe route exists.

        Diagonal edges require both adjacent cardinal cells to be traversable.
        Collider clearance is a conservative grid-space prefilter. The optional
        edge_validator is the final per-edge physical preflight and should use
        the same collider and static-geometry snapshot as runtime movement.
        """
        if not isinstance(coverage, SquareGridCoverageMap):
            raise TypeError("coverage must be a SquareGridCoverageMap.")
        if not isinstance(start, SquareGridCoord) or not isinstance(goal, SquareGridCoord):
            raise TypeError("start and goal must be SquareGridCoord values.")
        navigation = profile if profile is not None else SquareGridNavigationProfile()
        if not isinstance(navigation, SquareGridNavigationProfile):
            raise TypeError("profile must be a SquareGridNavigationProfile.")
        if not navigation.movement.can_move:
            return None
        if not isinstance(blocked_cells, Set) or any(
            not isinstance(cell, SquareGridCoord) for cell in blocked_cells
        ):
            raise TypeError("blocked_cells must contain SquareGridCoord values.")
        costs = _validate_terrain_costs(terrain_costs)
        if edge_validator is not None and not callable(edge_validator):
            raise TypeError("edge_validator must be callable or None.")

        allowed_terrain = navigation.movement.allowed_terrain_ids
        permitted_statuses = {SquareGridCellStatus.WALKABLE}
        if navigation.movement.can_traverse_blocked_cells:
            permitted_statuses.add(SquareGridCellStatus.BLOCKED)
        walkable = {
            coord: cell
            for coord, cell in coverage.cells.items()
            if cell.status in permitted_statuses
            and (
                allowed_terrain is None
                or bool(cell.terrain_ids)
                and set(cell.terrain_ids).issubset(allowed_terrain)
            )
        }
        if start not in walkable or goal not in walkable:
            return None
        if not navigation.movement.ignores_occupancy and goal in blocked_cells:
            return None

        clearance = navigation.collider_radius
        clearance_offsets = math.ceil(clearance / coverage.cell_size) + 1
        clearance_cache: dict[SquareGridCoord, bool] = {}

        def traversable(coord: SquareGridCoord, *, is_start: bool = False) -> bool:
            if coord not in walkable:
                return False
            if (
                not is_start
                and not navigation.movement.ignores_occupancy
                and coord in blocked_cells
            ):
                return False
            cached = clearance_cache.get(coord)
            if cached is not None:
                return cached
            if clearance <= 0.0:
                clearance_cache[coord] = True
                return True

            center = square_grid_to_world_point(
                coord, coverage.cell_size, origin=coverage.grid_origin
            )
            radius_sq = clearance * clearance
            epsilon = max(1e-12, radius_sq * 1e-12)
            for dx in range(-clearance_offsets, clearance_offsets + 1):
                for dy in range(-clearance_offsets, clearance_offsets + 1):
                    neighbour = SquareGridCoord(coord.x + dx, coord.y + dy)
                    dynamically_blocked = (
                        not navigation.movement.ignores_occupancy
                        and neighbour in blocked_cells
                        and not (is_start and neighbour == coord)
                    )
                    if neighbour in walkable and not dynamically_blocked:
                        continue
                    left = (
                        coverage.grid_origin.x
                        + neighbour.x * coverage.cell_size
                        - coverage.cell_size / 2.0
                    )
                    right = left + coverage.cell_size
                    top = (
                        coverage.grid_origin.y
                        + neighbour.y * coverage.cell_size
                        - coverage.cell_size / 2.0
                    )
                    bottom = top + coverage.cell_size
                    nearest_x = min(max(center.x, left), right)
                    nearest_y = min(max(center.y, top), bottom)
                    distance_sq = (
                        (center.x - nearest_x) ** 2
                        + (center.y - nearest_y) ** 2
                    )
                    if distance_sq < radius_sq - epsilon:
                        clearance_cache[coord] = False
                        return False
            clearance_cache[coord] = True
            return True

        if not traversable(start, is_start=True) or not traversable(goal):
            return None
        if start == goal:
            return (start,)

        terrain_multiplier = {
            coord: _terrain_multiplier(cell, costs)
            for coord, cell in walkable.items()
        }
        minimum_multiplier = min(terrain_multiplier.values(), default=1.0)
        cell_size = coverage.cell_size

        def heuristic(coord: SquareGridCoord) -> float:
            dx = abs(goal.x - coord.x)
            dy = abs(goal.y - coord.y)
            diagonal = min(dx, dy)
            straight = max(dx, dy) - diagonal
            return (
                diagonal * math.sqrt(2.0) + straight
            ) * minimum_multiplier

        start_h = heuristic(start)
        # (f, h, y, x, g) gives stable ordering without insertion-order dependence.
        frontier: list[tuple[float, float, int, int, float]] = [
            (start_h, start_h, start.y, start.x, 0.0)
        ]
        came_from: dict[SquareGridCoord, SquareGridCoord] = {}
        cost_so_far = {start: 0.0}
        edge_cache: dict[tuple[SquareGridCoord, SquareGridCoord], bool] = {}

        while frontier:
            _, _, current_y, current_x, current_cost = heapq.heappop(frontier)
            current = SquareGridCoord(current_x, current_y)
            if current_cost != cost_so_far.get(current):
                continue
            if current == goal:
                path = [goal]
                while path[-1] != start:
                    path.append(came_from[path[-1]])
                path.reverse()
                return tuple(path)

            for dx, dy, step_length in cls._NEIGHBOURS:
                neighbour = SquareGridCoord(current.x + dx, current.y + dy)
                if not traversable(neighbour):
                    continue
                if dx and dy:
                    side_x = SquareGridCoord(current.x + dx, current.y)
                    side_y = SquareGridCoord(current.x, current.y + dy)
                    if not traversable(side_x) or not traversable(side_y):
                        continue

                edge_key = (current, neighbour)
                if edge_validator is not None:
                    valid_edge = edge_cache.get(edge_key)
                    if valid_edge is None:
                        source_world = square_grid_to_world_point(
                            current, cell_size, origin=coverage.grid_origin
                        )
                        target_world = square_grid_to_world_point(
                            neighbour, cell_size, origin=coverage.grid_origin
                        )
                        valid_edge = bool(edge_validator(source_world, target_world))
                        edge_cache[edge_key] = valid_edge
                    if not valid_edge:
                        continue

                multiplier = (
                    terrain_multiplier[current] + terrain_multiplier[neighbour]
                ) / 2.0
                new_cost = current_cost + step_length * multiplier
                if new_cost >= cost_so_far.get(neighbour, math.inf):
                    continue
                cost_so_far[neighbour] = new_cost
                came_from[neighbour] = current
                estimate = heuristic(neighbour)
                heapq.heappush(
                    frontier,
                    (
                        new_cost + estimate,
                        estimate,
                        neighbour.y,
                        neighbour.x,
                        new_cost,
                    ),
                )
        return None


__all__ = [
    "SquareGridNavigationProfile",
    "SquareGridPathfinder",
    "make_physics_edge_validator",
]
