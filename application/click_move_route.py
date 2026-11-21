"""Single-player click-to-move route lifecycle and next-edge validation."""

from __future__ import annotations

import math
from dataclasses import dataclass
from time import perf_counter_ns

from core.domain.movement import MovementIntent, MovementMode
from core.domain.physics import Vector2
from core.domain.spatial import EntityPosition, LocalHexPosition


@dataclass(slots=True)
class _ActiveRoute:
    runtime: object
    actor_id: str
    map_id: str
    goal: LocalHexPosition
    physics_snapshot: object
    body: object
    cells: tuple[LocalHexPosition, ...]
    cursor: int = 0


class ClickMoveRouteController:
    """Own exactly one player's active click-to-move route.

    The controller stores immutable path cells and a cursor, never mutable
    entity views. HexWorldRuntime remains authoritative for actor position
    and occupancy. Every fixed step validates the next edge before using it.
    """

    ARRIVAL_TOLERANCE = 0.5

    __slots__ = (
        "_active",
        "_last_status",
        "_last_replan_reason",
        "_timing_enabled",
        "_path_durations_ms",
        "_arrival_durations_ms",
        "_command_started_ns",
        "_metrics",
    )

    def __init__(self, *, timing_enabled: bool = False) -> None:
        if not isinstance(timing_enabled, bool):
            raise TypeError("timing_enabled must be a bool.")
        self._active: _ActiveRoute | None = None
        self._last_status = "idle"
        self._last_replan_reason = None
        self._timing_enabled = timing_enabled
        self._path_durations_ms: list[float] = []
        self._arrival_durations_ms: list[float] = []
        self._command_started_ns = None
        self._metrics = {
            "player_click_path_queries": 0,
            "player_click_route_cache_hits": 0,
            "player_click_route_cache_misses": 0,
            "player_click_route_replans": 0,
            "player_click_route_invalidations": 0,
            "player_click_route_blocked_steps": 0,
            "player_click_route_waypoints_total": 0,
            "player_click_route_arrivals": 0,
            "player_click_route_failures": 0,
        }

    @property
    def active(self) -> bool:
        return self._active is not None

    @property
    def status(self) -> str:
        return self._last_status

    @property
    def last_replan_reason(self):
        return self._last_replan_reason

    def cancel(self, reason: str = "cancelled") -> None:
        """Discard the active command without changing runtime/world state."""
        if self._active is not None:
            self._metrics["player_click_route_invalidations"] += 1
        self._active = None
        self._last_status = "cancelled"
        self._last_replan_reason = reason
        self._command_started_ns = None

    def intent(
        self,
        runtime,
        actor_id: str,
        goal: LocalHexPosition,
        physics_snapshot,
        body,
        *,
        mode: MovementMode = MovementMode.NORMAL,
    ) -> MovementIntent:
        """Return this fixed step's waypoint direction or an idle intent."""
        if runtime is None:
            self.cancel("runtime_unavailable")
            return MovementIntent()
        if not isinstance(goal, LocalHexPosition):
            raise TypeError("goal must be a LocalHexPosition.")
        if not isinstance(mode, MovementMode):
            raise TypeError("mode must be a MovementMode.")
        if physics_snapshot is None or body is None:
            self.cancel("physics_unavailable")
            return MovementIntent()

        try:
            entity = runtime.entity(actor_id)
        except (KeyError, RuntimeError, ValueError):
            self.cancel("actor_unavailable")
            self._last_status = "failed"
            self._metrics["player_click_route_failures"] += 1
            return MovementIntent()

        map_id = entity.position.map_id
        if physics_snapshot.map_id != map_id:
            self.cancel("physics_map_mismatch")
            self._last_status = "failed"
            self._metrics["player_click_route_failures"] += 1
            return MovementIntent()

        current_cell = entity.position.cell
        continuous = getattr(entity, "continuous_position", None)
        if continuous is None:
            try:
                continuous = runtime.continuous_position(actor_id)
            except (KeyError, RuntimeError, ValueError):
                self.cancel("actor_unavailable")
                self._last_status = "failed"
                self._metrics["player_click_route_failures"] += 1
                return MovementIntent()
        current_point = continuous.point

        state = self._active
        replan_reason = self._context_change_reason(
            state, runtime, actor_id, map_id, goal, physics_snapshot, body,
        )
        if state is None:
            if not self._plan(
                runtime, actor_id, map_id, current_cell, goal,
                physics_snapshot, body, replan=False,
            ):
                return MovementIntent()
            state = self._active
        elif replan_reason is not None:
            self._invalidate(replan_reason)
            if not self._plan(
                runtime, actor_id, map_id, current_cell, goal,
                physics_snapshot, body, replan=True,
            ):
                return MovementIntent()
            state = self._active
        else:
            state = self._active

        if state is None:
            return MovementIntent()

        cursor = self._find_cursor(state.cells, state.cursor, current_cell)
        if cursor is None:
            self._invalidate("route_deviation")
            if not self._plan(
                runtime, actor_id, map_id, current_cell, goal,
                physics_snapshot, body, replan=True,
            ):
                return MovementIntent()
            state = self._active
            if state is None:
                return MovementIntent()
            cursor = 0
        state.cursor = cursor

        if current_cell == goal:
            target = physics_snapshot.cell_center(goal)
            dx = target.x - current_point.x
            dy = target.y - current_point.y
            if math.hypot(dx, dy) <= self.ARRIVAL_TOLERANCE:
                self._arrive()
                return MovementIntent()
            self._metrics["player_click_route_cache_hits"] += 1
            return MovementIntent(Vector2(dx, dy), mode)

        if cursor + 1 >= len(state.cells):
            self._invalidate("route_cursor_exhausted")
            if not self._plan(
                runtime, actor_id, map_id, current_cell, goal,
                physics_snapshot, body, replan=True,
            ):
                return MovementIntent()
            state = self._active
            if state is None or len(state.cells) < 2:
                self._fail("route_cursor_exhausted")
                return MovementIntent()
            cursor = 0
            state.cursor = cursor

        next_cell = state.cells[cursor + 1]
        if not self._next_edge_valid(
            runtime, entity, map_id, current_cell, next_cell,
            physics_snapshot, body, actor_id,
        ):
            self._metrics["player_click_route_blocked_steps"] += 1
            self._invalidate("next_edge_blocked")
            if not self._plan(
                runtime, actor_id, map_id, current_cell, goal,
                physics_snapshot, body, replan=True,
            ):
                return MovementIntent()
            state = self._active
            if state is None:
                return MovementIntent()
            cursor = 0
            state.cursor = cursor
            if current_cell == goal:
                target = physics_snapshot.cell_center(goal)
                dx = target.x - current_point.x
                dy = target.y - current_point.y
                if math.hypot(dx, dy) <= self.ARRIVAL_TOLERANCE:
                    self._arrive()
                    return MovementIntent()
                return MovementIntent(Vector2(dx, dy), mode)
            if len(state.cells) < 2 or not self._next_edge_valid(
                runtime, entity, map_id, current_cell, state.cells[1],
                physics_snapshot, body, actor_id,
            ):
                self._fail("replan_failed")
                return MovementIntent()
            next_cell = state.cells[1]
        else:
            self._metrics["player_click_route_cache_hits"] += 1

        target = physics_snapshot.cell_center(next_cell)
        dx = target.x - current_point.x
        dy = target.y - current_point.y
        return MovementIntent(Vector2(dx, dy), mode)

    def metrics_snapshot(self) -> dict:
        """Return deterministic counters and optional timing percentiles."""
        result = dict(self._metrics)
        result.update({
            "player_click_path_planning_p50_ms": self._percentile(self._path_durations_ms, 0.50),
            "player_click_path_planning_p95_ms": self._percentile(self._path_durations_ms, 0.95),
            "player_click_path_planning_p99_ms": self._percentile(self._path_durations_ms, 0.99),
            "player_click_route_arrival_p50_ms": self._percentile(self._arrival_durations_ms, 0.50),
            "player_click_route_arrival_p95_ms": self._percentile(self._arrival_durations_ms, 0.95),
            "player_click_route_arrival_p99_ms": self._percentile(self._arrival_durations_ms, 0.99),
        })
        return result

    @staticmethod
    def _percentile(values: list[float], percentile: float):
        if not values:
            return None
        ordered = sorted(values)
        index = int(round((len(ordered) - 1) * percentile))
        return ordered[index]

    @staticmethod
    def _context_change_reason(
        state, runtime, actor_id, map_id, goal, physics_snapshot, body,
    ):
        if state is None:
            return None
        if state.runtime is not runtime:
            return "runtime_replaced"
        if state.actor_id != actor_id:
            return "actor_changed"
        if state.map_id != map_id:
            return "map_changed"
        if state.goal != goal:
            return "new_goal"
        if state.physics_snapshot is not physics_snapshot:
            return "physics_snapshot_changed"
        if state.body != body:
            return "player_body_changed"
        return None

    @staticmethod
    def _find_cursor(
        cells: tuple[LocalHexPosition, ...],
        cursor: int,
        current_cell: LocalHexPosition,
    ) -> int | None:
        try:
            return cells.index(current_cell, cursor)
        except ValueError:
            return None

    def _plan(
        self,
        runtime,
        actor_id: str,
        map_id: str,
        current_cell: LocalHexPosition,
        goal: LocalHexPosition,
        physics_snapshot,
        body,
        *,
        replan: bool,
    ) -> bool:
        if replan:
            self._metrics["player_click_route_replans"] += 1
        else:
            self._metrics["player_click_route_cache_misses"] += 1

        if current_cell == goal:
            path = (current_cell,)
        else:
            started = perf_counter_ns() if self._timing_enabled else None
            self._metrics["player_click_path_queries"] += 1
            try:
                path = runtime.path_to(
                    actor_id,
                    goal,
                    edge_validator=lambda source, destination: physics_snapshot.can_reach_cell(
                        source, destination, body,
                    ),
                )
            except (KeyError, RuntimeError, ValueError):
                path = None
            if started is not None:
                self._path_durations_ms.append(
                    (perf_counter_ns() - started) / 1_000_000.0,
                )

        if (
            path is None
            or not path
            or path[0] != current_cell
            or path[-1] != goal
        ):
            self._fail("replan_failed" if replan else "no_path")
            return False

        self._active = _ActiveRoute(
            runtime, actor_id, map_id, goal, physics_snapshot, body,
            tuple(path), 0,
        )
        self._last_status = "following"
        if self._command_started_ns is None and self._timing_enabled:
            self._command_started_ns = perf_counter_ns()
        self._metrics["player_click_route_waypoints_total"] += max(0, len(path) - 1)
        return True

    def _next_edge_valid(
        self,
        runtime,
        entity,
        map_id: str,
        source: LocalHexPosition,
        destination: LocalHexPosition,
        physics_snapshot,
        body,
        actor_id: str,
    ) -> bool:
        try:
            if not runtime.map_definition(map_id).has_cell(destination):
                return False
            if not entity.profile.ignores_occupancy:
                occupancy = getattr(runtime, "occupancy", None)
                if occupancy is not None and not occupancy.can_enter(
                    EntityPosition(map_id, destination), excluding=actor_id,
                ):
                    return False
            return physics_snapshot.can_reach_cell(source, destination, body)
        except (KeyError, RuntimeError, ValueError):
            return False

    def _invalidate(self, reason: str) -> None:
        if self._active is not None:
            self._metrics["player_click_route_invalidations"] += 1
        self._active = None
        self._last_replan_reason = reason

    def _arrive(self) -> None:
        self._metrics["player_click_route_arrivals"] += 1
        if self._command_started_ns is not None:
            self._arrival_durations_ms.append(
                (perf_counter_ns() - self._command_started_ns) / 1_000_000.0,
            )
        self._active = None
        self._command_started_ns = None
        self._last_status = "arrived"
        self._last_replan_reason = "arrived"

    def _fail(self, reason: str) -> None:
        self._metrics["player_click_route_failures"] += 1
        self._active = None
        self._command_started_ns = None
        self._last_status = "blocked" if reason in {
            "next_edge_blocked", "replan_failed",
        } else "failed"
        self._last_replan_reason = reason


__all__ = ["ClickMoveRouteController"]
