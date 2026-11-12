import unittest

from world.map_definition import MapDefinition, MapDefinitionError


def valid_definition():
    return {
        "schema_version": 1,
        "map_id": "test_map",
        "name": "Test Map",
        "description": "",
        "size": {"width": 4, "height": 3},
        "terrain": {"default_tile": "grass"},
        "blocked_tiles": [[1, 1]],
        "features": [{"id": "water", "type": "river", "tiles": [[2, 0]], "walkable": False}],
        "landmarks": [{
            "id": "tree", "name": "Tree", "position": [0, 1],
            "type": "resource", "visual_type": "tree", "walkable": False,
            "interactable": True, "activities": ["gather"], "resource_node_id": "wood",
        }],
        "transitions": [{
            "id": "exit", "from_tiles": [[3, 1]], "target_map_id": "next_map",
            "target_tiles": [[0, 1]],
        }],
    }


class TestMapDefinition(unittest.TestCase):
    def test_builds_valid_definition(self):
        definition = MapDefinition.from_dict(valid_definition())
        self.assertEqual(definition.size.width, 4)
        self.assertEqual(definition.landmarks[0].resource_node_id, "wood")

    def test_rejects_out_of_bounds_landmark(self):
        data = valid_definition()
        data["landmarks"][0]["position"] = [4, 1]
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

    def test_rejects_out_of_bounds_transition_target(self):
        data = valid_definition()
        data["transitions"][0]["target_tiles"] = [[4, 1]]
        with self.assertRaises(MapDefinitionError):
            MapDefinition.from_dict(data)

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


if __name__ == "__main__":
    unittest.main()
