import unittest

from core.actions import ActionType, action_tick_cost


class TestActionCosts(unittest.TestCase):
    def test_fixed_gameplay_actions_have_canonical_tick_costs(self):
        for action_type in ActionType:
            with self.subTest(action_type=action_type):
                self.assertEqual(action_tick_cost(action_type).value, 1)

    def test_unknown_action_type_is_rejected(self):
        with self.assertRaises(ValueError):
            action_tick_cost("unknown")


if __name__ == "__main__":
    unittest.main()
