"""Regression tests for the gameplay window shortcuts and hidden navigation tabs."""

import unittest

from game_ui.game_window import NAV_SCREENS
from game_ui.input import InputMapper, InputState
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

    def collidepoint(self, position):
        x, y = position
        return self.x <= x < self.right and self.y <= y < self.bottom


class FakeBackend:
    KEYDOWN = "KEYDOWN"
    QUIT = "QUIT"
    MOUSEBUTTONDOWN = "MOUSEBUTTONDOWN"
    MOUSEBUTTONUP = "MOUSEBUTTONUP"
    MOUSEMOTION = "MOUSEMOTION"
    MOUSEWHEEL = "MOUSEWHEEL"
    Rect = FakeRect


class DummyScreen:
    def handle(self, _state):
        return None

    def render(self, _renderer):
        return None


class GameplayNavigationTests(unittest.TestCase):
    def test_gameplay_navigation_tabs_are_disabled(self):
        self.assertEqual(NAV_SCREENS, frozenset())

    def test_c_opens_and_closes_character_window(self):
        manager = WindowManager(FakeBackend, 960, 640)
        manager.register("character", DummyScreen(), (80, 90, 760, 470))

        manager.handle_input(InputState(actions={"character"}))
        self.assertTrue(manager.is_open("character"))

        manager.handle_input(InputState(actions={"character"}))
        self.assertFalse(manager.is_open("character"))

    def test_character_close_button_closes_window(self):
        manager = WindowManager(FakeBackend, 960, 640)
        manager.register("character", DummyScreen(), (80, 90, 760, 470))
        manager.open("character")
        window = manager.windows["character"]
        close_position = (window.bounds.right - 16, window.bounds.y + 16)

        manager.handle_input(InputState(
            mouse_pos=close_position,
            mouse_clicked=True,
            mouse_button_down=True,
        ))

        self.assertFalse(manager.is_open("character"))

    def test_p_maps_to_production_not_character(self):
        state = InputMapper(FakeBackend()).collect([
            type("KeyEvent", (), {
                "type": "KEYDOWN", "key": "p", "unicode": "p",
            })()
        ])
        self.assertIn("production", state.actions)
        self.assertNotIn("character", state.actions)

    def test_m_maps_to_map_and_x_is_not_a_map_shortcut(self):
        mapper = InputMapper(FakeBackend())
        map_state = mapper.collect([
            type("KeyEvent", (), {
                "type": "KEYDOWN", "key": "m", "unicode": "m",
            })()
        ])
        x_state = mapper.collect([
            type("KeyEvent", (), {
                "type": "KEYDOWN", "key": "x", "unicode": "x",
            })()
        ])
        self.assertIn("map", map_state.actions)
        self.assertNotIn("map", x_state.actions)

    def test_p_and_m_toggle_their_windows(self):
        manager = WindowManager(FakeBackend, 960, 640)
        manager.register("production", DummyScreen(), (24, 110, 912, 470))
        manager.register("map", DummyScreen(), (24, 110, 912, 470))

        manager.handle_input(InputState(actions={"production"}))
        manager.handle_input(InputState(actions={"map"}))
        self.assertTrue(manager.is_open("production"))
        self.assertTrue(manager.is_open("map"))

        manager.handle_input(InputState(actions={"production"}))
        manager.handle_input(InputState(actions={"map"}))
        self.assertFalse(manager.is_open("production"))
        self.assertFalse(manager.is_open("map"))


if __name__ == "__main__":
    unittest.main()
