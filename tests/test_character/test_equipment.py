import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from application.content_pack import populate_demo_content
from character import EquipmentSlot, ItemDefinition


class TestEquipment(unittest.TestCase):
    def test_equipment_replaces_same_slot_and_applies_stats(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)
        service.equip_item(ids.hero_id, ids.inventory_id, "iron_sword")
        self.assertEqual(service.equipment(ids.hero_id), {"main_hand": "iron_sword"})
        self.assertEqual(service.actor_stats(ids.hero_id)["weapon_damage"], 4)
        self.assertEqual(service.inventory(ids.inventory_id).items[0][0], "iron_helmet")

    def test_equipment_survives_save_load_with_item_catalog(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)
        service.equip_item(ids.hero_id, ids.inventory_id, "leather_armor")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "equipment.json"
            service.save(path)
            service.load(path)
        self.assertEqual(service.equipment(ids.hero_id), {"chest": "leather_armor"})
        self.assertEqual(service.item("leather_armor").slot, EquipmentSlot.CHEST)

    def test_non_equipment_item_is_rejected(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)
        bundle = application.holder.current
        object.__setattr__(
            bundle,
            "items",
            {**bundle.items, "bread_item": ItemDefinition("bread_item", "Ekmek")},
        )
        bundle.inventories[ids.inventory_id].add_item("bread_item")
        with self.assertRaises(ValueError):
            service.equip_item(ids.hero_id, ids.inventory_id, "bread_item")


if __name__ == "__main__":
    unittest.main()
