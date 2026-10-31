import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from application import GameApplication, GameplayService
from economy import Currency, Money
from resources import Inventory, Quantity, ResourceType, ResourceUnit


class TestEconomyIntegration(unittest.TestCase):
    def setUp(self):
        application = GameApplication.create_default()
        application.dunya_olustur("Pazar", world_id="world_market")
        bundle = application.holder.current
        ore = ResourceType("ore")
        seller = Inventory()
        buyer = Inventory()
        seller.add(ore, Quantity(3, ResourceUnit.ITEM))
        object.__setattr__(bundle, "inventories", MappingProxyType({"seller": seller, "buyer": buyer}))
        self.application = application
        self.service = GameplayService(application)
        self.ore = ore

    def test_trade_moves_resource_and_money_atomically(self):
        self.service.credit("buyer", "gold", 20)
        offer = self.service.publish_offer(
            "ore-offer", "seller", "seller", self.ore, 2,
            Money(5, Currency("gold")),
        )
        trade = self.service.buy_offer("ore-offer", "buyer", "buyer")

        self.assertEqual(trade.total, Money(10, Currency("gold")))
        self.assertEqual(self.service.balance("buyer", "gold").amount, 10)
        self.assertEqual(self.service.balance("seller", "gold").amount, 10)
        self.assertEqual(self.application.holder.current.inventories["buyer"].get(self.ore).value, 2)
        self.assertIsNone(self.application.holder.current.economy.market.get("ore-offer"))

    def test_failed_trade_preserves_offer_and_state(self):
        self.service.publish_offer(
            "ore-offer", "seller", "seller", self.ore, 2,
            Money(5, Currency("gold")),
        )
        with self.assertRaises(ValueError):
            self.service.buy_offer("ore-offer", "buyer", "buyer")
        self.assertEqual(self.application.holder.current.inventories["seller"].get(self.ore).value, 3)
        self.assertIsNotNone(self.application.holder.current.economy.market.get("ore-offer"))

    def test_economy_round_trip_is_persisted(self):
        self.service.credit("buyer", "gold", 20)
        self.service.publish_offer(
            "ore-offer", "seller", "seller", self.ore, 2,
            Money(5, Currency("gold")),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "economy-save.json"
            self.service.save(path)
            self.service.load(path)

        bundle = self.application.holder.current
        self.assertEqual(bundle.economy.ledger.balance("buyer", Currency("gold")).amount, 20)
        self.assertIsNotNone(bundle.economy.market.get("ore-offer"))
        self.assertEqual(bundle.economy.market.get("ore-offer").inventory_id, "seller")


if __name__ == "__main__":
    unittest.main()
