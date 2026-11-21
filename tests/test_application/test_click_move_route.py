from types import SimpleNamespace

from core.domain.movement import MovementMode
from core.domain.physics import Vector2
from core.domain.spatial import (
    EntityPosition,
    LocalHexPosition,
    MovementProfile,
    WorldPoint,
)
from application.click_move_route import ClickMoveRouteController


A = LocalHexPosition(0, 0)
B = LocalHexPosition(1, 0)
C = LocalHexPosition(2, 0)
D = LocalHexPosition(1, -1)
BODY = object()


class FakeSnapshot:
    map_id = "village"

    def __init__(self, blocked_edges=(), *, blocked_sweep=False):
        self.blocked_edges = set(blocked_edges)
        self.blocked_sweep = blocked_sweep
        self.sweep_calls = 0
        self.edge_checks = 0

    def cell_center(self, cell):
        return WorldPoint(cell.q * 10.0, cell.r * 10.0)

    def can_reach_cell(self, source, destination, _body):
        self.edge_checks += 1
        return (source, destination) not in self.blocked_edges

    def resolve_motion(self, _start, displacement, _body):
        self.sweep_calls += 1
        applied = Vector2(0.0, 0.0) if self.blocked_sweep else displacement
        impacts = (object(),) if self.blocked_sweep else ()
        return SimpleNamespace(
            applied_displacement=applied,
            impacts=impacts,
            unresolved_penetration=0.0,
        )


class FakeOccupancy:
    def __init__(self):
        self.blocked_cells = set()

    def can_enter(self, position, *, excluding=None):
        return position.cell not in self.blocked_cells


class FakeRuntime:
    def __init__(self, paths=(), *, cell=A, point=None):
        self.paths = list(paths)
        self.current_cell = cell
        self.current_point = point or WorldPoint(cell.q * 10.0, cell.r * 10.0)
        self.profile = MovementProfile()
        self.occupancy = FakeOccupancy()
        self.path_queries = 0

    def entity(self, actor_id):
        return SimpleNamespace(
            entity_id=actor_id,
            position=EntityPosition("village", self.current_cell),
            profile=self.profile,
            continuous_position=SimpleNamespace(point=self.current_point),
        )

    def map_definition(self, _map_id):
        return SimpleNamespace(has_cell=lambda _cell: True)

    def path_to(self, _actor_id, goal, *, edge_validator=None):
        self.path_queries += 1
        while self.paths:
            path = self.paths.pop(0)
            if path is None:
                return None
            if edge_validator is None or all(
                edge_validator(source, destination)
                for source, destination in zip(path, path[1:])
            ):
                return path
        path = (self.current_cell, goal)
        if edge_validator is not None and not all(
            edge_validator(source, destination)
            for source, destination in zip(path, path[1:])
        ):
            return None
        return path


def make_controller(*, timing_enabled=False):
    return ClickMoveRouteController(timing_enabled=timing_enabled)


def route_intent(controller, runtime, goal=C, snapshot=None, mode=MovementMode.NORMAL):
    return controller.intent(
        runtime,
        "hero",
        goal,
        snapshot or FakeSnapshot(),
        BODY,
        mode=mode,
    )


def test_same_active_goal_reuses_one_path_across_fixed_steps():
    runtime = FakeRuntime(paths=[(A, B, C)])
    controller = make_controller()
    snapshot = FakeSnapshot()

    first = route_intent(controller, runtime, snapshot=snapshot)
    second = route_intent(controller, runtime, snapshot=snapshot)

    assert first.is_moving
    assert second.is_moving
    assert runtime.path_queries == 1
    metrics = controller.metrics_snapshot()
    assert metrics["player_click_path_queries"] == 1
    assert metrics["player_click_route_cache_misses"] == 1
    assert metrics["player_click_route_cache_hits"] == 1
    assert snapshot.sweep_calls == 1
    assert snapshot.edge_checks == 2


def test_new_goal_replaces_active_route_and_replans():
    runtime = FakeRuntime(paths=[(A, B), (A, B, C)])
    controller = make_controller()
    snapshot = FakeSnapshot()

    route_intent(controller, runtime, goal=B, snapshot=snapshot)
    intent = route_intent(controller, runtime, goal=C, snapshot=snapshot)

    assert intent.is_moving
    assert runtime.path_queries == 2
    metrics = controller.metrics_snapshot()
    assert metrics["player_click_route_invalidations"] == 1
    assert metrics["player_click_route_replans"] == 1


