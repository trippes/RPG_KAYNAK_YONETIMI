import unittest
from resources import Inventory, Quantity, ResourceType, ResourceUnit, Recipe, RecipeError, InsufficientItemStockError, produce, ProductionJobManager, ProductionJobState, GameplaySnapshot, GameplayJsonCodec, WorldResourceNodeManager
from core.simulation import SimulationRuntime

class FailingOutputInventory(Inventory):
    def add_item(self, item_id, quantity=1):
        if item_id == "forced_failure":
            raise RuntimeError("simulated output failure")
        return super().add_item(item_id, quantity)

class TestItemCraftingTransactions(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.inventory = Inventory()
        self.inventory.add(self.wood, Quantity(8, ResourceUnit.ITEM))
        self.inventory.add_item("wooden_plank", 5)
        self.inventory.add_item("nail", 8)

    def test_successful_mixed_production_consumes_inputs_and_creates_outputs(self):
        recipe = Recipe("assemble_panel", ((self.wood, Quantity(2, ResourceUnit.ITEM)),), (),
            item_inputs=(("wooden_plank", 3), ("nail", 4)),
            item_outputs=(("wooden_floor_panel", 2),),
            structure_part_bindings=(("wooden_floor_panel", "wooden_floor_panel"),))
        produce(self.inventory, recipe)
        self.assertEqual(self.inventory.get(self.wood), Quantity(6, ResourceUnit.ITEM))
        self.assertEqual(self.inventory.item_quantity("wooden_plank"), 2)
        self.assertEqual(self.inventory.item_quantity("nail"), 4)
        self.assertEqual(self.inventory.item_quantity("wooden_floor_panel"), 2)

    def test_insufficient_item_material_preserves_every_input(self):
        recipe = Recipe("needs_hinges", (), (), item_inputs=(("wooden_plank", 2), ("hinge", 1)), item_outputs=(("wooden_door", 1),))
        before_resources, before_items = self.inventory.snapshot(), self.inventory.item_snapshot()
        with self.assertRaises(InsufficientItemStockError):
            produce(self.inventory, recipe)
        self.assertEqual(self.inventory.snapshot(), before_resources)
        self.assertEqual(self.inventory.item_snapshot(), before_items)

    def test_invalid_empty_duplicate_and_non_positive_item_recipes_are_rejected(self):
        with self.assertRaises(RecipeError): Recipe("empty", (), ())
        with self.assertRaises(RecipeError): Recipe("duplicate", (), (), item_inputs=(("plank", 1), ("plank", 2)), item_outputs=(("wall", 1),))
        with self.assertRaises(RecipeError): Recipe("zero", (), (), item_inputs=(("plank", 0),), item_outputs=(("wall", 1),))

    def test_production_job_consumes_and_delivers_item_stacks(self):
        inventory = Inventory()
        inventory.add_item("wooden_plank", 3)
        recipe = Recipe("job_panel", (), (), item_inputs=(("wooden_plank", 2),), item_outputs=(("wall_panel", 1),))
        jobs = ProductionJobManager(SimulationRuntime())
        job = jobs.start(recipe, inventory, 4, job_id="craft-panel")
        self.assertEqual(inventory.item_quantity("wooden_plank"), 1)
        jobs.advance_to(0)
        jobs.advance_to(4)
        self.assertEqual(job.state, ProductionJobState.COMPLETED)
        self.assertEqual(inventory.item_quantity("wall_panel"), 1)

    def test_cancelled_job_refunds_item_inputs(self):
        inventory = Inventory()
        inventory.add_item("wooden_plank", 3)
        recipe = Recipe("cancel_panel", (), (), item_inputs=(("wooden_plank", 2),), item_outputs=(("wall_panel", 1),))
        jobs = ProductionJobManager(SimulationRuntime())
        job = jobs.start(recipe, inventory, 4, job_id="cancel-panel")
        jobs.cancel(job.job_id)
        self.assertEqual(job.state, ProductionJobState.CANCELLED)
        self.assertEqual(inventory.item_quantity("wooden_plank"), 3)

    def test_item_recipe_persistence_round_trip_preserves_bindings(self):
        inventory = Inventory()
        inventory.add_item("wooden_plank", 4)
        recipe = Recipe("persist_panel", (), (), item_inputs=(("wooden_plank", 2),), item_outputs=(("floor_panel", 1),), structure_part_bindings=(("floor_panel", "floor_panel"),))
        jobs = ProductionJobManager(SimulationRuntime())
        jobs.start(recipe, inventory, 5, job_id="persist-panel")
        jobs.advance_to(0)
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, WorldResourceNodeManager(), jobs, {"persist_panel": recipe})
        restored = GameplayJsonCodec.decode(GameplayJsonCodec.encode(snapshot)).restore()
        restored_recipe = restored.recipes["persist_panel"]
        self.assertEqual(restored_recipe.item_inputs, (("wooden_plank", 2),))
        self.assertEqual(restored_recipe.structure_part_bindings, (("floor_panel", "floor_panel"),))
        self.assertEqual(restored.inventories["main"].item_quantity("wooden_plank"), 2)

    def test_failed_output_rolls_back_resource_and_item_consumption(self):
        inventory = FailingOutputInventory()
        inventory.add(self.wood, Quantity(4, ResourceUnit.ITEM))
        inventory.add_item("plank", 3)
        recipe = Recipe("rollback", ((self.wood, Quantity(2, ResourceUnit.ITEM)),),
            ((ResourceType("sawdust"), Quantity(1, ResourceUnit.ITEM)),),
            item_inputs=(("plank", 2),), item_outputs=(("forced_failure", 1),))
        before_resources, before_items = inventory.snapshot(), inventory.item_snapshot()
        with self.assertRaisesRegex(RuntimeError, "simulated output failure"):
            produce(inventory, recipe)
        self.assertEqual(inventory.snapshot(), before_resources)
        self.assertEqual(inventory.item_snapshot(), before_items)

if __name__ == "__main__":
    unittest.main()
