"""Regression tests for gameplay navigation and viewport resizing."""

import unittest
from types import SimpleNamespace

from game_ui.input import InputMapper, InputState
from game_ui.renderer import NAV_TABS
from game_ui.screens.main_screen import MainScreen
from game_ui.screens.dialogue_screen import DialogueScreen
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


class GameplayNavigationTests(unittest.TestCase):
    def test_market_is_not_exposed_as_keyboard_or_navigation_shortcut(self):
        state = InputMapper().collect([
            SimpleNamespace(type="KEYDOWN", key="m", unicode="m")
        ])
        self.assertNotIn("market", state.actions)
        self.assertNotIn("market", dict(NAV_TABS))

    def test_market_opens_from_vendor_dialogue_action(self):
        choice = SimpleNamespace(
            choice_id="open_market",
            text="Pazar ürünlerini görmek istiyorum.",
            action="open_market",
        )
        service = SimpleNamespace(
            application=SimpleNamespace(
                holder=SimpleNamespace(
                    current=SimpleNamespace(
                        social=SimpleNamespace(dialogues={})
                    )
                )
            ),
            choose_dialogue=lambda *_args: None,
        )
        screen = DialogueScreen(service)
        screen.context = ("hero", "market_vendor", "market_dialogue")
        screen.node = SimpleNamespace(node_id="start", choices=(choice,))
        screen.opening_stage = "dialogue"

        result = screen.handle(InputState(actions={"confirm"}))

        self.assertEqual(result, "market")
        self.assertFalse(screen.is_active())

    def test_opening_market_from_dialogue_restores_world_as_current_screen(self):
        from game_ui.game_window import GameWindow

        opened = []
        window = GameWindow.__new__(GameWindow)
        window.gameplay_active = True
        window.gameplay_screen = "main"
        window.current = "dialogue"
        window._current_location = lambda: SimpleNamespace(activities=("market",))
        window.window_manager = SimpleNamespace(
            windows={"market": object()},
            open=lambda window_id: opened.append(window_id),
        )

        self.assertTrue(window._set_current("market"))
        self.assertEqual(window.current, "main")
        self.assertEqual(opened, ["market"])

    def test_market_window_is_blocked_outside_market_locations(self):
        from game_ui.game_window import GameWindow

        opened = []
        notices = []
        window = GameWindow.__new__(GameWindow)
        window.gameplay_active = True
        window.gameplay_screen = "main"
        window.current = "main"
        window._current_location = lambda: SimpleNamespace(activities=())
        window._set_notice = lambda *args: notices.append(args)
        window.window_manager = SimpleNamespace(
            windows={"market": object()},
            open=lambda window_id: opened.append(window_id),
        )

        self.assertFalse(window._set_current("market"))
        self.assertEqual(opened, [])
        self.assertEqual(notices[0][1], "error")

    def test_main_screen_quick_menu_does_not_open_market(self):
        screen = MainScreen(service=None)
        self.assertNotIn("market", {target for target, _label in screen.menu_options})

    def test_resize_updates_viewport_and_shrinks_oversized_windows(self):
        backend = type("Backend", (), {"Rect": FakeRect})
        manager = WindowManager(backend, 960, 640)
        manager.register("inventory", object(), (24, 110, 912, 470))

        manager.resize(800, 500)

        window = manager.windows["inventory"]
        self.assertEqual((manager.width, manager.height), (800, 500))
        self.assertEqual(window.bounds.width, 800)
        self.assertLessEqual(window.bounds.height, 500)
        self.assertGreaterEqual(window.bounds.x, 0)
        self.assertLessEqual(window.bounds.right, 800)


    def test_empty_load_slot_starts_a_fresh_game(self):
        from pathlib import Path
        from game_ui.game_window import GameWindow

        window = GameWindow.__new__(GameWindow)
        window.selected_slot = None
        window.save_path = None
        window.screens = {"save_slots": SimpleNamespace(mode="load", selected=0)}
        started = []
        window._start_new_game = lambda: started.append(True)

        result = window._select_save_slot(2, Path("slot_3.json"), False)

        self.assertEqual(result, "opening")
        self.assertEqual(window.selected_slot, 2)
        self.assertEqual(window.save_path, Path("slot_3.json"))
        self.assertEqual(window.selected_slot, 2)
        self.assertEqual(started, [True])

    def test_save_picker_reselects_the_slot_used_to_start_new_game(self):
        from game_ui.game_window import GameWindow

        window = GameWindow.__new__(GameWindow)
        window.selected_slot = 6
        window.screens = {"save_slots": SimpleNamespace(selected=0)}

        result = window._open_save_slots("save", "main")

        self.assertEqual(result, "save_slots")
        self.assertEqual(window.screens["save_slots"].selected, 6)


if __name__ == "__main__":
    unittest.main()
