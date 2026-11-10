
import json
import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from application.content_pack import (
    ContentDefinitionError,
    load_starter_content,
    populate_opening_content,
    populate_gameplay_resources,
    _build_dialogue_from_definition,
)
from game_ui.input import InputState
from game_ui.screens.dialogue_screen import DialogueScreen


class TestContentPack(unittest.TestCase):

    def test_opening_content_excludes_demo_runtime_entities(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application)
        bundle = application.holder.current

        self.assertEqual(
            tuple(npc.npc_id for npc in bundle.social.npcs.all()),
            (ids.npc_id,),
        )
        self.assertEqual(
            tuple(bundle.social.dialogues),
            ("warden_intro",),
        )
        self.assertEqual(tuple(bundle.quest_log.all()), ())
        self.assertEqual(tuple(service.market_offers()), ())
        self.assertEqual(tuple(bundle.combat.all()), ())
        self.assertEqual(tuple(bundle.inventories), ())

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
            ids.npc_id,
            "warden_intro",
        )

        self.assertEqual(node.node_id, "start")
        self.assertEqual(node.speaker_id, ids.npc_id)
        self.assertIn("warden", service._character_factory.classes)
        self.assertIn("human", service._character_factory.races)

    def test_opening_dialogue_routes_to_character_creation(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application)

        screen = DialogueScreen(service)
        screen.set_target_npc(ids.npc_id)

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
        self.assertIn("npc", definition)
        self.assertIn("dialogue", definition)

    def test_starter_content_can_be_customized_without_python_changes(self):
        definition = load_starter_content()
        definition["npc"]["name"] = "Test Muhafızı"

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "starter_content.json"
            path.write_text(
                json.dumps(definition, ensure_ascii=False),
                encoding="utf-8",
            )

            application = GameApplication.create_default()
            _service, ids = populate_opening_content(
                application,
                definition_path=path,
            )

        npc = application.holder.current.social.npcs.get(ids.npc_id)
        self.assertEqual(npc.name, "Test Muhafızı")

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
