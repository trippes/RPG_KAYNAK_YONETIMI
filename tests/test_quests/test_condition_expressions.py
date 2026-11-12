"""Tests for generic quest prerequisite expressions."""
from __future__ import annotations

import unittest

from quests.condition import AllConditions, AnyConditions, Condition, NotCondition


class QuestConditionExpressionTests(unittest.TestCase):
    def test_all_conditions_uses_and_semantics(self):
        expression = AllConditions((
            Condition("flag", "met_contact"),
            Condition("reputation", "guild", 5),
        ))
        self.assertTrue(expression.evaluate({
            "flags": {"met_contact": True},
            "reputation": {"guild": 7},
        }))
        self.assertFalse(expression.evaluate({
            "flags": {"met_contact": True},
            "reputation": {"guild": 2},
        }))

    def test_any_conditions_uses_or_semantics(self):
        expression = AnyConditions((
            Condition("flag", "has_pass"),
            Condition("item", "entry_token", 1),
        ))
        self.assertTrue(expression.evaluate({
            "flags": {"has_pass": False},
            "items": {"entry_token": 1},
        }))
        self.assertFalse(expression.evaluate({
            "flags": {"has_pass": False},
            "items": {"entry_token": 0},
        }))

    def test_not_condition_negates_nested_expression(self):
        expression = NotCondition(Condition("flag", "wanted"))
        self.assertTrue(expression.evaluate({"flags": {"wanted": False}}))
        self.assertFalse(expression.evaluate({"flags": {"wanted": True}}))

    def test_conditions_can_be_nested(self):
        expression = AllConditions((
            Condition("flag", "chapter_open"),
            AnyConditions((
                Condition("reputation", "order", 10),
                NotCondition(Condition("flag", "banished")),
            )),
        ))
        self.assertTrue(expression.evaluate({
            "flags": {"chapter_open": True, "banished": False},
            "reputation": {"order": 0},
        }))

    def test_quest_state_condition_accepts_enum_or_string(self):
        expression = Condition("quest_state", "intro", "completed")
        self.assertTrue(expression.evaluate({
            "quest_states": {"intro": "completed"},
        }))

    def test_invalid_nested_condition_is_rejected(self):
        with self.assertRaises(TypeError):
            NotCondition(object())


if __name__ == "__main__":
    unittest.main()
