"""Tests for Eldoria's native Pygame movement input adapter."""

import unittest
from types import SimpleNamespace

from core.domain.movement import MovementIntent, MovementMode
from core.domain.physics import Vector2
from game_ui.movement_input import PygameMovementInput


class FakeKeys:
    def __init__(self, pressed=()):
        self.pressed = set(pressed)

    def __getitem__(self, key):
        return key in self.pressed


class FakeBackend:
    K_d = 1
    K_RIGHT = 2
    K_a = 3
    K_LEFT = 4
    K_w = 5
    K_UP = 6
    K_s = 7
    K_DOWN = 8
    K_LALT = 9
    K_RALT = 10
    K_LSHIFT = 11
    K_RSHIFT = 12
    WINDOWFOCUSLOST = 100
    WINDOWFOCUSGAINED = 101

    def __init__(self, provider):
        self.key = SimpleNamespace(get_pressed=provider)


class PygameMovementInputTests(unittest.TestCase):
    def setUp(self):
        self.keys = FakeKeys()
        self.backend = FakeBackend(lambda: self.keys)
        self.adapter = PygameMovementInput(self.backend)

    def test_wasd_and_arrows_map_to_native_direction(self):
        cases = (
            ({5}, Vector2(0.0, -1.0)),
            ({8}, Vector2(0.0, 1.0)),
            ({3}, Vector2(-1.0, 0.0)),
            ({2}, Vector2(1.0, 0.0)),
            ({5, 2}, Vector2(1.0, -1.0)),
            ({5, 6}, Vector2(0.0, -1.0)),
        )
        for pressed, expected in cases:
            with self.subTest(pressed=pressed):
                self.keys.pressed = pressed
                self.assertEqual(self.adapter.read_intent().direction, expected)

    def test_shift_is_hold_to_run(self):
        self.keys.pressed = {11}
        self.assertIs(self.adapter.read_intent().mode, MovementMode.RUNNING)
        self.keys.pressed.clear()
        self.assertIs(self.adapter.read_intent().mode, MovementMode.NORMAL)

    def test_alt_toggles_stealth_on_press_edges(self):
        self.keys.pressed = {9}
        self.assertIs(self.adapter.read_intent().mode, MovementMode.STEALTH)
        self.assertIs(self.adapter.read_intent().mode, MovementMode.STEALTH)
        self.keys.pressed.clear()
        self.adapter.read_intent()
        self.keys.pressed = {9}
        self.assertIs(self.adapter.read_intent().mode, MovementMode.NORMAL)

    def test_stealth_has_priority_over_running(self):
        self.keys.pressed = {9, 11}
        self.assertIs(self.adapter.read_intent().mode, MovementMode.STEALTH)

    def test_focus_loss_clears_input_and_requires_alt_release(self):
        self.keys.pressed = {9, 11, 1}
        self.adapter.handle_events([SimpleNamespace(type=100)])
        self.assertFalse(self.adapter.focused)
        self.assertEqual(self.adapter.read_intent(), MovementIntent())
        self.adapter.handle_events([SimpleNamespace(type=101)])
        self.assertTrue(self.adapter.focused)
        self.assertIs(self.adapter.read_intent().mode, MovementMode.NORMAL)
        self.keys.pressed.clear()
        self.adapter.read_intent()
        self.keys.pressed = {9}
        self.assertIs(self.adapter.read_intent().mode, MovementMode.STEALTH)

    def test_no_keys_produces_idle_intent(self):
        self.assertEqual(self.adapter.read_intent(), MovementIntent())


if __name__ == "__main__":
    unittest.main()
