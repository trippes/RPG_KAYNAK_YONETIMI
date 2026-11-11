import unittest

from quests import Objective, ObjectiveType, Quest, QuestLog, QuestSnapshot


class TestSequentialQuestPersistence(unittest.TestCase):
    def test_sequential_objective_mode_survives_snapshot_restore(self):
        quest = Quest(
            "ordered",
            "Ordered Quest",
            (
                Objective("first", "First", ObjectiveType.COLLECT, required=2),
                Objective("second", "Second", ObjectiveType.TALK),
            ),
            sequential_objectives=True,
        )
        quest.start()
        quest.update("first", 1)
        snapshot = QuestSnapshot.from_log(QuestLog((quest,)))
        restored = snapshot.restore({}).get("ordered")

        self.assertTrue(restored.sequential_objectives)
        self.assertEqual(restored.objectives[0].progress, 1)
        self.assertEqual(restored.objectives[1].progress, 0)


if __name__ == "__main__":
    unittest.main()
