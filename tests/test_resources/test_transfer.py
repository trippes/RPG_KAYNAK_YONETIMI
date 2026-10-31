import unittest

from resources import Inventory, Quantity, ResourceType, ResourceUnit, transfer_resources


class FailingInventory(Inventory):
    """Test double that fails after partially applying an add."""

    def add(self, resource_type, quantity):
        super().add(resource_type, quantity)
        raise RuntimeError("injected target add failure")


class TestResourceTransfer(unittest.TestCase):
    def setUp(self):
        self.iron = ResourceType("iron")
        self.wood = ResourceType("wood")
        self.source = Inventory()
        self.target = Inventory()

    def test_successful_transfer_updates_both_and_preserves_total(self):
        self.source.add(self.iron, Quantity(20, ResourceUnit.ITEM))
        self.target.add(self.iron, Quantity(5, ResourceUnit.ITEM))
        before_total = self.source.get(self.iron).value + self.target.get(self.iron).value

        transfer_resources(self.source, self.target, self.iron, Quantity(10, ResourceUnit.ITEM))

        self.assertEqual(self.source.get(self.iron), Quantity(10, ResourceUnit.ITEM))
        self.assertEqual(self.target.get(self.iron), Quantity(15, ResourceUnit.ITEM))
        after_total = self.source.get(self.iron).value + self.target.get(self.iron).value
        self.assertEqual(after_total, before_total)

    def test_insufficient_source_stock_preserves_both_inventories(self):
        self.source.add(self.iron, Quantity(4, ResourceUnit.ITEM))
        self.target.add(self.iron, Quantity(2, ResourceUnit.ITEM))
        source_before = self.source.snapshot()
        target_before = self.target.snapshot()

        with self.assertRaises(ValueError):
            transfer_resources(self.source, self.target, self.iron, Quantity(5, ResourceUnit.ITEM))

        self.assertEqual(self.source.snapshot(), source_before)
        self.assertEqual(self.target.snapshot(), target_before)

    def test_missing_source_stock_preserves_target_without_new_record(self):
        self.target.add(self.iron, Quantity(2, ResourceUnit.ITEM))
        source_before = self.source.snapshot()
        target_before = self.target.snapshot()

        with self.assertRaises(ValueError):
            transfer_resources(self.source, self.target, self.iron, Quantity(1, ResourceUnit.ITEM))

        self.assertEqual(self.source.snapshot(), source_before)
        self.assertEqual(self.target.snapshot(), target_before)

    def test_source_unit_mismatch_preserves_both_inventories(self):
        self.source.add(self.iron, Quantity(4, ResourceUnit.KG))
        source_before = self.source.snapshot()
        target_before = self.target.snapshot()

        with self.assertRaises(ValueError):
            transfer_resources(self.source, self.target, self.iron, Quantity(1, ResourceUnit.LITER))

        self.assertEqual(self.source.snapshot(), source_before)
        self.assertEqual(self.target.snapshot(), target_before)

    def test_target_unit_mismatch_preserves_both_inventories(self):
        self.source.add(self.iron, Quantity(4, ResourceUnit.KG))
        self.target.add(self.iron, Quantity(2, ResourceUnit.LITER))
        source_before = self.source.snapshot()
        target_before = self.target.snapshot()

        with self.assertRaises(ValueError):
            transfer_resources(self.source, self.target, self.iron, Quantity(1, ResourceUnit.KG))

        self.assertEqual(self.source.snapshot(), source_before)
        self.assertEqual(self.target.snapshot(), target_before)

    def test_zero_transfer_is_a_no_op(self):
        self.source.add(self.iron, Quantity(4, ResourceUnit.ITEM))
        source_before = self.source.snapshot()
        target_before = self.target.snapshot()

        transfer_resources(self.source, self.target, self.iron, Quantity(0, ResourceUnit.ITEM))

        self.assertEqual(self.source.snapshot(), source_before)
        self.assertEqual(self.target.snapshot(), target_before)

    def test_same_inventory_transfer_is_a_no_op(self):
        self.source.add(self.iron, Quantity(4, ResourceUnit.ITEM))
        before = self.source.snapshot()

        transfer_resources(self.source, self.source, self.iron, Quantity(2, ResourceUnit.ITEM))

        self.assertEqual(self.source.snapshot(), before)

    def test_invalid_parameter_types_are_rejected_without_mutation(self):
        source_before = self.source.snapshot()
        target_before = self.target.snapshot()
        cases = (
            (object(), self.target, self.iron, Quantity(1, ResourceUnit.ITEM)),
            (self.source, object(), self.iron, Quantity(1, ResourceUnit.ITEM)),
            (self.source, self.target, "iron", Quantity(1, ResourceUnit.ITEM)),
            (self.source, self.target, self.iron, 1),
        )

        for args in cases:
            with self.subTest(args=args):
                with self.assertRaises(TypeError):
                    transfer_resources(*args)
                self.assertEqual(self.source.snapshot(), source_before)
                self.assertEqual(self.target.snapshot(), target_before)

    def test_unexpected_target_add_failure_restores_both_snapshots(self):
        source = Inventory()
        target = FailingInventory()
        source.add(self.iron, Quantity(10, ResourceUnit.ITEM))
        target.add = FailingInventory.add.__get__(target, FailingInventory)
        source_before = source.snapshot()
        target_before = target.snapshot()

        with self.assertRaises(RuntimeError):
            transfer_resources(source, target, self.iron, Quantity(3, ResourceUnit.ITEM))

        self.assertEqual(source.snapshot(), source_before)
        self.assertEqual(target.snapshot(), target_before)

    def test_complete_transfer_preserves_zero_stock_policy(self):
        self.source.add(self.iron, Quantity(3, ResourceUnit.ITEM))

        transfer_resources(self.source, self.target, self.iron, Quantity(3, ResourceUnit.ITEM))

        self.assertIsNone(self.source.get(self.iron))
        self.assertEqual(self.target.get(self.iron), Quantity(3, ResourceUnit.ITEM))

    def test_other_resource_stocks_are_unchanged(self):
        self.source.add(self.iron, Quantity(10, ResourceUnit.ITEM))
        self.source.add(self.wood, Quantity(7, ResourceUnit.KG))
        self.target.add(self.wood, Quantity(2, ResourceUnit.KG))
        source_before_wood = self.source.get(self.wood)
        target_before_wood = self.target.get(self.wood)

        transfer_resources(self.source, self.target, self.iron, Quantity(4, ResourceUnit.ITEM))

        self.assertEqual(self.source.get(self.wood), source_before_wood)
        self.assertEqual(self.target.get(self.wood), target_before_wood)


if __name__ == "__main__":
    unittest.main()
