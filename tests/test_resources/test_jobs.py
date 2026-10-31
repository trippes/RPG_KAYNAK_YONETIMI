import unittest

from core.foundation import ActionId, Identifier
from core.simulation import SimulationRuntime, SimulationEvent
from core.time import Tick
from resources import (
    Inventory,
    ProductionJobManager,
    ProductionJobState,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
)


class FailingJobInventory(Inventory):
    def __init__(self, failing_resource):
        super().__init__()
        self.failing_resource = failing_resource

    def add(self, resource_type, quantity):
        super().add(resource_type, quantity)
        if resource_type == self.failing_resource:
            raise RuntimeError("injected job output failure")


class TestProductionJobs(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.tool = ResourceType("tool")
        self.recipe = Recipe(
            "tool",
            ((self.wood, Quantity(3, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
        )

    def _manager_and_inventory(self):
        return ProductionJobManager(SimulationRuntime()), Inventory()

    def test_valid_job_duration_and_ticks(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))

        job = manager.start(self.recipe, inventory, Tick(5), job_id="job_a")

        self.assertEqual(job.state, ProductionJobState.PLANNED)
        self.assertEqual(job.start_tick, Tick(0))
        self.assertEqual(job.end_tick, Tick(5))
        self.assertEqual(job.duration, Tick(5))
        self.assertEqual(str(job.action_id), "production_job:job_a")

    def test_existing_runtime_action_id_rejects_job_without_consuming(self):
        runtime = SimulationRuntime()
        manager = ProductionJobManager(runtime)
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        runtime.actions.create(
            Identifier("external"),
            Tick(1),
            action_id=ActionId("production_job:job_a"),
        )
        before = inventory.snapshot()

        with self.assertRaises(ValueError):
            manager.start(self.recipe, inventory, 5, job_id="job_a")

        self.assertEqual(inventory.snapshot(), before)
        self.assertIsNone(manager.get("job_a"))

    def test_zero_and_negative_duration_are_rejected(self):
        manager, inventory = self._manager_and_inventory()
        for duration in (0, -1):
            with self.subTest(duration=duration):
                with self.assertRaises(ValueError):
                    manager.start(self.recipe, inventory, duration)

    def test_start_consumes_inputs_once_and_schedules_job(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(6, ResourceUnit.ITEM))

        job = manager.start(self.recipe, inventory, 5, job_id="job_a")

        self.assertEqual(inventory.get(self.wood), Quantity(3, ResourceUnit.ITEM))
        self.assertEqual(manager.get("job_a"), job)
        with self.assertRaises(ValueError):
            manager.start(self.recipe, inventory, 5, job_id="job_a")
        self.assertEqual(inventory.get(self.wood), Quantity(3, ResourceUnit.ITEM))

    def test_insufficient_input_does_not_create_or_consume_job(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(2, ResourceUnit.ITEM))
        before = inventory.snapshot()

        with self.assertRaises(ValueError):
            manager.start(self.recipe, inventory, 5, job_id="job_a")

        self.assertEqual(inventory.snapshot(), before)
        self.assertIsNone(manager.get("job_a"))

    def test_job_is_running_at_start_tick_and_completes_at_end_tick(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        job = manager.start(self.recipe, inventory, 5, job_id="job_a")

        manager.advance_to(0)
        self.assertEqual(job.state, ProductionJobState.RUNNING)
        self.assertIsNone(inventory.get(self.tool))
        manager.advance_to(4)
        self.assertIsNone(inventory.get(self.tool))
        manager.advance_to(5)
        self.assertEqual(job.state, ProductionJobState.COMPLETED)
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_completion_is_idempotent_when_callback_is_repeated(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        job = manager.start(self.recipe, inventory, 5, job_id="job_a")
        manager.advance_to(5)
        before = inventory.snapshot()

        manager.consume(
            SimulationEvent(
                event_type="ActionCompleted",
                simulation_tick=Tick(5),
                source_id=Identifier("action_processor"),
                target_id=Identifier("production_job:job_a"),
                action_id=job.action_id,
                payload={},
                metadata={},
            )
        )

        self.assertEqual(job.state, ProductionJobState.COMPLETED)
        self.assertEqual(inventory.snapshot(), before)

    def test_cancel_running_job_refunds_inputs_once_and_has_no_output(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        job = manager.start(self.recipe, inventory, 5, job_id="job_a")
        manager.advance_to(0)

        manager.cancel("job_a")
        self.assertEqual(job.state, ProductionJobState.CANCELLED)
        self.assertEqual(inventory.get(self.wood), Quantity(3, ResourceUnit.ITEM))
        manager.advance_to(5)
        self.assertIsNone(inventory.get(self.tool))
        with self.assertRaises(ValueError):
            manager.cancel("job_a")

    def test_cancel_planned_job_refunds_inputs_and_never_starts(self):
        manager, inventory = self._manager_and_inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        job = manager.start(self.recipe, inventory, 5, job_id="job_a")

        manager.cancel("job_a")
        manager.advance_to(5)

        self.assertEqual(job.state, ProductionJobState.CANCELLED)
        self.assertEqual(inventory.get(self.wood), Quantity(3, ResourceUnit.ITEM))
        self.assertIsNone(inventory.get(self.tool))

    def test_failed_output_keeps_inventory_atomic_and_marks_job_failed(self):
        inventory = FailingJobInventory(self.tool)
        manager = ProductionJobManager(SimulationRuntime())
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        before = inventory.snapshot()
        job = manager.start(self.recipe, inventory, 5, job_id="job_a")

        with self.assertRaises(RuntimeError):
            manager.advance_to(5)

        self.assertEqual(job.state, ProductionJobState.FAILED)
        self.assertEqual(inventory.snapshot(), before)

    def test_output_and_refund_failure_leave_job_terminal_without_false_refund(self):
        class FailingOutputAndRefundInventory(Inventory):
            def __init__(self, output_resource, input_resource):
                super().__init__()
                self.output_resource = output_resource
                self.input_resource = input_resource
                self.fail_writes = False

            def add(self, resource_type, quantity):
                super().add(resource_type, quantity)
                if self.fail_writes and resource_type in {self.output_resource, self.input_resource}:
                    raise RuntimeError("injected output/refund failure")

        inventory = FailingOutputAndRefundInventory(self.tool, self.wood)
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        manager = ProductionJobManager(SimulationRuntime())
        job = manager.start(self.recipe, inventory, 1, job_id="job_a")
        inventory.fail_writes = True

        with self.assertRaises(RuntimeError):
            manager.advance_to(1)

        self.assertEqual(job.state, ProductionJobState.FAILED)
        self.assertFalse(job.inputs_refunded)
        self.assertTrue(inventory.is_empty())

        completion = SimulationEvent(
            event_type="ActionCompleted",
            simulation_tick=Tick(1),
            source_id=Identifier("test"),
            target_id=Identifier("production_job:job_a"),
            action_id=job.action_id,
            payload={},
            metadata={},
        )
        manager.consume(completion)
        self.assertEqual(job.state, ProductionJobState.FAILED)
        self.assertFalse(job.inputs_refunded)
        self.assertTrue(inventory.is_empty())

    def test_invalid_parameters_and_unknown_job_are_rejected(self):
        manager, inventory = self._manager_and_inventory()
        with self.assertRaises(TypeError):
            manager.start(object(), inventory, 1)
        with self.assertRaises(TypeError):
            manager.start(self.recipe, object(), 1)
        with self.assertRaises(TypeError):
            ProductionJobManager(object())
        with self.assertRaises(KeyError):
            manager.cancel("missing")

    def test_scheduler_failure_restores_inputs_and_does_not_publish_job(self):
        runtime = SimulationRuntime()
        manager = ProductionJobManager(runtime)
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        before = inventory.snapshot()

        original_schedule = runtime.actions.schedule
        runtime.actions.schedule = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("schedule failed"))
        try:
            with self.assertRaises(RuntimeError):
                manager.start(self.recipe, inventory, 5, job_id="job_a")
        finally:
            runtime.actions.schedule = original_schedule

        self.assertEqual(inventory.snapshot(), before)
        self.assertIsNone(manager.get("job_a"))
        self.assertEqual(
            runtime.actions.get(ActionId("production_job:job_a")).state.value,
            "cancelled",
        )

    def test_same_tick_jobs_follow_scheduler_order(self):
        runtime = SimulationRuntime()
        manager = ProductionJobManager(runtime)
        first_inventory = Inventory()
        second_inventory = Inventory()
        first_inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        second_inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        first = manager.start(self.recipe, first_inventory, 2, job_id="first")
        second = manager.start(self.recipe, second_inventory, 2, job_id="second")

        events = manager.advance_to(2)

        self.assertEqual(first.state, ProductionJobState.COMPLETED)
        self.assertEqual(second.state, ProductionJobState.COMPLETED)
        completed = [event.action_id for event in events if event.event_type == "ActionCompleted"]
        self.assertEqual(completed, [first.action_id, second.action_id])


if __name__ == "__main__":
    unittest.main()
