import tempfile
import unittest
from pathlib import Path

from application import GameApplication, GameplayService
from combat import Combatant
from economy import Currency, Merchant, Money
from npc import Faction, NPC
from resources import Inventory, Quantity, ResourceType, ResourceUnit
from types import MappingProxyType


class TestPhaseBIntegration(unittest.TestCase):
    def setUp(self):
        app = GameApplication.create_default()
        app.dunya_olustur("Market", world_id="market")
        bundle = app.holder.current
        ore = ResourceType("ore")
        seller = Inventory(); buyer = Inventory()
        seller.add(ore, Quantity(5, ResourceUnit.ITEM))
        object.__setattr__(bundle, "inventories", MappingProxyType({"seller": seller, "buyer": buyer}))
        self.app = app
        self.service = GameplayService(app)
        self.ore = ore

    def test_faction_reputation_and_npc_relationship_are_connected(self):
        self.service.register_faction(Faction("guild", "Guild"))
        self.service.register_npc(NPC("smith", "Smith", faction_ids=("guild",)))
        self.assertEqual(self.service.change_reputation("guild", 30), 30)
        self.assertEqual(self.service.reputation("guild"), (30, "friendly"))
        relationship = self.service.relationship("hero", "smith")
        relationship.change(10, 5)
        self.assertEqual(self.service.relationship("hero", "smith").trust, 5)

    def test_merchant_partial_sale_and_offer_expiration(self):
        merchant = self.service.register_merchant(Merchant("shop", account_id="shop", inventory_id="seller"))
        self.assertEqual(merchant.merchant_id, "shop")
        self.service.credit("buyer", "gold", 20)
        self.service.publish_offer("ore", "shop", "seller", self.ore, 5, Money(2, Currency("gold")), expires_at=10)
        self.service.buy_offer("ore", "buyer", "buyer", quantity=2)
        self.assertEqual(self.app.holder.current.inventories["buyer"].get(self.ore).value, 2)
        self.assertEqual(self.app.holder.current.economy.market.get("ore").quantity, 3)
        self.service.expire_market_offers(10)
        self.assertIsNone(self.app.holder.current.economy.market.get("ore"))

    def test_encounter_initiative_turn_and_persistence(self):
        self.service.add_combatant(Combatant("a", 10))
        self.service.add_combatant(Combatant("b", 10))
        encounter = self.service.create_combat_encounter("enc", ("a", "b"), {"b": 5, "a": 1})
        self.assertEqual(encounter.active_combatant_id, "b")
        self.assertEqual(self.service.next_combat_turn("enc"), "a")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "encounter.json"
            self.service.save(path)
            self.service.load(path)
        restored = self.app.holder.current.combat.encounter("enc")
        self.assertEqual(restored.active_combatant_id, "a")
        self.assertEqual(restored.round_number, 1)


if __name__ == "__main__":
    unittest.main()
