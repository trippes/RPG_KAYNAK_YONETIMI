"""NPC-owned immutable physics definition tests."""

from dataclasses import FrozenInstanceError
import unittest

from core.domain.physics import CircleShape, PhysicsBodyDefinition
from npc import NPC


class TestNPCPhysicsDefinition(unittest.TestCase):
    def test_npc_receives_its_own_circle_body_with_approved_radius(self):
        first = NPC("guard_a", "Guard A")
        second = NPC("guard_b", "Guard B")

        self.assertIsInstance(first.physics_body, PhysicsBodyDefinition)
        self.assertIsInstance(first.physics_body.collider, CircleShape)
        self.assertEqual(first.physics_body.collider.radius, 4.0)
        self.assertEqual(first.physics_body.body_id, first.npc_id)
        self.assertEqual(second.physics_body.body_id, second.npc_id)
        self.assertIsNot(first.physics_body, second.physics_body)
        self.assertIsNot(first.physics_body.collider, second.physics_body.collider)

    def test_npc_can_receive_an_explicit_individual_physics_definition(self):
        body = PhysicsBodyDefinition(
            body_id="large_guard",
            collider=CircleShape(radius=6.0),
        )

        npc = NPC("large_guard", "Large Guard", physics_body=body)

        self.assertIs(npc.physics_body, body)
        self.assertEqual(npc.physics_body.collider.radius, 6.0)

    def test_npc_rejects_physics_definition_owned_by_another_id(self):
        body = PhysicsBodyDefinition(
            body_id="other_npc",
            collider=CircleShape(radius=4.0),
        )

        with self.assertRaisesRegex(ValueError, "must match npc_id"):
            NPC("guard", "Guard", physics_body=body)

    def test_npc_physics_definition_is_immutable(self):
        npc = NPC("guard", "Guard")

        with self.assertRaises(FrozenInstanceError):
            npc.physics_body.body_height = 2.0


if __name__ == "__main__":
    unittest.main()
