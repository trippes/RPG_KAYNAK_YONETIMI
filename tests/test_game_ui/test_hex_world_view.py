import unittest
from pathlib import Path
from types import SimpleNamespace

from game_ui.input import InputState
from game_ui.screens.main_screen import MainScreen
from game_ui.hex_world_view import HexWorldView
from core.domain.spatial import EntityPosition, LocalHexPosition


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

    def test_confirm_uses_reciprocal_hex_map_transition(self):
        self.assertTrue(self.view.enter())
        self.view.handle(InputState(actions={"confirm"}))
        self.assertEqual(
            self.view.runtime.entity("hero").position,
            EntityPosition("hex_clearing_demo", LocalHexPosition(0, 0)),
        )
        self.view.handle(InputState(actions={"confirm"}))
        self.assertEqual(
            self.view.runtime.entity("hero").position.map_id,
            "hex_forest_demo",
        )

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

    def test_main_screen_h_key_enters_and_leaves_hex_world(self):
        screen = MainScreen(self.service)
        screen.handle(InputState(actions={"hex_portal"}))
        self.assertTrue(screen._hex_world_view.active)
        screen.handle(InputState(actions={"hex_portal"}))
        self.assertFalse(screen._hex_world_view.active)
        self.assertEqual(self.service.actor.location_id, "village")


if __name__ == "__main__":
    unittest.main()
