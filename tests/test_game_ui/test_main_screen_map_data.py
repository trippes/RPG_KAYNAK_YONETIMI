import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from game_ui.screens.main_screen import MainScreen


class FakeMapService:
    def __init__(self, location, package_path=None, use_default_package=True):
        self.actor = SimpleNamespace(
            actor_id="hero", world_id="world", location_id=location.location_id,
            position=SimpleNamespace(x=16, y=16),
        )
        world_map = SimpleNamespace(get=lambda location_id: location if location_id == location.location_id else None)
        self.application = SimpleNamespace(
            holder=SimpleNamespace(current=SimpleNamespace(
                movement=SimpleNamespace(map_for=lambda _world_id: world_map),
            )),
        )
        self._content_package_path = (
            package_path
            if package_path is not None or not use_default_package
            else Path(__file__).resolve().parents[2] / "content" / "demo_eldoria"
        )

    def state(self):
        return SimpleNamespace(actors=(self.actor,))

    def blocked_world_object_tiles(self, _world_id, _location_id):
        return set()


class TestMainScreenMapData(unittest.TestCase):
    def test_map_dimensions_come_from_json_not_a_screen_constant(self):
        location = SimpleNamespace(location_id="tiny", landmarks=(), name="Tiny")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "maps").mkdir()
            (root / "manifest.json").write_text(
                json.dumps({
                    "schema_version": 1, "package_id": "tiny",
                    "package_version": "1.0.0",
                    "files": {"starter": "starter.json"}, "maps": "maps",
                }),
                encoding="utf-8",
            )
            (root / "starter.json").write_text("{}", encoding="utf-8")
            definition = {
                "schema_version": 1,
                "map_id": "tiny",
                "name": "Tiny",
                "description": "",
                "size": {"width": 7, "height": 5},
                "terrain": {"default_tile": "grass"},
            }
            (root / "maps" / "tiny.json").write_text(
                json.dumps(definition), encoding="utf-8",
            )
            screen = MainScreen(FakeMapService(location, root))
            self.assertEqual(screen._map_width(), 7)
            self.assertEqual(screen._map_height(), 5)
            self.assertFalse(hasattr(MainScreen, "GRID_SIZE"))

    def test_bridge_tiles_override_the_non_walkable_river_feature(self):
        location = SimpleNamespace(location_id="village", landmarks=(), name="Village")
        screen = MainScreen(FakeMapService(location))
        blocked = screen._blocked_tiles()
        self.assertNotIn((18, 16), blocked)
        self.assertNotIn((19, 16), blocked)
        self.assertIn((18, 15), blocked)
        self.assertIn((19, 17), blocked)

    def test_village_wall_and_gate_openings_are_content_defined(self):
        location = SimpleNamespace(location_id="village", landmarks=(), name="Village")
        screen = MainScreen(FakeMapService(location))
        blocked = screen._blocked_tiles()
        self.assertIn((0, 1), blocked)
        self.assertNotIn((0, 16), blocked)
        self.assertNotIn((16, 0), blocked)
        self.assertNotIn((16, 30), blocked)
        self.assertNotIn((16, 31), blocked)

    def test_gate_tiles_are_derived_from_gate_landmarks(self):
        location = SimpleNamespace(location_id="village", landmarks=(), name="Village")
        screen = MainScreen(FakeMapService(location))
        gates = screen._gate_tiles()
        self.assertIn((16, 30), gates)
        self.assertIn((16, 31), gates)
        self.assertIn((0, 16), gates)

    def test_missing_package_context_does_not_fall_back_to_demo_content(self):
        location = SimpleNamespace(location_id="village", landmarks=(), name="Village")
        screen = MainScreen(FakeMapService(location, use_default_package=False))

        self.assertIsNone(screen._map_definition())
        self.assertIn("paketi bağlamı", screen.message)
        self.assertIsNone(screen._map_definition_cache)

    def test_supported_visual_styles_are_registered_centrally(self):
        self.assertIn("grass", MainScreen.TERRAIN_STYLES)
        self.assertIn("river", MainScreen.FEATURE_STYLES)
        self.assertIn("bridge", MainScreen.FEATURE_STYLES)
        self.assertIn("wall", MainScreen.FEATURE_STYLES)
        self.assertIn("tree", MainScreen.LANDMARK_STYLES)
        self.assertIn("mine", MainScreen.LANDMARK_STYLES)


if __name__ == "__main__":
    unittest.main()
