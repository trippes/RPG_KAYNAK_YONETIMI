from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from application.npc_avoidance import NPCAvoidanceSystem
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementProfile
from core.foundation import WorldId
from npc import BehaviorController, BehaviorState, NPC, NPCRegistry


def make_world(*, blocked=False):
    overrides = [{"q": 2, "r": 0, "blocked": True}] if blocked else []
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
        "cell_overrides": overrides,
        "transitions": [],
    })
    runtime = HexWorldRuntime({"field": definition}, world_id=WorldId("world"))
    runtime.register_entity(
        "hero", "player", EntityPosition("field", LocalHexPosition(0, 0)),
        MovementProfile(), local_spatial_bounds=AABB(-8, -8, 8, 8),
    )
    fleeing = NPC("fleeing", "Fleeing", behavior=BehaviorController(BehaviorState.FLEE))
    idle = NPC("idle", "Idle")
    registry = NPCRegistry((fleeing, idle))
    for npc, q in ((fleeing, 1), (idle, 3)):
        runtime.register_entity(
            npc.npc_id, "npc", EntityPosition("field", LocalHexPosition(q, 0)),
            MovementProfile(),
            local_spatial_bounds=AABB(-4, -4, 4, 4),
        )
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    return runtime, registry, snapshot


def test_flee_state_moves_npc_away_from_player_and_leaves_idle_npc_untouched():
    runtime, registry, snapshot = make_world()
    before_flee = runtime.continuous_position("fleeing").point
    before_idle = runtime.continuous_position("idle").point

    moved = NPCAvoidanceSystem(
        registry, runtime, snapshot, "hero",
    ).step(0.1)

    after_flee = runtime.continuous_position("fleeing").point
    assert moved == ("fleeing",)
    assert after_flee.x > before_flee.x
    assert runtime.continuous_position("idle").point == before_idle


def test_avoidance_does_not_cross_a_blocked_cell_without_an_escape_route():
    runtime, registry, snapshot = make_world(blocked=True)
    before = runtime.continuous_position("fleeing").point

    moved = NPCAvoidanceSystem(
        registry, runtime, snapshot, "hero",
    ).step(0.5)

    assert moved == ()
    assert runtime.continuous_position("fleeing").point == before
    assert runtime.entity("fleeing").position.cell == LocalHexPosition(1, 0)


def test_flee_pathfinding_routes_around_static_obstacles():
    cells = [
        [q, r]
        for q in range(-2, 6)
        for r in range(-4, 5)
        if max(abs(q - 1), abs(r), abs(q + r - 1)) <= 3
    ]
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
        "valid_cells": cells,
        "cell_overrides": [{"q": 2, "r": 0, "blocked": True}],
        "transitions": [],
    })
    runtime = HexWorldRuntime({"field": definition}, world_id=WorldId("world"))
    runtime.register_entity(
        "hero", "player", EntityPosition("field", LocalHexPosition(0, 0)),
        MovementProfile(), local_spatial_bounds=AABB(-8, -8, 8, 8),
    )
    fleeing = NPC(
        "fleeing", "Fleeing",
        behavior=BehaviorController(BehaviorState.FLEE),
    )
    registry = NPCRegistry((fleeing,))
    runtime.register_entity(
        "fleeing", "npc", EntityPosition("field", LocalHexPosition(1, 0)),
        MovementProfile(), local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    before = runtime.continuous_position("fleeing").point

    moved = NPCAvoidanceSystem(
        registry, runtime, snapshot, "hero",
    ).step(0.1)

    after = runtime.continuous_position("fleeing").point
    assert moved == ("fleeing",)
    assert after != before
    assert after.y != before.y
    assert runtime.entity("fleeing").position.cell != LocalHexPosition(2, 0)
