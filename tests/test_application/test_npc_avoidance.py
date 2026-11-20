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
    for npc, q in ((fleeing, 1), (idle, 2)):
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


def test_avoidance_is_bounded_by_static_map_collision():
    runtime, registry, snapshot = make_world(blocked=True)
    before = runtime.continuous_position("fleeing").point

    moved = NPCAvoidanceSystem(
        registry, runtime, snapshot, "hero",
    ).step(0.5)

    after = runtime.continuous_position("fleeing").point
    assert moved == ("fleeing",)
    assert after.x >= before.x
    assert runtime.entity("fleeing").position.cell == LocalHexPosition(1, 0)
