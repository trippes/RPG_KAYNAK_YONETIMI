import unittest

from resources import (
    InsufficientStockError,
    Inventory,
    Quantity,
    Recipe,
    ResourceNodeInsufficientError,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    produce,
)


class TestResourceProductionLoop(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.plank = ResourceType("plank")
        self.inventory = Inventory()
        self.node = WorldResourceNode(
            "forest-wood-node",
            "world-main",
            self.wood,
            Quantity(10, ResourceUnit.ITEM),
            Quantity(10, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        )
        self.recipe = Recipe(
            "wood-to-plank",
            ((self.wood, Quantity(2, ResourceUnit.ITEM)),),
            ((self.plank, Quantity(1, ResourceUnit.ITEM)),),
        )

    def test_gather_wood_then_produce_plank(self):
        self.node.extract_to(
            self.inventory,
            Quantity(3, ResourceUnit.ITEM),
        )

        self.assertEqual(
            self.node.quantity,
            Quantity(7, ResourceUnit.ITEM),
        )
        self.assertEqual(
            self.inventory.get(self.wood),
            Quantity(3, ResourceUnit.ITEM),
        )

        produce(self.inventory, self.recipe)

        self.assertEqual(
            self.node.quantity,
            Quantity(7, ResourceUnit.ITEM),
        )
        self.assertEqual(
            self.inventory.get(self.wood),
            Quantity(1, ResourceUnit.ITEM),
        )
        self.assertEqual(
            self.inventory.get(self.plank),
            Quantity(1, ResourceUnit.ITEM),
        )

    def test_insufficient_world_stock_changes_nothing(self):
        before = self.inventory.snapshot()

        with self.assertRaises(ResourceNodeInsufficientError):
            self.node.extract_to(
                self.inventory,
                Quantity(11, ResourceUnit.ITEM),
            )

        self.assertEqual(
            self.node.quantity,
            Quantity(10, ResourceUnit.ITEM),
        )
        self.assertEqual(self.inventory.snapshot(), before)

    def test_insufficient_wood_prevents_production_atomically(self):
        self.node.extract_to(
            self.inventory,
            Quantity(1, ResourceUnit.ITEM),
        )
        before = self.inventory.snapshot()

        with self.assertRaises(InsufficientStockError):
            produce(self.inventory, self.recipe)

        self.assertEqual(self.inventory.snapshot(), before)
        self.assertIsNone(self.inventory.get(self.plank))
        self.assertEqual(
            self.node.quantity,
            Quantity(9, ResourceUnit.ITEM),
        )


if __name__ == "__main__":
    unittest.main()
