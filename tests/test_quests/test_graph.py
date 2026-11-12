"""Tests for generic quest graph structure and runtime rules."""
from __future__ import annotations

import unittest

from quests.graph import QuestGraph, QuestGraphProgress, QuestLink, QuestLinkType
from quests.quest import Quest, QuestState
from quests.condition import AllConditions, Condition


class QuestGraphTests(unittest.TestCase):
    def test_branching_graph_is_content_driven(self):
        graph = QuestGraph(
            quest_ids=("start", "left_path", "right_path", "final"),
            links=(
                QuestLink("start", "left_path", QuestLinkType.ALTERNATIVE, "route"),
                QuestLink("start", "right_path", QuestLinkType.ALTERNATIVE, "route"),
                QuestLink("left_path", "final"),
                QuestLink("right_path", "final"),
            ),
        )
        self.assertEqual(("left_path", "right_path"), graph.successors("start"))
        self.assertEqual(("left_path", "right_path"), graph.predecessors("final"))

    def test_unknown_quest_reference_is_rejected(self):
        with self.assertRaises(KeyError):
            QuestGraph(quest_ids=("one",), links=(QuestLink("one", "missing"),))

    def test_cycle_is_rejected(self):
        with self.assertRaises(ValueError):
            QuestGraph(quest_ids=("one", "two", "three"), links=(
                QuestLink("one", "two"), QuestLink("two", "three"),
                QuestLink("three", "one"),
            ))

    def test_duplicate_links_are_rejected(self):
        graph = QuestGraph(quest_ids=("one", "two"))
        link = QuestLink("one", "two")
        graph.add_link(link)
        with self.assertRaises(ValueError):
            graph.add_link(link)

    def test_invalid_link_and_branch_values_are_rejected(self):
        with self.assertRaises(ValueError):
            QuestLink("one", "one")
        with self.assertRaises(ValueError):
            QuestLink("one", "two", QuestLinkType.ALTERNATIVE)
        with self.assertRaises(ValueError):
            QuestLink("one", "two", branch_group="")
        with self.assertRaises(ValueError):
            QuestLink("one", "two", link_type="unknown")

    def test_unlock_requires_all_normal_predecessors(self):
        graph = QuestGraph(
            ("root", "left", "right", "join"),
            (QuestLink("root", "left"), QuestLink("root", "right"),
             QuestLink("left", "join"), QuestLink("right", "join")),
        )
        states = {"root": "completed", "left": "completed", "right": "active"}
        self.assertFalse(graph.is_unlocked("join", states))
        states["right"] = QuestState.COMPLETED
        self.assertTrue(graph.is_unlocked("join", states))

    def test_alternative_choice_unlocks_only_selected_path(self):
        graph = QuestGraph(
            ("root", "choice_a", "choice_b"),
            (QuestLink("root", "choice_a", QuestLinkType.ALTERNATIVE, "route"),
             QuestLink("root", "choice_b", QuestLinkType.ALTERNATIVE, "route")),
        )
        states = {"root": "completed"}
        progress = QuestGraphProgress()
        self.assertFalse(graph.is_unlocked("choice_a", states, progress))
        progress.choose_branch(graph, "root", "route", "choice_b", states)
        self.assertFalse(graph.is_unlocked("choice_a", states, progress))
        self.assertTrue(graph.is_unlocked("choice_b", states, progress))
        with self.assertRaises(ValueError):
            progress.choose_branch(graph, "root", "route", "choice_a", states)

    def test_alternative_merge_accepts_any_completed_route(self):
        graph = QuestGraph(
            ("root", "path_a", "path_b", "join"),
            (QuestLink("root", "path_a", QuestLinkType.ALTERNATIVE, "route"),
             QuestLink("root", "path_b", QuestLinkType.ALTERNATIVE, "route"),
             QuestLink("path_a", "join", QuestLinkType.ALTERNATIVE, "merge"),
             QuestLink("path_b", "join", QuestLinkType.ALTERNATIVE, "merge")),
        )
        states = {"root": "completed", "path_a": "active", "path_b": "completed"}
        self.assertTrue(graph.is_unlocked("join", states))

    def test_branch_progress_round_trips_and_validates_content(self):
        graph = QuestGraph(
            ("root", "a", "b"),
            (QuestLink("root", "a", QuestLinkType.ALTERNATIVE, "route"),
             QuestLink("root", "b", QuestLinkType.ALTERNATIVE, "route")),
        )
        progress = QuestGraphProgress()
        progress.choose_branch(graph, "root", "route", "a", {"root": "completed"})
        restored = QuestGraphProgress.from_dict(progress.to_dict(), graph)
        self.assertEqual("a", restored.selected_branch("root", "route"))
        with self.assertRaises(ValueError):
            QuestGraphProgress.from_dict(
                {"selected_branches": [{"source_quest_id": "root",
                 "branch_group": "route", "target_quest_id": "missing"}]}, graph
            )

    def test_quest_local_prerequisites_are_combined_with_graph_rules(self):
        graph = QuestGraph(("root", "next"), (QuestLink("root", "next"),))
        quest = Quest(
            "next", "Next", (),
            prerequisites=AllConditions((Condition("flag", "ready"),)),
        )
        states = {"root": "completed"}
        self.assertFalse(graph.can_start(quest, states, {"flags": {"ready": False}}))
        self.assertTrue(graph.can_start(quest, states, {"flags": {"ready": True}}))


if __name__ == "__main__":
    unittest.main()
