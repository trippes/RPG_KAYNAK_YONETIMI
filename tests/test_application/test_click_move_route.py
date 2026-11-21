from types import SimpleNamespace

from core.domain.movement import MovementMode
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


class FakeSnapshot:
    map_id = "village"

    def __init__(self, blocked_edges=()):
        self.blocked_edges = set(blocked_edges)

    def cell_center(self, cell):
        return WorldPoint(cell.q * 10.0, cell.r * 10.0)

    def can_reach_cell(self, source, destination, _body):
        return (source, destination) not in self.blocked_edges


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
        if self.paths:
            return self.paths.pop(0)
        return (self.current_cell, goal)


def make_controller(*, timing_enabled=False):
    return ClickMoveRouteController(timing_enabled=timing_enabled)


def route_intent(controller, runtime, goal=C, snapshot=None, mode=MovementMode.NORMAL):
    return controller.intent(
        runtime,
        "hero",
        goal,
        snapshot or FakeSnapshot(),
        object(),
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


def test_static_collision_on_next_edge_triggers_alternative_route():
    runtime = FakeRuntime(paths=[(A, B, C), (A, D, C)])
    snapshot = FakeSnapshot(blocked_edges={(A, B)})
    controller = make_controller()

    intent = route_intent(controller, runtime, snapshot=snapshot)

    assert intent.is_moving
    assert runtime.path_queries == 2
    assert controller.metrics_snapshot()["player_click_route_blocked_steps"] == 1


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

    route_intent(controller, runtime, snapshot=FakeSnapshot())
    intent = route_intent(controller, runtime, snapshot=FakeSnapshot())

    assert intent.is_moving
    assert runtime.path_queries == 2
    assert controller.metrics_snapshot()["player_click_route_replans"] == 1


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
