from application.companion_commands import CompanionCommandService
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import AABB, EntityPosition, LocalHexPosition, MovementProfile
from core.foundation import WorldId
from npc import CompanionCommand, CompanionRegistry, NPC, NPCRegistry


def make_service():
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
    return CompanionCommandService(runtime, registry, companions, "hero"), runtime


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
