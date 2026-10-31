import unittest
from core.time import Tick
from resources import (
    Inventory,
    Quantity,
    ResourceNodeError,
    ResourceNodeInsufficientError,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


class TestWorldResourceNode(unittest.TestCase):
    def setUp(self):
        self.ore = ResourceType("ore")
        self.node = WorldResourceNode(
            "node-1", "world-1", self.ore,
            Quantity(5, ResourceUnit.KG),
            Quantity(10, ResourceUnit.KG),
            Quantity(2, ResourceUnit.KG),
        )

    def test_valid_and_rejects_invalid_configuration(self):
        self.assertEqual(self.node.current_quantity, Quantity(5, ResourceUnit.KG))
        with self.assertRaises(ValueError):
            WorldResourceNode(" ", "world-1", self.ore, Quantity(1, ResourceUnit.KG), Quantity(2, ResourceUnit.KG), Quantity(1, ResourceUnit.KG))
        with self.assertRaises(ResourceNodeError):
            WorldResourceNode("n", "w", self.ore, Quantity(3, ResourceUnit.KG), Quantity(2, ResourceUnit.KG), Quantity(1, ResourceUnit.KG))
        with self.assertRaises(ResourceNodeError):
            WorldResourceNode("n", "w", self.ore, Quantity(1, ResourceUnit.KG), Quantity(2, ResourceUnit.ITEM), Quantity(1, ResourceUnit.KG))
        with self.assertRaises(ValueError):
            WorldResourceNode("n", "w", self.ore, Quantity(1, ResourceUnit.KG), Quantity(2, ResourceUnit.KG), Quantity(1, ResourceUnit.KG), -1)

    def test_regeneration_is_tick_based_and_idempotent(self):
        self.node.regenerate_to(Tick(2))
        self.assertEqual(self.node.quantity, Quantity(9, ResourceUnit.KG))
        self.node.regenerate_to(2)
        self.assertEqual(self.node.quantity, Quantity(9, ResourceUnit.KG))
        self.node.regenerate_to(10)
        self.assertEqual(self.node.quantity, Quantity(10, ResourceUnit.KG))
        with self.assertRaises(ValueError):
            self.node.regenerate_to(9)

    def test_zero_rate_and_capacity_are_deterministic(self):
        node = WorldResourceNode("n", "w", self.ore, Quantity(0, ResourceUnit.KG), Quantity(0, ResourceUnit.KG), Quantity(0, ResourceUnit.KG))
        self.assertEqual(node.regenerate_to(100), Quantity(0, ResourceUnit.KG))

    def test_extraction_is_atomic(self):
        inventory = Inventory()
        self.node.extract_to(inventory, Quantity(2, ResourceUnit.KG))
        self.assertEqual(self.node.quantity, Quantity(3, ResourceUnit.KG))
        self.assertEqual(inventory.get(self.ore), Quantity(2, ResourceUnit.KG))
        before = (self.node.quantity, inventory.snapshot())
        with self.assertRaises(ResourceNodeInsufficientError):
            self.node.extract_to(inventory, Quantity(9, ResourceUnit.KG))
        self.assertEqual((self.node.quantity, inventory.snapshot()), before)

    def test_extraction_rejects_zero_and_unit_mismatch(self):
        inventory = Inventory()
        before = (self.node.quantity, inventory.snapshot())
        with self.assertRaises(ResourceNodeError):
            self.node.extract_to(inventory, Quantity(0, ResourceUnit.KG))
        with self.assertRaises(ResourceNodeError):
            self.node.extract_to(inventory, Quantity(1, ResourceUnit.LITER))
        self.assertEqual((self.node.quantity, inventory.snapshot()), before)

    def test_inventory_failure_preserves_node(self):
        class FailingInventory(Inventory):
            def add(self, resource_type, quantity):
                raise RuntimeError("write failed")

        inventory = FailingInventory()
        before = self.node.quantity
        with self.assertRaises(RuntimeError):
            self.node.extract_to(inventory, Quantity(1, ResourceUnit.KG))
        self.assertEqual(self.node.quantity, before)
        self.assertTrue(inventory.is_empty())


class TestWorldResourceNodeManager(unittest.TestCase):
    def make_node(self, node_id, world_id):
        return WorldResourceNode(
            node_id, world_id, ResourceType("ore"),
            Quantity(2, ResourceUnit.ITEM), Quantity(5, ResourceUnit.ITEM), Quantity(1, ResourceUnit.ITEM),
        )

    def test_registry_lookup_grouping_and_duplicates(self):
        manager = WorldResourceNodeManager()
        first = self.make_node("b", "w1")
        second = self.make_node("a", "w1")
        third = self.make_node("c", "w2")
        manager.add(first); manager.add(second); manager.add(third)
        self.assertIs(manager.get("b"), first)
        self.assertEqual(tuple(node.node_id for node in manager.for_world("w1")), ("a", "b"))
        self.assertEqual(tuple(node.node_id for node in manager.for_world("w2")), ("c",))
        with self.assertRaises(ValueError):
            manager.add(self.make_node("a", "w2"))

    def test_manager_extract_and_regenerate(self):
        manager = WorldResourceNodeManager()
        node = self.make_node("n", "w")
        manager.add(node)
        inventory = Inventory()
        manager.extract("n", inventory, Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(inventory.get(ResourceType("ore")), Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(manager.regenerate_to("n", 2), Quantity(3, ResourceUnit.ITEM))


if __name__ == "__main__":
    unittest.main()
