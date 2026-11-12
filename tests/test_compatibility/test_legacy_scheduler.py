import unittest

from time_system.scheduler import Scheduler


class TestLegacySchedulerContracts(unittest.TestCase):
    def test_ready_callbacks_run_in_fifo_order(self):
        scheduler = Scheduler()
        received = []
        scheduler.schedule(5, lambda: received.append("first"))
        scheduler.schedule(5, lambda: received.append("second"))

        processed = scheduler.process_until(5)

        self.assertEqual(received, ["first", "second"])
        self.assertEqual([event.event_id for event in processed], [1, 2])
        self.assertEqual(scheduler.pending_count, 0)

    def test_callback_can_cancel_later_ready_callback(self):
        scheduler = Scheduler()
        received = []
        later_id = None

        def cancel_later():
            received.append("first")
            self.assertTrue(scheduler.cancel(later_id))

        scheduler.schedule(1, cancel_later)
        later_id = scheduler.schedule(1, lambda: received.append("cancelled"))

        scheduler.process_until(1)

        self.assertEqual(received, ["first"])
        self.assertEqual(scheduler.pending_count, 0)

    def test_callback_added_work_is_deferred_to_next_process_call(self):
        scheduler = Scheduler()
        received = []

        def first():
            received.append("first")
            scheduler.schedule(1, lambda: received.append("second"))

        scheduler.schedule(1, first)
        scheduler.process_until(1)

        self.assertEqual(received, ["first"])
        self.assertEqual(scheduler.pending_count, 1)

        scheduler.process_until(1)

        self.assertEqual(received, ["first", "second"])
        self.assertEqual(scheduler.pending_count, 0)

    def test_callback_exception_does_not_repeat_completed_work(self):
        scheduler = Scheduler()
        received = []

        def fail_once():
            received.append("first")
            raise RuntimeError("callback failed")

        scheduler.schedule(1, fail_once)
        scheduler.schedule(1, lambda: received.append("second"))

        with self.assertRaisesRegex(RuntimeError, "callback failed"):
            scheduler.process_until(1)

        self.assertEqual(received, ["first"])
        self.assertEqual(scheduler.pending_count, 1)

        scheduler.process_until(1)

        self.assertEqual(received, ["first", "second"])
        self.assertEqual(scheduler.pending_count, 0)

    def test_cancelled_event_cannot_be_cancelled_twice(self):
        scheduler = Scheduler()
        event_id = scheduler.schedule(1, lambda: self.fail("must not run"))

        self.assertTrue(scheduler.cancel(event_id))
        self.assertFalse(scheduler.cancel(event_id))
        self.assertEqual(scheduler.pending_count, 0)
        self.assertEqual(scheduler.process_until(1), [])


if __name__ == "__main__":
    unittest.main()
