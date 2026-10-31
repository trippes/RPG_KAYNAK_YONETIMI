import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from core.application import GameSession
from core.simulation import SimulationRuntime
from resources import (
    Inventory,
    Quantity,
    ResourceNodeInsufficientError,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


class TestCore13WorldResourceCycle(unittest.TestCase):
    def setUp(self):
        self.ore = ResourceType("ore")

    def node(self, node_id="node", world_id="world"):
        return WorldResourceNode(
            node_id,
            world_id,
            self.ore,
            Quantity(0, ResourceUnit.ITEM),
            Quantity(100, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
        )

    def test_bound_manager_rejects_unknown_world_without_registration(self):
        session = GameSession()
        manager = WorldResourceNodeManager(session.worlds)
        with self.assertRaises(ValueError):
            manager.add(self.node())
        self.assertEqual(manager.count(), 0)

    def test_nodes_are_independent_by_world_and_duplicate_ids_are_rejected(self):
        session = GameSession()
        session.worlds.create("A", world_id="a")
        session.worlds.create("B", world_id="b")
        manager = WorldResourceNodeManager(session.worlds)
        first = self.node("same-shape", "a")
        second = self.node("other", "b")
        manager.add(first)
        manager.add(second)
        with self.assertRaises(ValueError):
            manager.add(self.node("same-shape", "b"))
        self.assertEqual(tuple(n.world_id for n in manager.for_world("a")), ("a",))
        self.assertEqual(tuple(n.world_id for n in manager.for_world("b")), ("b",))

    def test_extraction_failure_is_atomic_and_successful_extraction_regenerates(self):
        runtime = SimulationRuntime()
        manager = WorldResourceNodeManager()
        node = WorldResourceNode(
            "node", "world", self.ore,
            Quantity(100, ResourceUnit.ITEM), Quantity(100, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
        )
        manager.add(node)
        inventory = Inventory()
        with self.assertRaises(ResourceNodeInsufficientError):
            manager.extract("node", inventory, Quantity(101, ResourceUnit.ITEM))
        self.assertEqual(node.quantity, Quantity(100, ResourceUnit.ITEM))
        manager.extract("node", inventory, Quantity(20, ResourceUnit.ITEM))
        runtime.register_tick_listener(manager)
        runtime.advance_to(10)
        self.assertEqual(node.quantity, Quantity(90, ResourceUnit.ITEM))
        runtime.advance_to(10)
        self.assertEqual(node.quantity, Quantity(90, ResourceUnit.ITEM))

    def test_small_and_large_steps_have_the_same_result(self):
        first = WorldResourceNodeManager()
        second = WorldResourceNodeManager()
        first.add(WorldResourceNode(
            "node-a", "world", self.ore,
            Quantity(10, ResourceUnit.ITEM), Quantity(100, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
        ))
        second.add(WorldResourceNode(
            "node-b", "world", self.ore,
            Quantity(10, ResourceUnit.ITEM), Quantity(100, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
        ))
        first.nodes()[0].extract_to(Inventory(), Quantity(1, ResourceUnit.ITEM))
        second.nodes()[0].extract_to(Inventory(), Quantity(1, ResourceUnit.ITEM))
        runtime_first = SimulationRuntime()
        runtime_second = SimulationRuntime()
        runtime_first.register_tick_listener(first)
        runtime_second.register_tick_listener(second)
        for tick in range(1, 11):
            runtime_first.advance_to(tick)
        runtime_second.advance_to(10)
        self.assertEqual(first.get("node-a").quantity, second.get("node-b").quantity)
        self.assertEqual(first.get("node-a").last_simulation_tick, second.get("node-b").last_simulation_tick)

    def test_save_load_preserves_resource_cycle_listener(self):
        application = GameApplication.create_default()
        world = application.dunya_olustur("Main", world_id="world")
        node = self.node(world_id=world.world_id)
        node.regenerate_to(0)
        application.holder.current.resource_nodes.add(node)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            application.save(path)
            application.load(path)
        restored = application.holder.current.resource_nodes.get("node")
        application.advance_simulation(7)
        self.assertEqual(restored.quantity, Quantity(7, ResourceUnit.ITEM))


if __name__ == "__main__":
    unittest.main()
