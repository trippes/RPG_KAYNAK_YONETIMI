import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from game_ui.renderer import Renderer
from game_ui.screens.currency_exchange_screen import CurrencyExchangeScreen
from game_ui.screens.inventory_screen import InventoryScreen
from game_ui.screens.market_screen import MarketScreen
from game_ui.screens.production_screen import ProductionScreen


class _State:
    mouse_clicked = False
    mouse_pos = None
    mouse_motion = False
    mouse_button_up = False

    @staticmethod
    def pressed(action):
        return action == "equip"


class _Service:
    player_actor_id = "traveler_actor"
    player_inventory_id = "traveler_bag"
    player_account_id = "traveler_wallet"

    def __init__(self):
        self.inventory_calls = []
        self.balance_calls = []
        self.equip_calls = []
        self.exchange_calls = []
        self.buy_calls = []

    def inventory(self, inventory_id):
        self.inventory_calls.append(inventory_id)
        return SimpleNamespace(
            items=(("iron_sword", 1),),
            stocks=(("wood", 4, "item"),),
        )

    @staticmethod
    def item(item_id):
        return SimpleNamespace(item_id=item_id, name="Iron sword")

    def equip_item(self, actor_id, inventory_id, item_id):
        self.equip_calls.append((actor_id, inventory_id, item_id))

    def balance(self, account_id, currency):
        self.balance_calls.append((account_id, currency))
        return SimpleNamespace(amount=100)

    def exchange_currency(self, account_id, source, target, amount):
        self.exchange_calls.append((account_id, source, target, amount))

    def buy_offer(self, offer_id, actor_id, inventory_id, quantity=None, *, buyer_account_id=None):
        self.buy_calls.append(
            (offer_id, actor_id, inventory_id, quantity, buyer_account_id)
        )


class TestPlayerEconomyIdentity(unittest.TestCase):
    def setUp(self):
        self.service = _Service()

    def test_inventory_screen_uses_configured_inventory_and_actor(self):
        screen = InventoryScreen(self.service)
        self.assertEqual(screen.inventory_id, "traveler_bag")

        screen.handle(_State())
        self.assertEqual(
            self.service.equip_calls,
            [("traveler_actor", "traveler_bag", "iron_sword")],
        )
        self.assertEqual(InventoryScreen(self.service, "shared_chest").inventory_id, "shared_chest")

    def test_production_screen_uses_configured_inventory(self):
        screen = ProductionScreen(self.service)
        self.assertEqual(screen.inventory_id, "traveler_bag")
        self.assertEqual(
            ProductionScreen(self.service, "workshop_store").inventory_id,
            "workshop_store",
        )
        self.assertEqual(screen._inventory_stocks()["wood"], (4, "item"))
        self.assertEqual(self.service.inventory_calls[-1], "traveler_bag")

    def test_market_purchase_passes_actor_inventory_and_account_separately(self):
        screen = MarketScreen(self.service)
        offer = SimpleNamespace(offer_id="wood-offer", resource_type="wood")
        screen._buy((offer,))
        self.assertEqual(
            self.service.buy_calls,
            [("wood-offer", "traveler_actor", "traveler_bag", 1, "traveler_wallet")],
        )

    def test_currency_exchange_uses_configured_account(self):
        screen = CurrencyExchangeScreen(self.service)
        self.assertEqual(screen._balance("bronze"), 100)
        screen._exchange(0)
        self.assertEqual(self.service.balance_calls[0][0], "traveler_wallet")
        self.assertEqual(
            self.service.exchange_calls,
            [("traveler_wallet", "bronze", "silver", 60)],
        )

    def test_renderer_wallet_uses_account_id(self):
        renderer = Renderer.__new__(Renderer)
        renderer.text = Mock()
        renderer.text_width = Mock(side_effect=lambda value: len(str(value)))
        renderer.coin_icon = Mock()

        renderer.wallet(self.service)
        self.assertEqual(
            [account for account, _currency in self.service.balance_calls],
            ["traveler_wallet", "traveler_wallet", "traveler_wallet"],
        )

    def test_renderer_resource_bar_uses_inventory_id(self):
        renderer = Renderer.__new__(Renderer)
        renderer.width = 960
        renderer.height = 640
        renderer.pg = SimpleNamespace(Rect=Mock(side_effect=lambda *args: args))
        renderer.panel = Mock()
        renderer.text = Mock()
        renderer.text_width = Mock(side_effect=lambda value: len(str(value)))
        renderer.resource_icon = Mock()

        renderer.resource_bar(self.service)
        self.assertEqual(self.service.inventory_calls[-1], "traveler_bag")

    def test_renderer_hud_uses_actor_and_account_independently(self):
        self.service.state = Mock(return_value=SimpleNamespace(simulation_tick=0))

        def actor_stats(actor_id):
            self.assertEqual(actor_id, "traveler_actor")
            return {
                "name": "Traveler",
                "current_hit_points": 10,
                "max_hit_points": 10,
            }

        self.service.actor_stats = actor_stats
        self.service.application = SimpleNamespace(
            holder=SimpleNamespace(
                current=SimpleNamespace(
                    session=SimpleNamespace(
                        worlds=SimpleNamespace(
                            get_active=Mock(return_value=SimpleNamespace(name="Test world"))
                        )
                    )
                )
            )
        )
        renderer = Renderer.__new__(Renderer)
        renderer.width = 960
        renderer.nav_current = None
        renderer.pg = SimpleNamespace(Rect=Mock(side_effect=lambda *args: args))
        renderer.fit_text = Mock(side_effect=lambda value, *args, **kwargs: value)
        renderer.text_width = Mock(side_effect=lambda value: len(str(value)) * 8)
        renderer.text = Mock()
        renderer.panel = Mock()
        renderer.bar = Mock()
        renderer.coin_icon = Mock()
        renderer.calendar = Mock()

        renderer.hud(self.service)
        self.assertIn(("traveler_wallet", "gold"), self.service.balance_calls)


if __name__ == "__main__":
    unittest.main()
