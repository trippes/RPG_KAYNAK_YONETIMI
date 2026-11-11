"""Integration tests for quest journal window management."""

import unittest

from game_ui.input import InputState
from game_ui.window_manager import WindowManager
from game_ui.renderer import ResponsiveLayout


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



class DragSourceScreen(DummyScreen):
    pointer_capture = False

    def __init__(self):
        super().__init__()
        self.payload = {"item_id": "health_potion", "quantity": 2}
        self.cancelled = False

    def handle(self, state):
        self.inputs.append(state)
        if state.mouse_clicked:
            self.pointer_capture = True
        if state.mouse_button_up:
            self.pointer_capture = False
        return None

    def dragged_item_payload(self):
        return self.payload if self.pointer_capture else None

    def cancel_drag(self):
        self.pointer_capture = False
        self.cancelled = True


class DropTargetScreen(DummyScreen):
    def __init__(self):
        super().__init__()
        self.received = []

    def receive_external_item(self, item_id, quantity):
        self.received.append((item_id, quantity))
        return True

class ResponsiveLayoutTests(unittest.TestCase):
    def test_grid_column_count_tracks_available_width(self):
        narrow, narrow_columns, _ = ResponsiveLayout.grid(
            (0, 0, 240, 260), 20, min_cell=48, max_cell=64, gap=6
        )
        wide, wide_columns, _ = ResponsiveLayout.grid(
            (0, 0, 420, 260), 20, min_cell=48, max_cell=64, gap=6
        )

        self.assertEqual(len(narrow), 20)
        self.assertEqual(len(wide), 20)
        self.assertGreater(wide_columns, narrow_columns)

    def test_split_columns_fill_available_width_and_keep_gaps(self):
        columns = ResponsiveLayout.split_columns(
            (20, 30, 800, 300), (1, 2, 1), gap=10
        )

        self.assertEqual(columns[0][0], 20)
        self.assertEqual(columns[-1][0] + columns[-1][2], 820)
        self.assertEqual(columns[1][0] - (columns[0][0] + columns[0][2]), 10)
        self.assertEqual(columns[2][0] - (columns[1][0] + columns[1][2]), 10)


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


    def test_dragged_inventory_item_is_delivered_to_container_window(self):
        source = DragSourceScreen()
        target = DropTargetScreen()
        manager = WindowManager(self.backend, 960, 640)
        manager.register("inventory", source, (24, 110, 240, 300))
        manager.register("container", target, (300, 110, 240, 300))
        manager.open("inventory")
        manager.open("container")
        manager.focus("inventory")

        manager.handle_input(InputState(
            mouse_pos=(100, 170), mouse_clicked=True, mouse_button_down=True
        ))
        manager.handle_input(InputState(
            mouse_pos=(360, 190), mouse_motion=True
        ))
        manager.handle_input(InputState(
            mouse_pos=(360, 190), mouse_button_up=True
        ))

        self.assertEqual(target.received, [("health_potion", 2)])
        self.assertTrue(source.cancelled)
        self.assertEqual(manager.focused_id, "container")

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

    def test_frameless_window_keeps_content_at_window_origin_and_has_custom_close(self):
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "container", DummyScreen(), (40, 70, 920, 560),
            content_origin=(24, 126), title="Konteyner",
            frame=False, close_offset=(808, 25),
        )
        window = manager.open("container")

        self.assertEqual(manager._content_destination(window), (40, 70))
        self.assertEqual(manager._close_rect(window).topleft, (848, 95))
        self.assertEqual(manager._title_rect(window).height, 18)

        manager.handle_input(InputState(
            mouse_pos=(860, 107), mouse_clicked=True, mouse_button_down=True,
        ))
        self.assertFalse(manager.is_open("container"))

    def test_responsive_frameless_close_button_scales_with_container(self):
        screen = DummyScreen()
        screen.scale_to_window = True
        screen.design_size = (920, 560)
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "container", screen, (40, 70, 460, 280),
            content_origin=(24, 126), frame=False, close_offset=(808, 25),
        )

        close = manager._close_rect(manager.windows["container"])

        self.assertEqual(close.topleft, (444, 82))
        self.assertEqual((close.width, close.height), (12, 12))

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

    def test_right_edge_resizes_window_and_stops_at_screen_boundary(self):
        self.manager.open("quest_log")
        window = self.manager.windows["quest_log"]
        start = (window.bounds.right - 2, window.bounds.y + 180)

        self.manager.handle_input(InputState(
            mouse_pos=start, mouse_clicked=True, mouse_button_down=True,
        ))
        self.assertTrue(window.resizing)
        self.assertEqual(window.resize_edges, ("right",))

        self.manager.handle_input(InputState(
            mouse_pos=(start[0] + 80, start[1]), mouse_motion=True,
        ))
        self.assertEqual(window.bounds.right, 960)
        self.assertEqual(window.bounds.width, 936)

        self.manager.handle_input(InputState(
            mouse_pos=(960, start[1]), mouse_button_up=True,
        ))
        self.assertFalse(window.resizing)

    def test_bottom_right_corner_resizes_both_dimensions(self):
        self.manager.open("quest_log")
        window = self.manager.windows["quest_log"]
        start = (window.bounds.right - 2, window.bounds.bottom - 2)

        self.manager.handle_input(InputState(
            mouse_pos=start, mouse_clicked=True, mouse_button_down=True,
        ))
        self.assertEqual(set(window.resize_edges), {"right", "bottom"})

        self.manager.handle_input(InputState(
            mouse_pos=(start[0] - 1000, start[1] - 1000), mouse_motion=True,
        ))
        self.assertEqual(
            (window.bounds.width, window.bounds.height),
            (self.manager.MIN_WIDTH, self.manager.MIN_HEIGHT),
        )

        self.manager.handle_input(InputState(
            mouse_pos=(start[0] - 1000, start[1] - 1000), mouse_button_up=True,
        ))
        self.assertFalse(window.resizing)

    def test_window_resize_respects_screen_specific_minimum_dimensions(self):
        class CharacterLikeScreen(DummyScreen):
            responsive_layout = True
            min_window_width = 600
            min_window_height = 520

            def __init__(self):
                super().__init__()
                self.viewport = None

            def set_viewport(self, width, height):
                self.viewport = (width, height)

        screen = CharacterLikeScreen()
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "character", screen, (80, 20, 760, 550),
            content_origin=(24, 126), title="Karakter",
        )
        window = manager.windows["character"]
        manager._begin_resize(
            window, (window.bounds.right - 1, window.bounds.bottom - 1),
            ("right", "bottom"),
        )
        manager._resize_window(
            window, (window.bounds.right - 1000, window.bounds.bottom - 1000)
        )

        self.assertEqual(
            (window.bounds.width, window.bounds.height), (600, 520)
        )
        self.assertEqual(screen.viewport, (600, 488))

    def test_responsive_window_uses_dynamic_pointer_coordinates_and_viewport(self):
        class ResponsiveScreen(DummyScreen):
            responsive_layout = True

            def __init__(self):
                super().__init__()
                self.viewport_calls = []

            def set_viewport(self, width, height):
                self.viewport_calls.append((width, height))

        screen = ResponsiveScreen()
        manager = WindowManager(self.backend, 1200, 800)
        manager.register(
            "inventory", screen, (24, 110, 900, 500),
            content_origin=(24, 126), title="Envanter",
        )
        window = manager.windows["inventory"]

        self.assertEqual(screen.viewport_calls[-1], (900, 468))
        self.assertEqual(
            manager._screen_position(window, (124, 210)),
            (124, 194),
        )

        manager._begin_resize(
            window, (window.bounds.right - 1, window.bounds.bottom - 1),
            ("right", "bottom"),
        )
        manager._resize_window(window, (window.bounds.right + 40, window.bounds.bottom + 30))

        self.assertEqual(screen.viewport_calls[-1], (941, 499))


    def test_scaled_window_pointer_coordinates_map_to_design_surface(self):
        screen = DummyScreen()
        screen.scale_to_window = True
        screen.design_size = (760, 438)
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "character", screen, (80, 90, 600, 370),
            content_origin=(24, 126), title="Karakter",
        )
        window = manager.windows["character"]

        self.assertEqual(
            manager._screen_position(window, (380, 291)),
            (404, 345),
        )

    def test_scaled_content_rect_is_clamped_to_backing_surface(self):
        class SizedSurface:
            def __init__(self, size):
                self.size = size

            def get_size(self):
                return self.size

        screen = DummyScreen()
        screen.scale_to_window = True
        screen.design_size = (100, 100)
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "inventory", screen, (24, 110, 700, 400),
            content_origin=(1, 1),
        )
        window = manager.windows["inventory"]

        # At this scale round(1 * scale) + round(100 * scale) is
        # 52, while the backing surface edge round(101 * scale) is 51.
        source = SizedSurface((51, 51))
        rect = manager._scaled_content_rect(window, source, 0.5051)

        self.assertGreaterEqual(rect.x, 0)
        self.assertGreaterEqual(rect.y, 0)
        self.assertGreaterEqual(rect.width, 0)
        self.assertGreaterEqual(rect.height, 0)
        self.assertLessEqual(rect.right, source.size[0])
        self.assertLessEqual(rect.bottom, source.size[1])

    def test_responsive_content_uses_fixed_design_canvas_with_content_origin(self):
        screen = DummyScreen()
        screen.scale_to_window = True
        screen.design_size = (912, 438)
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "inventory", screen, (24, 110, 700, 400),
            content_origin=(24, 126),
        )

        self.assertEqual(
            manager._content_canvas_size(manager.windows["inventory"]),
            (936, 564),
        )

    def test_responsive_resize_does_not_change_screen_viewport(self):
        class ViewportScreen(DummyScreen):
            scale_to_window = True
            design_size = (912, 438)

            def __init__(self):
                super().__init__()
                self.viewport_calls = []

            def set_viewport(self, width, height):
                self.viewport_calls.append((width, height))

        screen = ViewportScreen()
        manager = WindowManager(self.backend, 960, 640)
        manager.register("inventory", screen, (24, 110, 700, 400))
        window = manager.windows["inventory"]
        manager._begin_resize(window, (window.bounds.right - 1, window.bounds.bottom - 1), ("right", "bottom"))
        manager._resize_window(window, (window.bounds.right + 40, window.bounds.bottom + 30))

        self.assertEqual(screen.viewport_calls, [])

    def test_responsive_content_preserves_design_aspect_ratio(self):
        screen = DummyScreen()
        screen.scale_to_window = True
        screen.design_size = (760, 438)
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "character", screen, (80, 90, 600, 400),
            content_origin=(24, 126), title="Karakter",
        )
        window = manager.windows["character"]

        scale, offset_x, offset_y = manager._content_transform(window)
        rendered_width = screen.design_size[0] * scale
        rendered_height = screen.design_size[1] * scale
        available_height = window.bounds.height - manager.TITLE_HEIGHT

        self.assertAlmostEqual(rendered_width / rendered_height, 760 / 438)
        self.assertAlmostEqual(offset_x, 0)
        self.assertGreater(offset_y, 0)
        self.assertLessEqual(rendered_height, available_height)

    def test_letterboxed_content_pointer_maps_to_design_center(self):
        screen = DummyScreen()
        screen.scale_to_window = True
        screen.design_size = (760, 438)
        manager = WindowManager(self.backend, 960, 640)
        manager.register(
            "character", screen, (80, 90, 600, 400),
            content_origin=(24, 126), title="Karakter",
        )
        window = manager.windows["character"]
        scale, offset_x, offset_y = manager._content_transform(window)
        destination_x, destination_y = manager._content_destination(window)
        center = (
            round(destination_x + offset_x + screen.design_size[0] * scale / 2),
            round(destination_y + offset_y + screen.design_size[1] * scale / 2),
        )

        self.assertEqual(
            manager._screen_position(window, center),
            (24 + 760 // 2, 126 + 438 // 2),
        )

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