def test_runtime_replacement_invalidates_route_and_replans():
    first_runtime = FakeRuntime(paths=[(A, B, C)])
    second_runtime = FakeRuntime(paths=[(A, D, C)])
    controller = make_controller()
    snapshot = FakeSnapshot()

    route_intent(controller, first_runtime, snapshot=snapshot)
    intent = route_intent(controller, second_runtime, snapshot=snapshot)

    assert intent.is_moving
    assert first_runtime.path_queries == 1
    assert second_runtime.path_queries == 1
    assert controller.metrics_snapshot()["player_click_route_replans"] == 1


def test_blocked_next_occupancy_edge_replans_once_to_alternative_route():
    runtime = FakeRuntime(paths=[(A, B, C), (A, D, C)])
    runtime.occupancy.blocked_cells.add(B)
    controller = make_controller()

    intent = route_intent(controller, runtime)

    assert intent.is_moving
    assert runtime.path_queries == 2
    metrics = controller.metrics_snapshot()
    assert metrics["player_click_route_blocked_steps"] == 1
    assert metrics["player_click_route_replans"] == 1
    assert metrics["player_click_route_failures"] == 0


def test_blocked_edge_with_failed_replan_stops_without_replan_loop():
    runtime = FakeRuntime(paths=[(A, B, C), None])
    runtime.occupancy.blocked_cells.add(B)
    controller = make_controller()

    intent = route_intent(controller, runtime)

    assert not intent.is_moving
    assert not controller.active
    assert runtime.path_queries == 2
    metrics = controller.metrics_snapshot()
    assert metrics["player_click_route_replans"] == 1
    assert metrics["player_click_route_failures"] == 1
    assert controller.status == "blocked"


def test_authoritative_player_deviation_replans_from_current_runtime_cell():
    runtime = FakeRuntime(paths=[(A, B, C), (D, C)])
    controller = make_controller()
    snapshot = FakeSnapshot()

    route_intent(controller, runtime, snapshot=snapshot)
    runtime.current_cell = D
    runtime.current_point = snapshot.cell_center(D)
    intent = route_intent(controller, runtime, snapshot=snapshot)

    assert intent.is_moving
    assert runtime.path_queries == 2
    assert controller.metrics_snapshot()["player_click_route_replans"] == 1


def test_pathfinder_edge_validator_rejects_static_collision_route():
    runtime = FakeRuntime(paths=[(A, B, C), (A, D, C)])
    snapshot = FakeSnapshot(blocked_edges={(A, B)})
    controller = make_controller()

    intent = route_intent(controller, runtime, snapshot=snapshot)

    assert intent.is_moving
    assert runtime.path_queries == 1
    assert controller.metrics_snapshot()["player_click_route_blocked_steps"] == 0
    assert controller.metrics_snapshot()["player_click_route_replans"] == 0


def test_arrival_uses_authoritative_goal_cell_and_center_tolerance():
    snapshot = FakeSnapshot()
    runtime = FakeRuntime(cell=C, point=snapshot.cell_center(C))
    controller = make_controller()

    intent = route_intent(controller, runtime, goal=C, snapshot=snapshot)

    assert not intent.is_moving
    assert not controller.active
    assert controller.status == "arrived"
    assert runtime.path_queries == 0
    assert controller.metrics_snapshot()["player_click_route_arrivals"] == 1
    assert controller.movement_target.position == snapshot.cell_center(C)
    assert controller.consume_movement_target().position == snapshot.cell_center(C)
    assert controller.movement_target is None


def test_running_or_stealth_mode_is_preserved_in_route_intent():
    runtime = FakeRuntime(paths=[(A, B, C)])
    controller = make_controller()

    intent = route_intent(
        controller, runtime, mode=MovementMode.RUNNING,
    )

    assert intent.mode is MovementMode.RUNNING


def test_changed_physics_snapshot_invalidates_and_replans():
    runtime = FakeRuntime(paths=[(A, B, C), (A, D, C)])
    controller = make_controller()
    first_snapshot = FakeSnapshot()
    second_snapshot = FakeSnapshot()

    route_intent(controller, runtime, snapshot=first_snapshot)
    intent = route_intent(controller, runtime, snapshot=second_snapshot)

    assert intent.is_moving
    assert runtime.path_queries == 2
    assert controller.metrics_snapshot()["player_click_route_replans"] == 1
    assert first_snapshot.edge_checks == 2
    assert second_snapshot.edge_checks == 2


