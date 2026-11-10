import unittest

from economy import (
    Currency, Economy, Market, MarketCatalogEntry, MarketProfile, Money,
)
from resources import Inventory, ResourceType


class TestLocationMarket(unittest.TestCase):
    def setUp(self):
        gold = Currency("gold")
        self.catalog = (
            MarketCatalogEntry(ResourceType("wood"), Money(3, gold), 2, 5),
            MarketCatalogEntry(ResourceType("iron_ore"), Money(8, gold), 1, 3),
            MarketCatalogEntry(ResourceType("bread"), Money(4, gold), 2, 6),
            MarketCatalogEntry(ResourceType("water"), Money(2, gold), 3, 7),
        )
        self.market = Market()
        self.market.register_profile(MarketProfile(
            "village", "village", "trader_village", "merchant_village",
            "inventory_village", 10, self.catalog, visible_products=2,
        ))
        self.market.register_profile(MarketProfile(
            "inn", "village", "innkeeper", "merchant_inn",
            "inventory_inn", 10,
            (self.catalog[2], self.catalog[3], self.catalog[0]),
            visible_products=2,
        ))

    def test_market_offers_are_scoped_to_their_market(self):
        village_inventory = Inventory()
        inn_inventory = Inventory()
        village = self.market.restock("village", village_inventory, 0)
        inn = self.market.restock("inn", inn_inventory, 0)

        self.assertEqual({offer.market_id for offer in village}, {"village"})
        self.assertEqual({offer.market_id for offer in inn}, {"inn"})
        self.assertEqual(self.market.offers("village"), village)
        self.assertEqual(self.market.offers("inn"), inn)
        self.assertNotEqual(
            {offer.resource_type for offer in village},
            {offer.resource_type for offer in inn},
        )

    def test_stock_is_stable_within_cycle_and_rotates_on_restock(self):
        inventory = Inventory()
        first = self.market.restock("village", inventory, 0)
        unchanged = self.market.restock("village", inventory, 9)
        second = self.market.restock("village", inventory, 10)

        self.assertEqual(first, unchanged)
        self.assertNotEqual(
            {offer.resource_type for offer in first},
            {offer.resource_type for offer in second},
        )
        self.assertTrue(all(offer.expires_at == 20 for offer in second))

    def test_market_profiles_and_offer_scope_survive_economy_round_trip(self):
        inventory = Inventory()
        self.market.restock("village", inventory, 0)
        economy = Economy(market=self.market)
        snapshot = economy.snapshot()
        restored_ledger, restored_market, _merchants = snapshot.from_dict(
            snapshot.to_dict()
        ).restore()

        self.assertEqual(restored_market.profile("village").location_id, "village")
        self.assertEqual(restored_market.profile("village").last_restock_cycle, 0)
        self.assertEqual(restored_market.offers("village"), self.market.offers("village"))
        self.assertEqual(restored_ledger.accounts(), ())


if __name__ == "__main__":
    unittest.main()
