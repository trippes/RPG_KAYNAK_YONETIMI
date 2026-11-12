import unittest

from application import GameApplication, GameplayService
from game_ui.screens.quest_log_screen import QuestLogScreen
from quests import (
    Objective, ObjectiveType, Quest, QuestGraph, QuestLink, QuestLinkType,
)


class TestQuestGraphGameplayIntegration(unittest.TestCase):
    def setUp(self):
        self.application = GameApplication.create_default()
        self.service = GameplayService(self.application)
        self.bundle = self.application.holder.current

        self.root = Quest(
            "root", "Başlangıç", (
                Objective("finish_root", "Başlangıç görevini bitir", ObjectiveType.CUSTOM),
            ),
        )
        self.left = Quest(
            "left", "Sol Yol", (
                Objective("finish_left", "Sol yolu tamamla", ObjectiveType.CUSTOM),
            ),
        )
        self.right = Quest(
            "right", "Sağ Yol", (
                Objective("finish_right", "Sağ yolu tamamla", ObjectiveType.CUSTOM),
            ),
        )
        for quest in (self.root, self.left, self.right):
            self.bundle.quest_log.add(quest)

        self.graph = QuestGraph(
            ("root", "left", "right"),
            (
                QuestLink("root", "left", QuestLinkType.ALTERNATIVE, "route"),
                QuestLink("root", "right", QuestLinkType.ALTERNATIVE, "route"),
            ),
        )
        self.service.register_quest_graph(self.graph)

    def test_quest_acceptance_progress_and_branch_choice_share_runtime_state(self):
        self.assertEqual(
            tuple(q.quest_id for q in self.service.available_quests()),
            ("root",),
        )

        self.service.start_quest(self.root, owner_id="hero")
        self.service.update_quest_objective("root", "finish_root")

        self.assertEqual(self.root.state.value, "completed")
        self.service.choose_quest_branch("root", "route", "right")

        self.assertEqual(
            tuple(q.quest_id for q in self.service.available_quests()),
            ("right",),
        )
        self.assertEqual(
            self.bundle.quest_graph_progress.to_dict()["selected_branches"][0][
                "target_quest_id"
            ],
            "right",
        )

    def test_standalone_quests_can_coexist_with_graph_quests(self):
        side_quest = Quest("side", "Bağımsız Yan Görev", ())
        self.service.register_quest_definition(side_quest)

        available_ids = {
            quest.quest_id for quest in self.service.available_quests()
        }

        self.assertIn("root", available_ids)
        self.assertIn("side", available_ids)
        self.assertNotIn("left", available_ids)
        self.assertNotIn("right", available_ids)

    def test_quest_journal_reads_branch_options_and_selected_path(self):
        self.service.start_quest(self.root, owner_id="hero")
        self.service.update_quest_objective("root", "finish_root")
        screen = QuestLogScreen(self.service)

        groups = screen._branch_groups(self.root)

        self.assertEqual(len(groups), 1)
        self.assertEqual(groups[0][0], "route")
        self.assertEqual(groups[0][1], ("left", "right"))
        self.assertIsNone(groups[0][2])

        self.service.choose_quest_branch("root", "route", "left")
        self.assertEqual(screen._branch_groups(self.root)[0][2], "left")

    def test_dialogue_actions_can_be_registered_by_content(self):
        calls = []
        self.service.register_dialogue_action(
            "content_action",
            lambda actor_id, npc_id: calls.append((actor_id, npc_id)),
        )

        self.service._run_dialogue_action("content_action", "hero", "any_npc")

        self.assertEqual(calls, [("hero", "any_npc")])


if __name__ == "__main__":
    unittest.main()
