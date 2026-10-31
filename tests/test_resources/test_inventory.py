import unittest

from resources import Inventory, Quantity, ResourceType, ResourceUnit


class TestInventory(unittest.TestCase):
    def setUp(self):
        self.inventory = Inventory()
        self.wood = ResourceType("wood")
        self.stone = ResourceType("stone")
        self.iron = ResourceType("iron")

    def test_empty_inventory_is_reported(self):
        self.assertTrue(self.inventory.is_empty())
        self.assertEqual(self.inventory.resource_type_count(), 0)
        self.assertIsNone(self.inventory.get(self.wood))
        self.assertEqual(self.inventory.snapshot(), ())

    def test_first_stock_is_added_and_can_be_queried(self):
        self.inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.get(self.wood), Quantity(5, ResourceUnit.ITEM))
        self.assertFalse(self.inventory.is_empty())
        self.assertEqual(self.inventory.resource_type_count(), 1)

    def test_multiple_resource_types_have_independent_stocks(self):
        self.inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        self.inventory.add(self.stone, Quantity(3, ResourceUnit.KG))

        self.assertEqual(self.inventory.get(self.wood), Quantity(5, ResourceUnit.ITEM))
        self.assertEqual(self.inventory.get(self.stone), Quantity(3, ResourceUnit.KG))
        self.assertEqual(self.inventory.resource_type_count(), 2)

    def test_same_resource_and_unit_are_accumulated(self):
        self.inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        self.inventory.add(ResourceType("wood"), Quantity(7, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.get(self.wood), Quantity(12, ResourceUnit.ITEM))

    def test_sufficient_stock_is_removed(self):
        self.inventory.add(self.wood, Quantity(10, ResourceUnit.ITEM))

        self.inventory.remove(self.wood, Quantity(4, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.get(self.wood), Quantity(6, ResourceUnit.ITEM))

    def test_insufficient_stock_is_rejected_without_mutation(self):
        self.inventory.add(self.wood, Quantity(10, ResourceUnit.ITEM))
        before = self.inventory.snapshot()

        with self.assertRaises(ValueError):
            self.inventory.remove(self.wood, Quantity(11, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.snapshot(), before)

    def test_missing_positive_stock_removal_is_rejected_without_mutation(self):
        before = self.inventory.snapshot()

        with self.assertRaises(ValueError):
            self.inventory.remove(self.wood, Quantity(1, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.snapshot(), before)

    def test_unit_mismatch_is_rejected_without_mutation(self):
        self.inventory.add(self.wood, Quantity(5, ResourceUnit.KG))
        before = self.inventory.snapshot()

        with self.assertRaises(ValueError):
            self.inventory.add(self.wood, Quantity(2, ResourceUnit.LITER))
        with self.assertRaises(ValueError):
            self.inventory.remove(self.wood, Quantity(2, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.snapshot(), before)

    def test_full_removal_deletes_zero_stock_record(self):
        self.inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))

        self.inventory.remove(self.wood, Quantity(5, ResourceUnit.ITEM))

        self.assertIsNone(self.inventory.get(self.wood))
        self.assertTrue(self.inventory.is_empty())
        self.assertEqual(self.inventory.snapshot(), ())

    def test_zero_addition_does_not_create_a_stock_record(self):
        self.inventory.add(self.wood, Quantity(0, ResourceUnit.ITEM))

        self.assertIsNone(self.inventory.get(self.wood))
        self.assertTrue(self.inventory.is_empty())

    def test_zero_removal_is_a_no_op(self):
        self.inventory.remove(self.wood, Quantity(0, ResourceUnit.ITEM))
        self.inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        before = self.inventory.snapshot()

        self.inventory.remove(self.wood, Quantity(0, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.snapshot(), before)

    def test_invalid_input_types_are_rejected(self):
        with self.assertRaises(TypeError):
            self.inventory.add("wood", Quantity(1, ResourceUnit.ITEM))
        with self.assertRaises(TypeError):
            self.inventory.add(self.wood, 1)
        with self.assertRaises(TypeError):
            self.inventory.remove("wood", Quantity(1, ResourceUnit.ITEM))
        with self.assertRaises(TypeError):
            self.inventory.get("wood")

    def test_snapshot_is_deterministically_sorted_and_not_mutable(self):
        self.inventory.add(self.stone, Quantity(1, ResourceUnit.KG))
        self.inventory.add(self.wood, Quantity(2, ResourceUnit.ITEM))
        snapshot = self.inventory.snapshot()

        self.assertEqual([item[0].value for item in snapshot], ["stone", "wood"])
        with self.assertRaises(AttributeError):
            snapshot[0][1].value = 99


if __name__ == "__main__":
    unittest.main()
