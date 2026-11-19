"""NPC-owned immutable physics definition tests."""

from dataclasses import FrozenInstanceError

import pytest

from core.domain.physics import CircleShape, PhysicsBodyDefinition
from npc import NPC


def test_npc_receives_its_own_circle_body_with_approved_radius():
    first = NPC("guard_a", "Guard A")
    second = NPC("guard_b", "Guard B")

    assert isinstance(first.physics_body, PhysicsBodyDefinition)
    assert isinstance(first.physics_body.collider, CircleShape)
    assert first.physics_body.collider.radius == 4.0
    assert first.physics_body.body_id == first.npc_id
    assert second.physics_body.body_id == second.npc_id
    assert first.physics_body is not second.physics_body
    assert first.physics_body.collider is not second.physics_body.collider


def test_npc_can_receive_an_explicit_individual_physics_definition():
    body = PhysicsBodyDefinition(
        body_id="large_guard",
        collider=CircleShape(radius=6.0),
    )

    npc = NPC("large_guard", "Large Guard", physics_body=body)

    assert npc.physics_body is body
    assert npc.physics_body.collider.radius == 6.0


def test_npc_rejects_physics_definition_owned_by_another_id():
    body = PhysicsBodyDefinition(
        body_id="other_npc",
        collider=CircleShape(radius=4.0),
    )

    with pytest.raises(ValueError, match="must match npc_id"):
        NPC("guard", "Guard", physics_body=body)


def test_npc_physics_definition_is_immutable():
    npc = NPC("guard", "Guard")

    with pytest.raises(FrozenInstanceError):
        npc.physics_body.body_height = 2.0
