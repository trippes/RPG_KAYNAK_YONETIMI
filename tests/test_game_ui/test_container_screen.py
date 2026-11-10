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
        self.unlocked = []
        self.view = SimpleNamespace(
            container_id="chest_01",
            name="Wooden chest",
            items=(("apple", 2),),
            contents_weight_kg=1.0,
            contents_slots=1,
            contents_volume_liters=0.5,
            max_contents_weight_kg=10.0,
            max_slots=10,
            max_contents_volume_liters=8.0,
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
        return SimpleNamespace(items=(("bread", 3),))

    def item(self, item_id):
        return SimpleNamespace(name=item_id.capitalize())

    def transfer_actor_item_from_container(self, *args):
        self.transfers.append(("from", args))

    def transfer_actor_item_to_container(self, *args):
        self.transfers.append(("to", args))

    def unlock_with_key(self, *args):
        self.unlocked.append(args)
        self.lock.locked = False
        return True


class ContainerScreenTests(unittest.TestCase):
    def setUp(self):
        self.service = FakeContainerService()
        self.screen = ContainerScreen(self.service)
        self.screen.set_container("chest_01")

    def test_confirm_transfers_selected_container_item_to_player(self):
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(len(self.service.transfers), 1)
        self.assertEqual(self.service.transfers[0][0], "from")
        self.assertEqual(self.service.transfers[0][1][0], "hero")
        self.assertEqual(self.service.transfers[0][1][1], "player")
        self.assertEqual(self.service.transfers[0][1][3], "apple")

    def test_switching_side_then_confirm_transfers_player_item_to_container(self):
        self.screen.handle(InputState(actions={"right"}))
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(self.service.transfers[0][0], "to")
        self.assertEqual(self.service.transfers[0][1][3], "bread")

    def test_locked_container_uses_matching_key_action(self):
        self.service.lock = SimpleNamespace(
            locked=True, jammed=False, broken=False,
            lock_id="chest_lock_01", required_key_id="chest_key",
            lockpick_profile_id=None, force_profile_id=None,
        )
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(
            self.service.unlocked,
            [("hero", "player", "chest_lock_01", "chest_key")],
        )
        self.assertIn("anahtarla açıldı", self.screen.message)

    def test_missing_actor_inventory_is_reported_without_transfer(self):
        self.service.actor.inventory_id = None
        self.screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(self.service.transfers, [])
        self.assertIn("envanteri", self.screen.message.lower())


if __name__ == "__main__":
    unittest.main()