def test_optional_path_and_arrival_percentiles_are_collected():
    snapshot = FakeSnapshot()
    runtime = FakeRuntime(paths=[(A, B, C)])
    controller = make_controller(timing_enabled=True)

    route_intent(controller, runtime, snapshot=snapshot)
    runtime.current_cell = C
    runtime.current_point = snapshot.cell_center(C)
    route_intent(controller, runtime, snapshot=snapshot)

    metrics = controller.metrics_snapshot()
    assert metrics["player_click_path_planning_p50_ms"] is not None
    assert metrics["player_click_route_arrival_p50_ms"] is not None


def test_route_deviation_and_blocked_edge_allow_only_one_replan_per_step():
    runtime = FakeRuntime(paths=[(A, B, C), (D, B, C)])
    controller = make_controller()
    snapshot = FakeSnapshot()
    route_intent(controller, runtime, snapshot=snapshot)

    runtime.current_cell = D
    runtime.current_point = snapshot.cell_center(D)
    runtime.occupancy.blocked_cells.add(B)
    intent = route_intent(controller, runtime, snapshot=snapshot)

    assert not intent.is_moving
    assert runtime.path_queries == 2
    assert controller.metrics_snapshot()["player_click_route_replans"] == 1
    assert controller.status == "blocked"


def test_collinear_waypoint_is_merged_after_clear_swept_collision_check():
    runtime = FakeRuntime(paths=[(A, B, C)])
    controller = make_controller()

    intent = route_intent(controller, runtime)

    assert intent.is_moving
    assert intent.direction.x == 20.0
    assert intent.direction.y == 0.0


def test_smoothing_falls_back_to_next_waypoint_when_sweep_hits_collision():
    runtime = FakeRuntime(paths=[(A, B, C)])
    snapshot = FakeSnapshot(blocked_sweep=True)
    controller = make_controller()

    intent = route_intent(controller, runtime, snapshot=snapshot)

    assert intent.is_moving
    assert intent.direction.x == 10.0
    assert intent.direction.y == 0.0


def test_smoothing_never_merges_a_turning_waypoint():
    runtime = FakeRuntime(paths=[(A, B, D)])
    controller = make_controller()

    intent = route_intent(controller, runtime, goal=D)

    assert intent.is_moving
    assert intent.direction.x == 10.0
    assert intent.direction.y == 0.0


def test_smoothing_checks_dynamic_occupancy_of_second_edge():
    runtime = FakeRuntime(paths=[(A, B, C)])
    runtime.occupancy.blocked_cells.add(C)
    controller = make_controller()

    intent = route_intent(controller, runtime)

    assert intent.is_moving
    assert intent.direction.x == 10.0
    assert runtime.path_queries == 1


def test_route_exposes_smoothed_waypoint_as_explicit_movement_target():
    runtime = FakeRuntime(paths=[(A, B, C)])
    controller = make_controller()

    intent = route_intent(controller, runtime)

    assert intent.is_moving
    assert controller.movement_target.position == WorldPoint(20.0, 0.0)
    assert controller.movement_target.arrival_tolerance == 0.5


def test_route_uses_turning_waypoint_as_braking_target():
    runtime = FakeRuntime(paths=[(A, B, D)])
    controller = make_controller()

    intent = route_intent(controller, runtime, goal=D)

    assert intent.is_moving
    assert controller.movement_target.position == WorldPoint(10.0, 0.0)


def test_route_does_not_turn_at_hex_boundary_before_waypoint_arrival():
    runtime = FakeRuntime(paths=[(A, B, D)])
    controller = make_controller()
    snapshot = FakeSnapshot()

    first = route_intent(controller, runtime, goal=D, snapshot=snapshot)
    runtime.current_cell = B
    runtime.current_point = WorldPoint(8.0, 0.0)
    second = route_intent(controller, runtime, goal=D, snapshot=snapshot)

    assert first.is_moving
    assert second.is_moving
    assert second.direction.x == 2.0
    assert second.direction.y == 0.0
    assert controller.movement_target.position == WorldPoint(10.0, 0.0)
