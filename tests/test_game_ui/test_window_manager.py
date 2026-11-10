"""Integration tests for quest journal window management."""

import unittest

from game_ui.input import InputState
from game_ui.window_manager import WindowManager


class FakeRect:
    def __init__(self, *values):
        if len(values) == 1:
            values = tuple(values[0])
        self.x, self.y, self.width, self.height = values

    @property
    def right(self):
        return self.x + self.width

    @property
    def bottom(self):
        return self.y + self.height

    @property
    def topleft(self):
        return self.x, self.y

    @topleft.setter
    def topleft(self, value):
        self.x, self.y = value

    def collidepoint(self, position):
        x, y = position
        return self.x <= x < self.right and self.y <= y < self.bottom


class DummyScreen:
    pointer_capture = False

    def __init__(self):
        self.inputs = []

    def handle(self, state):
        self.inputs.append(state)
        return None

    def render(self, _renderer):
        return None


class QuestWindowManagerTests(unittest.TestCase):
    def setUp(self):
        self.backend = type("Backend", (), {"Rect": FakeRect})
        self.screen = DummyScreen()
        self.manager = WindowManager(self.backend, 960, 640)
        self.manager.register(
            "quest_log",
            self.screen,
            (24, 110, 912, 470),
            content_origin=(24, 126),
            title="Görev Günlüğü",
        )

    def test_j_shortcut_opens_and_closes_quest_window(self):
        self.assertTrue(
            self.manager.handle_input(InputState(actions={"quest_log"}))
        )
        self.assertTrue(self.manager.is_open("quest_log"))

        self.assertTrue(
            self.manager.handle_input(InputState(actions={"quest_log"}))
        )
        self.assertFalse(self.manager.is_open("quest_log"))

    def test_close_button_closes_only_the_quest_window(self):
        self.manager.open("quest_log")
        window = self.manager.windows["quest_log"]
        close_position = (window.bounds.right - 16, window.bounds.y + 16)
        self.manager.handle_input(
            InputState(
                mouse_pos=close_position,
                mouse_clicked=True,
                mouse_button_down=True,
            )
        )
        self.assertFalse(self.manager.is_open("quest_log"))

    def test_title_bar_drag_moves_window_and_releases_pointer(self):
        self.manager.open("quest_log")
        window = self.manager.windows["quest_log"]
        self.manager.handle_input(
            InputState(
                mouse_pos=(100, 120),
                mouse_clicked=True,
                mouse_button_down=True,
            )
        )
        self.assertTrue(window.dragging)

        self.manager.handle_input(
            InputState(mouse_pos=(180, 190), mouse_motion=True)
        )
        self.assertEqual(window.bounds.topleft, (48, 180))

        self.manager.handle_input(
            InputState(mouse_pos=(180, 190), mouse_button_up=True)
        )
        self.assertFalse(window.dragging)

    def test_content_click_is_translated_to_screen_coordinates(self):
        self.manager.open("quest_log")
        self.manager.handle_input(
            InputState(
                mouse_pos=(124, 210),
                mouse_clicked=True,
                mouse_button_down=True,
            )
        )
        self.assertEqual(self.screen.inputs[-1].mouse_pos, (124, 194))
        self.assertTrue(self.screen.inputs[-1].mouse_clicked)


if __name__ == "__main__":
    unittest.main()
