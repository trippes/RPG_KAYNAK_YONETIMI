import unittest

from core.compatibility.legacy_scheduler_adapter import LegacyCallbackSchedulerAdapter
from core.simulation.scheduler import CanonicalScheduler
from core.time import Tick


class TestLegacyCallbackSchedulerAdapter(unittest.TestCase):
    def test_callbacks_are_executed_by_canonical_work_scheduler(self):
        adapter = LegacyCallbackSchedulerAdapter()
        self.assertIsInstance(adapter.canonical_scheduler, CanonicalScheduler)
        received = []
        adapter.schedule(3, lambda: received.append("first"))
        adapter.schedule(3, lambda: received.append("second"))

        processed = adapter.process_until(3)

        self.assertEqual(received, ["first", "second"])
        self.assertEqual([event.event_id for event in processed], [1, 2])
        self.assertEqual(adapter.pending_count, 0)

    def test_callback_can_cancel_later_ready_work(self):
        adapter = LegacyCallbackSchedulerAdapter()
        received = []
        later_id = None

        def cancel_later():
            received.append("first")
            self.assertTrue(adapter.cancel(later_id))

        adapter.schedule(1, cancel_later)
        later_id = adapter.schedule(1, lambda: received.append("cancelled"))

        adapter.process_until(1)

        self.assertEqual(received, ["first"])
        self.assertEqual(adapter.pending_count, 0)

    def test_work_added_by_callback_is_deferred(self):
        adapter = LegacyCallbackSchedulerAdapter()
        received = []

        def first():
            received.append("first")
            adapter.schedule(1, lambda: received.append("second"))

        adapter.schedule(1, first)
        adapter.process_until(1)
        self.assertEqual(received, ["first"])
        self.assertEqual(adapter.pending_count, 1)

        adapter.process_until(1)
        self.assertEqual(received, ["first", "second"])

    def test_exception_consumes_current_work_and_preserves_later_work(self):
        adapter = LegacyCallbackSchedulerAdapter()
        received = []

        def fail():
            received.append("failed")
            raise RuntimeError("callback failed")

        adapter.schedule(1, fail)
        adapter.schedule(1, lambda: received.append("later"))
        with self.assertRaisesRegex(RuntimeError, "callback failed"):
            adapter.process_until(1)

        self.assertEqual(received, ["failed"])
        self.assertEqual(adapter.pending_count, 1)
        adapter.process_until(1)
        self.assertEqual(received, ["failed", "later"])

    def test_due_in_past_work_runs_on_next_process_call(self):
        adapter = LegacyCallbackSchedulerAdapter(start_tick=10)
        received = []
        adapter.schedule(2, lambda: received.append(True))
        adapter.process_until(10)
        self.assertEqual(received, [True])

    def test_cancel_is_idempotent_and_clear_removes_callbacks(self):
        adapter = LegacyCallbackSchedulerAdapter()
        event_id = adapter.schedule(5, lambda: self.fail("must not run"))
        self.assertTrue(adapter.cancel(event_id))
        self.assertFalse(adapter.cancel(event_id))
        adapter.schedule(6, lambda: self.fail("must not run"))
        adapter.clear()
        self.assertEqual(adapter.pending_count, 0)
        self.assertEqual(adapter.process_until(6), [])


if __name__ == "__main__":
    unittest.main()
