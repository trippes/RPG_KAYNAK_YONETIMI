import unittest

from core.simulation.scheduler import CanonicalScheduler
from core.time import Tick


class TestCanonicalScheduler(unittest.TestCase):
    def test_same_tick_work_is_in_insertion_order(self):
        scheduler = CanonicalScheduler()
        first = scheduler.schedule(Tick(5), "first")
        second = scheduler.schedule(Tick(5), "second")
        scheduler.advance_to(Tick(5))
        self.assertEqual(scheduler.pop_ready(), (first, second))

    def test_past_schedule_and_backward_progression_are_rejected(self):
        scheduler = CanonicalScheduler(Tick(5))
        with self.assertRaises(ValueError):
            scheduler.schedule(Tick(4), "past")
        with self.assertRaises(ValueError):
            scheduler.advance_to(Tick(4))

    def test_cancellation_is_deterministic(self):
        scheduler = CanonicalScheduler()
        cancelled = scheduler.schedule(Tick(1), "cancelled")
        active = scheduler.schedule(Tick(1), "active")
        self.assertTrue(scheduler.cancel(cancelled.work_id))
        scheduler.advance_to(Tick(1))
        self.assertEqual(scheduler.pop_ready(), (active,))
        self.assertFalse(scheduler.cancel(cancelled.work_id))

    def test_scheduler_has_no_callback_requirement(self):
        scheduler = CanonicalScheduler()
        work = scheduler.schedule(Tick(1), "typed.work", {"value": 3})
        self.assertEqual(work.payload, {"value": 3})

