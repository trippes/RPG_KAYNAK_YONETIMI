"""Tests for generic, content-driven quest graph rules."""
from __future__ import annotations

import unittest

from quests.graph import QuestGraph, QuestLink, QuestLinkType


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
            QuestGraph(
                quest_ids=("one",),
                links=(QuestLink("one", "missing"),),
            )

    def test_cycle_is_rejected(self):
        with self.assertRaises(ValueError):
            QuestGraph(
                quest_ids=("one", "two", "three"),
                links=(
                    QuestLink("one", "two"),
                    QuestLink("two", "three"),
                    QuestLink("three", "one"),
                ),
            )

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
            QuestLink("one", "two", branch_group="")
        with self.assertRaises(ValueError):
            QuestLink("one", "two", link_type="unknown")


if __name__ == "__main__":
    unittest.main()
