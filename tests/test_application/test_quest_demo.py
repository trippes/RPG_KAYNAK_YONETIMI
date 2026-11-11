import unittest

from application.content_pack import populate_opening_content
from application.game_application import GameApplication
from application.quest_demo import populate_caravan_quest_demo
from resources import Inventory
from game_ui.screens.quest_log_screen import QuestLogScreen


class TestQuestDemoContent(unittest.TestCase):
    def setUp(self):
        application = GameApplication.create_default(inventories={"player": Inventory()})
        self.service, _ids = populate_opening_content(application)
        self.quest = populate_caravan_quest_demo(self.service)

    def test_fresh_game_has_two_available_quests_and_both_npcs(self):
        bundle = self.service.application.holder.current
        self.assertEqual(
            {quest.quest_id for quest in bundle.quest_log.available()},
            {"carpenter_wood", "lost_caravan"},
        )
        self.assertIsNotNone(bundle.social.npcs.get("village_carpenter"))
        self.assertIsNotNone(bundle.social.npcs.get("caravan_merchant"))
        self.assertIsNotNone(bundle.social.dialogues.get("carpenter_dialogue"))
        self.assertIsNotNone(bundle.social.dialogues.get("caravan_merchant_dialogue"))

    def test_quest_journal_switches_details_and_long_quest_can_scroll(self):
        screen = QuestLogScreen(self.service)
        screen.category = 1  # Available
        quests = screen._quests()
        caravan_index = next(
            index for index, quest in enumerate(quests)
            if quest.quest_id == "lost_caravan"
        )
        screen.selected = caravan_index
        self.assertEqual(screen._quests()[screen.selected].title, "Kayıp Kervanın İzinde")

        screen.detail_scroll = 999
        screen._clamp_detail_scroll()
        self.assertGreater(screen.detail_scroll, 0)

        screen.selected = next(
            index for index, quest in enumerate(quests)
            if quest.quest_id == "carpenter_wood"
        )
        screen.detail_scroll = 0
        self.assertEqual(screen._quests()[screen.selected].title, "Marangozun Odun İsteği")

    def test_caravan_objectives_advance_in_order_and_complete(self):
        self.service.start_quest(
            self.quest, owner_id="hero", reward_inventory_id="player",
        )
        self.service._advance_quests("collect", "forest_wood", 3, "hero", "player")
        self.assertEqual(self.quest.objectives[0].progress, 3)
        self.assertEqual(self.quest.objectives[1].progress, 0)

        # Repeating an earlier-stage event cannot skip the active iron stage.
        self.service._advance_quests("collect", "forest_wood", 3, "hero", "player")
        self.assertEqual(self.quest.objectives[1].progress, 0)

        self.service._advance_quests("collect", "north_iron_mine", 2, "hero", "player")
        self.assertEqual(self.quest.objectives[1].progress, 2)
        self.service._advance_quests("talk", "warden_lyra", 1, "hero", "player")
        self.assertEqual(self.quest.objectives[2].progress, 1)
        self.service._advance_quests("talk", "caravan_merchant", 1, "hero", "player")

        self.assertEqual(self.quest.state.value, "completed")


if __name__ == "__main__":
    unittest.main()
