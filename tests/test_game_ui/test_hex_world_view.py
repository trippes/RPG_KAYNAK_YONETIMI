import unittest
from pathlib import Path
from types import SimpleNamespace

from game_ui.input import InputState
from game_ui.screens.main_screen import MainScreen
from game_ui.hex_world_view import HexWorldView
from core.domain.spatial import EntityPosition, HexDirection, LocalHexPosition


class _FakeService:
    def __init__(self):
        self.actor = SimpleNamespace(
            actor_id="hero",
            world_id="legacy_world",
            location_id="village",
            position=SimpleNamespace(x=7, y=9),
        )
        self._content_package_path = (
            Path(__file__).resolve().parents[2] / "content" / "demo_eldoria"
        )

    def state(self):
        return SimpleNamespace(actors=(self.actor,))


class TestHexWorldView(unittest.TestCase):
    def setUp(self):
        self.service = _FakeService()
        self.view = HexWorldView(self.service)

    def test_enter_registers_existing_player_in_hex_runtime(self):
        self.assertTrue(self.view.enter())
        entity = self.view.runtime.entity("hero")
        self.assertEqual(entity.position.map_id, "hex_forest_demo")
        self.assertEqual(entity.position.cell, LocalHexPosition(0, 0))
        self.assertEqual(self.service.actor.location_id, "village")
        self.assertEqual(
            (self.service.actor.position.x, self.service.actor.position.y),
            (7, 9),
        )

    def test_keyboard_movement_uses_hex_runtime(self):
        self.assertTrue(self.view.enter())
        self.view.handle(InputState(actions={"up"}))
        self.assertEqual(
            self.view.runtime.entity("hero").position.cell,
            LocalHexPosition(1, -1),
        )

    def test_blocked_hex_cell_does_not_move_player(self):
        self.assertTrue(self.view.enter())
        self.view.handle(InputState(actions={"hex_north_west"}))
        self.assertEqual(
            self.view.runtime.entity("hero").position.cell,
            LocalHexPosition(0, 0),
        )
        self.assertIn("blocked", self.view.message.lower())

    def test_far_ore_landmark_is_connected_by_a_walkable_route(self):
        self.assertTrue(self.view.enter())
        target = LocalHexPosition(3, 2)
        path = self.view.runtime.path_to("hero", target)
        self.assertIsNotNone(path)
        self.assertEqual(path[0], LocalHexPosition(0, 0))
        self.assertEqual(path[-1], target)
        self.assertTrue(self.view._move_to(target))
        self.assertEqual(
            self.view.runtime.entity("hero").position.cell,
            target,
        )

    def test_path_movement_uses_visual_interpolation_without_delaying_runtime(self):
        self.assertTrue(self.view.enter())
        target = LocalHexPosition(3, 2)
        self.assertTrue(self.view._move_to(target))
        self.assertEqual(self.view.runtime.entity("hero").position.cell, target)
        self.assertTrue(self.view._movement_path)
        self.view.update(10.0)
        self.assertFalse(self.view._movement_path)

    def test_enter_does_not_change_hex_maps(self):
        self.assertTrue(self.view.enter())
        self.view.handle(InputState(actions={"confirm"}))
        self.assertEqual(
            self.view.runtime.entity("hero").position,
            EntityPosition("hex_forest_demo", LocalHexPosition(0, 0)),
        )

    def test_crossing_east_boundary_automatically_enters_clearing(self):
        self.assertTrue(self.view.enter())
        self.assertTrue(self.view._move_to(LocalHexPosition(3, 2)))
        self.assertTrue(self.view._move(HexDirection.EAST))
        self.assertEqual(
            self.view.runtime.entity("hero").position,
            EntityPosition("hex_clearing_demo", LocalHexPosition(-1, 0)),
        )

    def test_crossing_west_boundary_returns_to_forest_automatically(self):
        self.assertTrue(self.view.enter())
        self.assertTrue(self.view._move_to(LocalHexPosition(3, 2)))
        self.assertTrue(self.view._move(HexDirection.EAST))
        self.assertTrue(self.view._move(HexDirection.WEST))
        self.assertEqual(
            self.view.runtime.entity("hero").position,
            EntityPosition("hex_forest_demo", LocalHexPosition(3, 2)),
        )

    def test_unlinked_map_boundary_blocks_movement(self):
        self.assertTrue(self.view.enter())
        self.assertTrue(self.view._move_to(LocalHexPosition(3, 2)))
        before = self.view.runtime.entity("hero").position
        self.assertFalse(self.view._move(HexDirection.NORTH_EAST))
        self.assertEqual(self.view.runtime.entity("hero").position, before)

    def test_leave_keeps_legacy_actor_location_and_position(self):
        self.assertTrue(self.view.enter())
        self.view.handle(InputState(actions={"up"}))
        self.view.leave()
        self.assertFalse(self.view.active)
        self.assertEqual(self.service.actor.location_id, "village")
        self.assertEqual(
            (self.service.actor.position.x, self.service.actor.position.y),
            (7, 9),
        )

    def test_mouse_wheel_adjusts_hex_world_zoom_with_limits(self):
        self.assertTrue(self.view.enter())
        self.view.handle(InputState(mouse_wheel=1))
        self.assertAlmostEqual(self.view._zoom, 1.1)
        self.view.handle(InputState(mouse_wheel=-20))
        self.assertEqual(self.view._zoom, 0.75)

    def test_render_composes_zoomed_terrain_and_world_entities(self):
        class FakeDraw:
            polygons = 0
            circles = 0
            lines = 0

            @classmethod
            def polygon(cls, *args, **kwargs):
                cls.polygons += 1

            @classmethod
            def circle(cls, *args, **kwargs):
                cls.circles += 1

            @classmethod
            def line(cls, *args, **kwargs):
                cls.lines += 1

        class FakeRenderer:
            def __init__(self):
                self.pg = SimpleNamespace(draw=FakeDraw)
                self.surface = object()
                self.width = 960
                self.height = 640

            def frame(self, *args, **kwargs): pass
            def text(self, *args, **kwargs): pass
            def footer(self, *args, **kwargs): pass

        self.assertTrue(self.view.enter())
        self.view._zoom = 1.4
        self.view.render(FakeRenderer())
        self.assertGreater(FakeDraw.polygons, 0)
        self.assertGreater(FakeDraw.circles, 0)

    def test_main_screen_h_key_enters_and_leaves_hex_world(self):
        screen = MainScreen(self.service)
        screen.handle(InputState(actions={"hex_portal"}))
        self.assertTrue(screen._hex_world_view.active)
        screen.handle(InputState(actions={"hex_portal"}))
        self.assertFalse(screen._hex_world_view.active)
        self.assertEqual(self.service.actor.location_id, "village")


if __name__ == "__main__":
    unittest.main()
