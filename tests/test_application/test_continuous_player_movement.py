"""Native continuous player movement application orchestration tests."""

import pytest

from application.actor_system import WorldActor, WorldActorRegistry
from application.continuous_player_movement import ContinuousPlayerMovementController
from application.hex_actor_binding import ActorHexBindingService
from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from core.domain.movement import (
    MovementConfig, MovementIntent, MovementIntegrator, MovementMode,
    MovementState, MovementTarget,
)
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


def make_controller(*, obstacle=None, actor_active=True, occupied=False, movement_config=None):
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
        movement_config or MovementConfig(
            max_speed=60.0, acceleration=100000.0,
            deceleration=100000.0, braking_deceleration=100000.0,
        ),
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
        binding, snapshot, player_body,
        MovementConfig(
            max_speed=300.0, acceleration=100000.0,
            deceleration=100000.0, braking_deceleration=100000.0,
        ),
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


def test_movement_integrator_accelerates_from_rest_with_delta_time_limit():
    config = MovementConfig(max_speed=100.0, acceleration=120.0)
    integrator = MovementIntegrator(config)
    initial = MovementState(WorldPoint(0.0, 0.0))

    result = integrator.step(initial, east_intent(), 0.1)

    assert result.velocity.x == pytest.approx(12.0)
    assert result.velocity.y == pytest.approx(0.0)
    assert result.position.x == pytest.approx(1.2)
    assert result.position.y == pytest.approx(0.0)


def test_movement_integrator_decelerates_instead_of_stopping_instantly():
    config = MovementConfig(max_speed=100.0, deceleration=40.0)
    integrator = MovementIntegrator(config)
    initial = MovementState(
        WorldPoint(0.0, 0.0),
        Vector2(10.0, 0.0),
        MovementMode.NORMAL,
    )

    result = integrator.step(initial, MovementIntent(), 0.1)

    assert result.velocity.x == pytest.approx(6.0)
    assert result.position.x == pytest.approx(0.6)


def test_movement_integrator_respects_mode_speed_limit_after_acceleration():
    config = MovementConfig(
        max_speed=100.0,
        running_speed_multiplier=1.5,
        acceleration=1000.0,
    )
    integrator = MovementIntegrator(config)
    initial = MovementState(WorldPoint(0.0, 0.0))

    result = integrator.step(
        initial,
        MovementIntent(Vector2(1.0, 0.0), MovementMode.RUNNING),
        1.0,
    )

    assert result.velocity.x == pytest.approx(150.0)


def test_movement_integrator_brakes_and_never_proposes_past_target():
    config = MovementConfig(
        max_speed=100.0,
        acceleration=1000.0,
        braking_deceleration=360.0,
    )
    integrator = MovementIntegrator(config)
    initial = MovementState(
        WorldPoint(0.0, 0.0),
        Vector2(100.0, 0.0),
    )
    target = MovementTarget(WorldPoint(5.0, 0.0), arrival_tolerance=0.5)

    result = integrator.step(initial, east_intent(), 0.1, target=target)

    assert result.position.x <= 4.5
    assert result.position.x >= 0.0
    assert result.velocity.x == pytest.approx(45.0)


def test_movement_target_rejects_invalid_arrival_tolerance():
    with pytest.raises(ValueError):
        MovementTarget(WorldPoint(1.0, 1.0), arrival_tolerance=-0.1)
    with pytest.raises(TypeError):
        MovementTarget(WorldPoint(1.0, 1.0), arrival_tolerance=True)


def test_continuous_controller_carries_accepted_velocity_between_steps():
    config = MovementConfig(max_speed=60.0, acceleration=60.0)
    _actors, runtime, controller = make_controller(movement_config=config)

    first = controller.step("hero", east_intent(), 0.1)
    second = controller.step("hero", east_intent(), 0.1)

    assert first.state.velocity.x == pytest.approx(6.0)
    assert second.state.velocity.x == pytest.approx(12.0)
    assert runtime.continuous_position("hero").point.x == pytest.approx(1.8)



def test_controller_reconciles_velocity_to_static_collision_displacement():
    wall = StaticObstacle(
        "vertical-wall", "corridor",
        ConvexPolygonShape((
            WorldPoint(20.0, -100.0), WorldPoint(25.0, -100.0),
            WorldPoint(25.0, 100.0), WorldPoint(20.0, 100.0),
        )),
        WorldPoint(0.0, 0.0),
    )
    config = MovementConfig(
        max_speed=300.0, acceleration=100000.0,
        deceleration=100000.0, braking_deceleration=100000.0,
    )
    _actors, runtime, controller = make_controller(
        obstacle=wall, movement_config=config,
    )
    start = runtime.continuous_position("hero").point
    delta_seconds = 0.15

    result = controller.step(
        "hero", MovementIntent(Vector2(1.0, 0.5)), delta_seconds,
    )

    accepted = runtime.continuous_position("hero").point
    assert result.movement.success
    assert result.collision_resolution is not None
    assert result.state.position == accepted
    assert result.state.velocity.x == pytest.approx(
        (accepted.x - start.x) / delta_seconds,
    )
    assert result.state.velocity.y == pytest.approx(
        (accepted.y - start.y) / delta_seconds,
    )
    assert result.state.velocity.x < 300.0


def test_controller_discards_velocity_when_authoritative_position_changes_externally():
    config = MovementConfig(max_speed=60.0, acceleration=60.0)
    _actors, runtime, controller = make_controller(movement_config=config)

    first = controller.step("hero", east_intent(), 0.1)
    assert first.state.velocity.x == pytest.approx(6.0)

    moved = runtime.set_continuous_position("hero", WorldPoint(10.0, 0.0))
    assert moved.success
    second = controller.step("hero", east_intent(), 0.1)

    assert second.state.position == runtime.continuous_position("hero").point
    assert second.state.velocity.x == pytest.approx(6.0)
    assert second.state.velocity.x != pytest.approx(12.0)


def test_failed_player_commit_does_not_accept_proposed_velocity():
    runtime, controller = make_dynamic_controller(blocking_crate=True)

    result = controller.step(
        "hero", MovementIntent(Vector2(1.0, 0.0)), 0.15,
    )

    assert not result.movement.success
    assert result.state.position == WorldPoint(0.0, 0.0)
    assert result.state.velocity == Vector2(0.0, 0.0)
    assert controller.last_state == result.state
    assert runtime.continuous_position("hero").point == result.state.position
