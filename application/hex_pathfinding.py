"""Deterministic A* pathfinding on masked axial hex maps."""
from __future__ import annotations

import heapq

from application.hex_map_definition import HexMapDefinition
from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile, MovementRequest
from .hex_movement_rules import MovementRules


class HexPathfinder:
    """Find shortest unweighted local-map paths using axial hex distance."""

    @staticmethod
    def find_path(
        map_definition: HexMapDefinition,
        start: LocalHexPosition,
        goal: LocalHexPosition,
        profile: MovementProfile | None = None,
        blocked_cells=(),
    ) -> tuple[LocalHexPosition, ...] | None:
        if not isinstance(map_definition, HexMapDefinition):
            raise TypeError("map_definition must be a HexMapDefinition.")
        if not isinstance(start, LocalHexPosition) or not isinstance(goal, LocalHexPosition):
            raise TypeError("start and goal must be LocalHexPosition values.")
        if profile is None:
            profile = MovementProfile()
        if not isinstance(profile, MovementProfile):
            raise TypeError("profile must be a MovementProfile.")
        blocked = frozenset() if profile.ignores_occupancy else frozenset(blocked_cells)
        if any(not isinstance(cell, LocalHexPosition) for cell in blocked):
            raise TypeError("blocked_cells must contain LocalHexPosition values.")
        if not map_definition.has_cell(start) or not map_definition.has_cell(goal):
            return None
        if not profile.can_move:
            return None
        if start == goal:
            return (start,)
        if goal in blocked:
            return None

        start_coord = start.to_hex_coord()
        goal_coord = goal.to_hex_coord()
        frontier = [(start_coord.distance_to(goal_coord), 0, start.q, start.r)]
        came_from = {}
        cost_so_far = {start: 0}

        while frontier:
            _, current_cost, q, r = heapq.heappop(frontier)
            current = LocalHexPosition(q, r)
            if current_cost != cost_so_far.get(current):
                continue
            if current == goal:
                path = [goal]
                while path[-1] != start:
                    path.append(came_from[path[-1]])
                path.reverse()
                return tuple(path)

            for neighbor_coord in current.to_hex_coord().neighbors():
                neighbor = LocalHexPosition.from_hex_coord(neighbor_coord)
                if neighbor in blocked and neighbor != goal:
                    continue
                if neighbor != goal and map_definition.is_blocked(neighbor) and not profile.can_traverse_blocked_cells:
                    continue
                request = MovementRequest(
                    "pathfinder",
                    EntityPosition(map_definition.map_id, current),
                    EntityPosition(map_definition.map_id, neighbor),
                    profile,
                )
                result = MovementRules.evaluate(request, map_definition)
                if not result.success:
                    continue
                new_cost = current_cost + 1
                if new_cost >= cost_so_far.get(neighbor, float("inf")):
                    continue
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                heuristic = neighbor_coord.distance_to(goal_coord)
                heapq.heappush(
                    frontier,
                    (new_cost + heuristic, new_cost, neighbor.q, neighbor.r),
                )
        return None


__all__ = ["HexPathfinder"]
