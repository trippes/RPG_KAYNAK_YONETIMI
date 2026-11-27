import math
import unittest

from application.simulation_time_driver import SimulationTimeDriver


class SimulationTimeDriverTests(unittest.TestCase):
    def test_default_rate_is_3600_ticks_per_real_second(self):
        driver = SimulationTimeDriver()
        self.assertEqual(driver.ticks_per_real_second, 3600)
        self.assertEqual(driver.advance(1.0), 3600)
        self.assertEqual(driver.advance(10.0), 36000)

    def test_sixty_fps_frames_produce_sixty_ticks_each(self):
        driver = SimulationTimeDriver()
        self.assertEqual(sum(driver.advance(1 / 60) for _ in range(60)), 3600)

    def test_fractional_ticks_are_carried_between_frames(self):
        driver = SimulationTimeDriver(ticks_per_real_second=10)
        self.assertEqual(driver.advance(0.04), 0)
        self.assertEqual(driver.advance(0.05), 0)
        self.assertEqual(driver.advance(0.01), 1)
        self.assertAlmostEqual(driver.fractional_ticks, 0.0)

    def test_inactive_time_is_not_accumulated(self):
        driver = SimulationTimeDriver(ticks_per_real_second=10)
        self.assertEqual(driver.advance(0.06), 0)
        self.assertEqual(driver.advance(3.0, active=False), 0)
        self.assertEqual(driver.fractional_ticks, 0.0)
        self.assertEqual(driver.advance(0.04), 0)

    def test_speed_multiplier_is_central_and_preserves_fraction(self):
        driver = SimulationTimeDriver(ticks_per_real_second=10)
        self.assertEqual(driver.advance(0.05), 0)
        driver.set_speed_multiplier(2)
        self.assertEqual(driver.advance(0.025), 1)
        self.assertEqual(driver.advance(1.0), 20)

    def test_zero_elapsed_time_does_not_advance_or_discard_fraction(self):
        driver = SimulationTimeDriver(ticks_per_real_second=10)
        self.assertEqual(driver.advance(0.05), 0)
        self.assertEqual(driver.advance(0.0), 0)
        self.assertAlmostEqual(driver.fractional_ticks, 0.5)
        self.assertEqual(driver.advance(0.05), 1)

    def test_invalid_rate_is_rejected(self):
        for value in (0, -1):
            with self.subTest(value=value), self.assertRaises(ValueError):
                SimulationTimeDriver(value)
        for value in (True, 1.5):
            with self.subTest(value=value), self.assertRaises(TypeError):
                SimulationTimeDriver(value)

    def test_invalid_multiplier_is_rejected(self):
        driver = SimulationTimeDriver()
        for value in (0, -1, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                driver.set_speed_multiplier(value)
        with self.assertRaises(TypeError):
            driver.set_speed_multiplier(True)

    def test_invalid_elapsed_time_is_rejected(self):
        driver = SimulationTimeDriver()
        with self.assertRaises(TypeError):
            driver.advance(True)
        for value in (-0.1, math.inf, math.nan):
            with self.subTest(value=value), self.assertRaises(ValueError):
                driver.advance(value)

    def test_active_flag_must_be_boolean(self):
        with self.assertRaises(TypeError):
            SimulationTimeDriver().advance(0.1, active=1)


if __name__ == "__main__":
    unittest.main()
