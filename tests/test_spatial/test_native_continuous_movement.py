"""Tests for Eldoria-native continuous movement domain contracts."""
import math
import unittest

from core.domain.movement import (
    MovementConfig,
    MovementIntegrator,
    MovementIntent,
    MovementMode,
    MovementState,
)
from core.domain.physics import Vector2
from core.domain.spatial import WorldPoint


class NativeMovementConfigTests(unittest.TestCase):
    def test_speed_multipliers_are_mode_specific(self):
        config = MovementConfig(100, running_speed_multiplier=1.6, stealth_speed_multiplier=0.4)
        self.assertEqual(config.speed_multiplier_for(MovementMode.NORMAL), 1.0)
        self.assertEqual(config.speed_multiplier_for(MovementMode.RUNNING), 1.6)
        self.assertEqual(config.speed_multiplier_for(MovementMode.STEALTH), 0.4)

    def test_config_rejects_invalid_values(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                MovementConfig(value)
        with self.assertRaises(ValueError):
            MovementConfig(-1)
        with self.assertRaises(TypeError):
            MovementConfig(True)


class NativeMovementIntegratorTests(unittest.TestCase):
    def setUp(self):
        self.integrator = MovementIntegrator(MovementConfig(
            120, acceleration=1_000_000.0,
            deceleration=1_000_000.0, braking_deceleration=1_000_000.0,
        ))
        self.state = MovementState(WorldPoint(10, 20))

    def test_normalized_diagonal_motion_has_constant_speed(self):
        result = self.integrator.step(
            self.state, MovementIntent(Vector2(1, 1)), 0.5
        )
        expected = 120 / math.sqrt(2) * 0.5
        self.assertAlmostEqual(result.position.x, 10 + expected)
        self.assertAlmostEqual(result.position.y, 20 + expected)
        self.assertAlmostEqual(result.velocity.length, 120)

    def test_running_and_stealth_multipliers_change_displacement(self):
        running = self.integrator.step(
            self.state, MovementIntent(Vector2(1, 0), MovementMode.RUNNING), 1
        )
        stealth = self.integrator.step(
            self.state, MovementIntent(Vector2(1, 0), MovementMode.STEALTH), 1
        )
        self.assertEqual(running.position, WorldPoint(190, 20))
        self.assertEqual(stealth.position, WorldPoint(70, 20))

    def test_idle_intent_preserves_position_and_zeros_velocity(self):
        result = self.integrator.step(self.state, MovementIntent(), 3)
        self.assertEqual(result.position, self.state.position)
        self.assertEqual(result.velocity, Vector2(0, 0))

    def test_zero_duration_preserves_position(self):
        result = self.integrator.step(
            self.state, MovementIntent(Vector2(1, 0)), 0
        )
        self.assertEqual(result.position, self.state.position)
        self.assertEqual(result.velocity, Vector2(0, 0))

    def test_invalid_delta_is_rejected(self):
        for value in (-1, math.nan, math.inf, True, "0.1"):
            with self.subTest(value=value), self.assertRaises((TypeError, ValueError)):
                self.integrator.step(self.state, MovementIntent(Vector2(1, 0)), value)

    def test_step_does_not_mutate_previous_state(self):
        self.integrator.step(self.state, MovementIntent(Vector2(1, 0)), 1)
        self.assertEqual(self.state.position, WorldPoint(10, 20))
        self.assertEqual(self.state.velocity, Vector2(0, 0))


if __name__ == "__main__":
    unittest.main()
