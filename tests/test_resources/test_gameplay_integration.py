import unittest

from resources import (
    GameplayJsonCodec,
    GameplayPersistenceError,
    GameplaySnapshot,
    Inventory,
    ProductionJobManager,
    ProductionJobState,
    Quantity,
    Recipe,
    ResourceNodeInsufficientError,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)
from core.simulation import SimulationRuntime


class FailingOutputInventory(Inventory):
    def __init__(self, failing_resource):
        super().__init__()
        self.failing_resource = failing_resource

    def add(self, resource_type, quantity):
        super().add(resource_type, quantity)
        if resource_type == self.failing_resource:
            raise RuntimeError("integration output failure")


class TestGameplayEndToEnd(unittest.TestCase):
    def test_node_production_tick_regeneration_and_snapshot_restore(self):
        iron = ResourceType("iron")
        tool = ResourceType("tool")
        inventory = Inventory()
        nodes = WorldResourceNodeManager()
        node = WorldResourceNode(
            "iron-node-1", "world-main", iron,
            Quantity(8, ResourceUnit.ITEM),
            Quantity(10, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
        )
        nodes.add(node)

        nodes.extract("iron-node-1", inventory, Quantity(5, ResourceUnit.ITEM))
        self.assertEqual(inventory.get(iron), Quantity(5, ResourceUnit.ITEM))
        self.assertEqual(node.quantity, Quantity(3, ResourceUnit.ITEM))

        recipe = Recipe(
            "iron-tool",
            ((iron, Quantity(3, ResourceUnit.ITEM)),),
            ((tool, Quantity(1, ResourceUnit.ITEM)),),
        )
        manager = ProductionJobManager(SimulationRuntime())
        job = manager.start(recipe, inventory, 4, job_id="job-main")
        self.assertEqual(inventory.get(iron), Quantity(2, ResourceUnit.ITEM))
        manager.advance_to(3)
        self.assertIsNone(inventory.get(tool))
        manager.advance_to(4)
        self.assertEqual(job.state, ProductionJobState.COMPLETED)
        self.assertEqual(inventory.get(tool), Quantity(1, ResourceUnit.ITEM))
        manager.advance_to(4)
        self.assertEqual(inventory.get(tool), Quantity(1, ResourceUnit.ITEM))

        nodes.regenerate_to("iron-node-1", 5)
        self.assertEqual(node.quantity, Quantity(8, ResourceUnit.ITEM))
        nodes.regenerate_to("iron-node-1", 5)
        self.assertEqual(node.quantity, Quantity(8, ResourceUnit.ITEM))

        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, manager)
        payload = GameplayJsonCodec.encode(snapshot)
        restored_snapshot = GameplayJsonCodec.decode(payload)
        self.assertEqual(payload, GameplayJsonCodec.encode(restored_snapshot))
        restored = restored_snapshot.restore()
        self.assertEqual(restored.inventories["main"].snapshot(), inventory.snapshot())
        restored_node = restored.nodes.get("iron-node-1")
        self.assertEqual(restored_node.world_id, "world-main")
        self.assertEqual(restored_node.quantity, Quantity(8, ResourceUnit.ITEM))
        self.assertEqual(restored_node.last_simulation_tick.value, 5)
        self.assertEqual(restored.jobs.get("job-main").state, ProductionJobState.COMPLETED)
        restored.jobs.advance_to(20)
        self.assertEqual(restored.inventories["main"].get(tool), Quantity(1, ResourceUnit.ITEM))

    def test_insufficient_extraction_and_production_preserve_state(self):
        iron = ResourceType("iron")
        node = WorldResourceNode(
            "node", "world", iron,
            Quantity(1, ResourceUnit.ITEM),
            Quantity(2, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        )
        inventory = Inventory()
        with self.assertRaises(ResourceNodeInsufficientError):
            node.extract_to(inventory, Quantity(2, ResourceUnit.ITEM))
        self.assertTrue(inventory.is_empty())
        self.assertEqual(node.quantity, Quantity(1, ResourceUnit.ITEM))

        recipe = Recipe(
            "tool", ((iron, Quantity(2, ResourceUnit.ITEM)),),
            ((ResourceType("tool"), Quantity(1, ResourceUnit.ITEM)),),
        )
        manager = ProductionJobManager(SimulationRuntime())
        with self.assertRaises(ValueError):
            manager.start(recipe, inventory, 2, job_id="job")
        self.assertTrue(inventory.is_empty())

    def test_output_failure_and_invalid_restore_do_not_leave_partial_state(self):
        iron = ResourceType("iron")
        tool = ResourceType("tool")
        inventory = FailingOutputInventory(tool)
        inventory.add(iron, Quantity(3, ResourceUnit.ITEM))
        recipe = Recipe("tool", ((iron, Quantity(3, ResourceUnit.ITEM)),), ((tool, Quantity(1, ResourceUnit.ITEM)),))
        manager = ProductionJobManager(SimulationRuntime())
        before = inventory.snapshot()
        manager.start(recipe, inventory, 2, job_id="job")
        with self.assertRaises(RuntimeError):
            manager.advance_to(2)
        self.assertEqual(inventory.snapshot(), before)

        payload = GameplaySnapshot.from_runtime({"main": inventory}, WorldResourceNodeManager(), manager).to_dict()
        payload["jobs"][0]["inventory_id"] = "missing"
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
