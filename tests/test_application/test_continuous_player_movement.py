"""Native continuous player movement application orchestration tests."""

import pytest

from application.actor_system import WorldActor, WorldActorRegistry
from application.continuous_player_movement import ContinuousPlayerMovementController
from application.hex_actor_binding import ActorHexBindingService
from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from core.domain.movement import MovementConfig, MovementIntent
from core.domain.physics import (
    BoundaryPolicy, CircleShape, ConvexPolygonShape, PhysicsBodyDefinition,
    StaticObstacle, Vector2,
)
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementFailureReason, WorldPoint
from core.foundation import WorldId


def make_map():
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "corridor",
        "name": "Movement Test Corridor",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [2, 0], [0, 1], [1, 1]],
        "cell_overrides": [],
    })


def make_controller(*, obstacle=None, actor_active=True, occupied=False):
    map_definition = make_map()
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player", active=actor_active))
    runtime = HexWorldRuntime(
        {"corridor": map_definition},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("corridor", LocalHexPosition(0, 0)),
    )
    if occupied:
        runtime.register_entity(
            "guard",
            "npc",
            EntityPosition("corridor", LocalHexPosition(1, 0)),
        )
    obstacles = () if obstacle is None else (obstacle,)
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        32.0,
        boundary_policy=BoundaryPolicy.OPEN,
        object_obstacles=obstacles,
    )
    body = PhysicsBodyDefinition(
        "player-body",
        CircleShape(8.0, WorldPoint(0.0, 0.0)),
    )
    controller = ContinuousPlayerMovementController(
        binding,
        snapshot,
        body,
        MovementConfig(max_speed=60.0),
    )
    return actors, runtime, controller


def east_intent():
    return MovementIntent(Vector2(1.0, 0.0))


def test_continuous_step_updates_authoritative_position_without_replacing_actor_identity():
    actors, runtime, controller = make_controller()

    result = controller.step("hero", east_intent(), 1.0 / 60.0)

    assert result.movement.success
    assert result.state.position == WorldPoint(1.0, 0.0)
    assert runtime.continuous_position("hero").point == WorldPoint(1.0, 0.0)
    assert runtime.entity("hero").position.cell == LocalHexPosition(0, 0)
    assert runtime.occupancy.get("hero").position.cell == LocalHexPosition(0, 0)
    assert actors.get("hero").actor_id == "hero"


def test_crossing_hex_boundary_updates_continuous_position_and_derived_occupancy():
    _actors, runtime, controller = make_controller()

    for _ in range(30):
        result = controller.step("hero", east_intent(), 1.0 / 60.0)
        assert result.movement.success

    entity = runtime.entity("hero")
    assert entity.continuous_position.point.x == pytest.approx(30.0)
    assert entity.position.cell == LocalHexPosition(1, 0)
    assert runtime.occupancy.get("hero").position.cell == entity.position.cell


def test_static_collision_resolution_prevents_continuous_player_from_crossing_obstacle():
    obstacle = StaticObstacle(
        "rock",
        "corridor",
        CircleShape(4.0, WorldPoint(0.0, 0.0)),
        WorldPoint(20.0, 0.0),
    )
    _actors, runtime, controller = make_controller(obstacle=obstacle)

    for _ in range(30):
        result = controller.step("hero", east_intent(), 1.0 / 60.0)

    point = runtime.continuous_position("hero").point
    assert result.collision_resolution is not None
    assert result.collision_resolution.impacts
    assert 7.9 < point.x < 8.1


def test_occupied_destination_does_not_commit_continuous_position_or_occupancy():
    _actors, runtime, controller = make_controller(occupied=True)

    for _ in range(30):
        result = controller.step("hero", east_intent(), 1.0 / 60.0)

    entity = runtime.entity("hero")
    assert not result.movement.success
    assert result.movement.reason is MovementFailureReason.OCCUPIED_CELL
    assert result.dynamic_pushes == ()
    assert entity.position.cell == LocalHexPosition(0, 0)
    assert runtime.occupancy.get("hero").position.cell == LocalHexPosition(0, 0)
    assert runtime.continuous_position("hero").point.x < 28.0


def test_inactive_actor_does_not_move():
    _actors, runtime, controller = make_controller(actor_active=False)

    result = controller.step("hero", east_intent(), 1.0 / 60.0)

    assert not result.movement.success
    assert result.movement.reason is MovementFailureReason.MOVEMENT_NOT_ALLOWED
    assert runtime.continuous_position("hero").point == WorldPoint(0.0, 0.0)


