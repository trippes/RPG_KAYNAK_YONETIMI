from application.dynamic_actor_collision import DynamicActorCollisionResolver
from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from core.domain.physics import (
    CircleShape, ConvexPolygonShape, PhysicsBodyDefinition, StaticObstacle,
)
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementProfile, WorldPoint
from core.foundation import WorldId


def make_runtime():
    definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "field",
        "name": "Field",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [2, 0], [3, 0]],
        "cell_overrides": [],
        "transitions": [],
    })
    runtime = HexWorldRuntime({"field": definition}, world_id=WorldId("world"))
    runtime.register_entity(
        "hero", "player", EntityPosition("field", LocalHexPosition(0, 0)),
        MovementProfile(), blocks_movement=False, blocks_occupancy=False,
        local_spatial_bounds=AABB(-8, -8, 8, 8),
    )
    runtime.register_entity(
        "guard", "npc", EntityPosition("field", LocalHexPosition(1, 0)),
        MovementProfile(), blocks_movement=False, blocks_occupancy=False,
        local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    return runtime, definition


def test_player_contact_pushes_npc_and_updates_canonical_continuous_position():
    runtime, definition = make_runtime()
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    player_body = PhysicsBodyDefinition("hero", CircleShape(8.0))
    npc_body = PhysicsBodyDefinition("guard", CircleShape(4.0))
    start = runtime.continuous_position("hero").point
    proposed = WorldPoint(45.0, 0.0)

    result = DynamicActorCollisionResolver(runtime, snapshot).resolve_player_motion(
        "hero", start, proposed, player_body, {"guard": npc_body},
    )

    npc_position = runtime.continuous_position("guard").point
    assert result.pushes
    assert result.pushes[0].entity_id == "guard"
    assert npc_position.x > 55.0
    assert npc_position.y == 0.0


def test_non_overlapping_npc_is_not_moved():
    runtime, definition = make_runtime()
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    player_body = PhysicsBodyDefinition("hero", CircleShape(8.0))
    npc_body = PhysicsBodyDefinition("guard", CircleShape(4.0))
    before = runtime.continuous_position("guard").point

    result = DynamicActorCollisionResolver(runtime, snapshot).resolve_player_motion(
        "hero", runtime.continuous_position("hero").point,
        WorldPoint(10.0, 0.0), player_body, {"guard": npc_body},
    )

    assert result.pushes == ()
    assert runtime.continuous_position("guard").point == before


def test_disabled_npc_body_is_not_pushed():
    runtime, definition = make_runtime()
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    player_body = PhysicsBodyDefinition("hero", CircleShape(8.0))
    npc_body = PhysicsBodyDefinition("guard", CircleShape(4.0), enabled=False)
    before = runtime.continuous_position("guard").point

    result = DynamicActorCollisionResolver(runtime, snapshot).resolve_player_motion(
        "hero", runtime.continuous_position("hero").point,
        WorldPoint(45.0, 0.0), player_body, {"guard": npc_body},
    )

    assert result.pushes == ()
    assert runtime.continuous_position("guard").point == before



def test_overlapping_npcs_are_separated_by_dynamic_pair_resolution():
    runtime, definition = make_runtime()
    from core.domain.physics import PhysicsBodyDefinition, CircleShape

    body = PhysicsBodyDefinition("guard", CircleShape(4.0))
    runtime.set_continuous_position("guard", WorldPoint(80.0, 0.0))
    runtime.register_entity(
        "guard_two", "npc", EntityPosition("field", LocalHexPosition(2, 0)),
        MovementProfile(), local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    runtime.set_continuous_position("guard_two", WorldPoint(85.0, 0.0))
    second_body = PhysicsBodyDefinition("guard_two", CircleShape(4.0))
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)

    moved = DynamicActorCollisionResolver(runtime, snapshot).resolve_npc_pairs({
        "guard": body,
        "guard_two": second_body,
    })

    first = runtime.continuous_position("guard").point
    second = runtime.continuous_position("guard_two").point
    assert set(moved) == {"guard", "guard_two"}
    assert abs(second.x - first.x) >= 8.0


def test_player_push_commits_player_and_npc_position_occupancy_and_broadphase_together():
    runtime, definition = make_runtime()
    # Moving actors may share a hex cell; their colliders, not cell occupancy,
    # determine physical separation at sub-cell precision.
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    start = runtime.continuous_position("hero").point
    resolution = DynamicActorCollisionResolver(runtime, snapshot).resolve_player_motion(
        "hero", start, WorldPoint(45.0, 0.0),
        PhysicsBodyDefinition("hero", CircleShape(8.0)),
        {"guard": PhysicsBodyDefinition("guard", CircleShape(4.0))},
    )

    committed = runtime.set_continuous_position("hero", resolution.player_position)

    assert committed.success
    for entity_id in ("hero", "guard"):
        entity = runtime.entity(entity_id)
        occupant = runtime.occupancy.get(entity_id)
        assert occupant.position == entity.position
        point = runtime.continuous_position(entity_id).point
        assert entity_id in runtime.query_spatial_candidates(
            "field", AABB.around_point(point, 0.1),
        )
    assert len(runtime.occupancy.at(runtime.entity("hero").position)) == 2


def test_continuous_static_collision_slides_along_a_wall_without_tunnelling():
    runtime, definition = make_runtime()
    wall = StaticObstacle(
        "vertical-wall", "field",
        ConvexPolygonShape((
            WorldPoint(20.0, -100.0), WorldPoint(25.0, -100.0),
            WorldPoint(25.0, 100.0), WorldPoint(20.0, 100.0),
        )),
        WorldPoint(0.0, 0.0),
    )
    snapshot = build_hex_physics_snapshot(
        WorldId("world"), definition, 32.0, object_obstacles=(wall,),
    )
    result = snapshot.resolve_motion(
        WorldPoint(0.0, 0.0), Vector2(40.0, 30.0),
        PhysicsBodyDefinition("hero", CircleShape(8.0)),
    )

    assert result.applied_displacement.x < 12.1
    assert result.applied_displacement.y > 25.0
    assert result.unresolved_penetration <= 1e-7
