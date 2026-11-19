"""Regression tests for full-frame clearing during screen rendering."""

import unittest
from types import SimpleNamespace

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
