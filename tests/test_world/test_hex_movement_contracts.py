import unittest

from core.domain.spatial import (
    EntityPosition,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
    MovementRequest,
    MovementResult,
)


class TestHexMovementContracts(unittest.TestCase):
    def test_entity_position_is_map_scoped_and_immutable(self):
        first = EntityPosition("forest", LocalHexPosition(0, 0))
        other_map = EntityPosition("mine", LocalHexPosition(0, 0))
        self.assertNotEqual(first, other_map)
        self.assertEqual(first, EntityPosition("forest", LocalHexPosition(0, 0)))
        with self.assertRaises((AttributeError, TypeError)):
            first.map_id = "mine"

    def test_entity_position_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            EntityPosition("", LocalHexPosition(0, 0))
        with self.assertRaises(TypeError):
            EntityPosition("forest", (0, 0))

    def test_movement_profile_normalizes_terrain_capabilities(self):
        profile = MovementProfile(allowed_terrain_ids={"grass", "road"})
        self.assertEqual(profile.allowed_terrain_ids, frozenset({"grass", "road"}))
        self.assertFalse(profile.ignores_occupancy)
        self.assertTrue(MovementProfile(ignores_occupancy=True).ignores_occupancy)
        with self.assertRaises(TypeError):
            MovementProfile(ignores_occupancy=1)
        with self.assertRaises(TypeError):
            MovementProfile(can_move=1)
        with self.assertRaises(ValueError):
            MovementProfile(allowed_terrain_ids={"grass", ""})

    def test_movement_request_requires_consistent_domain_types(self):
        source = EntityPosition("forest", LocalHexPosition(0, 0))
        target = EntityPosition("forest", LocalHexPosition(1, 0))
        request = MovementRequest("hero", source, target)
        self.assertEqual(request.entity_id, "hero")
        self.assertEqual(request.profile, MovementProfile())
        with self.assertRaises(ValueError):
            MovementRequest("", source, target)

    def test_movement_result_success_and_failure_contract(self):
        position = EntityPosition("forest", LocalHexPosition(0, 0))
        success = MovementResult(True, position)
        failure = MovementResult(
            False, position, MovementFailureReason.BLOCKED_CELL, "Blocked",
        )
        self.assertTrue(success.success)
        self.assertFalse(failure.success)
        self.assertEqual(failure.reason, MovementFailureReason.BLOCKED_CELL)
        with self.assertRaises(ValueError):
            MovementResult(False, position)
        with self.assertRaises(ValueError):
            MovementResult(True, position, MovementFailureReason.BLOCKED_CELL)


if __name__ == "__main__":
    unittest.main()
