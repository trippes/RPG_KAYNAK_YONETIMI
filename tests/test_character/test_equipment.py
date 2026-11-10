
import tempfile
import unittest
from pathlib import Path
from types import MappingProxyType

from application import GameApplication, GameplayService
from character import (
    CharacterClass,
    CharacterFactory,
    EquipmentSlot,
    ItemDefinition,
    Race,
)
from resources import Inventory


class TestEquipment(unittest.TestCase):
    def setUp(self):
        self.application = GameApplication.create_default()
        self.application.dunya_olustur("Test World", world_id="test_world")

        factory = CharacterFactory(
            {"human": Race("human", "İnsan")},
            {"fighter": CharacterClass("fighter", "Savaşçı", hit_points=10)},
        )
        self.application.karakter_olustur(
            factory, "hero", "Arin", "human", "fighter"
        )

        bundle = self.application.holder.current

        self.items = {
            "iron_sword": ItemDefinition(
                "iron_sword",
                "Demir Kılıç",
                slot=EquipmentSlot.MAIN_HAND,
                damage=4,
            ),
            "iron_helmet": ItemDefinition(
                "iron_helmet",
                "Demir Miğfer",
                slot=EquipmentSlot.HEAD,
                defense=2,
            ),
            "leather_armor": ItemDefinition(
                "leather_armor",
                "Deri Zırh",
                slot=EquipmentSlot.CHEST,
                defense=3,
            ),
            "bread_item": ItemDefinition("bread_item", "Ekmek"),
        }

        object.__setattr__(
            bundle, "items", MappingProxyType(dict(self.items))
        )
        bundle.characters["hero"].bind_item_catalog(bundle.items)

        inventory = Inventory()
        inventory.add_item("iron_sword")
        inventory.add_item("iron_helmet")
        inventory.add_item("leather_armor")
        inventory.add_item("bread_item")

        object.__setattr__(
            bundle,
            "inventories",
            MappingProxyType({"main": inventory}),
        )

        self.service = GameplayService(self.application)

    def test_equipment_replaces_same_slot_and_applies_stats(self):
        self.service.equip_item("hero", "main", "iron_sword")

        self.assertEqual(
            self.service.equipment("hero"),
            {"main_hand": "iron_sword"},
        )
        self.assertEqual(
            self.service.actor_stats("hero")["weapon_damage"], 4
        )
        inventory = self.service.inventory("main")
        remaining_items = dict(inventory.items)
        self.assertEqual(remaining_items.get("iron_helmet", 0), 1)
        self.assertEqual(remaining_items.get("leather_armor", 0), 1)
        self.assertEqual(remaining_items.get("bread_item", 0), 1)
        self.assertEqual(remaining_items.get("iron_sword", 0), 0)

    def test_equipment_survives_save_load_with_item_catalog(self):
        self.service.equip_item("hero", "main", "leather_armor")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "equipment.json"
            self.service.save(path)
            self.service.load(path)

        self.assertEqual(
            self.service.equipment("hero"),
            {"chest": "leather_armor"},
        )
        self.assertEqual(
            self.service.item("leather_armor").slot,
            EquipmentSlot.CHEST,
        )

    def test_default_attribute_bonuses_are_independent_and_immutable(self):
        first = ItemDefinition("first", "Birinci")
        second = ItemDefinition("second", "İkinci")

        self.assertIsNot(first.attribute_bonuses, second.attribute_bonuses)
        self.assertEqual(dict(first.attribute_bonuses), {})
        with self.assertRaises(TypeError):
            first.attribute_bonuses["strength"] = 1

    def test_non_equipment_item_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.equip_item("hero", "main", "bread_item")

    def test_equipped_item_without_catalog_fails_loudly(self):
        character = self.application.holder.current.characters["hero"]
        character.equip(self.items["iron_sword"])
        with self.assertRaisesRegex(ValueError, "missing from the catalog"):
            character.bind_item_catalog({})
        del character._item_catalog
        with self.assertRaises(RuntimeError):
            character.weapon_damage

    def test_item_catalog_rejects_mismatched_registry_keys(self):
        character = self.application.holder.current.characters["hero"]
        with self.assertRaisesRegex(ValueError, "catalog key"):
            character.bind_item_catalog({"wrong_id": self.items["iron_sword"]})


if __name__ == "__main__":
    unittest.main()
