import unittest
from types import SimpleNamespace

from application import GameplayServiceError
from game_ui.input import InputState
from game_ui.screens.container_screen import ContainerScreen


class FakeContainerService:
    def __init__(self):
        self.actor = SimpleNamespace(actor_id="hero", inventory_id="player")
        self.lock = None
        self.transfers = []
        self.view = SimpleNamespace(
            container_id="chest_01", name="Wooden chest",
            items=(("apple", 2), ("potion", 5)),
        )

    def state(self):
        return SimpleNamespace(actors=(self.actor,))

    def container_lock_state(self, _container_id):
        return self.lock

    def open_container(self, _actor_id, _inventory_id, _container_id):
        if self.lock is not None and (self.lock.locked or self.lock.jammed):
            raise GameplayServiceError("locked")
        return self.view

    def inventory(self, _inventory_id):
        return SimpleNamespace(items=())

    def item(self, item_id):
        return SimpleNamespace(name=item_id.capitalize(), tags=("potion", "consumable") if item_id == "potion" else (), category="potion" if item_id == "potion" else "misc")

    def transfer_actor_item_from_container(self, *args):
        self.transfers.append(("from_container", *args))

    def transfer_actor_item_to_container(self, *args):
        self.transfers.append(("to_container", *args))

    def resolve_lockpick(self, *args, **kwargs):
        return SimpleNamespace(attempted=True, success=True, roll=17, modifier=3, total=20, difficulty_class=18, message="opened")

    def resolve_force_lock(self, *args, **kwargs):
        return SimpleNamespace(attempted=True, success=False, roll=8, modifier=1, total=9, difficulty_class=15, message="failed")

    def unlock_with_key(self, *args):
        self.lock.locked = False
        return True


class ContainerScreenTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeContainerService()
        self.screen = ContainerScreen(self.service)
        self.screen.set_container("chest_01")

    def test_external_inventory_drop_transfers_stack_into_container(self):
        self.assertTrue(self.screen.receive_external_item("health_potion", 3))
        self.assertEqual(
            self.service.transfers,
            [("to_container", "hero", "player", "chest_01", "health_potion", 3)],
        )
        self.assertIn("sandığa aktarıldı", self.screen.message)

    def test_confirm_takes_full_selected_stack(self):
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(self.service.transfers[0][3:], ("apple", 2))

    def test_dragging_item_transfers_full_stack_on_release(self):
        self.screen._row_rects = (SimpleNamespace(collidepoint=lambda pos: True),)
        self.screen.handle(InputState(mouse_pos=(10, 10), mouse_clicked=True))
        self.assertTrue(self.screen.pointer_capture)
        self.screen.handle(InputState(mouse_pos=(500, 500), mouse_button_up=True))
        self.assertFalse(self.screen.pointer_capture)
        self.assertEqual(self.service.transfers[0][3:], ("apple", 2))

    def test_take_all_transfers_each_stack(self):
        self.screen._take_all_rect = SimpleNamespace(collidepoint=lambda pos: True)
        self.screen.handle(InputState(mouse_pos=(1, 1), mouse_clicked=True))
        self.assertEqual([call[3:] for call in self.service.transfers], [("apple", 2), ("potion", 5)])
        self.assertIn("7 eşya", self.screen.message)


    def test_loot_grid_starts_with_six_by_four_slots_and_grows_by_rows(self):
        self.assertEqual(self.screen._visible_rows(0), 4)
        self.assertEqual(self.screen.COLUMNS, 6)
        self.assertEqual(self.screen._visible_rows(24), 4)
        self.assertEqual(self.screen._visible_rows(25), 5)
        self.assertEqual(self.screen._max_scroll(25), 1)

    def test_category_filter_keeps_potion_items(self):
        entries = self.screen._filtered_entries(self.service.view)
        self.assertEqual([entry[0] for entry in entries if entry[3] == "potion"], ["potion"])
        self.screen.category = "potion"
        filtered = self.screen._filtered_entries(self.service.view)
        self.assertEqual([entry[0] for entry in filtered], ["potion"])

    def test_search_filters_by_item_name(self):
        self.screen.search_text = "pot"
        filtered = self.screen._filtered_entries(self.service.view)
        self.assertEqual([entry[0] for entry in filtered], ["potion"])

    def test_locked_container_uses_matching_key_action(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False,
            lock_id="chest_lock_01", required_key_id="chest_key",
            lockpick_profile_id=None, force_profile_id=None,
        )
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertIn("anahtarla açıldı", self.screen.message)

    def test_lockpick_action_reports_d20_result(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False, lock_id="chest_lock",
            required_key_id=None, lockpick_profile_id="pick", force_profile_id=None,
            lockpick_allowed_tool_tags=(), force_required_tool_tags=(),
        )
        self.screen.handle(InputState(actions={"lockpick"}))
        self.assertIn("d20: 17", self.screen.message)

    def test_force_action_reports_failed_d20_check(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False, lock_id="chest_lock",
            required_key_id=None, lockpick_profile_id=None, force_profile_id="force",
            lockpick_allowed_tool_tags=(), force_required_tool_tags=(),
        )
        self.screen.handle(InputState(actions={"force_lock"}))
        self.assertIn("BAŞARISIZ", self.screen.message)

    def test_missing_actor_inventory_prevents_transfer(self):
        self.service.actor.inventory_id = None
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(self.service.transfers, [])
        self.assertIn("envanteri", self.screen.message.lower())


if __name__ == "__main__":
    unittest.main()
