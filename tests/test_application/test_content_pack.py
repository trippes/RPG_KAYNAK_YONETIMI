
import json
import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from application.content_pack import (
    ContentDefinitionError,
    load_starter_content,
    load_npc_definitions,
    populate_opening_content,
    populate_gameplay_resources,
    _build_dialogue_from_definition,
)
from game_ui.input import InputState
from game_ui.screens.dialogue_screen import DialogueScreen
from game_ui.screens.trade_screen import TradeScreen
from resources import Quantity, ResourceType, ResourceUnit


class TestContentPack(unittest.TestCase):

    def test_opening_content_registers_only_opening_phase_npcs(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application)
        bundle = application.holder.current

        self.assertEqual(
            tuple(npc.npc_id for npc in bundle.social.npcs.all()),
            ("warden_lyra", "village_carpenter"),
        )
        self.assertEqual(
            tuple(bundle.social.dialogues),
            ("warden_intro",),
        )
        self.assertEqual(tuple(bundle.quest_log.all()), ())
        self.assertEqual(tuple(service.market_offers()), ())
        self.assertEqual(tuple(bundle.combat.all()), ())
        self.assertEqual(tuple(bundle.inventories), ())

    def test_location_markets_register_after_opening_phase(self):
        application = GameApplication.create_default()
        service, _ids = populate_opening_content(application)

        self.assertIsNone(service.market_for_npc("innkeeper_mira"))
        self.assertIsNone(service.market_for_npc("caravan_merchant"))
        self.assertIsNotNone(application.holder.current.social.npcs.get("village_carpenter"))

        populate_gameplay_resources(service)

        self.assertIsNotNone(application.holder.current.social.npcs.get("innkeeper_mira"))
        self.assertIsNotNone(application.holder.current.social.npcs.get("caravan_merchant"))
        self.assertIsNone(service.market_for_npc("village_trader"))
        self.assertIsNone(service.market_for_npc("village_craftsman"))
        inn_profile = service.market_for_npc("innkeeper_mira")
        self.assertEqual(inn_profile.market_id, "village_inn")
        self.assertEqual(
            {offer.resource_type.value for offer in service.market_offers("village_inn")},
            {"bread", "water"},
        )
        self.assertNotIn("merchant_village", application.holder.current.economy.merchants)
        self.assertNotIn("trade_arda", application.holder.current.economy.merchants)

    def test_gameplay_resources_are_created_after_opening_phase(self):
        application = GameApplication.create_default()
        service, _ids = populate_opening_content(application)

        self.assertEqual(tuple(application.holder.current.inventories), ())
        populate_gameplay_resources(service)

        bundle = application.holder.current
        self.assertIn("player", bundle.inventories)
        self.assertIsNotNone(bundle.resource_nodes.get("north_mine_iron"))
        self.assertEqual(
            bundle.resource_nodes.get("north_mine_iron").location_id,
            "north_mine",
        )

    def test_opening_content_preserves_eren_dialogue_and_character_creation_factory(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application)

        node = service.talk_to_npc(
            ids.hero_id,
            "warden_lyra",
            "warden_intro",
        )

        self.assertEqual(node.node_id, "start")
        self.assertEqual(node.speaker_id, "warden_lyra")
        self.assertIn("warden", service._character_factory.classes)
        self.assertIn("human", service._character_factory.races)

    def test_opening_dialogue_routes_to_character_creation(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application)

        screen = DialogueScreen(service)
        screen.set_target_npc("warden_lyra")

        result = screen.handle(InputState(actions={"confirm"}))

        self.assertEqual(result, "character_creation")
        self.assertTrue(service._creation_from_eren)

    def test_starter_content_can_be_loaded(self):
        definition = load_starter_content()

        self.assertEqual(definition["schema_version"], 1)
        self.assertIn("ids", definition)
        self.assertIn("world", definition)
        self.assertIn("character", definition)
        self.assertIn("locations", definition)
        self.assertNotIn("npc", definition)
        self.assertIn("dialogue", definition)

    def test_npc_content_can_be_customized_without_python_changes(self):
        records = [dict(record) for record in load_npc_definitions()]
        records[0]["name"] = "Test Muhafızı"

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "npcs.json"
            path.write_text(
                json.dumps({"schema_version": 1, "npcs": records}, ensure_ascii=False),
                encoding="utf-8",
            )

            application = GameApplication.create_default()
            _service, ids = populate_opening_content(
                application,
                npc_definitions_path=path,
            )

        npc = application.holder.current.social.npcs.get(ids.npc_id)
        self.assertEqual(npc.name, "Test Muhafızı")

    def test_npc_definitions_reject_duplicate_ids(self):
        records = [dict(record) for record in load_npc_definitions()]
        records.append(dict(records[0]))

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "npcs.json"
            path.write_text(
                json.dumps({"schema_version": 1, "npcs": records}, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ContentDefinitionError, "Duplicate NPC id"):
                load_npc_definitions(path)

    def test_future_content_schema_is_rejected(self):
        definition = load_starter_content()
        definition["schema_version"] = 99

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.json"
            path.write_text(
                json.dumps(definition, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaises(ContentDefinitionError):
                load_starter_content(path)

    def test_missing_required_section_is_rejected(self):
        definition = load_starter_content()
        definition.pop("dialogue")

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(
                json.dumps(definition, ensure_ascii=False),
                encoding="utf-8",
            )

            with self.assertRaises(ContentDefinitionError):
                load_starter_content(path)

    def test_dialogue_builder_rejects_duplicate_node_ids(self):
        definition = {
            "id": "invalid_dialogue",
            "start_node": "start",
            "nodes": [
                {"id": "start", "text": "First", "choices": []},
                {"id": "start", "text": "Duplicate", "choices": []},
            ],
        }
        with self.assertRaisesRegex(ContentDefinitionError, "Duplicate dialogue node"):
            _build_dialogue_from_definition(definition, "npc")

    def test_dialogue_builder_rejects_missing_choice_targets(self):
        definition = {
            "id": "invalid_dialogue",
            "start_node": "start",
            "nodes": [
                {
                    "id": "start",
                    "text": "Start",
                    "choices": [
                        {"id": "continue", "text": "Continue", "next": "missing"},
                    ],
                },
            ],
        }
        with self.assertRaisesRegex(ContentDefinitionError, "missing nodes"):
            _build_dialogue_from_definition(definition, "npc")

    def test_dialogue_builder_rejects_malformed_choice_records(self):
        definition = {
            "id": "invalid_dialogue",
            "start_node": "start",
            "nodes": [{"id": "start", "text": "Start", "choices": ["not-an-object"]}],
        }
        with self.assertRaisesRegex(ContentDefinitionError, "must be an object"):
            _build_dialogue_from_definition(definition, "npc")


if __name__ == "__main__":
    unittest.main()
