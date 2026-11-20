from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from application.npc_behavior_system import NPCBehaviorSystem
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
    npc = NPC(
        "guard", "Guard",
        behavior=BehaviorController(BehaviorState.PATROL),
        patrol_route=(LocalHexPosition(1, 0), LocalHexPosition(2, 0)),
        patrol_interval_seconds=0.25,
    )
    npcs = NPCRegistry((npc,))
    runtime.register_entity(
        "guard", "npc", EntityPosition("field", LocalHexPosition(1, 0)),
        MovementProfile(), local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    snapshot = build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
    return runtime, npcs, snapshot


def test_patrol_uses_runtime_pathfinding_and_advances_one_waypoint_step():
    runtime, npcs, snapshot = make_world()
    system = NPCBehaviorSystem(npcs, runtime, snapshot)

    assert system.step(0.1) == ()
    assert runtime.entity("guard").position.cell == LocalHexPosition(1, 0)

    moved = system.step(0.15)

    assert moved == ("guard",)
    assert runtime.entity("guard").position.cell == LocalHexPosition(2, 0)
    assert runtime.patrol_indices["guard"] == 0


def test_patrol_does_not_move_through_blocked_waypoint():
    runtime, npcs, snapshot = make_world(blocked=True)
    system = NPCBehaviorSystem(npcs, runtime, snapshot)

    moved = system.step(0.25)

    assert moved == ()
    assert runtime.entity("guard").position.cell == LocalHexPosition(1, 0)
