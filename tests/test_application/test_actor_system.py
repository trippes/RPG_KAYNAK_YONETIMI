import tempfile
import unittest
from pathlib import Path

from application import (
    ActivityState,
    ActorError,
    GameApplication,
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
    Quantity,
    Recipe,
    ResourceNodeInsufficientError,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


class TestActorSystem(unittest.TestCase):
    def setUp(self):
        session = GameSession()
        world = session.worlds.create("Actors", world_id="world_actors")
        session.worlds.set_active(world.world_id)
        self.ore = ResourceType("ore")
        self.tool = ResourceType("tool")
        inventory = Inventory()
        nodes = WorldResourceNodeManager(session.worlds)
        nodes.add(WorldResourceNode(
            "node", world.world_id, self.ore,
            Quantity(5, ResourceUnit.ITEM), Quantity(5, ResourceUnit.ITEM),
            Quantity(0, ResourceUnit.ITEM),
        ))
        recipe = Recipe(
            "tool", ((self.ore, Quantity(2, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
            processing_time=3, facility_type="workshop",
        )
        facilities = ProductionFacilityRegistry()
        facilities.add(ProductionFacility("workshop", "workshop", 1))
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=ProductionJobManager(session.simulation),
            resource_nodes=nodes,
            inventories={"main": inventory},
            recipes={"tool": recipe},
            facilities=facilities,
        )
        self.application = GameApplication(SessionHolder(bundle))
        self.service = GameplayService(self.application)
        self.inventory = inventory

    def test_registers_world_bound_actor_and_sorted_snapshot(self):
        self.service.register_actor("b", "miner")
        self.service.register_actor("a", "worker")
        self.assertEqual([actor.actor_id for actor in self.service.actors_state()], ["a", "b"])
        self.assertEqual(self.service.actor("a").world_id, "world_actors")
        with self.assertRaises(ActorError):
            self.service.register_actor("a", "worker")
        with self.assertRaises(ActorError):
            self.service.register_actor("remote", "worker", "missing-world")

    def test_actor_active_state_and_same_actor_overlap_are_controlled(self):
        self.service.register_actor("worker", "worker")
        self.service.set_actor_active("worker", False)
        with self.assertRaises(GameplayServiceError):
            self.service.start_gathering("worker", "node", "main", Quantity(1, ResourceUnit.ITEM))
        self.service.set_actor_active("worker", True)
        self.service.start_gathering("worker", "node", "main", Quantity(1, ResourceUnit.ITEM))
        self.service.collect("node", "main", Quantity(1, ResourceUnit.ITEM))

    def test_gather_activity_uses_atomic_collection_and_completes_after_duration(self):
        self.service.register_actor("miner", "miner")
        result = self.service.start_gathering(
            "miner", "node", "main", Quantity(2, ResourceUnit.ITEM), "gather-1"
        )
        self.assertEqual(result.state, ActivityState.RUNNING.value)
        self.service.advance_by(self.service.gathering_duration("miner"))
        self.assertEqual(self.service.activity("gather-1").state, ActivityState.COMPLETED.value)
        self.assertEqual(self.inventory.get(self.ore), Quantity(2, ResourceUnit.ITEM))
        self.assertIsNone(self.service.actor("miner").activity_id)

    def test_failed_gather_does_not_change_inventory_or_node(self):
        self.service.register_actor("miner", "miner")
        with self.assertRaises(ResourceNodeInsufficientError):
            self.service.start_gathering("miner", "node", "main", Quantity(6, ResourceUnit.ITEM), "bad")
        self.assertTrue(self.inventory.is_empty())
        self.assertEqual(self.application.holder.current.resource_nodes.get("node").quantity.value, 5)
        self.assertEqual(self.service.activity("bad").state, ActivityState.FAILED.value)

    def test_production_activity_tracks_job_and_duplicate_completion(self):
        self.service.register_actor("worker", "worker")
        self.service.collect("node", "main", Quantity(2, ResourceUnit.ITEM))
        activity = self.service.start_actor_production(
            "worker", "tool", "main", "workshop", "prod-1"
        )
        self.assertEqual(activity.state, ActivityState.RUNNING.value)
        self.service.advance_to(2)
        self.assertEqual(self.service.activity("prod-1").state, ActivityState.RUNNING.value)
        self.service.advance_to(3)
        self.assertEqual(self.service.activity("prod-1").state, ActivityState.COMPLETED.value)
        self.assertEqual(self.inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        self.service.advance_to(3)
        self.assertEqual(self.inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_production_cancel_clears_actor_and_does_not_complete(self):
        self.service.register_actor("worker", "worker")
        self.service.collect("node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_actor_production("worker", "tool", "main", "workshop", "cancel-me")
        result = self.service.cancel_activity("cancel-me", "player cancelled")
        self.assertEqual(result.state, ActivityState.CANCELLED.value)
        self.assertIsNone(self.service.actor("worker").activity_id)
        self.assertEqual(self.inventory.get(self.ore), Quantity(2, ResourceUnit.ITEM))
        self.service.advance_to(3)
        self.assertIsNone(self.inventory.get(self.tool))

    def test_two_actors_respect_shared_node_and_facility_capacity(self):
        self.service.register_actor("first", "worker")
        self.service.register_actor("second", "worker")
        self.service.collect("node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_actor_production("first", "tool", "main", "workshop", "first-job")
        with self.assertRaises(ValueError):
            self.service.start_actor_production("second", "tool", "main", "workshop", "second-job")
        self.assertEqual(self.service.activity("second-job").state, ActivityState.FAILED.value)
        with self.assertRaises(ResourceNodeInsufficientError):
            self.service.start_gathering("second", "node", "main", Quantity(4, ResourceUnit.ITEM), "too-much")

    def test_state_snapshot_includes_actors_and_activities_without_mutation(self):
        self.service.register_actor("worker", "worker")
        before = self.service.state()
        self.service.start_gathering("worker", "node", "main", Quantity(1, ResourceUnit.ITEM), "gather")
        after = self.service.state()
        self.assertEqual(before.simulation_tick, after.simulation_tick)
        self.assertEqual(after.actors[0].actor_id, "worker")
        self.assertEqual(after.activities[0].activity_id, "gather")

    def test_actor_and_active_production_restore_without_duplicate_output(self):
        self.service.register_actor("worker", "worker")
        self.service.collect("node", "main", Quantity(2, ResourceUnit.ITEM))
        self.service.start_actor_production("worker", "tool", "main", "workshop", "persisted")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "actor-save.json"
            self.service.save(path)
            self.service.load(path)
            self.assertEqual(self.service.actor("worker").activity_id, "persisted")
            self.assertEqual(self.service.activity("persisted").state, ActivityState.RUNNING.value)
            self.service.advance_to(3)
            self.service.advance_to(3)
            self.assertEqual(self.service.inventory("main").stocks, (("tool", 1, "item"),))

    def test_active_gathering_restore_still_delivers_resources(self):
        self.service.register_actor("worker", "worker")
        self.service.start_gathering(
            "worker", "node", "main", Quantity(1, ResourceUnit.ITEM), "persisted-gather"
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gather-save.json"
            self.service.save(path)
            self.service.load(path)
            self.assertEqual(
                self.service.activity("persisted-gather").state,
                ActivityState.RUNNING.value,
            )
            self.service.advance_by(150)
            self.assertEqual(
                self.service.activity("persisted-gather").state,
                ActivityState.COMPLETED.value,
            )
            self.assertIn(("ore", 1, "item"), self.service.inventory("main").stocks)

    def test_invalid_actor_save_does_not_replace_active_bundle(self):
        self.service.register_actor("worker", "worker")
        active = self.application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            self.service.save(path)
            import json
            data = json.loads(path.read_text(encoding="utf-8"))
            data["actors"]["actors"][0]["world_id"] = "missing"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(Exception):
                self.service.load(path)
        self.assertIs(self.application.holder.current, active)
        self.assertEqual(self.service.actor("worker").world_id, "world_actors")


if __name__ == "__main__":
    unittest.main()
