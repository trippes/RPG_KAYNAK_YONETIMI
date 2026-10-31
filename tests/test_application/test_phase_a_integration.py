import json
import tempfile
import unittest
from pathlib import Path

from application import GameApplication, GameplayService
from combat import Combatant, CombatRuntime
from economy import Currency
from quests import Objective, ObjectiveType, Quest, Reward


class TestPhaseAIntegration(unittest.TestCase):
    def test_combat_domain_is_the_runtime_owner(self):
        runtime = CombatRuntime()
        runtime.add(Combatant("a", 10, attack=5))
        runtime.add(Combatant("b", 10, defense=2))
        self.assertEqual(runtime.attack_once("a", "b").damage, 3)

    def test_quest_events_grant_currency_reward(self):
        application = GameApplication.create_default()
        application.dunya_olustur("Quest World", world_id="quest_world")
        service = GameplayService(application)
        quest = Quest(
            "collect-quest", "Collect", (
                Objective("ore", "Collect ore", ObjectiveType.COLLECT, "ore-node"),
            ), Reward(currency=7),
        )
        service.start_quest(quest, owner_id="hero")
        service.update_quest_objective("collect-quest", "ore", owner_id="hero")
        self.assertEqual(service.balance("hero", "gold").amount, 7)

    def test_invalid_social_schema_does_not_replace_active_bundle(self):
        application = GameApplication.create_default()
        application.dunya_olustur("Social World", world_id="social_world")
        service = GameplayService(application)
        active = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            service.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["social"] = {"schema": "future-social", "schema_version": 2, "npcs": [], "relationships": [], "dialogues": []}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                service.load(path)
        self.assertIs(application.holder.current, active)


if __name__ == "__main__":
    unittest.main()
