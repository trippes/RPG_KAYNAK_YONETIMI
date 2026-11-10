import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from application import GameApplication, GameplayService
from application.content_pack import populate_opening_content
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
            "inventory_village", 1, self.catalog, visible_products=2,
        ))
        self.market.register_profile(MarketProfile(
            "inn", "village", "innkeeper", "merchant_inn",
            "inventory_inn", 1,
            (self.catalog[2], self.catalog[3], self.catalog[0]),
            visible_products=2,
        ))

    def test_market_offers_are_scoped_to_their_market(self):
        village = self.market.restock("village", Inventory(), 0)
        inn = self.market.restock("inn", Inventory(), 0)

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
        unchanged = self.market.restock("village", inventory, 86_399)
        second = self.market.restock("village", inventory, 86_400)

        self.assertEqual(first, unchanged)
        self.assertNotEqual(
            {offer.resource_type for offer in first},
            {offer.resource_type for offer in second},
        )
        self.assertTrue(all(offer.expires_at == 172_800 for offer in second))

    def test_market_profiles_and_offer_scope_survive_economy_round_trip(self):
        inventory = Inventory()
        self.market.restock("village", inventory, 0)
        self.market.record_purchase("village", ResourceType("wood"), 2)
        economy = Economy(market=self.market)
        snapshot = economy.snapshot()
        restored_ledger, restored_market, _merchants = snapshot.from_dict(
            snapshot.to_dict()
        ).restore()

        self.assertEqual(restored_market.profile("village").location_id, "village")
        self.assertEqual(restored_market.profile("village").last_restock_cycle, 0)
        self.assertEqual(restored_market.profile("village").demand["wood"], 2)
        self.assertEqual(restored_market.offers("village"), self.market.offers("village"))
        self.assertEqual(restored_ledger.accounts(), ())

    def test_demand_increases_the_next_restock_price(self):
        demanded = Market()
        baseline = Market()
        gold = Currency("gold")
        price_catalog = (
            MarketCatalogEntry(ResourceType("wood"), Money(100, gold), 2, 5),
            *self.catalog[1:],
        )
        for market in (demanded, baseline):
            market.register_profile(MarketProfile(
                "market", "village", "trader", "merchant", "inventory",
                1, price_catalog, visible_products=4,
            ))
        demanded.restock("market", Inventory(), 0)
        demanded.record_purchase("market", ResourceType("wood"), 2)
        demanded.restock("market", Inventory(), 86_400)
        baseline.restock("market", Inventory(), 0)
        baseline.restock("market", Inventory(), 86_400)

        demanded_wood = next(
            offer for offer in demanded.offers("market")
            if offer.resource_type == ResourceType("wood")
        )
        baseline_wood = next(
            offer for offer in baseline.offers("market")
            if offer.resource_type == ResourceType("wood")
        )
        self.assertGreater(demanded_wood.unit_price.amount, baseline_wood.unit_price.amount)

    def test_gameplay_service_restock_and_purchase_use_selected_market(self):
        application = GameApplication.create_default()
        service, _ids = populate_opening_content(application)
        bundle = application.holder.current
        inventories = dict(bundle.inventories)
        inventories["player"] = Inventory()
        object.__setattr__(bundle, "inventories", MappingProxyType(inventories))
        profile = MarketProfile(
            "village", "village", "trader_village", "merchant_village",
            "inventory_village", 1, self.catalog, visible_products=2,
        )
        service.register_market_profile(profile)
        service.credit("hero", "gold", 100)

        offers = service.market_offers("village")
        trade = service.buy_offer(offers[0].offer_id, "hero", "player", quantity=1)

        self.assertEqual(trade.quantity.value, 1)
        self.assertEqual(service.market_offers("village")[0].market_id, "village")
        self.assertGreater(service.balance("merchant_village", "gold").amount, 0)

        with tempfile.TemporaryDirectory() as directory:
            save_path = Path(directory) / "market-save.json"
            service.save(save_path)
            service.load(save_path)

        restored = application.holder.current
        merchant = restored.economy.merchants["merchant_village"]
        self.assertIs(
            merchant.inventory,
            restored.inventories["inventory_village"],
        )
        self.assertEqual(
            restored.economy.market.profile("village").last_restock_cycle,
            0,
        )


if __name__ == "__main__":
    unittest.main()
