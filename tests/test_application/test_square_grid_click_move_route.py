from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from application.square_grid_cache import SquareGridChunkCache
from application.square_grid_click_move_route import SquareGridClickMoveRouteController
from core.domain.movement import MovementMode
from core.domain.physics import CircleShape, PhysicsBodyDefinition
from core.domain.spatial import EntityPosition, LocalHexPosition, WorldPoint, axial_to_world_point
from core.foundation import WorldId


def _world():
    valid_cells = [
        [q, r]
        for q in range(-3, 4)
        for r in range(-3, 4)
    ]
    definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "square-route-map",
        "name": "Square route map",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": valid_cells,
    })
    runtime = HexWorldRuntime({definition.map_id: definition})
    runtime.register_entity(
        "hero", "player",
        EntityPosition(definition.map_id, LocalHexPosition(0, 0)),
    )
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"), definition, 32.0,
    )
    body = PhysicsBodyDefinition(
        "player-body", CircleShape(8.0, WorldPoint(0.0, 0.0)),
    )
    controller = SquareGridClickMoveRouteController(
        SquareGridChunkCache(), cell_size=16.0,
    )
    return runtime, snapshot, body, controller


def test_click_route_uses_exact_continuous_goal_without_snapping_actor():
    runtime, snapshot, body, controller = _world()
    goal = WorldPoint(2.0, 1.0)

    intent = controller.intent(runtime, "hero", goal, snapshot, body)

    assert intent.is_moving
    assert controller.movement_target.position == goal
    assert runtime.continuous_position("hero").point == WorldPoint(0.0, 0.0)
    assert controller.status == "following"


def test_square_grid_click_route_produces_world_waypoint_and_keeps_runtime_authoritative():
    runtime, snapshot, body, controller = _world()
    goal = axial_to_world_point(
        LocalHexPosition(1, 0).to_hex_coord(), snapshot.hex_size,
    )

    intent = controller.intent(
        runtime, "hero", goal, snapshot, body, mode=MovementMode.RUNNING,
    )

    assert intent.is_moving
    assert intent.mode is MovementMode.RUNNING
    assert controller.movement_target is not None
    assert isinstance(controller.movement_target.position, WorldPoint)
    assert runtime.continuous_position("hero").point == WorldPoint(0.0, 0.0)
    assert controller.metrics_snapshot()["player_square_grid_path_queries"] == 1


def test_click_route_rejects_goal_outside_canonical_hex_map_mask():
    runtime, snapshot, body, controller = _world()

    intent = controller.intent(
        runtime, "hero", WorldPoint(10000.0, 10000.0), snapshot, body,
    )

    assert not intent.is_moving
    assert not controller.active
    assert controller.status == "target_outside_map"
