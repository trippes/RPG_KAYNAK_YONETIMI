import tempfile
import unittest
from pathlib import Path

from application import (
    GameApplication,
    GameplayChainStage,
    GameplayService,
    GameplayServiceError,
    ProductionFacility,
    ProductionFacilityRegistry,
    SessionBundle,
    SessionHolder,
)
from core.application import GameSession
from resources import (
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


class TestGameplayService(unittest.TestCase):
    def setUp(self):
        session = GameSession()
        world = session.worlds.create("Playable", world_id="world_playable")
        session.worlds.set_active(world.world_id)

        self.ore = ResourceType("ore")
        self.ingot = ResourceType("ingot")
        self.tool = ResourceType("tool")
        inventory = Inventory()
        nodes = WorldResourceNodeManager(session.worlds)
        nodes.add(WorldResourceNode(
            "ore-node", world.world_id, self.ore,
            Quantity(6, ResourceUnit.ITEM),
            Quantity(10, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        ))
        self.recipes = {
            "smelt": Recipe(
                "smelt",
                ((self.ore, Quantity(2, ResourceUnit.ITEM)),),
                ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
                processing_time=2,
                facility_type="smelter",
            ),
            "tool": Recipe(
                "tool",
                ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
                ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
                processing_time=3,
                facility_type="workshop",
            ),
        }
        facilities = ProductionFacilityRegistry()
        facilities.add(ProductionFacility("smelter-1", "smelter", 1))
        facilities.add(ProductionFacility("workshop-1", "workshop", 1))
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=ProductionJobManager(session.simulation),
            resource_nodes=nodes,
            inventories={"main": inventory},
            recipes=self.recipes,
            facilities=facilities,
        )
        self.application = GameApplication(SessionHolder(bundle))
        self.service = GameplayService(self.application)
        self.inventory = inventory

    def test_collects_from_active_world_atomically(self):
        self.service.collect("ore-node", "main", Quantity(4, ResourceUnit.ITEM))

        self.assertEqual(self.inventory.get(self.ore), Quantity(4, ResourceUnit.ITEM))
        self.assertEqual(
            self.application.holder.current.resource_nodes.get("ore-node").quantity,
            Quantity(2, ResourceUnit.ITEM),
        )

    def test_invalid_node_inventory_and_wrong_world_are_rejected(self):
        with self.assertRaises(KeyError):
            self.service.collect("missing", "main", Quantity(1, ResourceUnit.ITEM))
        with self.assertRaises(KeyError):
            self.service.collect("ore-node", "missing", Quantity(1, ResourceUnit.ITEM))

        other = self.application.dunya_olustur("Other", world_id="world_other", aktif_yap=False)
        self.application.holder.current.resource_nodes.add(WorldResourceNode(
            "other-node", other.world_id, self.ore,
            Quantity(1, ResourceUnit.ITEM), Quantity(1, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        ))
        with self.assertRaises(GameplayServiceError):
            self.service.collect("other-node", "main", Quantity(1, ResourceUnit.ITEM))

    def test_insufficient_collection_preserves_node_and_inventory(self):
        before = self.service.state()
        with self.assertRaises(ResourceNodeInsufficientError):
            self.service.collect("ore-node", "main", Quantity(7, ResourceUnit.ITEM))
        after = self.service.state()
        self.assertEqual(before.inventories, after.inventories)
        self.assertEqual(before.nodes, after.nodes)

    def test_single_production_uses_tick_runtime_and_is_idempotent(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        job = self.service.start_production("smelt", "main", "smelter-1")
        self.service.advance_to(1)
        self.assertEqual(job.state, ProductionJobState.RUNNING)
        self.assertIsNone(self.inventory.get(self.ingot))
        self.service.advance_to(2)
        self.assertEqual(job.state, ProductionJobState.COMPLETED)
        self.assertEqual(self.inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))
        self.service.advance_to(2)
        self.assertEqual(self.inventory.get(self.ingot), Quantity(1, ResourceUnit.ITEM))

    def test_wrong_facility_and_capacity_are_rejected_without_consumption(self):
        self.service.collect("ore-node", "main", Quantity(4, ResourceUnit.ITEM))
        before = self.inventory.snapshot()
        with self.assertRaises(ValueError):
            self.service.start_production("smelt", "main", "workshop-1")
        self.assertEqual(self.inventory.snapshot(), before)

        self.service.start_production("smelt", "main", "smelter-1")
        with self.assertRaises(ValueError):
            self.service.start_production("smelt", "main", "smelter-1")
        self.assertEqual(self.application.holder.current.facilities.get("smelter-1").capacity.reserved, 1)

    def test_two_stage_chain_uses_intermediate_output(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        chain = self.service.start_chain("ore-to-tool", (
            GameplayChainStage("smelt", "main", "smelter-1"),
            GameplayChainStage("tool", "main", "workshop-1"),
        ))
        self.service.advance_to(1)
        self.assertEqual(chain.current_stage_index, 0)
        self.assertIsNone(self.inventory.get(self.ingot))
        self.service.advance_to(2)
        self.assertEqual(chain.current_stage_index, 1)
        # The second stage consumes the intermediate product at its start.
        self.assertIsNone(self.inventory.get(self.ingot))
        self.assertIsNone(self.inventory.get(self.tool))
        self.service.advance_to(5)
        self.assertEqual(chain.state.value, "completed")
        self.assertEqual(self.inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        self.service.advance_to(5)
        self.assertEqual(self.inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_state_is_read_only_and_save_load_preserves_active_job(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_production("smelt", "main", "smelter-1")
        snapshot = self.service.state()
        self.assertEqual(snapshot.simulation_tick, 0)
        self.assertEqual(snapshot.inventories[0].stocks, ())

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "playable-save.json"
            self.service.save(path)
            self.service.load(path)
            restored = self.service.state()
            self.assertEqual(restored.simulation_tick, 0)
            self.assertEqual(restored.facilities[0].active_job_ids, ("facility:smelter-1:job:000001",))
            self.service.advance_to(2)
            self.service.advance_to(2)
            self.assertEqual(self.service.inventory("main").stocks, (("ingot", 1, "item"),))

    def test_load_switch_discards_runtime_only_chain_registry(self):
        self.service.collect("ore-node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_chain("chain", (("smelt", "main", "smelter-1"),))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chain-save.json"
            self.service.save(path)
            self.service.load(path)
            self.assertEqual(self.service.state().chains, ())


if __name__ == "__main__":
    unittest.main()
