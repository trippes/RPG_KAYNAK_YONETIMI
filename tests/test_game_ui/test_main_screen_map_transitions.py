import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from game_ui.screens.main_screen import MainScreen


class _WorldMap:
    def __init__(self, locations):
        self.locations = {item.location_id: item for item in locations}

    def get(self, location_id):
        return self.locations.get(location_id)


class _TransitionService:
    def __init__(self, source, target, package_path):
        self.actor = SimpleNamespace(
            actor_id="hero", world_id="world", location_id=source.location_id,
            position=SimpleNamespace(x=3, y=1),
        )
        self.world_map = _WorldMap((source, target))
        self.application = SimpleNamespace(holder=SimpleNamespace(current=SimpleNamespace(
            movement=SimpleNamespace(map_for=lambda _world_id: self.world_map),
        )))
        self._content_package_path = package_path
        self.placed = None
        self.tile_position = None

    def state(self):
        return SimpleNamespace(actors=(self.actor,))

    def place_actor(self, actor_id, location_id):
        self.placed = (actor_id, location_id)
        self.actor.location_id = location_id

    def set_actor_tile_position(self, actor_id, x, y):
        self.tile_position = (actor_id, x, y)
        self.actor.position = SimpleNamespace(x=x, y=y)

    def advance_by(self, _ticks):
        pass


class TestMainScreenJsonTransitions(unittest.TestCase):
    def _write_map(self, root, map_id, width, height, transitions=()):
        data = {
            "schema_version": 1, "map_id": map_id, "name": map_id,
            "description": "", "size": {"width": width, "height": height},
            "terrain": {"default_tile": "grass"}, "transitions": list(transitions),
        }
        (root / "maps" / f"{map_id}.json").write_text(json.dumps(data), encoding="utf-8")

    def _screen(self, source_position=(3, 1), direction="east"):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        (root / "maps").mkdir()
        transition = {
            "id": "source_to_target", "from_tiles": [[3, 1]],
            "target_map_id": "target", "target_tiles": [[5, 6]],
            "direction": direction,
        }
        self._write_map(root, "source", 4, 3, [transition])
        self._write_map(root, "target", 8, 7)
        source = SimpleNamespace(location_id="source", name="Source", position=(0, 0))
        target = SimpleNamespace(location_id="target", name="Target", position=(99, 99))
        service = _TransitionService(source, target, root)
        service.actor.position = SimpleNamespace(x=source_position[0], y=source_position[1])
        return MainScreen(service), service

    def test_crosses_using_json_target_and_target_map_dimensions(self):
        screen, service = self._screen()
        self.assertTrue(screen._cross_boundary(service.actor, 1, 0))
        self.assertEqual(service.placed, ("hero", "target"))
        self.assertEqual(service.tile_position, ("hero", 5, 6))

    def test_transition_requires_matching_direction(self):
        screen, service = self._screen()
        self.assertTrue(screen._cross_boundary(service.actor, 0, 1))
        self.assertIsNone(service.placed)
        self.assertIn("geçiş", screen.message.lower())

    def test_transition_without_source_tile_match_does_not_move(self):
        screen, service = self._screen(source_position=(2, 1))
        self.assertTrue(screen._cross_boundary(service.actor, 1, 0))
        self.assertIsNone(service.placed)

    def test_missing_target_location_is_reported_without_moving_actor(self):
        screen, service = self._screen()
        service.world_map.locations.pop("target")
        self.assertTrue(screen._cross_boundary(service.actor, 1, 0))
        self.assertIsNone(service.placed)


if __name__ == "__main__":
    unittest.main()
