"""End-to-end behavior tests for the quest journal window content."""

import unittest
from types import SimpleNamespace

from game_ui.input import InputState
from game_ui.screens.quest_log_screen import QuestLogScreen
from quests.objective import Objective, ObjectiveType
from quests.quest import Quest, QuestLog, QuestState
from quests.reward import Reward


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

    def collidepoint(self, position):
        x, y = position
        return self.x <= x < self.right and self.y <= y < self.bottom


class FakeRenderer:
    def __init__(self, width=960, height=640):
        self.width = width
        self.height = height
        self.pg = SimpleNamespace(Rect=FakeRect)
        self.drawn = []

    def panel(self, rect, *_args):
        self.drawn.append(("panel", rect))

    def text(self, value, *_args, **_kwargs):
        self.drawn.append(("text", str(value)))

    def button(self, rect, label, selected=False):
        self.drawn.append(("button", label, selected))

    def bar(self, *_args):
        self.drawn.append(("bar",))

    def fit_text(self, value, _width, **_kwargs):
        return str(value)

    def hovered(self, _rect):
        return False


class QuestJournalWindowTests(unittest.TestCase):
    def setUp(self):
        quests = []
        for index in range(12):
            quests.append(
                Quest(
                    f"quest-{index:02d}",
                    f"Görev {index}",
                    (
                        Objective(
                            f"objective-{index}",
                            "Eski kuleye ulaş",
                            ObjectiveType.REACH,
                            required=3,
                            progress=min(index, 3),
                        ),
                    ),
                    Reward(
                        experience=25,
                        currency=5,
                        items=(("unknown-item", 2),),
                    ),
                    state=QuestState.ACTIVE,
                )
            )
        self.log = QuestLog(quests)
        self.service = SimpleNamespace(
            application=SimpleNamespace(
                holder=SimpleNamespace(current=SimpleNamespace(quest_log=self.log))
            ),
            item=lambda _item_id: None,
        )
        self.screen = QuestLogScreen(self.service)

    def test_keyboard_moves_selection_and_keeps_it_visible(self):
        for _ in range(8):
            self.screen.handle(InputState(actions={"down"}))

        self.assertEqual(self.screen.selected, 8)
        _x, list_y, _width, list_height = self.screen._list_bounds()
        row_y = list_y + 38 + self.screen.selected * 54 - self.screen.scroll
        self.assertGreaterEqual(row_y, list_y + 34)
        self.assertLessEqual(row_y + 48, list_y + list_height - 8)

    def test_left_and_right_change_category_and_reset_selection(self):
        self.screen.selected = 5
        self.screen.scroll = 90
        self.screen.handle(InputState(actions={"right"}))
        self.assertEqual(self.screen.category, 1)
        self.assertEqual(self.screen.selected, 0)
        self.assertEqual(self.screen.scroll, 0)

        self.screen.handle(InputState(actions={"left"}))
        self.assertEqual(self.screen.category, 0)

    def test_clicking_offscreen_row_does_not_select_it(self):
        row = self.screen._row_bounds()[8]
        self.screen.handle(
            InputState(
                mouse_pos=(row[0] + 5, row[1] + 5),
                mouse_clicked=True,
            )
        )
        self.assertEqual(self.screen.selected, 0)

    def test_clicking_visible_row_selects_it(self):
        row = self.screen._row_bounds()[1]
        self.screen.handle(
            InputState(
                mouse_pos=(row[0] + 5, row[1] + 5),
                mouse_clicked=True,
            )
        )
        self.assertEqual(self.screen.selected, 1)

    def test_wheel_scroll_is_clamped(self):
        self.screen.handle(
            InputState(mouse_pos=(100, 300), mouse_wheel=-100)
        )
        self.assertGreater(self.screen.scroll, 0)
        self.screen.handle(
            InputState(mouse_pos=(100, 300), mouse_wheel=100)
        )
        self.assertEqual(self.screen.scroll, 0)

    def test_render_shows_categories_objectives_and_rewards(self):
        renderer = FakeRenderer()
        self.screen.render(renderer)
        rendered_text = [entry[1] for entry in renderer.drawn if entry[0] == "text"]
        self.assertIn("MACERA DEFTERİ", rendered_text)
        self.assertIn("Hedefler", rendered_text)
        self.assertIn("Ödüller", rendered_text)
        self.assertIn("XP 25", rendered_text)
        self.assertTrue(any(entry[0] == "bar" for entry in renderer.drawn))

    def test_reward_panel_stays_inside_cropped_window_content(self):
        renderer = FakeRenderer(width=960, height=640)
        self.screen.render(renderer)

        x, y, width, height = self.screen._reward_bounds()
        self.assertGreaterEqual(x, 24)
        self.assertGreaterEqual(y, 126)
        self.assertLessEqual(x + width, renderer.width)
        self.assertLessEqual(y + height, renderer.height)

        reward_panels = [
            entry[1] for entry in renderer.drawn
            if entry[0] == "panel" and entry[1].x == x and entry[1].y == y
        ]
        self.assertEqual(len(reward_panels), 1)

    def test_empty_category_renders_without_error(self):
        self.screen._select_category(2)
        renderer = FakeRenderer()
        self.screen.render(renderer)
        rendered_text = [entry[1] for entry in renderer.drawn if entry[0] == "text"]
        self.assertIn("Bir görev seçin.", rendered_text)

    def test_mouse_tab_switch_resets_scroll_and_selection(self):
        self.screen.selected = 4
        self.screen.scroll = 70
        x, y, width, height = self.screen._tab_bounds()[2]
        self.screen.handle(
            InputState(
                mouse_pos=(x + width // 2, y + height // 2),
                mouse_clicked=True,
            )
        )
        self.assertEqual(self.screen.category, 2)
        self.assertEqual(self.screen.selected, 0)
        self.assertEqual(self.screen.scroll, 0)


if __name__ == "__main__":
    unittest.main()
