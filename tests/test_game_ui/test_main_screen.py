import unittest
from types import SimpleNamespace

from game_ui.input import InputState
from game_ui.screens.main_screen import MainScreen


class FakeWorldMap:
    def __init__(self, location):
        self.location = location

    def get(self, location_id):
        return self.location if self.location.location_id == location_id else None


class FakeService:
    def __init__(self):
        self.actor = SimpleNamespace(
            actor_id="hero", world_id="world_1", location_id="village",
            position=SimpleNamespace(x=5, y=5),
        )
        self.placement = SimpleNamespace(
            object_id="chest_entity", x=6, y=5, width=1, height=1,
        )
        location = SimpleNamespace(location_id="village", landmarks=(), name="Village")
        self.bundle = SimpleNamespace(
            movement=SimpleNamespace(map_for=lambda _world_id: FakeWorldMap(location)),
            social=SimpleNamespace(npcs=SimpleNamespace(all=lambda: ())),
        )
        self.application = SimpleNamespace(
            holder=SimpleNamespace(current=self.bundle)
        )

    def state(self):
        return SimpleNamespace(actors=(self.actor,))

    def world_objects_for_location(self, _world_id, _location_id):
        return (self.placement,)

    def container_for_entity(self, entity_id):
        return "chest_01" if entity_id == "chest_entity" else None


class MainScreenContainerTargetTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeService()
        self.screen = MainScreen(self.service)
        self.screen.renderer_width = 960
        self.screen.renderer_height = 640

    def test_clicking_placed_container_selects_it_and_enter_opens_when_adjacent(self):
        origin_x, origin_y = self.screen._grid_origin()
        click_position = (origin_x + 6 * 16 + 4, origin_y + 5 * 16 + 4)
        self.screen.handle(InputState(
            mouse_pos=click_position,
            mouse_clicked=True,
            mouse_button_down=True,
        ))
        self.assertEqual(self.screen.selected_container_id, "chest_01")
        self.assertEqual(self.screen.handle(InputState(actions={"confirm"})), "container:chest_01")

    def test_container_cannot_be_opened_from_far_away(self):
        self.service.actor.position = SimpleNamespace(x=1, y=1)
        origin_x, origin_y = self.screen._grid_origin()
        click_position = (origin_x + 6 * 16 + 4, origin_y + 5 * 16 + 4)
        self.screen.handle(InputState(
            mouse_pos=click_position,
            mouse_clicked=True,
            mouse_button_down=True,
        ))
        self.assertIsNone(self.screen.handle(InputState(actions={"confirm"})))
        self.assertIn("yaklaşın", self.screen.message.lower())


if __name__ == "__main__":
    unittest.main()