def test_idle_intent_does_not_mutate_runtime_position():
    _actors, runtime, controller = make_controller()

    result = controller.step(
        "hero",
        MovementIntent(),
        1.0 / 60.0,
    )

    assert result.movement.success
    assert runtime.continuous_position("hero").point == WorldPoint(0.0, 0.0)


def test_controller_rejects_snapshot_from_another_map():
    map_definition = make_map()
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime({"corridor": map_definition}, world_id=WorldId("eldoria"))
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial("hero", "player", EntityPosition("corridor", LocalHexPosition(0, 0)))
    foreign_map = parse_hex_map({
        "schema_version": 2,
        "map_id": "other-map",
        "name": "Other Map",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0]],
        "cell_overrides": [],
    })
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        foreign_map,
        32.0,
        boundary_policy=BoundaryPolicy.OPEN,
    )
    body = PhysicsBodyDefinition("player-body", CircleShape(8.0))
    controller = ContinuousPlayerMovementController(
        binding,
        snapshot,
        body,
        MovementConfig(max_speed=60.0),
    )
    with pytest.raises(ValueError, match="different map"):
        controller.step("hero", east_intent(), 1.0 / 60.0)


def make_dynamic_controller(*, blocking_crate=False):
    map_definition = make_map()
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    actors.add(WorldActor("guard", "eldoria", "npc"))
    runtime = HexWorldRuntime(
        {"corridor": map_definition}, world_id=WorldId("eldoria"),
    )
    runtime.register_entity(
        "hero", "player", EntityPosition("corridor", LocalHexPosition(0, 0)),
        blocks_movement=False, blocks_occupancy=False,
        local_spatial_bounds=AABB(-8, -8, 8, 8),
    )
    runtime.register_entity(
        "guard", "npc", EntityPosition("corridor", LocalHexPosition(1, 0)),
        blocks_movement=False, blocks_occupancy=False,
        local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    if blocking_crate:
        runtime.register_entity(
            "crate", "object", EntityPosition("corridor", LocalHexPosition(1, 0)),
            blocks_movement=True, blocks_occupancy=True,
        )
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"), map_definition, 32.0,
    )
    player_body = PhysicsBodyDefinition("hero", CircleShape(8.0))
    npc_body = PhysicsBodyDefinition("guard", CircleShape(4.0))
    binding = ActorHexBindingService(
        actors, runtime, WorldId("eldoria"),
        physics_snapshot=snapshot, player_body=player_body,
    )
    controller = ContinuousPlayerMovementController(
        binding, snapshot, player_body, MovementConfig(max_speed=300.0),
        npc_bodies={"guard": npc_body},
    )
    return runtime, controller


def test_continuous_controller_pushes_npc_and_keeps_occupancy_in_sync():
    runtime, controller = make_dynamic_controller()

    result = controller.step(
        "hero", MovementIntent(Vector2(1.0, 0.0)), 0.15,
    )

    assert result.movement.success
    assert runtime.continuous_position("hero").point.x == pytest.approx(45.0)
    assert runtime.continuous_position("guard").point.x > 55.0
    for entity_id in ("hero", "guard"):
        assert runtime.occupancy.get(entity_id).position == runtime.entity(entity_id).position


def test_failed_player_commit_rolls_back_provisional_npc_push():
    runtime, controller = make_dynamic_controller(blocking_crate=True)
    npc_start = runtime.continuous_position("guard").point

    result = controller.step(
        "hero", MovementIntent(Vector2(1.0, 0.0)), 0.15,
    )

    assert not result.movement.success
    assert result.movement.reason is MovementFailureReason.OCCUPIED_CELL
    assert runtime.continuous_position("hero").point == WorldPoint(0.0, 0.0)
    assert runtime.continuous_position("guard").point == npc_start
    for entity_id in ("hero", "guard"):
        assert runtime.occupancy.get(entity_id).position == runtime.entity(entity_id).position


def test_continuous_controller_slides_along_static_wall_instead_of_stopping():
    wall = StaticObstacle(
        "vertical-wall", "corridor",
        ConvexPolygonShape((
            WorldPoint(20.0, -100.0), WorldPoint(25.0, -100.0),
            WorldPoint(25.0, 100.0), WorldPoint(20.0, 100.0),
        )),
        WorldPoint(0.0, 0.0),
    )
    _actors, runtime, controller = make_controller(obstacle=wall)
    intent = MovementIntent(Vector2(1.0, 0.5))

    for _ in range(30):
        result = controller.step("hero", intent, 1.0 / 60.0)

    point = runtime.continuous_position("hero").point
    assert result.collision_resolution is not None
    assert point.x < 12.1
    assert point.y > 5.0
    assert runtime.occupancy.get("hero").position == runtime.entity("hero").position
