import tempfile
import unittest
from pathlib import Path

from application import Combatant, GameApplication, GameplayService
from character import CharacterClass, CharacterFactory, Race
from npc import NPC
from quests import Dialogue, DialogueChoice, DialogueNode, Objective, ObjectiveType, Quest
from world import Location, WorldMap


class TestSocialCombatIntegration(unittest.TestCase):
    def setUp(self):
        self.application = GameApplication.create_default()
        self.application.dunya_olustur("Town", world_id="town")
        factory = CharacterFactory({"human": Race("human", "Human")}, {"fighter": CharacterClass("fighter", "Fighter", 10)})
        self.application.karakter_olustur(factory, "hero", "Hero", "human", "fighter")
        self.service = GameplayService(self.application)
        world_map = WorldMap("town")
        world_map.add_location(Location("square", "Square"))
        self.service.register_world_map(world_map)
        self.service.place_actor("hero", "square")

    def test_npc_dialogue_requires_same_location_and_quest_can_start(self):
        self.service.register_npc(NPC("elder", "Elder", location_id="square"))
        self.service.register_dialogue(Dialogue("intro", (DialogueNode("start", "elder", "Welcome", (DialogueChoice("accept", "Accept"),)),), "start"))
        node = self.service.talk_to_npc("hero", "elder", "intro")
        self.assertEqual(node.text, "Welcome")
        self.assertEqual(self.service.state().simulation_tick, 1)
        quest = Quest("intro-quest", "First Task", (Objective("talk", "Talk", ObjectiveType.TALK, "elder"),))
        self.service.start_quest(quest)
        self.assertEqual(self.application.holder.current.quest_log.active()[0].quest_id, "intro-quest")

    def test_combat_damage_status_and_persistence(self):
        self.service.register_npc(NPC("elder", "Elder", location_id="square"))
        self.service.add_combatant(Combatant("hero", 20, attack=7, defense=2))
        self.service.add_combatant(Combatant("slime", 10, attack=2, defense=1))
        self.application.holder.current.combat.get("slime").add_status("poison", 2)
        result = self.service.combat_attack("hero", "slime")
        self.assertEqual(result.damage, 6)
        self.assertEqual(self.service.state().simulation_tick, 1)
        self.service.advance_combat_round()
        self.assertEqual(self.service.state().simulation_tick, 2)
        self.assertEqual(self.application.holder.current.combat.get("slime").statuses["poison"], 1)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "social-combat.json"
            self.service.save(path)
            self.service.load(path)
        self.assertEqual(self.application.holder.current.combat.get("slime").hit_points, 4)
        self.assertIsNotNone(self.application.holder.current.social.npcs.get("elder"))


if __name__ == "__main__":
    unittest.main()
