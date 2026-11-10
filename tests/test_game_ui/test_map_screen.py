"""Tests for the world map window."""

import unittest
from types import SimpleNamespace

from game_ui.input import InputState
from game_ui.screens.map_screen import MapScreen


class MapScreenTests(unittest.TestCase):
    def test_confirming_another_location_explains_world_map_is_read_only(self):
        locations = [
            SimpleNamespace(location_id="village", position=(0, 0), name="Köy", location_type="settlement"),
            SimpleNamespace(location_id="forest", position=(100, 0), name="Orman", location_type="wilderness"),
        ]
        world_map = SimpleNamespace(
            locations=lambda: tuple(locations),
            get=lambda location_id: next((item for item in locations if item.location_id == location_id), None),
            neighbors=lambda _location_id: (),
        )
        actor = SimpleNamespace(location_id="village", world_id="world")
        service = SimpleNamespace(
            state=lambda: SimpleNamespace(actors=(actor,)),
            application=SimpleNamespace(
                holder=SimpleNamespace(
                    current=SimpleNamespace(
                        movement=SimpleNamespace(map_for=lambda _world_id: world_map)
                    )
                )
            ),
        )
        screen = MapScreen(service)
        screen._context()
        screen.selected = 1

        screen.handle(InputState(actions={"confirm"}))

        self.assertIn("harita penceresini kapatıp dünya ekranını kullan", screen.message)
        self.assertNotIn("Yerel Harita", screen.message)


if __name__ == "__main__":
    unittest.main()
