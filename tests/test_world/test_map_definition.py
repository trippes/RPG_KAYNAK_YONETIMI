import unittest

from world.map_definition import MapDefinition, MapDefinitionError


def valid_definition():
    return {
        "schema_version": 1, "map_id": "test_map", "name": "Test Map",
        "description": "", "size": {"width": 4, "height": 3},
        "terrain": {"default_tile": "grass"}, "blocked_tiles": [[1, 1]],
        "features": [{"id": "water", "type": "river", "tiles": [[2, 0]], "walkable": False}],
        "landmarks": [{
            "id": "tree", "name": "Tree", "position": [0, 1], "type": "resource",
            "visual_type": "tree", "walkable": False, "interactable": True,
            "activities": ["gather"], "resource_node_id": "wood",
        }],
        "transitions": [{
            "id": "exit", "from_tiles": [[3, 1]], "target_map_id": "next_map",
            "target_tiles": [[0, 1]], "direction": "east",
        }],
    }


class TestMapDefinition(unittest.TestCase):
    def test_builds_valid_definition(self):
        definition = MapDefinition.from_dict(valid_definition())
        self.assertEqual(definition.size.width, 4)
        self.assertEqual(definition.landmarks[0].resource_node_id, "wood")
        self.assertEqual(definition.transitions[0].target_tiles, ((0, 1),))

    def test_rejects_out_of_bounds_landmark(self):
        data = valid_definition()
        data["landmarks"][0]["position"] = [4, 1]
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_rejects_out_of_bounds_transition_source(self):
        data = valid_definition()
        data["transitions"][0]["from_tiles"] = [[4, 1]]
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_target_coordinates_are_not_checked_against_source_map(self):
        data = valid_definition()
        data["transitions"][0]["target_tiles"] = [[9, 1]]
        definition = MapDefinition.from_dict(data)
        self.assertEqual(definition.transitions[0].target_tiles, ((9, 1),))

    def test_rejects_duplicate_feature_ids(self):
        data = valid_definition()
        data["features"].append({"id": "water", "type": "bridge", "tiles": [[1, 0]], "walkable": True})
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_rejects_empty_transition_tiles(self):
        data = valid_definition()
        data["transitions"][0]["from_tiles"] = []
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_rejects_missing_target_tiles(self):
        data = valid_definition()
        data["transitions"][0]["target_tiles"] = []
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_rejects_invalid_direction(self):
        data = valid_definition()
        data["transitions"][0]["direction"] = "diagonal"
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_reads_optional_world_and_starting_positions(self):
        data = valid_definition()
        data["world_position"] = [120, 240]
        data["starting_position"] = [2, 2]
        data["metadata"] = {"biome": "temperate"}
        definition = MapDefinition.from_dict(data)

        self.assertEqual(definition.world_position, (120, 240))
        self.assertEqual(definition.starting_position, (2, 2))
        self.assertEqual(definition.metadata, {"biome": "temperate"})

    def test_rejects_starting_position_outside_map_bounds(self):
        data = valid_definition()
        data["starting_position"] = [4, 2]
        with self.assertRaisesRegex(MapDefinitionError, "outside map"):
            MapDefinition.from_dict(data)

    def test_rejects_unknown_top_level_fields(self):
        data = valid_definition()
        data["unexpected"] = True
        with self.assertRaisesRegex(MapDefinitionError, "unsupported fields"):
            MapDefinition.from_dict(data)

    def test_parses_map_activities_and_explicit_transition_directionality(self):
        data = valid_definition()
        data["activities"] = ["travel", "gather"]
        data["transitions"][0]["bidirectional"] = True
        definition = MapDefinition.from_dict(data)
        self.assertEqual(definition.activities, ("travel", "gather"))
        self.assertTrue(definition.transitions[0].bidirectional)


if __name__ == "__main__":
    unittest.main()
