from application.companion_commands import CompanionCommandService
from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementProfile
from core.foundation import WorldId
from npc import CompanionCommand, CompanionRegistry, NPC, NPCRegistry


def make_service(*, with_physics=False):
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
        MovementProfile(), local_spatial_bounds=AABB(-8, -8, 8, 8),
    )
    npc = NPC("guard", "Guard")
    registry = NPCRegistry((npc,))
    runtime.register_entity(
        "guard", "npc", EntityPosition("field", LocalHexPosition(3, 0)),
        MovementProfile(), local_spatial_bounds=AABB(-4, -4, 4, 4),
    )
    companions = CompanionRegistry()
    snapshot = (
        build_hex_physics_snapshot(WorldId("world"), definition, 32.0)
        if with_physics else None
    )
    return CompanionCommandService(
        runtime, registry, companions, "hero", physics_snapshot=snapshot,
    ), runtime


def test_companion_can_be_enlisted_and_commanded_to_wait():
    service, runtime = make_service()
    service.enlist("guard")
    state = service.command("guard", CompanionCommand.WAIT)

    assert state.command is CompanionCommand.WAIT
    assert state.wait_position == runtime.continuous_position("guard")
    assert service.tick(1.0) == ()


def test_follow_command_moves_companion_one_pathfinding_step_toward_player():
    service, runtime = make_service()
    service.enlist("guard")
    before = runtime.entity("guard").position.cell

    moved = service.tick(0.25)

    assert moved == ("guard",)
    assert runtime.entity("guard").position.cell != before
    assert runtime.entity("guard").position.cell == LocalHexPosition(2, 0)


def test_wait_then_follow_resumes_movement():
    service, runtime = make_service()
    service.enlist("guard")
    service.command("guard", CompanionCommand.WAIT)
    assert service.tick(1.0) == ()
    service.command("guard", CompanionCommand.FOLLOW)
    assert service.tick(0.25) == ("guard",)


def test_follow_uses_continuous_physics_motion_instead_of_teleporting_between_cells():
    service, runtime = make_service(with_physics=True)
    service.enlist("guard")
    before = runtime.continuous_position("guard").point

    moved = service.tick(0.25)

    after = runtime.continuous_position("guard").point
    assert moved == ("guard",)
    assert after.x < before.x
    assert after != service.physics_snapshot.cell_center(LocalHexPosition(2, 0))
    assert 0 < before.x - after.x <= service.FOLLOW_SPEED * 0.25 + 1e-7


def test_wait_command_clears_pending_follow_target_before_resuming():
    service, runtime = make_service(with_physics=True)
    service.enlist("guard")
    service.tick(0.1)
    service.command("guard", CompanionCommand.WAIT)
    waiting_position = runtime.continuous_position("guard")
    assert service.tick(1.0) == ()
    assert runtime.continuous_position("guard") == waiting_position
    service.command("guard", CompanionCommand.FOLLOW)
    assert service.tick(0.25) == ("guard",)
