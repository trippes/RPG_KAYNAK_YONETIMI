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
            position=SimpleNamespace(x=5, y=5), inventory_id="player",
        )
        self.placement = SimpleNamespace(
            object_id="chest_entity", x=6, y=5, width=1, height=1,
        )
        self.lock = SimpleNamespace(
            locked=False, jammed=False, broken=False,
            lock_id="chest_lock", required_key_id=None,
            lockpick_profile_id=None, force_profile_id=None,
            lockpick_allowed_tool_tags=("lockpick",), force_required_tool_tags=(),
        )
        self.inventory_items = ()
        self.unlocked_with_key = False
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

    def container_lock_state(self, _container_id):
        return self.lock

    def inventory(self, _inventory_id):
        return SimpleNamespace(items=self.inventory_items)

    def unlock_with_key(self, _actor_id, _inventory_id, _lock_id, _key_id):
        if not any(item_id == _key_id and quantity > 0 for item_id, quantity in self.inventory_items):
            return False
        self.lock.locked = False
        self.unlocked_with_key = True
        return True


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


    def test_right_clicking_unlocked_chest_opens_context_actions(self):
        origin_x, origin_y = self.screen._grid_origin()
        position = (origin_x + 6 * 16 + 4, origin_y + 5 * 16 + 4)
        self.screen.handle(InputState(mouse_pos=position, mouse_right_clicked=True))
        self.assertTrue(self.screen.context_menu_open)
        self.assertEqual(
            self.screen.context_menu_actions,
            (("open", "Aç"), ("inspect", "İncele")),
        )

    def test_locked_chest_with_key_offers_open_action(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False,
            lock_id="chest_lock", required_key_id="chest_key",
            lockpick_profile_id="pick_profile", force_profile_id="force_profile",
            lockpick_allowed_tool_tags=("lockpick",), force_required_tool_tags=(),
        )
        self.service.inventory_items = (("chest_key", 1),)
        origin_x, origin_y = self.screen._grid_origin()
        position = (origin_x + 6 * 16 + 4, origin_y + 5 * 16 + 4)
        self.screen.handle(InputState(mouse_pos=position, mouse_right_clicked=True))
        self.assertEqual(
            self.screen.context_menu_actions,
            (("open", "Aç"), ("force", "Kilidi zorla"), ("inspect", "İncele")),
        )

    def test_locked_chest_without_key_offers_unlock_action(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False,
            lock_id="chest_lock", required_key_id="chest_key",
            lockpick_profile_id="pick_profile", force_profile_id="force_profile",
            lockpick_allowed_tool_tags=("lockpick",), force_required_tool_tags=(),
        )
        origin_x, origin_y = self.screen._grid_origin()
        position = (origin_x + 6 * 16 + 4, origin_y + 5 * 16 + 4)
        self.screen.handle(InputState(mouse_pos=position, mouse_right_clicked=True))
        self.assertEqual(
            self.screen.context_menu_actions,
            (("unlock", "Kilidi Aç"), ("force", "Kilidi zorla"), ("inspect", "İncele")),
        )

    def test_open_action_uses_inventory_key_and_opens_container(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False,
            lock_id="chest_lock", required_key_id="chest_key",
            lockpick_profile_id="pick_profile", force_profile_id=None,
            lockpick_allowed_tool_tags=("lockpick",), force_required_tool_tags=(),
        )
        self.service.inventory_items = (("chest_key", 1),)
        self.screen.selected_container_id = "chest_01"
        self.assertEqual(
            self.screen._execute_container_action("open"),
            "container:chest_01",
        )
        self.assertTrue(self.service.unlocked_with_key)
        self.assertFalse(self.service.lock.locked)

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
