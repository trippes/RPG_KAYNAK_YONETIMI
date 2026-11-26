from types import SimpleNamespace
import unittest

from application import (
    CombatEncounterView,
    CombatSnapshotView,
    CombatantView,
)
from game_ui.input import InputState
from game_ui.screens.combat_screen import CombatScreen


class _ServiceStub:
    def __init__(self):
        self.snapshot = CombatSnapshotView(
            combatants=(
                CombatantView("hero", 10, 10, ()),
                CombatantView("goblin", 5, 8, ("poison",)),
            ),
            encounters=(
                CombatEncounterView("opening", 2, "goblin"),
            ),
        )
        self.attacks = []
        self.turns = []
        self.rounds_advanced = 0

    def combat_state(self):
        return self.snapshot

    def combat_attack(self, attacker_id, defender_id):
        self.attacks.append((attacker_id, defender_id))
        return SimpleNamespace(attacker_id=attacker_id, damage=3)

    def next_combat_turn(self, encounter_id):
        self.turns.append(encounter_id)
        return "hero"

    def advance_combat_round(self):
        self.rounds_advanced += 1


class _RendererStub:
    def __init__(self):
        self.pg = SimpleNamespace(Rect=lambda *values: values)
        self.text_calls = []

    def frame(self, *args, **kwargs):
        pass

    def hud(self, *args, **kwargs):
        pass

    def panel(self, *args, **kwargs):
        pass

    def text(self, *args, **kwargs):
        self.text_calls.append((args, kwargs))

    def footer(self, *args, **kwargs):
        pass


class TestCombatScreen(unittest.TestCase):
    def test_screen_uses_service_views_without_application_access(self):
        service = _ServiceStub()
        screen = CombatScreen(service)

        screen.handle(InputState(actions={"confirm"}))
        self.assertEqual(service.attacks, [("hero", "goblin")])

        screen.handle(InputState(actions={"wait"}))
        self.assertEqual(service.turns, ["opening"])

        renderer = _RendererStub()
        screen.render(renderer)
        rendered = " ".join(str(args[0]) for args, _ in renderer.text_calls)
        self.assertIn("hero", rendered)
        self.assertIn("goblin", rendered)
        self.assertIn("poison", rendered)


if __name__ == "__main__":
    unittest.main()
