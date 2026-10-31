import tempfile
import unittest
from pathlib import Path

from core.simulation import SimulationRuntime
from resources import (
    GameplayFileAdapter,
    GameplayJsonCodec,
    GameplayPersistenceError,
    GameplaySnapshot,
    Inventory,
    ProductionJobManager,
    ProductionJobState,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


class TestGameplayPersistence(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.tool = ResourceType("tool")
        self.recipe = Recipe(
            "tool_recipe",
            ((self.wood, Quantity(3, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
        )

    def _runtime(self):
        inventory = Inventory()
        inventory.add(self.wood, Quantity(6, ResourceUnit.ITEM))
        nodes = WorldResourceNodeManager()
        nodes.add(WorldResourceNode(
            "node-1", "world-1", self.wood,
            Quantity(2, ResourceUnit.KG), Quantity(10, ResourceUnit.KG),
            Quantity(2, ResourceUnit.KG), 4,
        ))
        jobs = ProductionJobManager(SimulationRuntime())
        return inventory, nodes, jobs

    def test_snapshot_json_round_trip_is_deterministic(self):
        inventory, nodes, jobs = self._runtime()
        jobs.start(self.recipe, inventory, 5, job_id="job-1")
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        encoded = GameplayJsonCodec.encode(snapshot)
        decoded = GameplayJsonCodec.decode(encoded)
        self.assertEqual(encoded, GameplayJsonCodec.encode(decoded))
        restored = decoded.restore()
        self.assertEqual(restored.inventories["main"].snapshot(), inventory.snapshot())
        self.assertEqual(restored.nodes.get("node-1").quantity, Quantity(2, ResourceUnit.KG))
        self.assertEqual(restored.nodes.get("node-1").last_simulation_tick.value, 4)
        self.assertEqual(str(restored.jobs.get("job-1").action_id), "production_job:job-1")

    def test_active_job_restores_without_consuming_inputs_again(self):
        inventory, nodes, jobs = self._runtime()
        job = jobs.start(self.recipe, inventory, 5, job_id="job-1")
        jobs.advance_to(0)
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        restored = snapshot.restore()
        restored_job = restored.jobs.get("job-1")
        self.assertEqual(restored_job.state, ProductionJobState.RUNNING)
        self.assertEqual(restored.inventories["main"].get(self.wood), Quantity(3, ResourceUnit.ITEM))
        restored.jobs.advance_to(5)
        self.assertEqual(restored_job.state, ProductionJobState.COMPLETED)
        self.assertEqual(restored.inventories["main"].get(self.tool), Quantity(1, ResourceUnit.ITEM))
        restored.jobs.advance_to(5)
        self.assertEqual(restored.inventories["main"].get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_completed_job_is_not_rescheduled(self):
        inventory, nodes, jobs = self._runtime()
        job = jobs.start(self.recipe, inventory, 2, job_id="job-1")
        jobs.advance_to(2)
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        restored = snapshot.restore()
        restored_job = restored.jobs.get("job-1")
        self.assertEqual(restored_job.state, ProductionJobState.COMPLETED)
        restored.jobs.advance_to(10)
        self.assertEqual(restored.inventories["main"].get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_old_completed_job_can_restore_without_rescheduling(self):
        inventory, nodes, jobs = self._runtime()
        jobs.start(self.recipe, inventory, 2, job_id="job-1")
        jobs.advance_to(2)
        jobs.advance_to(10)
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        restored = snapshot.restore()
        self.assertEqual(restored.jobs.get("job-1").state, ProductionJobState.COMPLETED)
        self.assertEqual(restored.inventories["main"].get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_invalid_references_and_duplicate_ids_are_rejected(self):
        inventory, nodes, jobs = self._runtime()
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs).to_dict()
        snapshot["jobs"] = [{
            "job_id": "job-1", "recipe_id": "missing", "inventory_id": "main",
            "state": "completed", "start_tick": 0, "duration": 1, "end_tick": 1,
            "action_id": "action-1", "inputs_refunded": False,
        }]
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(snapshot)

    def test_job_tick_range_and_duplicate_action_ids_are_rejected(self):
        inventory, nodes, jobs = self._runtime()
        jobs.start(self.recipe, inventory, 5, job_id="job-1")
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs).to_dict()

        future_start = dict(snapshot)
        future_start["jobs"] = [dict(future_start["jobs"][0], start_tick=6, end_tick=11)]
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(future_start)

        reversed_ticks = dict(snapshot)
        reversed_ticks["jobs"] = [dict(reversed_ticks["jobs"][0], end_tick=-1)]
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(reversed_ticks)

        duplicate_action = dict(snapshot)
        first = dict(duplicate_action["jobs"][0], job_id="job-1")
        second = dict(duplicate_action["jobs"][0], job_id="job-2")
        duplicate_action["jobs"] = [first, second]
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(duplicate_action)

        inconsistent_action = dict(snapshot)
        inconsistent_action["jobs"] = [
            dict(inconsistent_action["jobs"][0], action_id="action_000001")
        ]
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(inconsistent_action)
        snapshot["jobs"] = []
        snapshot["inventories"] = [
            {"inventory_id": "main", "stocks": []},
            {"inventory_id": "main", "stocks": []},
        ]
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(snapshot)

    def test_file_adapter_uses_utf8_and_rejects_future_version(self):
        inventory, nodes, jobs = self._runtime()
        snapshot = GameplaySnapshot.from_runtime({"ana_depo_ı": inventory}, nodes, jobs)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "gameplay.json"
            GameplayFileAdapter.save(snapshot, path)
            loaded = GameplayFileAdapter.load(path)
            self.assertIn("ana_depo_ı", loaded.to_dict()["inventories"][0]["inventory_id"])
        invalid = snapshot.to_dict()
        invalid["schema_version"] = 2
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_dict(invalid)

    def test_same_inventory_under_two_ids_is_rejected(self):
        inventory, nodes, jobs = self._runtime()
        with self.assertRaises(GameplayPersistenceError):
            GameplaySnapshot.from_runtime(
                {"main": inventory, "alias": inventory}, nodes, jobs
            )

    def test_restore_can_use_supplied_runtime_without_creating_another(self):
        inventory, nodes, jobs = self._runtime()
        jobs.start(self.recipe, inventory, 5, job_id="job-1")
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        runtime = SimulationRuntime(start_tick=snapshot.simulation_tick)

        restored = snapshot.restore(runtime=runtime)

        self.assertIs(restored.jobs.runtime, runtime)
        self.assertEqual(runtime.current_tick.value, snapshot.simulation_tick)
        self.assertEqual(runtime.actions.scheduler.pending_count, 1)
        self.assertEqual(
            restored.inventories["main"].get(self.wood),
            Quantity(3, ResourceUnit.ITEM),
        )

    def test_restore_rejects_supplied_runtime_tick_mismatch(self):
        inventory, nodes, jobs = self._runtime()
        jobs.start(self.recipe, inventory, 5, job_id="job-1")
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        runtime = SimulationRuntime(start_tick=1)

        with self.assertRaises(GameplayPersistenceError):
            snapshot.restore(runtime=runtime)

        self.assertEqual(runtime.current_tick.value, 1)

    def test_terminal_jobs_are_not_scheduled_on_supplied_runtime(self):
        inventory, nodes, jobs = self._runtime()
        jobs.start(self.recipe, inventory, 2, job_id="job-1")
        jobs.advance_to(2)
        snapshot = GameplaySnapshot.from_runtime({"main": inventory}, nodes, jobs)
        runtime = SimulationRuntime(start_tick=snapshot.simulation_tick)

        restored = snapshot.restore(runtime=runtime)

        self.assertEqual(runtime.actions.scheduler.pending_count, 0)
        restored.jobs.advance_to(10)
        self.assertEqual(
            restored.inventories["main"].get(self.tool),
            Quantity(1, ResourceUnit.ITEM),
        )


if __name__ == "__main__":
    unittest.main()
