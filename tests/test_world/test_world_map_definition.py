import copy
import unittest

from application.hex_map_definition import parse_hex_map
from core.domain.spatial import HexDirection
from application.world_map_definition import (
    WorldMapDefinitionError,
    parse_world_map,
    validate_world_map,
)


def hex_map(map_id, transitions=()):
    return parse_hex_map({
        "schema_version": 2,
        "map_id": map_id,
        "name": map_id,
        "description": "",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [-1, 0]],
        "transitions": list(transitions),
    })


def exit_record(identifier, target, direction, entry, *, mode="bidirectional",
                active=True, source=((0, 0),), destination=((0, 0),)):
    return {
        "id": identifier,
        "source_cells": [list(item) for item in source],
        "exit_direction": direction,
        "target_map_id": target,
        "target_entry_direction": entry,
        "target_cells": [list(item) for item in destination],
        "active": active,
        "traversal_mode": mode,
    }


def world(records):
    return parse_world_map({
        "schema_version": 1,
        "id": "test_world",
        "name": "Test World",
        "maps": records,
    })


def placement(map_id, q, r):
    return {"map_id": map_id, "position": {"q": q, "r": r}}


class TestWorldMapDefinition(unittest.TestCase):
    def test_valid_empty_world_is_allowed(self):
        definition = world([])
        validate_world_map(definition, {})
        self.assertEqual(definition.placements, ())

    def test_valid_placement_and_neighbor_lookup(self):
        definition = world([placement("a", 0, 0), placement("b", 1, 0)])
        validate_world_map(definition, {"a": hex_map("a"), "b": hex_map("b")})
        self.assertEqual(definition.neighbor("a", __import__(
            "core.domain.spatial", fromlist=["HexDirection"]
        ).HexDirection.EAST).map_id, "b")
        self.assertIsNone(definition.neighbor("a", __import__(
            "core.domain.spatial", fromlist=["HexDirection"]
        ).HexDirection.WEST))

    def test_duplicate_map_ids_and_world_coordinates_are_rejected(self):
        with self.assertRaisesRegex(WorldMapDefinitionError, "duplicate map_id"):
            world([placement("a", 0, 0), placement("a", 1, 0)])
        with self.assertRaisesRegex(WorldMapDefinitionError, "duplicate axial"):
            world([placement("a", 0, 0), placement("b", 0, 0)])

    def test_invalid_world_coordinate_types_are_rejected(self):
        for q, r in ((True, 0), (0, 1.2), ("1", 0)):
            with self.subTest(q=q, r=r), self.assertRaises(WorldMapDefinitionError):
                world([{"map_id": "a", "position": {"q": q, "r": r}}])

    def test_unknown_and_unplaced_map_references_are_rejected(self):
        with self.assertRaisesRegex(WorldMapDefinitionError, "unknown hex maps"):
            validate_world_map(world([placement("missing", 0, 0)]), {"a": hex_map("a")})
        with self.assertRaisesRegex(WorldMapDefinitionError, "unplaced hex maps"):
            validate_world_map(world([]), {"a": hex_map("a")})

    def test_valid_bidirectional_link_checks_world_direction_and_cells(self):
        a = hex_map("a", [exit_record("a_to_b", "b", "east", "west")])
        b = hex_map("b", [exit_record("b_to_a", "a", "west", "east")])
        validate_world_map(world([placement("a", 0, 0), placement("b", 1, 0)]), {"a": a, "b": b})

    def test_missing_reciprocal_bidirectional_link_is_rejected(self):
        a = hex_map("a", [exit_record("a_to_b", "b", "east", "west")])
        b = hex_map("b")
        with self.assertRaisesRegex(WorldMapDefinitionError, "reciprocal"):
            validate_world_map(world([placement("a", 0, 0), placement("b", 1, 0)]), {"a": a, "b": b})

    def test_wrong_world_direction_is_rejected(self):
        a = hex_map("a", [exit_record("a_to_b", "b", "east", "west", mode="one_way")])
        b = hex_map("b")
        with self.assertRaisesRegex(WorldMapDefinitionError, "does not lead"):
            validate_world_map(world([placement("a", 0, 0), placement("b", 0, 1)]), {"a": a, "b": b})

    def test_wrong_entry_direction_is_rejected(self):
        a = hex_map("a", [exit_record("a_to_b", "b", "east", "east", mode="one_way")])
        b = hex_map("b")
        with self.assertRaisesRegex(WorldMapDefinitionError, "target_entry_direction"):
            validate_world_map(world([placement("a", 0, 0), placement("b", 1, 0)]), {"a": a, "b": b})

    def test_missing_target_map_is_rejected_for_active_transition(self):
        a = hex_map("a", [exit_record("a_to_missing", "missing", "east", "west", mode="one_way")])
        with self.assertRaisesRegex(WorldMapDefinitionError, "missing target"):
            validate_world_map(world([placement("a", 0, 0)]), {"a": a})

    def test_invalid_target_cell_is_rejected(self):
        a = hex_map("a", [exit_record(
            "a_to_b", "b", "east", "west", mode="one_way", destination=((9, 9),)
        )])
        b = hex_map("b")
        with self.assertRaisesRegex(WorldMapDefinitionError, "target cell"):
            validate_world_map(world([placement("a", 0, 0), placement("b", 1, 0)]), {"a": a, "b": b})

    def test_one_way_transition_is_explicit_and_needs_no_reciprocal(self):
        a = hex_map("a", [exit_record("a_to_b", "b", "east", "west", mode="one_way")])
        b = hex_map("b")
        validate_world_map(world([placement("a", 0, 0), placement("b", 1, 0)]), {"a": a, "b": b})

    def test_inactive_future_transition_is_not_a_world_edge(self):
        a = hex_map("a", [exit_record(
            "future_exit", "future_map", "east", "west", active=False, mode="one_way"
        )])
        validate_world_map(world([placement("a", 0, 0)]), {"a": a})

    def test_world_json_rejects_unknown_fields_and_unsupported_versions(self):
        data = {
            "schema_version": 1, "id": "world", "name": "World",
            "maps": [placement("a", 0, 0)],
        }
        invalid = copy.deepcopy(data)
        invalid["unexpected"] = True
        with self.assertRaisesRegex(WorldMapDefinitionError, "unsupported fields"):
            parse_world_map(invalid)
        invalid = copy.deepcopy(data)
        invalid["schema_version"] = 2
        with self.assertRaisesRegex(WorldMapDefinitionError, "Unsupported"):
            parse_world_map(invalid)

    def test_world_json_rejects_missing_fields_and_wrong_types(self):
        with self.assertRaisesRegex(WorldMapDefinitionError, "missing fields"):
            parse_world_map({"schema_version": 1, "id": "world", "maps": []})
        with self.assertRaisesRegex(WorldMapDefinitionError, "must be a list"):
            parse_world_map({
                "schema_version": 1, "id": "world", "name": "World", "maps": {}
            })


if __name__ == "__main__":
    unittest.main()
