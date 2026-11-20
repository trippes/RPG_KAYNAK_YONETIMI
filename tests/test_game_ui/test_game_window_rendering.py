"""Regression tests for full-frame clearing during screen rendering."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.domain.movement import MovementConfig, MovementIntent
from core.domain.physics import Vector2
from game_ui.game_window import GameWindow


class RecordingRenderer:
    def __init__(self, calls):
        self.calls = calls

    def clear(self):
        self.calls.append("clear")


class RecordingScreen:
    def __init__(self, name, calls):
        self.name = name
        self.calls = calls

    def render(self, _renderer):
        self.calls.append(self.name)


class RecordingWindowManager:
    def __init__(self, calls):
        self.calls = calls

    def render(self, _renderer):
        self.calls.append("windows")


class RecordingDialogue(RecordingScreen):
    def is_active(self):
        return True


class TestGameWindowRendering(unittest.TestCase):
    def test_gameplay_frame_clears_before_world_and_overlays(self):
        calls = []
        window = SimpleNamespace(
            renderer=RecordingRenderer(calls),
            gameplay_active=True,
            gameplay_screen="main",
            screens={
                "main": RecordingScreen("world", calls),
                "dialogue": RecordingDialogue("dialogue", calls),
            },
            window_manager=RecordingWindowManager(calls),
        )

        GameWindow._render_current(window)

        self.assertEqual(calls, ["clear", "world", "windows", "dialogue"])

    def test_click_to_move_uses_shared_fixed_step_controller_intent(self):
        calls = []

        class Clock:
            step_seconds = 1.0 / 60.0

            def advance(self, _elapsed, *, active):
                self.active = active
                return 1 if active else 0

        class Controller:
            def __init__(self, *_args, **_kwargs):
                pass

            def step(self, actor_id, intent, delta_seconds):
                calls.append((actor_id, intent, delta_seconds))

        click_intent = MovementIntent(Vector2(1.0, 0.0))
        screen = SimpleNamespace(
            click_move_intent=lambda: click_intent,
        )
        service = SimpleNamespace(
            player_actor_id="hero",
            hex_actor_binding=SimpleNamespace(
                physics_snapshot=object(), player_body=object(),
            ),
            npc_physics_bodies={},
        )
        window = SimpleNamespace(
            service=service,
            _movement_configs={"hero": MovementConfig(max_speed=100.0)},
            movement_input=SimpleNamespace(focused=True),
            _movement_clock=Clock(),
            screens={"main": screen},
            gameplay_screen="main",
        )

        with patch("game_ui.game_window.ContinuousPlayerMovementController", Controller):
            GameWindow._advance_continuous_player_movement(
                window, 1.0 / 60.0, MovementIntent(),
                active=True, click_to_move=True,
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0], "hero")
        self.assertIs(calls[0][1], click_intent)
        self.assertEqual(calls[0][2], 1.0 / 60.0)

    def test_non_gameplay_screen_clears_before_rendering_screen(self):
        calls = []
        window = SimpleNamespace(
            renderer=RecordingRenderer(calls),
            gameplay_active=False,
            current="save_slots",
            screens={"save_slots": RecordingScreen("save_slots", calls)},
        )

        GameWindow._render_current(window)

        self.assertEqual(calls, ["clear", "save_slots"])


if __name__ == "__main__":
    unittest.main()
