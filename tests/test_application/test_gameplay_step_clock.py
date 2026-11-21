import math
import unittest

from application.gameplay_step_clock import FixedStepAccumulator


class FixedStepAccumulatorTests(unittest.TestCase):
    def test_default_step_matches_sixty_steps_per_second(self):
        clock = FixedStepAccumulator()
        self.assertAlmostEqual(clock.step_seconds, 1.0 / 60.0)

    def test_partial_elapsed_time_is_carried_forward(self):
        clock = FixedStepAccumulator(step_seconds=0.1)
        self.assertEqual(clock.advance(0.04), 0)
        self.assertEqual(clock.advance(0.05), 0)
        self.assertEqual(clock.advance(0.01), 1)
        self.assertAlmostEqual(clock.accumulated_seconds, 0.0)

    def test_large_frame_time_returns_all_due_steps(self):
        clock = FixedStepAccumulator(step_seconds=0.02)
        self.assertEqual(clock.advance(0.1), 5)

    def test_catch_up_is_bounded_and_excess_whole_steps_are_reported(self):
        clock = FixedStepAccumulator(step_seconds=0.02, max_substeps=3)

        self.assertEqual(clock.advance(0.2), 3)
        self.assertEqual(clock.last_substeps, 3)
        self.assertAlmostEqual(clock.last_dropped_seconds, 0.14)
        self.assertAlmostEqual(clock.total_dropped_seconds, 0.14)
        self.assertAlmostEqual(clock.accumulated_seconds, 0.0)

        self.assertEqual(clock.advance(0.02), 1)
        self.assertEqual(clock.last_substeps, 1)
        self.assertAlmostEqual(clock.last_dropped_seconds, 0.0)
        self.assertAlmostEqual(clock.total_dropped_seconds, 0.14)

    def test_max_substeps_must_be_a_positive_integer(self):
        for value in (0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                FixedStepAccumulator(max_substeps=value)
        for value in (True, 1.5):
            with self.subTest(value=value), self.assertRaises(TypeError):
                FixedStepAccumulator(max_substeps=value)

    def test_inactive_gameplay_discards_partial_time(self):
        clock = FixedStepAccumulator(step_seconds=0.1)
        self.assertEqual(clock.advance(0.06), 0)
        self.assertEqual(clock.advance(3.0, active=False), 0)
        self.assertEqual(clock.accumulated_seconds, 0.0)
        self.assertEqual(clock.advance(0.04), 0)

    def test_zero_elapsed_time_does_not_advance(self):
        clock = FixedStepAccumulator()
        self.assertEqual(clock.advance(0.0), 0)

    def test_invalid_step_duration_is_rejected(self):
        for value in (0, -0.1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                FixedStepAccumulator(value)
        with self.assertRaises(TypeError):
            FixedStepAccumulator(True)
        with self.assertRaises(ValueError):
            FixedStepAccumulator(math.inf)

    def test_invalid_elapsed_time_is_rejected(self):
        clock = FixedStepAccumulator()
        with self.assertRaises(TypeError):
            clock.advance(True)
        with self.assertRaises(ValueError):
            clock.advance(-0.1)
        with self.assertRaises(ValueError):
            clock.advance(math.nan)

    def test_active_flag_must_be_boolean(self):
        clock = FixedStepAccumulator()
        with self.assertRaises(TypeError):
            clock.advance(0.1, active=1)


if __name__ == "__main__":
    unittest.main()
