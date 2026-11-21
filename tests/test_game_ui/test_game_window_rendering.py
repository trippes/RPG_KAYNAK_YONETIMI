"""Regression tests for full-frame clearing during screen rendering."""

import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core.domain.movement import MovementConfig, MovementIntent, MovementMode
from core.domain.physics import Vector2
from application.gameplay_step_clock import FixedStepAccumulator
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

            def step(self, actor_id, intent, delta_seconds, *, target=None):
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
        self.assertEqual(calls[0][1], click_intent)
        self.assertEqual(calls[0][2], 1.0 / 60.0)

    def test_npc_behaviors_advance_on_fixed_steps_while_player_is_idle(self):
        calls = []
        service = SimpleNamespace(
            advance_npc_patrols=lambda delta: calls.append(("patrol", delta)),
            advance_npc_avoidance=lambda delta: calls.append(("avoidance", delta)),
            advance_companions=lambda delta: calls.append(("companions", delta)),
        )
        window = SimpleNamespace(
            service=service,
            _npc_simulation_clock=FixedStepAccumulator(),
            _set_notice=lambda *_args: None,
        )

        GameWindow._advance_npc_simulation(
            window, 1.0 / 30.0, active=True,
        )

        self.assertEqual(
            [name for name, _delta in calls],
            ["patrol", "avoidance", "companions"] * 2,
        )
        self.assertTrue(all(delta == 1.0 / 60.0 for _name, delta in calls))

    def test_npc_simulation_uses_the_central_service_entry_point(self):
        calls = []
        service = SimpleNamespace(
            advance_npc_simulation=lambda delta: calls.append(delta),
        )
        window = SimpleNamespace(
            service=service,
            _npc_simulation_clock=FixedStepAccumulator(),
            _set_notice=lambda *_args: None,
        )

        GameWindow._advance_npc_simulation(
            window, 1.0 / 30.0, active=True,
        )

        self.assertEqual(calls, [1.0 / 60.0, 1.0 / 60.0])

    def test_npc_simulation_clock_resets_when_gameplay_is_paused(self):
        calls = []
        service = SimpleNamespace(
            advance_npc_patrols=lambda delta: calls.append(("patrol", delta)),
            advance_npc_avoidance=lambda delta: calls.append(("avoidance", delta)),
            advance_companions=lambda delta: calls.append(("companions", delta)),
        )
        clock = FixedStepAccumulator()
        window = SimpleNamespace(
            service=service,
            _npc_simulation_clock=clock,
            _set_notice=lambda *_args: None,
        )

        GameWindow._advance_npc_simulation(
            window, 1.0 / 120.0, active=True,
        )
        self.assertEqual(clock.accumulated_seconds, 1.0 / 120.0)

        GameWindow._advance_npc_simulation(
            window, 1.0 / 60.0, active=False,
        )

        self.assertEqual(calls, [])
        self.assertEqual(clock.accumulated_seconds, 0.0)

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


    def test_click_to_move_preserves_current_movement_mode(self):
        calls = []

        class Clock:
            step_seconds = 1.0 / 60.0

            def advance(self, _elapsed, *, active):
                return 1 if active else 0

        class Controller:
            def __init__(self, *_args, **_kwargs):
                pass

            def step(self, actor_id, intent, delta_seconds, *, target=None):
                calls.append((actor_id, intent, delta_seconds))

        click_intent = MovementIntent(Vector2(1.0, 0.0))
        screen = SimpleNamespace(click_move_intent=lambda: click_intent)
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
                window, 1.0 / 60.0,
                MovementIntent(mode=MovementMode.STEALTH),
                active=True, click_to_move=True,
            )

        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1].direction, click_intent.direction)
        self.assertIs(calls[0][1].mode, MovementMode.STEALTH)

    def test_click_to_move_continues_when_keyboard_focus_is_lost(self):
        calls = []

        class Clock:
            step_seconds = 1.0 / 60.0

            def advance(self, _elapsed, *, active):
                self.active = active
                return 1 if active else 0

        class Controller:
            def __init__(self, *_args, **_kwargs):
                pass

            def step(self, actor_id, intent, delta_seconds, *, target=None):
                calls.append((actor_id, intent, delta_seconds))

        screen = SimpleNamespace(
            click_move_intent=lambda: MovementIntent(Vector2(1.0, 0.0)),
        )
        service = SimpleNamespace(
            player_actor_id="hero",
            hex_actor_binding=SimpleNamespace(
                physics_snapshot=object(), player_body=object(),
            ),
            npc_physics_bodies={},
        )
        clock = Clock()
        window = SimpleNamespace(
            service=service,
            _movement_configs={"hero": MovementConfig(max_speed=100.0)},
            movement_input=SimpleNamespace(focused=False),
            _movement_clock=clock,
            screens={"main": screen},
            gameplay_screen="main",
        )

        with patch("game_ui.game_window.ContinuousPlayerMovementController", Controller):
            GameWindow._advance_continuous_player_movement(
                window, 1.0 / 60.0, MovementIntent(),
                active=True, click_to_move=True,
            )

        self.assertTrue(clock.active)
        self.assertEqual(len(calls), 1)

if __name__ == "__main__":
    unittest.main()
