import unittest

from application import (
    ProductionCapacity,
    ProductionCapacityError,
    ProductionChain,
    ProductionChainStage,
    ProductionChainState,
)
from core.simulation import SimulationRuntime
from resources import (
    GameplaySnapshot,
    Inventory,
    ProductionJobManager,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
    WorldResourceNodeManager,
)


class TestProductionCapacity(unittest.TestCase):
    def setUp(self):
        self.ore = ResourceType("ore")
        self.ingot = ResourceType("ingot")
        self.recipe = Recipe(
            "smelt",
            ((self.ore, Quantity(1, ResourceUnit.ITEM)),),
            ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
        )

    def _job_context(self, capacity=1):
        runtime = SimulationRuntime()
        jobs = ProductionJobManager(runtime)
        pool = ProductionCapacity(capacity)
        inventory = Inventory()
        inventory.add(self.ore, Quantity(2, ResourceUnit.ITEM))
        return runtime, jobs, pool, inventory

    def test_capacity_rejects_second_job_without_consuming_input(self):
        _, jobs, pool, inventory = self._job_context()
        pool.start(jobs, self.recipe, inventory, 2, job_id="job-a")
        before = inventory.snapshot()

        with self.assertRaises(ProductionCapacityError):
            pool.start(jobs, self.recipe, inventory, 2, job_id="job-b")

        self.assertEqual(pool.reserved, 1)
        self.assertEqual(inventory.snapshot(), before)
        self.assertIsNone(jobs.get("job-b"))
        jobs.advance_to(2)
        pool.start(jobs, self.recipe, inventory, 2, job_id="job-b")
        self.assertEqual(pool.reserved, 1)

    def test_completion_releases_capacity_once(self):
        _, jobs, pool, inventory = self._job_context()
        job = pool.start(jobs, self.recipe, inventory, 2, job_id="job-a")
        jobs.advance_to(2)

        self.assertEqual(job.state.value, "completed")
        self.assertEqual(pool.reserved, 0)
        pool.consume(jobs.runtime.events.dequeue()) if jobs.runtime.events.count() else None
        self.assertEqual(pool.reserved, 0)

    def test_cancel_and_failure_release_capacity(self):
        runtime, jobs, pool, inventory = self._job_context()
        first = pool.start(jobs, self.recipe, inventory, 2, job_id="job-a")
        pool.cancel(jobs, first.job_id)
        self.assertEqual(pool.reserved, 0)
        self.assertEqual(inventory.get(self.ore), Quantity(2, ResourceUnit.ITEM))

        second = pool.start(jobs, self.recipe, inventory, 2, job_id="job-b")
        jobs.advance_to(0)
        runtime.actions.fail(second.action_id, "test failure")
        jobs.advance_to(0)
        self.assertEqual(pool.reserved, 0)

    def test_start_failure_rolls_back_reservation(self):
        _, jobs, pool, inventory = self._job_context()
        inventory.remove(self.ore, Quantity(2, ResourceUnit.ITEM))
        with self.assertRaises(ValueError):
            pool.start(jobs, self.recipe, inventory, 2, job_id="job-a")
        self.assertEqual(pool.reserved, 0)
        self.assertIsNone(jobs.get("job-a"))
        self.assertIsNone(inventory.get(self.ore))

    def test_capacity_is_shared_by_independent_chains(self):
        runtime = SimulationRuntime()
        jobs = ProductionJobManager(runtime)
        pool = ProductionCapacity(1)
        first_inventory = Inventory()
        second_inventory = Inventory()
        first_inventory.add(self.ore, Quantity(1, ResourceUnit.ITEM))
        second_inventory.add(self.ore, Quantity(1, ResourceUnit.ITEM))
        stage_one = ProductionChainStage(self.recipe, first_inventory, 1)
        stage_two = ProductionChainStage(self.recipe, second_inventory, 1)
        first = ProductionChain(jobs, (stage_one,), "first", capacity=pool)
        second = ProductionChain(jobs, (stage_two,), "second", capacity=pool)

        first.start()
        with self.assertRaises(ProductionCapacityError):
            second.start()
        self.assertEqual(second.state, ProductionChainState.FAILED)
        self.assertEqual(pool.reserved, 1)

        first.advance_to(1)
        self.assertEqual(pool.reserved, 0)

    def test_chain_releases_and_reacquires_capacity_between_stages(self):
        runtime = SimulationRuntime()
        jobs = ProductionJobManager(runtime)
        pool = ProductionCapacity(1)
        inventory = Inventory()
        inventory.add(self.ore, Quantity(1, ResourceUnit.ITEM))
        output_recipe = Recipe(
            "forge",
            ((self.ingot, Quantity(1, ResourceUnit.ITEM)),),
            ((ResourceType("tool"), Quantity(1, ResourceUnit.ITEM)),),
        )
        chain = ProductionChain(
            jobs,
            (ProductionChainStage(self.recipe, inventory, 1),
             ProductionChainStage(output_recipe, inventory, 1)),
            "chain",
            capacity=pool,
        )
        chain.start()
        chain.advance_to(1)
        self.assertEqual(chain.state, ProductionChainState.RUNNING)
        self.assertEqual(pool.reserved, 1)
        chain.advance_to(2)
        self.assertEqual(chain.state, ProductionChainState.COMPLETED)
        self.assertEqual(pool.reserved, 0)

    def test_restored_active_capacity_job_can_be_explicitly_reconciled(self):
        runtime, jobs, pool, inventory = self._job_context()
        pool.start(jobs, self.recipe, inventory, 5, job_id="job-a")
        jobs.advance_to(0)
        snapshot = GameplaySnapshot.from_runtime({"main": inventory},
                                                  WorldResourceNodeManager(), jobs)
        restored_runtime = SimulationRuntime(start_tick=snapshot.simulation_tick)
        restored = snapshot.restore(runtime=restored_runtime)
        restored_pool = ProductionCapacity(1)
        restored_pool.attach_existing(restored.jobs, ("job-a",))

        self.assertEqual(restored_pool.reserved, 1)
        restored.jobs.advance_to(5)
        self.assertEqual(restored_pool.reserved, 0)


if __name__ == "__main__":
    unittest.main()
