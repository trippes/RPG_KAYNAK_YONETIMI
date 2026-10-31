import json
import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from application.content_pack import ContentDefinitionError, load_demo_content, populate_demo_content
from application.playtest import run_demo_playtest, run_determinism_check
from resources import Quantity, ResourceUnit
from combat import Combatant


class TestContentPack(unittest.TestCase):
    def test_demo_quest_chain_is_reproducible_end_to_end(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)

        service.talk_to_npc(ids.hero_id, ids.carpenter_id, "carpenter_intro")
        service.choose_dialogue(
            ids.hero_id, ids.carpenter_id, "carpenter_intro",
            "carpenter_start", "accept_carpenter_quest",
        )
        service.move_actor(ids.hero_id, ids.forest_id)
        service.advance_by(1)
        for _ in range(3):
            service.start_gathering_at_location(
                ids.hero_id, ids.forest_id, ids.node_id, ids.inventory_id,
                Quantity(1, ResourceUnit.ITEM),
            )
            service.advance_by(1)
        service.move_actor(ids.hero_id, ids.village_id)
        service.advance_by(1)
        service.talk_to_npc(ids.hero_id, ids.carpenter_id, "carpenter_intro")
        service.choose_dialogue(
            ids.hero_id, ids.carpenter_id, "carpenter_intro",
            "carpenter_start", "deliver_carpenter_wood",
        )

        quest = application.holder.current.quest_log.get(ids.carpenter_quest_id)
        self.assertEqual(quest.state.value, "completed")
        self.assertEqual(service.balance(ids.hero_id, "gold").amount, 15)
        self.assertEqual(service.reputation(ids.faction_id), (5, "neutral"))
        self.assertNotIn("wood", {resource for resource, _amount, _unit in service.inventory(ids.inventory_id).stocks})

    def test_demo_market_and_combat_are_ready_for_play(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)

        self.assertIn(ids.market_offer_id, {offer.offer_id for offer in service.market_offers()})
        service.credit(ids.hero_id, "gold", 2)
        service.buy_offer(ids.market_offer_id, ids.hero_id, ids.inventory_id, quantity=1)
        self.assertEqual(service.inventory(ids.inventory_id).stocks[-1][0], "plank")

        combatants = application.holder.current.combat.all()
        self.assertEqual(tuple(item.combatant_id for item in combatants), (ids.enemy_id, ids.hero_id))
        service.combat_attack(ids.hero_id, ids.enemy_id)
        self.assertEqual(application.holder.current.combat.get(ids.enemy_id).hit_points, 4)

    def test_demo_content_can_be_changed_without_python_code(self):
        definition = load_demo_content()
        definition["quest"]["title"] = "Yeni Erzak Görevi"
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "content.json"
            path.write_text(json.dumps(definition, ensure_ascii=False), encoding="utf-8")
            application = GameApplication.create_default()
            populate_demo_content(application, definition_path=path)
        self.assertEqual(application.holder.current.quest_log.get("forest_supplies").title, "Yeni Erzak Görevi")

    def test_content_resource_order_does_not_change_node_setup(self):
        definition = load_demo_content()
        definition["resources"] = list(reversed(definition["resources"]))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "reordered-content.json"
            path.write_text(json.dumps(definition, ensure_ascii=False), encoding="utf-8")
            application = GameApplication.create_default()
            service, ids = populate_demo_content(application, definition_path=path)

        node = application.holder.current.resource_nodes.get(ids.node_id)
        self.assertEqual(node.resource_type.value, "wood")
        self.assertIn(
            "plank",
            {resource for resource, _amount, _unit in service.inventory(ids.merchant_inventory_id).stocks},
        )

    def test_future_content_schema_is_rejected(self):
        definition = load_demo_content()
        definition["schema_version"] = 99
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.json"
            path.write_text(json.dumps(definition), encoding="utf-8")
            with self.assertRaises(ContentDefinitionError):
                load_demo_content(path)

    def test_demo_playtest_covers_the_full_loop(self):
        report = run_demo_playtest()
        self.assertEqual(report.completed_steps[-1], "save_load_restore")
        self.assertTrue(report.enemy_defeated)
        self.assertEqual(report.restored_quest_state, "completed")
        self.assertGreaterEqual(report.gold_after_purchase, 0)
        self.assertEqual(report.plank_count_after_purchase, 1)

    def test_demo_playtest_is_deterministic(self):
        first, second = run_determinism_check()
        self.assertEqual(first, second)

    def test_hilmi_quest_aliases_and_progress_survive_save_load(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)
        service.talk_to_npc(ids.hero_id, ids.carpenter_id, "carpenter_intro")
        service.choose_dialogue(
            ids.hero_id, ids.carpenter_id, "carpenter_intro",
            "carpenter_start", "accept_carpenter_quest",
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "active-quest.json"
            service.save(path)
            service.load(path)

        restored = application.holder.current.quest_log.get(ids.carpenter_quest_id)
        self.assertIs(service.carpenter_quest, restored)
        self.assertEqual(restored.state.value, "active")
        self.assertEqual(
            service.carpenter_quest_reward_inventory_id,
            ids.inventory_id,
        )

    def test_innkeeper_dialogue_and_consumable_food(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)
        node = service.talk_to_npc(
            ids.hero_id, ids.innkeeper_id, "innkeeper_intro",
        )
        self.assertEqual(node.node_id, "innkeeper_start")
        service.credit(ids.hero_id, "gold", 2)
        service.buy_offer(ids.bread_offer_id, ids.hero_id, ids.inventory_id, quantity=1)
        character = service.actor_character(ids.hero_id)
        character.current_hit_points = character.max_hit_points - 2
        healed = service.consume_item(ids.hero_id, ids.inventory_id, "bread")
        self.assertEqual(healed, character.max_hit_points)
        self.assertEqual(
            service.inventory(ids.inventory_id).stocks,
            (),
        )

    def test_npc_positions_survive_save_load(self):
        application = GameApplication.create_default()
        service, ids = populate_demo_content(application)
        expected = {
            ids.npc_id: (16, 30),
            ids.carpenter_id: (21, 15),
            ids.innkeeper_id: (20, 23),
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "npc-positions.json"
            service.save(path)
            service.load(path)

        for npc_id, position in expected.items():
            npc = application.holder.current.social.npcs.get(npc_id)
            self.assertEqual((npc.position.x, npc.position.y), position)


if __name__ == "__main__":
    unittest.main()
