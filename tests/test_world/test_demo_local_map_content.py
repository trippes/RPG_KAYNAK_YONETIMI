import json
import unittest
from pathlib import Path

from world.map_loader import load_map_definition


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "demo_eldoria"
MAPS = PACKAGE / "maps"
ALIASES = {"village_id": "village", "forest_id": "forest"}


class TestDemoLocalMapContent(unittest.TestCase):
    def test_every_starter_location_has_a_valid_map_file(self):
        starter = json.loads((PACKAGE / "starter_content.json").read_text(encoding="utf-8"))
        expected = {ALIASES.get(item["id"], item["id"]) for item in starter["locations"]}
        actual = {path.stem for path in MAPS.glob("*.json")}
        self.assertEqual(actual, expected)
        for path in sorted(MAPS.glob("*.json")):
            self.assertEqual(load_map_definition(path).map_id, path.stem)

    def test_local_landmarks_preserve_starter_coordinates(self):
        starter = json.loads((PACKAGE / "starter_content.json").read_text(encoding="utf-8"))
        for location in starter["locations"]:
            map_id = ALIASES.get(location["id"], location["id"])
            definition = load_map_definition(MAPS / f"{map_id}.json")
            expected = {
                item["id"]: tuple(item["position"])
                for item in location.get("landmarks", ())
                if isinstance(item.get("position"), list)
                and len(item["position"]) == 2
                and all(type(value) is int for value in item["position"])
                and 0 <= item["position"][0] < definition.size.width
                and 0 <= item["position"][1] < definition.size.height
            }
            actual = {item.landmark_id: item.position for item in definition.landmarks}
            self.assertEqual(actual, expected, map_id)

    def test_river_and_bridge_are_declared_as_map_features(self):
        for path in MAPS.glob("*.json"):
            definition = load_map_definition(path)
            features = {item.feature_id: item for item in definition.features}
            self.assertIn("river", features, path.stem)
            self.assertIn("bridge", features, path.stem)
            self.assertEqual(len(features["river"].tiles), definition.size.height * 2)
            self.assertEqual(len(features["bridge"].tiles), 2)

    def test_resource_landmarks_reference_declared_resource_nodes(self):
        resources = json.loads((PACKAGE / "resources.json").read_text(encoding="utf-8"))
        node_ids = {item["id"] for item in resources["nodes"]}
        for path in MAPS.glob("*.json"):
            definition = load_map_definition(path)
            for landmark in definition.landmarks:
                if landmark.resource_node_id is not None:
                    self.assertIn(landmark.resource_node_id, node_ids)


if __name__ == "__main__":
    unittest.main()
