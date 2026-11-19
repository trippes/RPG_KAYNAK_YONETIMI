import json
import shutil
import tempfile
import unittest
from pathlib import Path

from application import GameApplication
from application.content_loader import load_content_package
from application.content_pack import (
    load_character_definitions,
    load_gameplay_rules,
    load_npc_definitions,
    load_quest_definitions,
    load_resource_definitions,
    populate_gameplay_resources,
    populate_gameplay_placements,
    populate_opening_content,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "demo_eldoria"


class TestContentPack(unittest.TestCase):
    def test_demo_package_has_only_axial_map_and_no_gameplay_demo_records(self):
        package = load_content_package(PACKAGE)
        self.assertEqual(tuple(package.hex_map_definitions), ("starting_valley",))
        self.assertIsNone(package.world_map_definition)
        self.assertEqual(load_npc_definitions(package_path=PACKAGE), ())
        self.assertEqual(load_quest_definitions(package_path=PACKAGE), ())
        self.assertEqual(load_resource_definitions(package_path=PACKAGE), ())
        self.assertTrue(load_character_definitions(package_path=PACKAGE))
        self.assertTrue(load_gameplay_rules(package_path=PACKAGE))
        starter = package.files["starter"]
        self.assertEqual(set(starter["ids"]), {"world_id", "hero_id"})
        self.assertNotIn("dialogue", starter)
        self.assertNotIn("markets", starter)
        self.assertNotIn("trade_partners", starter)
        self.assertNotIn("faction", starter)

    def test_opening_content_creates_character_without_demo_npcs_or_map(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application, content_package_path=PACKAGE)
        bundle = application.holder.current
        self.assertEqual(ids.hero_id, "hero")
        self.assertEqual(ids.world_id, "eldoria_world")
        self.assertIsNotNone(service.actor(ids.hero_id))
        self.assertEqual(bundle.social.npcs.all(), ())
        self.assertEqual(tuple(bundle.social.dialogues), ())
        self.assertEqual(tuple(bundle.quest_log.all()), ())
        self.assertIn("human", service._character_factory.races)

    def test_gameplay_setup_keeps_generic_inventory_but_no_legacy_world_content(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application, content_package_path=PACKAGE)
        populate_gameplay_resources(service, content_package_path=PACKAGE)
        bundle = application.holder.current
        self.assertIn("player", bundle.inventories)
        self.assertIsNone(bundle.resource_nodes.get("north_mine_iron"))
        self.assertIsNone(service.market_for_npc("innkeeper_mira"))
        self.assertEqual(tuple(bundle.social.npcs.all()), ())
        self.assertEqual(tuple(bundle.quest_log.all()), ())


    def test_empty_demo_package_has_no_gameplay_placements_to_apply(self):
        application = GameApplication.create_default()
        service, _ids = populate_opening_content(
            application, content_package_path=PACKAGE,
        )

        self.assertEqual(
            populate_gameplay_placements(
                service, content_package_path=PACKAGE,
            ),
            (),
        )


    def test_gameplay_setup_registers_resource_nodes_from_content_definitions(self):
        with tempfile.TemporaryDirectory() as directory:
            package_path = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package_path)
            (package_path / "resources.json").write_text(json.dumps({
                "schema_version": 1,
                "nodes": [{
                    "id": "oak_01",
                    "resource_type": "wood",
                    "unit": "item",
                    "initial_quantity": 10,
                    "capacity": 20,
                    "regeneration_rate": 1,
                    "gathering_duration_ticks": 60,
                }],
            }), encoding="utf-8")

            application = GameApplication.create_default()
            service, _ids = populate_opening_content(
                application, content_package_path=package_path,
            )
            populate_gameplay_resources(service, content_package_path=package_path)
            populate_gameplay_resources(service, content_package_path=package_path)

            node = application.holder.current.resource_nodes.get("oak_01")
            self.assertIsNotNone(node)
            self.assertEqual(node.quantity.value, 10)
            self.assertEqual(node.capacity.value, 20)
            self.assertEqual(node.resource_type.value, "wood")
            self.assertEqual(node.gathering_duration_ticks.value, 60)



if __name__ == "__main__":
    unittest.main()
