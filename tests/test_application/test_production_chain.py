import unittest

from application import ProductionChain, ProductionChainStage, ProductionChainState
from core.foundation import Identifier
from core.simulation import SimulationEvent, SimulationRuntime
from core.time import Tick
from resources import (
    Inventory,
    ProductionJobManager,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
)


class TestProductionChain(unittest.TestCase):
    def setUp(self):
        self.ore = ResourceType("ore")
        self.ingot = ResourceType("ingot")
        self.tool = ResourceType("tool")

    def _chain(self, inventory=None, second_input=2):
        inventory = inventory or Inventory()
        stage_one = ProductionChainStage(
            Recipe("smelt", ((self.ore, Quantity(3, ResourceUnit.ITEM)),),
                   ((self.ingot, Quantity(2, ResourceUnit.ITEM)),)),
            inventory,
            2,
        )
        stage_two = ProductionChainStage(
            Recipe("forge", ((self.ingot, Quantity(second_input, ResourceUnit.ITEM)),),
                   ((self.tool, Quantity(1, ResourceUnit.ITEM)),)),
            inventory,
            3,
        )
        runtime = SimulationRuntime()
        jobs = ProductionJobManager(runtime)
        return ProductionChain(jobs, (stage_one, stage_two), "chain-a"), jobs, inventory

    def test_two_stage_chain_completes_using_intermediate_output(self):
        chain, jobs, inventory = self._chain()
        inventory.add(self.ore, Quantity(3, ResourceUnit.ITEM))

        first = chain.start()
        self.assertEqual(chain.state, ProductionChainState.RUNNING)
        self.assertIsNone(inventory.get(self.ore))

        chain.advance_to(1)
        self.assertEqual(chain.current_stage_index, 0)
        self.assertEqual(len(jobs.jobs()), 1)

        chain.advance_to(2)
        self.assertEqual(first.state.value, "completed")
        self.assertEqual(chain.current_stage_index, 1)
        second = chain.current_job
        self.assertIsNotNone(second)
        self.assertEqual(second.state.value, "running")
        self.assertIsNone(inventory.get(self.ingot))

        chain.advance_to(5)
        self.assertEqual(chain.state, ProductionChainState.COMPLETED)
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        self.assertEqual(len(chain.jobs), 2)

    def test_next_stage_does_not_start_before_previous_completion(self):
        chain, jobs, inventory = self._chain()
        inventory.add(self.ore, Quantity(3, ResourceUnit.ITEM))
        chain.start()

        chain.advance_to(1)
        self.assertEqual(len(jobs.jobs()), 1)
        self.assertIsNone(inventory.get(self.ingot))

        chain.advance_to(2)
        self.assertEqual(len(jobs.jobs()), 2)

    def test_duplicate_completion_does_not_create_another_job(self):
        chain, jobs, inventory = self._chain()
        inventory.add(self.ore, Quantity(3, ResourceUnit.ITEM))
        chain.start()
        chain.advance_to(2)
        second = chain.current_job
        before_count = len(jobs.jobs())
        duplicate = SimulationEvent(
            event_type="ActionCompleted",
            simulation_tick=Tick(2),
            source_id=Identifier("test"),
            target_id=Identifier("production_job:chain-a:stage:0"),
            action_id=chain.jobs[0].action_id,
            payload={},
            metadata={},
        )
        chain.consume(duplicate)
        self.assertIs(chain.current_job, second)
        self.assertEqual(len(jobs.jobs()), before_count)

    def test_failed_first_stage_stops_chain(self):
        chain, jobs, inventory = self._chain()
        inventory.add(self.ore, Quantity(3, ResourceUnit.ITEM))
        first = chain.start()
        chain.advance_to(0)
        jobs.runtime.actions.fail(first.action_id, "test failure")

        chain.advance_to(0)

        self.assertEqual(chain.state, ProductionChainState.FAILED)
        self.assertEqual(len(chain.jobs), 1)
        self.assertIsNone(inventory.get(self.ingot))

    def test_cancelled_chain_stops_without_starting_next_stage(self):
        chain, jobs, inventory = self._chain()
        inventory.add(self.ore, Quantity(3, ResourceUnit.ITEM))
        chain.start()
        chain.cancel()

        self.assertEqual(chain.state, ProductionChainState.CANCELLED)
        self.assertEqual(len(jobs.jobs()), 1)
        self.assertEqual(inventory.get(self.ore), Quantity(3, ResourceUnit.ITEM))
        chain.advance_to(10)
        self.assertEqual(len(jobs.jobs()), 1)

    def test_next_stage_input_failure_marks_chain_failed(self):
        chain, jobs, inventory = self._chain(second_input=3)
        inventory.add(self.ore, Quantity(3, ResourceUnit.ITEM))
        chain.start()

        with self.assertRaises(Exception):
            chain.advance_to(2)

        self.assertEqual(chain.state, ProductionChainState.FAILED)
        self.assertEqual(len(jobs.jobs()), 1)
        self.assertEqual(inventory.get(self.ingot), Quantity(2, ResourceUnit.ITEM))

    def test_start_failure_marks_chain_failed_without_job(self):
        chain, jobs, inventory = self._chain()

        with self.assertRaises(Exception):
            chain.start()

        self.assertEqual(chain.state, ProductionChainState.FAILED)
        self.assertEqual(chain.jobs, ())
        self.assertEqual(jobs.jobs(), ())


if __name__ == "__main__":
    unittest.main()
