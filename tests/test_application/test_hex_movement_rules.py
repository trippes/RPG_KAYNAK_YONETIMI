import unittest

from application.hex_map_definition import parse_hex_map
from application.hex_movement_rules import MovementRules
from core.domain.spatial import (
    EntityPosition,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
    MovementRequest,
)


def make_map():
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "forest",
        "name": "Forest",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass", "water"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [2, 0], [0, 1]],
        "cell_overrides": [
            {"q": 2, "r": 0, "blocked": True},
            {"q": 0, "r": 1, "terrain": "water"},
        ],
    })


class TestHexMovementRules(unittest.TestCase):
    def setUp(self):
        self.map = make_map()
        self.source = EntityPosition("forest", LocalHexPosition(0, 0))

    def request(self, target, profile=None, source=None):
        return MovementRequest(
            "hero",
            source or self.source,
            EntityPosition("forest", target),
            profile or MovementProfile(),
        )

    def test_adjacent_valid_target_is_accepted_without_mutation(self):
        target = LocalHexPosition(1, 0)
        result = MovementRules.evaluate(self.request(target), self.map)
        self.assertTrue(result.success)
        self.assertEqual(result.position.cell, target)
        self.assertEqual(self.source.cell, LocalHexPosition(0, 0))

    def test_invalid_source_outside_valid_cells_is_rejected(self):
        source = EntityPosition("forest", LocalHexPosition(9, 9))
        result = MovementRules.evaluate(
            self.request(LocalHexPosition(1, 0), source=source), self.map,
        )
        self.assertFalse(result.success)
        self.assertEqual(result.reason, MovementFailureReason.INVALID_SOURCE)
        self.assertEqual(result.position, source)

    def test_invalid_target_outside_valid_cells_is_rejected(self):
        result = MovementRules.evaluate(self.request(LocalHexPosition(8, 8)), self.map)
        self.assertEqual(result.reason, MovementFailureReason.INVALID_TARGET)
        self.assertEqual(result.position, self.source)

    def test_non_adjacent_target_is_rejected(self):
        result = MovementRules.evaluate(self.request(LocalHexPosition(2, 0)), self.map)
        self.assertEqual(result.reason, MovementFailureReason.NON_ADJACENT_TARGET)

    def test_blocked_target_is_rejected_by_default(self):
        result = MovementRules.evaluate(self.request(LocalHexPosition(2, 0)), self.map)
        self.assertEqual(result.reason, MovementFailureReason.BLOCKED_CELL)

    def test_profile_can_explicitly_traverse_blocked_target(self):
        profile = MovementProfile(can_traverse_blocked_cells=True)
        result = MovementRules.evaluate(
            self.request(LocalHexPosition(2, 0), profile), self.map,
        )
        self.assertTrue(result.success)

    def test_terrain_restriction_is_enforced(self):
        profile = MovementProfile(allowed_terrain_ids={"grass"})
        result = MovementRules.evaluate(
            self.request(LocalHexPosition(0, 1), profile), self.map,
        )
        self.assertEqual(result.reason, MovementFailureReason.TERRAIN_NOT_ALLOWED)

    def test_non_movable_profile_is_rejected(self):
        result = MovementRules.evaluate(
            self.request(LocalHexPosition(1, 0), MovementProfile(can_move=False)),
            self.map,
        )
        self.assertEqual(result.reason, MovementFailureReason.MOVEMENT_NOT_ALLOWED)

    def test_cross_map_request_is_not_a_local_move(self):
        request = MovementRequest(
            "hero",
            self.source,
            EntityPosition("mine", LocalHexPosition(0, 0)),
        )
        result = MovementRules.evaluate(request, self.map)
        self.assertEqual(result.reason, MovementFailureReason.INVALID_TRANSITION)

    def test_source_map_must_match_map_definition(self):
        source = EntityPosition("mine", LocalHexPosition(0, 0))
        request = MovementRequest(
            "hero", source, EntityPosition("mine", LocalHexPosition(1, 0)),
        )
        result = MovementRules.evaluate(request, self.map)
        self.assertEqual(result.reason, MovementFailureReason.INVALID_SOURCE)

    def test_same_cell_is_not_a_movement_step(self):
        result = MovementRules.evaluate(self.request(LocalHexPosition(0, 0)), self.map)
        self.assertEqual(result.reason, MovementFailureReason.NON_ADJACENT_TARGET)

    def test_invalid_call_types_are_rejected(self):
        with self.assertRaises(TypeError):
            MovementRules.evaluate(object(), self.map)
        with self.assertRaises(TypeError):
            MovementRules.evaluate(self.request(LocalHexPosition(1, 0)), object())


if __name__ == "__main__":
    unittest.main()
