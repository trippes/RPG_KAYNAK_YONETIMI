import unittest

from core.foundation import EntityId
from core.simulation import ActionProcessor, ActionState
from core.time import Tick


class TestActionProcessor(unittest.TestCase):
    def test_lifecycle_events_are_deterministic(self):
        processor = ActionProcessor()
        action = processor.create(EntityId("entity_1"), Tick(2))
        processor.schedule(action.action_id, Tick(3))
        events = processor.advance_to(Tick(5))
        self.assertEqual(
            [event.event_type for event in events],
            ["ActionCreated", "ActionScheduled", "ActionStarted", "ActionCompleted"],
        )
        self.assertEqual(action.state, ActionState.COMPLETED)
        self.assertEqual(action.completed_tick, Tick(5))
        self.assertEqual([event.simulation_tick.value for event in events], [0, 0, 3, 5])

    def test_zero_duration_action_completes_at_start_tick(self):
        processor = ActionProcessor()
        action = processor.create(EntityId("entity_1"), Tick(0))
        processor.schedule(action.action_id, Tick(2))
        events = processor.advance_to(Tick(2))
        self.assertEqual(action.state, ActionState.COMPLETED)
        self.assertEqual(action.completed_tick, Tick(2))
        self.assertEqual(events[-1].event_type, "ActionCompleted")

    def test_cancelled_action_does_not_start(self):
        processor = ActionProcessor()
        action = processor.create(EntityId("entity_1"), Tick(1))
        processor.schedule(action.action_id, Tick(2))
        processor.cancel(action.action_id, "cancelled")
        events = processor.advance_to(Tick(3))
        self.assertEqual(action.state, ActionState.CANCELLED)
        self.assertNotIn("ActionStarted", [event.event_type for event in events])
        self.assertEqual(processor.scheduler.pending_count, 0)

    def test_failed_started_action_clears_completion_work(self):
        processor = ActionProcessor()
        action = processor.create(EntityId("entity_1"), Tick(5))
        processor.schedule(action.action_id, Tick(0))
        processor.advance_to(Tick(0))
        self.assertEqual(processor.scheduler.pending_count, 1)
        processor.fail(action.action_id, "failed")
        self.assertEqual(processor.scheduler.pending_count, 0)

    def test_backwards_progression_is_rejected(self):
        processor = ActionProcessor()
        processor.advance_to(Tick(3))
        with self.assertRaises(ValueError):
            processor.advance_to(Tick(2))

