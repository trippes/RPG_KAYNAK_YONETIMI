import json
import unittest
from pathlib import Path

from world.map_loader import load_map_definition, load_map_definitions


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "demo_eldoria"
MAPS = PACKAGE / "maps"
EXPECTED_MAPS = {
    "village", "forest", "south_forest", "west_forest", "east_forest",
    "north_mine", "south_mine", "west_mine", "east_mine",
}
EXPECTED_WORLD_POSITIONS = {
    "village": (180, 220),
    "forest": (180, 50),
    "south_forest": (180, 390),
    "west_forest": (30, 220),
    "east_forest": (330, 220),
    "north_mine": (300, 50),
    "south_mine": (300, 390),
    "west_mine": (30, 390),
    "east_mine": (480, 220),
}
EXPECTED_CONNECTIONS = {
    frozenset(("village", "forest")),
    frozenset(("village", "south_forest")),
    frozenset(("village", "west_forest")),
    frozenset(("village", "east_forest")),
    frozenset(("forest", "north_mine")),
    frozenset(("south_forest", "south_mine")),
    frozenset(("west_forest", "west_mine")),
    frozenset(("east_forest", "east_mine")),
}


class TestDemoLocalMapContent(unittest.TestCase):
    def test_all_nine_demo_maps_are_discovered_from_json(self):
        definitions = load_map_definitions(MAPS)
        self.assertEqual(set(definitions), EXPECTED_MAPS)
        self.assertEqual({path.stem for path in MAPS.glob("*.json")}, EXPECTED_MAPS)

    def test_world_positions_are_declared_by_local_map_files(self):
        definitions = load_map_definitions(MAPS)
        self.assertTrue(all(item.world_position is not None for item in definitions.values()))
        positions = [item.world_position for item in definitions.values()]
        self.assertEqual(len(positions), len(set(positions)))
        self.assertEqual(
            {map_id: item.world_position for map_id, item in definitions.items()},
            EXPECTED_WORLD_POSITIONS,
        )

    def test_all_landmark_coordinates_are_inside_their_local_maps(self):
        for path in MAPS.glob("*.json"):
            definition = load_map_definition(path)
            for landmark in definition.landmarks:
                x, y = landmark.position
                self.assertTrue(
                    0 <= x < definition.size.width and 0 <= y < definition.size.height,
                    f"{definition.map_id}:{landmark.landmark_id}",
                )

    def test_river_and_bridge_are_declared_as_map_features(self):
        for path in MAPS.glob("*.json"):
            definition = load_map_definition(path)
            features = {item.feature_id: item for item in definition.features}
            self.assertIn("river", features, path.stem)
            self.assertIn("bridge", features, path.stem)
            self.assertEqual(len(features["river"].tiles), definition.size.height * 2)
            self.assertEqual(len(features["bridge"].tiles), 2)

    def test_resource_landmarks_match_the_resource_catalog(self):
        resources = json.loads((PACKAGE / "resources.json").read_text(encoding="utf-8"))
        node_ids = {item["id"] for item in resources["nodes"]}
        definitions = load_map_definitions(MAPS)
        for definition in definitions.values():
            for landmark in definition.landmarks:
                if landmark.resource_node_id is not None:
                    self.assertIn(landmark.resource_node_id, node_ids)
        for record in resources["nodes"]:
            map_id = {"village_id": "village", "forest_id": "forest"}.get(
                record["location_id"], record["location_id"],
            )
            landmark = next(
                item for item in definitions[map_id].landmarks
                if item.landmark_id == record["landmark_id"]
            )
            self.assertEqual(landmark.resource_node_id, record["id"])

    def test_bidirectional_exits_have_reciprocal_local_transitions(self):
        definitions = load_map_definitions(MAPS)
        for map_id, definition in definitions.items():
            for transition in definition.transitions:
                if not transition.bidirectional:
                    continue
                target = definitions[transition.target_map_id]
                reciprocal = any(
                    candidate.bidirectional
                    and candidate.target_map_id == map_id
                    and set(candidate.from_tiles).intersection(transition.target_tiles)
                    and set(candidate.target_tiles).intersection(transition.from_tiles)
                    for candidate in target.transitions
                )
                self.assertTrue(reciprocal, transition.transition_id)

    def test_only_the_starting_map_declares_a_starting_position(self):
        definitions = load_map_definitions(MAPS)
        starting = [
            item for item in definitions.values()
            if item.starting_position is not None
        ]
        self.assertEqual(len(starting), 1)
        self.assertEqual(starting[0].map_id, "village")
        self.assertEqual(starting[0].starting_position, (16, 29))

    def test_world_graph_preserves_all_eight_original_connections(self):
        definitions = load_map_definitions(MAPS)
        actual = {
            frozenset((map_id, transition.target_map_id))
            for map_id, definition in definitions.items()
            for transition in definition.transitions
            if transition.bidirectional
        }
        self.assertEqual(actual, EXPECTED_CONNECTIONS)


if __name__ == "__main__":
    unittest.main()
