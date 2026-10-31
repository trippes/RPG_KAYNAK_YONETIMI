import unittest

from resources import (
    InsufficientStockError,
    Inventory,
    Quantity,
    Recipe,
    RecipeError,
    ResourceType,
    ResourceUnit,
    ResourceUnitMismatchError,
    consume_resources,
    produce,
)


class FailingOutputInventory(Inventory):
    def __init__(self, failing_resource):
        super().__init__()
        self.failing_resource = failing_resource

    def add(self, resource_type, quantity):
        super().add(resource_type, quantity)
        if resource_type == self.failing_resource:
            raise RuntimeError("injected output failure")


class FailingRemoveInventory(Inventory):
    def __init__(self, failing_resource):
        super().__init__()
        self.failing_resource = failing_resource

    def remove(self, resource_type, quantity):
        super().remove(resource_type, quantity)
        if resource_type == self.failing_resource:
            raise RuntimeError("injected remove failure")


class TestRecipe(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.iron = ResourceType("iron")
        self.tool = ResourceType("tool")

    def test_valid_recipe_is_deterministic_and_immutable(self):
        recipe = Recipe(
            "tool",
            inputs=((self.iron, Quantity(2, ResourceUnit.ITEM)), (self.wood, Quantity(3, ResourceUnit.ITEM))),
            outputs=((self.tool, Quantity(1, ResourceUnit.ITEM)),),
        )

        self.assertEqual(recipe.recipe_id, "tool")
        self.assertEqual([item[0].value for item in recipe.inputs], ["iron", "wood"])
        self.assertEqual([item[0].value for item in recipe.outputs], ["tool"])
        with self.assertRaises((AttributeError, TypeError)):
            recipe.recipe_id = "other"
        with self.assertRaises((AttributeError, TypeError)):
            recipe.inputs += ((self.wood, Quantity(1, ResourceUnit.ITEM)),)

    def test_empty_id_inputs_outputs_zero_and_wrong_types_are_rejected(self):
        valid = ((self.wood, Quantity(1, ResourceUnit.ITEM)),)
        for recipe_id in ("", "   "):
            with self.subTest(recipe_id=recipe_id):
                with self.assertRaises(RecipeError):
                    Recipe(recipe_id, valid, valid)
        with self.assertRaises(RecipeError):
            Recipe("x", (), valid)
        with self.assertRaises(RecipeError):
            Recipe("x", valid, ())
        with self.assertRaises(RecipeError):
            Recipe("x", ((self.wood, Quantity(0, ResourceUnit.ITEM)),), valid)
        with self.assertRaises(TypeError):
            Recipe("x", (("wood", Quantity(1, ResourceUnit.ITEM)),), valid)
        with self.assertRaises(TypeError):
            Recipe("x", ((self.wood, 1),), valid)

    def test_duplicate_resource_types_are_rejected(self):
        duplicate = ((self.wood, Quantity(1, ResourceUnit.ITEM)), (ResourceType("wood"), Quantity(2, ResourceUnit.ITEM)))

        with self.assertRaises(RecipeError):
            Recipe("duplicate-input", duplicate, ((self.tool, Quantity(1, ResourceUnit.ITEM)),))
        with self.assertRaises(RecipeError):
            Recipe("duplicate-output", ((self.wood, Quantity(1, ResourceUnit.ITEM)),), duplicate)


class TestConsumption(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.iron = ResourceType("iron")
        self.stone = ResourceType("stone")

    def test_single_and_multiple_consumption(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        inventory.add(self.iron, Quantity(4, ResourceUnit.KG))

        consume_resources(inventory, ((self.wood, Quantity(2, ResourceUnit.ITEM)),))
        consume_resources(inventory, ((self.wood, Quantity(1, ResourceUnit.ITEM)), (self.iron, Quantity(2, ResourceUnit.KG))))

        self.assertEqual(inventory.get(self.wood), Quantity(2, ResourceUnit.ITEM))
        self.assertEqual(inventory.get(self.iron), Quantity(2, ResourceUnit.KG))

    def test_insufficient_later_input_preserves_all_inputs(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        before = inventory.snapshot()

        with self.assertRaises(InsufficientStockError):
            consume_resources(inventory, ((self.wood, Quantity(2, ResourceUnit.ITEM)), (self.iron, Quantity(1, ResourceUnit.ITEM))))

        self.assertEqual(inventory.snapshot(), before)

    def test_consumption_unit_mismatch_preserves_inventory(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(5, ResourceUnit.KG))
        before = inventory.snapshot()

        with self.assertRaises(ResourceUnitMismatchError):
            consume_resources(inventory, ((self.wood, Quantity(1, ResourceUnit.LITER)),))

        self.assertEqual(inventory.snapshot(), before)

    def test_unexpected_later_remove_failure_restores_all_consumed_inputs(self):
        inventory = FailingRemoveInventory(self.iron)
        inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        inventory.add(self.iron, Quantity(4, ResourceUnit.ITEM))
        before = inventory.snapshot()

        with self.assertRaises(RuntimeError):
            consume_resources(
                inventory,
                ((self.wood, Quantity(2, ResourceUnit.ITEM)), (self.iron, Quantity(1, ResourceUnit.ITEM))),
            )

        self.assertEqual(inventory.snapshot(), before)

    def test_invalid_consumption_parameters_and_unrelated_stocks(self):
        inventory = Inventory()
        inventory.add(self.stone, Quantity(7, ResourceUnit.ITEM))
        before = inventory.snapshot()

        with self.assertRaises(TypeError):
            consume_resources(inventory, (("wood", Quantity(1, ResourceUnit.ITEM)),))
        with self.assertRaises(ValueError):
            consume_resources(inventory, ((self.wood, Quantity(0, ResourceUnit.ITEM)),))

        self.assertEqual(inventory.snapshot(), before)


class TestProduction(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.iron = ResourceType("iron")
        self.tool = ResourceType("tool")
        self.nail = ResourceType("nail")

    def test_single_input_single_output_production(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        recipe = Recipe("tool", ((self.wood, Quantity(3, ResourceUnit.ITEM)),), ((self.tool, Quantity(1, ResourceUnit.ITEM)),))

        produce(inventory, recipe)

        self.assertEqual(inventory.get(self.wood), Quantity(2, ResourceUnit.ITEM))
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_multiple_inputs_and_outputs_production(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(5, ResourceUnit.ITEM))
        inventory.add(self.iron, Quantity(2, ResourceUnit.ITEM))
        recipe = Recipe(
            "tool-set",
            ((self.wood, Quantity(3, ResourceUnit.ITEM)), (self.iron, Quantity(2, ResourceUnit.ITEM))),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)), (self.nail, Quantity(4, ResourceUnit.ITEM))),
        )

        produce(inventory, recipe)

        self.assertEqual(inventory.get(self.wood), Quantity(2, ResourceUnit.ITEM))
        self.assertIsNone(inventory.get(self.iron))
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(inventory.get(self.nail), Quantity(4, ResourceUnit.ITEM))

    def test_insufficient_input_preserves_all_stocks(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        inventory.add(self.iron, Quantity(1, ResourceUnit.ITEM))
        before = inventory.snapshot()
        recipe = Recipe("tool", ((self.wood, Quantity(3, ResourceUnit.ITEM)), (self.iron, Quantity(2, ResourceUnit.ITEM))), ((self.tool, Quantity(1, ResourceUnit.ITEM)),))

        with self.assertRaises(InsufficientStockError):
            produce(inventory, recipe)

        self.assertEqual(inventory.snapshot(), before)

    def test_output_unit_mismatch_preserves_all_stocks(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        inventory.add(self.tool, Quantity(1, ResourceUnit.KG))
        before = inventory.snapshot()
        recipe = Recipe("tool", ((self.wood, Quantity(3, ResourceUnit.ITEM)),), ((self.tool, Quantity(1, ResourceUnit.ITEM)),))

        with self.assertRaises(ResourceUnitMismatchError):
            produce(inventory, recipe)

        self.assertEqual(inventory.snapshot(), before)

    def test_output_failure_restores_consumed_inputs(self):
        inventory = FailingOutputInventory(self.tool)
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        before = inventory.snapshot()
        recipe = Recipe("tool", ((self.wood, Quantity(3, ResourceUnit.ITEM)),), ((self.tool, Quantity(1, ResourceUnit.ITEM)),))

        with self.assertRaises(RuntimeError):
            produce(inventory, recipe)

        self.assertEqual(inventory.snapshot(), before)

    def test_second_output_failure_leaves_no_partial_production(self):
        inventory = FailingOutputInventory(self.nail)
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        before = inventory.snapshot()
        recipe = Recipe(
            "tool-set",
            ((self.wood, Quantity(3, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)), (self.nail, Quantity(2, ResourceUnit.ITEM))),
        )

        with self.assertRaises(RuntimeError):
            produce(inventory, recipe)

        self.assertEqual(inventory.snapshot(), before)

    def test_same_resource_input_and_output_has_correct_net_change(self):
        inventory = Inventory()
        inventory.add(self.iron, Quantity(5, ResourceUnit.ITEM))
        recipe = Recipe("refine", ((self.iron, Quantity(5, ResourceUnit.ITEM)),), ((self.iron, Quantity(2, ResourceUnit.ITEM)),))

        produce(inventory, recipe)

        self.assertEqual(inventory.get(self.iron), Quantity(2, ResourceUnit.ITEM))

    def test_same_resource_input_output_unit_mismatch_is_rejected(self):
        inventory = Inventory()
        inventory.add(self.iron, Quantity(5, ResourceUnit.ITEM))
        recipe = Recipe("invalid-refine", ((self.iron, Quantity(5, ResourceUnit.ITEM)),), ((self.iron, Quantity(2, ResourceUnit.KG)),))
        before = inventory.snapshot()

        with self.assertRaises(ResourceUnitMismatchError):
            produce(inventory, recipe)

        self.assertEqual(inventory.snapshot(), before)

    def test_unrelated_stocks_are_preserved(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        inventory.add(self.stone if hasattr(self, "stone") else ResourceType("stone"), Quantity(9, ResourceUnit.KG))
        recipe = Recipe("tool", ((self.wood, Quantity(3, ResourceUnit.ITEM)),), ((self.tool, Quantity(1, ResourceUnit.ITEM)),))
        unrelated = inventory.get(ResourceType("stone"))

        produce(inventory, recipe)

        self.assertEqual(inventory.get(ResourceType("stone")), unrelated)

    def test_invalid_recipe_or_inventory_is_rejected(self):
        inventory = Inventory()
        with self.assertRaises(TypeError):
            produce({}, Recipe("tool", ((self.wood, Quantity(1, ResourceUnit.ITEM)),), ((self.tool, Quantity(1, ResourceUnit.ITEM)),)))
        with self.assertRaises(TypeError):
            produce(inventory, object())


if __name__ == "__main__":
    unittest.main()
