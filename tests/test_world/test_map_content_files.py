"""Regression checks for migrated local-map content files."""

import json
import unittest
from pathlib import Path

from world.map_loader import load_map_definition


ROOT = Path(__file__).resolve().parents[2]
MAPS_DIR = ROOT / "data" / "maps"
EXPECTED_MAP_IDS = {
    "village",
    "forest",
    "south_forest",
    "west_forest",
    "east_forest",
    "north_mine",
    "south_mine",
    "west_mine",
    "east_mine",
}


class TestMigratedMapContent(unittest.TestCase):
    def test_every_starter_location_has_a_valid_map_file(self):
        files = sorted(MAPS_DIR.glob("*.json"))
        self.assertEqual({path.stem for path in files}, EXPECTED_MAP_IDS)
        definitions = [load_map_definition(path) for path in files]
        self.assertEqual({item.map_id for item in definitions}, EXPECTED_MAP_IDS)

    def test_map_landmarks_keep_their_legacy_tile_coordinates(self):
        starter = json.loads((ROOT / "data" / "starter_content.json").read_text(encoding="utf-8"))
        aliases = {"village_id": "village", "forest_id": "forest"}
        for location in starter["locations"]:
            map_id = aliases.get(location["id"], location["id"])
            definition = load_map_definition(MAPS_DIR / f"{map_id}.json")
            expected = {
                item["id"]: tuple(item["position"])
                for item in location.get("landmarks", ())
                if (
                    isinstance(item.get("position"), list)
                    and len(item["position"]) == 2
                    and all(isinstance(value, int) for value in item["position"])
                    and 0 <= item["position"][0] < definition.size.width
                    and 0 <= item["position"][1] < definition.size.height
                )
            }
            actual = {item.landmark_id: item.position for item in definition.landmarks}
            self.assertEqual(actual, expected, map_id)

    def test_each_map_preserves_the_existing_river_and_bridge_layout(self):
        for path in MAPS_DIR.glob("*.json"):
            definition = load_map_definition(path)
            features = {item.feature_id: item for item in definition.features}
            self.assertEqual(set(features), {"river", "bridge"}, path.stem)
            self.assertEqual(
                set(features["river"].tiles),
                {(x, y) for x in (18, 19) for y in range(32)},
                path.stem,
            )
            self.assertEqual(set(features["bridge"].tiles), {(18, 16), (19, 16)}, path.stem)


if __name__ == "__main__":
    unittest.main()
