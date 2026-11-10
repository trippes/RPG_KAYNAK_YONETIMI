import unittest

from character import ItemDefinition
from resources import ResourceDefinition, ResourceUnit
from containers import (
    BreakProfile, BreakProfileRegistry, ContainerDefinition,
    ContainerInstance, ContainerManager, ContainerManagerError,
)


class TestContainerDomain(unittest.TestCase):
    def setUp(self):
        self.items = {
            "bread": ItemDefinition("bread", "Bread", weight=0.25, volume_liters=0.5, tags=("food",)),
            "ore": ItemDefinition("ore", "Ore", weight=2, volume_liters=1, tags=("raw", "ore")),
        }
        self.resources = {
            "wood": ResourceDefinition("wood", "Wood", ResourceUnit.ITEM, 1.5, 2, "raw", ("wood",)),
        }
        self.manager = ContainerManager(self.items, self.resources)
        self.manager.register_definition(ContainerDefinition(
            "chest", "Chest", empty_weight_kg=8, outer_volume_liters=40,
            max_contents_weight_kg=10, max_slots=3, max_contents_volume_liters=8,
            nesting_enabled=True, max_nesting_depth=2,
        ))
        self.manager.register_definition(ContainerDefinition(
            "bag", "Bag", empty_weight_kg=1, outer_volume_liters=5,
            max_contents_weight_kg=5, max_slots=4, max_contents_volume_liters=4,
            nesting_enabled=True, max_nesting_depth=2, container_tags=("portable",),
        ))
        self.manager.register(ContainerInstance("chest_01", "entity_chest_01", "chest"))
        self.manager.register(ContainerInstance("bag_01", "entity_bag_01", "bag"))

    def test_add_item_respects_all_three_capacity_dimensions(self):
        self.manager.add_item("chest_01", "bread", 4)
        with self.assertRaises(ContainerManagerError):
            self.manager.add_item("chest_01", "ore", 5)
        self.assertEqual(self.manager.inventory("chest_01").item_quantity("ore"), 0)

    def test_zero_capacity_rejects_content(self):
        self.manager.register_definition(ContainerDefinition("sealed", "Sealed", max_slots=0))
        self.manager.register(ContainerInstance("sealed_01", "entity_sealed", "sealed"))
        with self.assertRaises(ContainerManagerError):
            self.manager.add_item("sealed_01", "bread")

    def test_none_capacity_is_unlimited(self):
        self.manager.register_definition(ContainerDefinition("unlimited", "Unlimited"))
        self.manager.register(ContainerInstance("unlimited_01", "entity_unlimited", "unlimited"))
        self.manager.add_item("unlimited_01", "ore", 20)
        self.assertEqual(self.manager.inventory("unlimited_01").item_quantity("ore"), 20)

    def test_tag_policy_is_enforced(self):
        self.manager.register_definition(ContainerDefinition("food_box", "Food box", allowed_item_tags=("food",)))
        self.manager.register(ContainerInstance("food_01", "entity_food", "food_box"))
        with self.assertRaises(ContainerManagerError):
            self.manager.add_item("food_01", "ore")

    def test_nested_container_counts_as_one_slot_and_outer_volume(self):
        self.manager.contain("chest_01", "bag_01")
        usage = self.manager.usage("chest_01")
        self.assertEqual(usage.slots, 1)
        self.assertEqual(usage.volume_liters, 5)
        self.assertEqual(usage.weight_kg, 1)

    def test_nested_weight_includes_child_contents_once(self):
        self.manager.add_item("bag_01", "bread", 2)
        self.manager.contain("chest_01", "bag_01")
        self.assertAlmostEqual(self.manager.usage("chest_01").weight_kg, 1.5)

    def test_container_cannot_have_two_parents(self):
        self.manager.register_definition(ContainerDefinition("box", "Box"))
        self.manager.register(ContainerInstance("box_01", "entity_box", "box"))
        self.manager.contain("chest_01", "bag_01")
        with self.assertRaises(ContainerManagerError):
            self.manager.contain("box_01", "bag_01")

    def test_cycle_is_rejected(self):
        self.manager.contain("chest_01", "bag_01")
        with self.assertRaises(ContainerManagerError):
            self.manager.contain("bag_01", "chest_01")

    def test_parent_capacity_is_rechecked_when_child_changes(self):
        self.manager.register_definition(ContainerDefinition("small_parent", "Small", max_contents_weight_kg=1.4))
        self.manager.register(ContainerInstance("parent_01", "entity_parent", "small_parent"))
        self.manager.contain("parent_01", "bag_01")
        with self.assertRaises(ContainerManagerError):
            self.manager.add_item("bag_01", "bread", 2)
        self.assertEqual(self.manager.inventory("bag_01").item_quantity("bread"), 0)

    def test_nesting_depth_is_enforced_by_each_ancestor(self):
        self.manager.register_definition(ContainerDefinition("tiny_nest", "Tiny", max_nesting_depth=1))
        self.manager.register(ContainerInstance("tiny_01", "entity_tiny", "tiny_nest"))
        self.manager.contain("tiny_01", "bag_01")
        self.manager.register_definition(ContainerDefinition("inner", "Inner", max_nesting_depth=2))
        self.manager.register(ContainerInstance("inner_01", "entity_inner", "inner"))
        with self.assertRaises(ContainerManagerError):
            self.manager.contain("bag_01", "inner_01")

    def test_break_profile_initializes_instance_durability(self):
        profiles = BreakProfileRegistry((BreakProfile("wooden", 50),))
        manager = ContainerManager(break_profiles=profiles)
        manager.register_definition(ContainerDefinition("crate", "Crate", break_profile_id="wooden"))
        instance = manager.register(ContainerInstance("crate_01", "entity_crate", "crate"))
        self.assertEqual(instance.durability, 50)

    def test_duplicate_entity_capability_is_rejected(self):
        with self.assertRaises(ContainerManagerError):
            self.manager.register(ContainerInstance("another", "entity_chest_01", "bag"))

    def test_failed_capacity_addition_rolls_back_inventory(self):
        self.manager.add_item("chest_01", "bread", 4)
        before = self.manager.inventory("chest_01").item_snapshot()
        with self.assertRaises(ContainerManagerError):
            self.manager.add_item("chest_01", "bread", 20)
        self.assertEqual(self.manager.inventory("chest_01").item_snapshot(), before)


if __name__ == "__main__":
    unittest.main()
