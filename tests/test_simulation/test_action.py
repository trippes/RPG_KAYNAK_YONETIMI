import unittest

from core.foundation import ActionId, EntityId
from core.simulation.action import Action, ActionState
from core.time import Tick


class TestCanonicalAction(unittest.TestCase):
    def make_action(self, duration=3):
        return Action(
            action_id=ActionId("action_1"),
            owner_id=EntityId("entity_1"),
            created_tick=Tick(0),
            duration=Tick(duration),
            context={"kind": "test"},
        )

    def test_valid_lifecycle_and_duration(self):
        action = self.make_action()
        action.schedule(Tick(2))
        action.start(Tick(2))
        self.assertEqual(action.completion_tick, Tick(5))
        action.complete(Tick(5), result={"ok": True})
        self.assertEqual(action.state, ActionState.COMPLETED)
        self.assertEqual(action.completed_tick, Tick(5))

    def test_cancel_is_valid_before_completion(self):
        action = self.make_action()
        action.cancel(Tick(0), "user_cancelled")
        self.assertEqual(action.state, ActionState.CANCELLED)

    def test_failed_and_invalid_transitions(self):
        action = self.make_action()
        with self.assertRaises(ValueError):
            action.start(Tick(0))
        action.schedule(Tick(0))
        action.start(Tick(0))
        action.fail(Tick(1), {"reason": "test"})
        self.assertEqual(action.state, ActionState.FAILED)
        with self.assertRaises(ValueError):
            action.complete(Tick(3))

    def test_action_state_is_not_publicly_mutable(self):
        action = self.make_action()
        with self.assertRaises(AttributeError):
            action.state = ActionState.STARTED

