from core.domain.physics import CircleShape, PhysicsBodyDefinition
from core.domain.spatial import ContinuousEntityPosition, LocalHexPosition, WorldPoint
from npc import (
    BehaviorController, BehaviorState, CompanionCommand, CompanionRegistry,
    NPC, NPCRegistry,
)
from application.extended_persistence import SocialSnapshot
from application.social_runtime import SocialRuntime


def test_social_snapshot_persists_npc_behavior_and_companion_wait_command():
    npc = NPC(
        "guard", "Guard",
        behavior=BehaviorController(BehaviorState.FLEE),
        patrol_route=(LocalHexPosition(1, 0), LocalHexPosition(2, 0)),
        patrol_interval_seconds=0.25,
        physics_body=PhysicsBodyDefinition("guard_body", CircleShape(5)),
    )
    companions = CompanionRegistry()
    companions.add("guard")
    wait_position = ContinuousEntityPosition("field", WorldPoint(12.5, 24.0))
    companions.set_command("guard", CompanionCommand.WAIT, wait_position)
    social = SocialRuntime(
        npcs=NPCRegistry((npc,)),
        companions=companions,
    )

    encoded = SocialSnapshot.from_runtime(social).to_dict()
    restored = SocialSnapshot.from_dict(encoded).restore()

    restored_npc = restored.npcs.get("guard")
    assert restored_npc.behavior_state is BehaviorState.FLEE
    assert restored_npc.patrol_route == (
        LocalHexPosition(1, 0), LocalHexPosition(2, 0),
    )
    assert restored_npc.patrol_interval_seconds == 0.25
    assert restored_npc.physics_body.body_id == "guard_body"
    assert restored_npc.physics_body.collider.radius == 5
    state = restored.companions.get("guard")
    assert state.command is CompanionCommand.WAIT
    assert state.wait_position == wait_position


def test_social_snapshot_v1_migrates_without_companion_state():
    legacy = {
        "schema": "rpg-social",
        "schema_version": 1,
        "npcs": [{"npc_id": "guard", "name": "Guard"}],
        "relationships": [],
        "dialogues": [],
        "factions": [],
        "reputation": [],
    }

    restored = SocialSnapshot.from_dict(legacy).restore()

    assert restored.npcs.get("guard").behavior_state is BehaviorState.IDLE
    assert restored.companions.all() == ()


def test_social_snapshot_rejects_companion_references_to_unknown_npcs():
    payload = {
        "schema": "rpg-social",
        "schema_version": 2,
        "npcs": [],
        "relationships": [],
        "dialogues": [],
        "factions": [],
        "reputation": [],
        "companions": [{"npc_id": "missing", "command": "follow", "wait_position": None}],
    }

    try:
        SocialSnapshot.from_dict(payload)
    except ValueError as error:
        assert "unknown NPC" in str(error)
    else:
        raise AssertionError("Unknown companion NPC must be rejected.")
