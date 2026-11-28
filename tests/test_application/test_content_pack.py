import json
import shutil
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from core.domain.spatial import LocalHexPosition, axial_to_world_point
from resources import Quantity, ResourceType, ResourceUnit

from application import GameApplication
from application.content_loader import load_content_package
from application.hex_world_initializer import initialize_hex_world
from application import content_pack as content_pack_module
from application.content_pack import (
    ContentDefinitionError,
    _resolve_content_package_path,
    load_character_definitions,
    load_container_definitions,
    load_gameplay_rules,
    load_item_definitions,
    load_movement_configs,
    load_npc_definitions,
    load_production_definitions,
    load_quest_definitions,
    load_resource_definitions,
    load_starter_content,
    populate_gameplay_resources,
    populate_opening_content,
)

ROOT = Path(__file__).resolve().parents[2]
PACKAGE = ROOT / "content" / "demo_eldoria"


class TestContentPack(unittest.TestCase):
    def test_demo_package_loads_opening_guard_and_patrol_placement(self):
        package = load_content_package(PACKAGE)
        self.assertEqual(tuple(package.hex_map_definitions), ("starting_valley",))
        self.assertIsNone(package.world_map_definition)
        npcs = load_npc_definitions(package_path=PACKAGE)
        self.assertEqual(tuple(npc["id"] for npc in npcs), ("warden_lyra",))
        self.assertEqual(npcs[0]["behavior_state"], "patrol")
        self.assertEqual(npcs[0]["patrol_route"], [[1, 0], [2, 0], [2, 1], [1, 1]])
        containers = load_container_definitions(package_path=PACKAGE)
        self.assertEqual(tuple(item["container_id"] for item in containers), ("village_chest",))
        self.assertEqual(containers[0]["contents"], [
            {"item_id": "old_copper_ring", "quantity": 1},
            {"item_id": "wooden_plank", "quantity": 22},
            {"item_id": "nail", "quantity": 22},
            {"item_id": "hinge", "quantity": 2},
            {"item_id": "iron", "quantity": 20},
        ])
        items = load_item_definitions(package_path=PACKAGE)
        self.assertEqual(tuple(item.item_id for item in items), ("old_copper_ring", "wooden_plank", "nail", "hinge", "wooden_floor_panel", "wooden_wall_panel", "wooden_post", "wooden_door", "wooden_window", "wooden_roof_panel", "iron"))
        facilities, recipes = load_production_definitions(package_path=PACKAGE)
        self.assertEqual(tuple(facility.facility_id for facility in facilities), ("village-workbench",))
        self.assertEqual(tuple(recipe.recipe_id for recipe in recipes), ("wooden_plank", "iron_nails", "iron_hinge", "wooden_floor_panel", "wooden_wall_panel", "wooden_post", "wooden_door", "wooden_window", "wooden_roof_panel"))
        self.assertEqual(load_quest_definitions(package_path=PACKAGE), ())
        resources = load_resource_definitions(package_path=PACKAGE)
        self.assertEqual(tuple(node["id"] for node in resources), ("herb_patch_01", "iron_vein_01"))
        self.assertTrue(load_character_definitions(package_path=PACKAGE))
        self.assertTrue(load_gameplay_rules(package_path=PACKAGE))
        starter = package.files["starter"]
        self.assertEqual(set(starter["ids"]), {"world_id", "hero_id"})
        self.assertEqual(starter["dialogue"]["id"], "warden_intro")
        self.assertNotIn("markets", starter)
        self.assertNotIn("trade_partners", starter)
        self.assertNotIn("faction", starter)

    def test_demo_package_loads_player_movement_profile(self):
        configs = load_movement_configs(package_path=PACKAGE)

        self.assertEqual(set(configs), {"hero"})
        self.assertEqual(configs["hero"].max_speed, 200.0)
        self.assertEqual(configs["hero"].running_speed_multiplier, 1.5)
        self.assertEqual(configs["hero"].stealth_speed_multiplier, 0.5)
        self.assertEqual(configs["hero"].acceleration, 300.0)
        self.assertEqual(configs["hero"].deceleration, 360.0)
        self.assertEqual(configs["hero"].braking_deceleration, 480.0)

    def test_movement_test_package_loads_acceleration_and_braking_profiles(self):
        package = ROOT / "content" / "movement_test"
        configs = load_movement_configs(package_path=package)

        self.assertEqual(set(configs), {"hero", "test_guard", "test_target"})
        self.assertEqual(configs["hero"].acceleration, 300.0)
        self.assertEqual(configs["hero"].deceleration, 360.0)
        self.assertEqual(configs["hero"].braking_deceleration, 480.0)

    def test_opening_content_registers_guard_and_intro_dialogue_before_character_creation(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application, content_package_path=PACKAGE)
        bundle = application.holder.current
        self.assertEqual(ids.hero_id, "hero")
        self.assertEqual(ids.world_id, "eldoria_world")
        self.assertIsNotNone(service.actor(ids.hero_id))
        self.assertEqual(
            tuple(npc.npc_id for npc in bundle.social.npcs.all()),
            ("warden_lyra",),
        )
        self.assertEqual(tuple(bundle.social.dialogues), ("warden_intro",))
        self.assertEqual(tuple(bundle.quest_log.all()), ())
        self.assertIn("human", service._character_factory.races)

    def test_gameplay_setup_keeps_guard_and_generic_inventory_without_legacy_world_content(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(application, content_package_path=PACKAGE)
        populate_gameplay_resources(service, content_package_path=PACKAGE)
        bundle = application.holder.current
        self.assertIn("player", bundle.inventories)
        self.assertIsNone(bundle.resource_nodes.get("north_mine_iron"))
        herb = bundle.resource_nodes.get("herb_patch_01")
        self.assertIsNotNone(herb)
        self.assertEqual(herb.quantity.value, 12)
        self.assertIsNone(service.market_for_npc("innkeeper_mira"))
        self.assertEqual(
            tuple(npc.npc_id for npc in bundle.social.npcs.all()),
            ("warden_lyra",),
        )
        self.assertEqual(tuple(bundle.quest_log.all()), ())


    def test_demo_package_places_guard_in_the_starting_hex_world(self):
        application = GameApplication.create_default()
        service, ids = populate_opening_content(
            application, content_package_path=PACKAGE,
        )

        populate_gameplay_resources(service, content_package_path=PACKAGE)
        runtime = initialize_hex_world(
            service, content_package_path=PACKAGE,
        )
        self.assertIsNotNone(runtime)
        guard = runtime.entity("warden_lyra")
        self.assertEqual(guard.kind, "npc")
        self.assertEqual((guard.position.cell.q, guard.position.cell.r), (1, 0))
        herb = runtime.entity("herb_patch_01")
        self.assertEqual(herb.kind, "object")
        self.assertEqual((herb.position.cell.q, herb.position.cell.r), (-1, 0))
        world_point = axial_to_world_point(
            LocalHexPosition(-1, 0).to_hex_coord(), runtime.HEX_SIZE,
        )
        self.assertEqual(
            service.world_target_at_world_point("starting_valley", world_point),
            ("resource_node", "herb_patch_01"),
        )
        chest_point = axial_to_world_point(
            LocalHexPosition(0, 1).to_hex_coord(), runtime.HEX_SIZE,
        )
        self.assertEqual(
            service.world_target_at_world_point("starting_valley", chest_point),
            ("container", "village_chest"),
        )
        opened = service.open_container(
            ids.hero_id, "player", "village_chest",
        )
        self.assertEqual(opened.container_id, "village_chest")
        self.assertEqual(
            opened.items,
            (("hinge", 2), ("iron", 20), ("nail", 22), ("old_copper_ring", 1), ("wooden_plank", 22)),
        )
        self.assertIsNone(service.container_lock_state("village_chest"))
        for item_id, quantity in (
            ("old_copper_ring", 1),
            ("wooden_plank", 22),
            ("nail", 22),
            ("hinge", 2),
            ("iron", 20),
        ):
            service.transfer_actor_item_from_container(
                ids.hero_id, "player", "village_chest", item_id, quantity,
            )
        self.assertEqual(
            service.inventory("player").items,
            (("hinge", 2), ("iron", 20), ("nail", 22), ("old_copper_ring", 1), ("wooden_plank", 22)),
        )
        populate_gameplay_resources(service, content_package_path=PACKAGE)
        self.assertEqual(
            service.container_state("village_chest").items,
            (),
            "reloading gameplay content must not respawn an already-looted item",
        )
        activity = service.start_gathering_one(
            ids.hero_id, "herb_patch_01", "player",
        )
        self.assertEqual(activity.activity_type, "gather")
        self.assertEqual(activity.target_id, "herb_patch_01")
        application.holder.current.inventories["player"].add(
            ResourceType("wood"), Quantity(2, ResourceUnit.ITEM),
        )
        job = service.start_production(
            "wooden_plank", "player", "village-workbench",
        )
        self.assertEqual(job.recipe.recipe_id, "wooden_plank")


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
            placement_path = (
                package_path / "gameplay_placements" / "starting_valley.json"
            )
            placement_data = json.loads(
                placement_path.read_text(encoding="utf-8")
            )
            placement_data["placements"] = [
                placement for placement in placement_data["placements"]
                if placement["domain_id"] != "iron_vein_01"
            ]
            for placement in placement_data["placements"]:
                if placement["domain_id"] == "herb_patch_01":
                    placement["domain_id"] = "oak_01"
            placement_path.write_text(
                json.dumps(placement_data), encoding="utf-8",
            )

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



    def test_opening_content_rejects_container_contents_with_unknown_item(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            containers_path = package / "containers.json"
            containers = json.loads(containers_path.read_text(encoding="utf-8"))
            containers["containers"][0]["contents"][0]["item_id"] = "missing_item"
            containers_path.write_text(json.dumps(containers), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "Container 'village_chest' references missing item 'missing_item'"
            ):
                populate_opening_content(
                    GameApplication.create_default(),
                    content_package_path=package,
                )

    def test_opening_content_rejects_quest_rewards_with_unknown_item(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            quests_path = package / "quests.json"
            quests = {
                "schema_version": 1,
                "quests": [{
                    "id": "guard_report",
                    "title": "Muhafıza haber ver",
                    "giver_npc_id": "warden_lyra",
                    "objectives": [{
                        "id": "speak_to_guard",
                        "description": "Muhafızla konuş",
                        "type": "talk",
                        "target_id": "warden_lyra",
                    }],
                    "reward": {
                        "items": [{"id": "missing_item", "quantity": 1}],
                    },
                }],
            }
            quests_path.write_text(json.dumps(quests), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "Quest 'guard_report' reward references missing item 'missing_item'"
            ):
                populate_opening_content(
                    GameApplication.create_default(),
                    content_package_path=package,
                )

    def test_content_definition_loaders_reject_boolean_schema_versions(self):
        loaders = (
            ("starter_content.json", load_starter_content),
            ("npcs.json", load_npc_definitions),
            ("characters.json", load_character_definitions),
            ("quests.json", load_quest_definitions),
            ("gameplay_rules.json", load_gameplay_rules),
            ("items.json", load_item_definitions),
            ("containers.json", load_container_definitions),
            ("resources.json", load_resource_definitions),
        )
        for filename, loader in loaders:
            with self.subTest(filename=filename):
                with tempfile.TemporaryDirectory() as directory:
                    package = Path(directory) / "demo_eldoria"
                    shutil.copytree(PACKAGE, package)
                    source = package / filename
                    payload = json.loads(source.read_text(encoding="utf-8"))
                    payload["schema_version"] = True
                    source.write_text(json.dumps(payload), encoding="utf-8")

                    with self.assertRaises(ContentDefinitionError):
                        loader(package_path=package)

    def test_active_package_config_rejects_boolean_schema_version(self):
        with tempfile.TemporaryDirectory() as directory:
            content_root = Path(directory)
            (content_root / "active_package.json").write_text(
                json.dumps({
                    "schema_version": True,
                    "package_path": "demo_eldoria",
                }),
                encoding="utf-8",
            )
            with patch.object(content_pack_module, "CONTENT_ROOT", content_root):
                with self.assertRaises(ContentDefinitionError):
                    _resolve_content_package_path()


    def test_npc_definitions_reject_duplicate_dialogue_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            npcs_path = package / "npcs.json"
            payload = json.loads(npcs_path.read_text(encoding="utf-8"))
            duplicate = dict(payload["npcs"][0])
            duplicate["id"] = "second_guard"
            duplicate["name"] = "Second Guard"
            payload["npcs"].append(duplicate)
            npcs_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "Duplicate NPC dialogue id: warden_intro"
            ):
                load_npc_definitions(package_path=package)

    def test_npc_definitions_reject_invalid_dialogue_id(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            npcs_path = package / "npcs.json"
            payload = json.loads(npcs_path.read_text(encoding="utf-8"))
            payload["npcs"][0]["dialogue_id"] = ""
            npcs_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "NPC 'warden_lyra' has an invalid dialogue_id"
            ):
                load_npc_definitions(package_path=package)

    def test_opening_dialogue_rejects_npc_loaded_in_gameplay_phase(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            npcs_path = package / "npcs.json"
            payload = json.loads(npcs_path.read_text(encoding="utf-8"))
            payload["npcs"][0]["load_phase"] = "gameplay"
            npcs_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "outside the opening load phase"
            ):
                populate_opening_content(
                    GameApplication.create_default(),
                    content_package_path=package,
                )

    def test_dialogue_rejects_node_speaker_different_from_owning_npc(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            starter_path = package / "starter_content.json"
            payload = json.loads(starter_path.read_text(encoding="utf-8"))
            payload["dialogue"]["nodes"][0]["speaker"] = "different_npc"
            starter_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "but its owning NPC is 'warden_lyra'"
            ):
                populate_opening_content(
                    GameApplication.create_default(),
                    content_package_path=package,
                )


    def test_opening_content_rejects_npc_reference_to_undefined_dialogue(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            starter_path = package / "starter_content.json"
            payload = json.loads(starter_path.read_text(encoding="utf-8"))
            payload["dialogue"]["id"] = "different_dialogue"
            starter_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError,
                "NPC 'warden_lyra' references unknown opening dialogue 'warden_intro'",
            ):
                populate_opening_content(
                    GameApplication.create_default(),
                    content_package_path=package,
                )

    def test_opening_content_rejects_dialogue_id_collision_with_quest_dialogue(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            quests_path = package / "quests.json"
            quests_path.write_text(json.dumps({
                "schema_version": 1,
                "quests": [{
                    "id": "duplicate_dialogue_quest",
                    "title": "Diyalog kimliği çakışması",
                    "giver_npc_id": "warden_lyra",
                    "objectives": [{
                        "id": "speak_to_guard",
                        "description": "Muhafızla konuş",
                        "type": "talk",
                        "target_id": "warden_lyra",
                    }],
                    "dialogue": {
                        "id": "warden_intro",
                        "start_node": "start",
                        "nodes": [{
                            "id": "start",
                            "text": "Bu diyalog kimliği başka bir içerikte kullanılıyor.",
                            "choices": [],
                        }],
                    },
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "Duplicate dialogue id 'warden_intro'"
            ):
                populate_opening_content(
                    GameApplication.create_default(),
                    content_package_path=package,
                )


    def test_starter_content_rejects_invalid_required_section_fields(self):
        mutations = (
            ("ids section type", lambda data: data.update({"ids": []})),
            ("missing configured ID", lambda data: data["ids"].pop("hero_id")),
            ("empty configured ID", lambda data: data["ids"].update({"hero_id": ""})),
            ("world section type", lambda data: data.update({"world": []})),
            ("empty world name", lambda data: data["world"].update({"name": ""})),
            ("boolean world width", lambda data: data["world"].update({"width": True})),
            ("zero world height", lambda data: data["world"].update({"height": 0})),
            ("character section type", lambda data: data.update({"character": []})),
            ("empty character name", lambda data: data["character"].update({"name": ""})),
            ("empty race reference", lambda data: data["character"]["race"].update({"id": ""})),
            ("missing class reference", lambda data: data["character"].update({"class": {}})),
            ("invalid optional faction", lambda data: data.update({"faction": {"name": ""}})),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "demo_eldoria"
                shutil.copytree(PACKAGE, package)
                starter_path = package / "starter_content.json"
                payload = json.loads(starter_path.read_text(encoding="utf-8"))
                mutate(payload)
                starter_path.write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaises(ContentDefinitionError):
                    load_starter_content(package_path=package)

    def test_starter_world_dimensions_remain_optional(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            starter_path = package / "starter_content.json"
            payload = json.loads(starter_path.read_text(encoding="utf-8"))
            payload["world"].pop("width")
            payload["world"].pop("height")
            starter_path.write_text(json.dumps(payload), encoding="utf-8")

            loaded = load_starter_content(package_path=package)

            self.assertNotIn("width", loaded["world"])
            self.assertNotIn("height", loaded["world"])


    def test_optional_string_list_fields_reject_scalar_strings(self):
        cases = (
            (
                "item tags",
                "items.json",
                lambda data: data["items"][0].update({"tags": "abc"}),
                load_item_definitions,
            ),
            (
                "container tag filters",
                "containers.json",
                lambda data: data["containers"][0].update({"allowed_item_tags": "abc"}),
                load_container_definitions,
            ),
            (
                "production facility capabilities",
                "starter_content.json",
                lambda data: data["production"]["facilities"][0].update({"capabilities": "abc"}),
                load_production_definitions,
            ),
            (
                "recipe required capabilities",
                "starter_content.json",
                lambda data: data["production"]["recipes"][0].update({"required_capabilities": "abc"}),
                load_production_definitions,
            ),
        )
        for label, filename, mutate, loader in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "demo_eldoria"
                shutil.copytree(PACKAGE, package)
                source = package / filename
                payload = json.loads(source.read_text(encoding="utf-8"))
                mutate(payload)
                source.write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaises(ContentDefinitionError):
                    loader(package_path=package)


    def test_starter_content_rejects_invalid_optional_section_shapes(self):
        mutations = (
            ("hex_start", lambda data: data["world"].update({"hex_start": []})),
            ("dialogue", lambda data: data.update({"dialogue": []})),
            ("production", lambda data: data.update({"production": []})),
            ("markets", lambda data: data.update({"markets": {}})),
            ("trade_partners", lambda data: data.update({"trade_partners": "invalid"})),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "demo_eldoria"
                shutil.copytree(PACKAGE, package)
                starter_path = package / "starter_content.json"
                payload = json.loads(starter_path.read_text(encoding="utf-8"))
                mutate(payload)
                starter_path.write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaises(ContentDefinitionError):
                    load_starter_content(package_path=package)


    def test_item_optional_metadata_requires_mapping_and_text_types(self):
        mutations = (
            (
                "attribute bonuses object",
                lambda data: data["items"][0].update({
                    "attribute_bonuses": [["strength", 1]]
                }),
            ),
            (
                "known attribute bonus",
                lambda data: data["items"][0].update({
                    "attribute_bonuses": {"not_an_attribute": 1}
                }),
            ),
            (
                "description text",
                lambda data: data["items"][0].update({"description": 123}),
            ),
        )
        for label, mutate in mutations:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "demo_eldoria"
                shutil.copytree(PACKAGE, package)
                items_path = package / "items.json"
                payload = json.loads(items_path.read_text(encoding="utf-8"))
                mutate(payload)
                items_path.write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaises(ContentDefinitionError):
                    load_item_definitions(package_path=package)


    def test_optional_market_and_trade_partner_fields_are_validated(self):
        def market_record():
            return {
                "market_id": "village_market",
                "location_id": "village_square",
                "npc_id": "warden_lyra",
                "merchant_id": "village_merchant",
                "inventory_id": "market_inventory",
                "restock_interval": 1,
                "catalog": [{
                    "resource_type": "wood",
                    "base_price": 2,
                    "min_quantity": 1,
                    "max_quantity": 5,
                }],
                "dialogue": {"id": "market_dialogue"},
            }

        def trade_record():
            return {
                "npc_id": "warden_lyra",
                "merchant_id": "village_trader",
                "inventory_id": "trade_inventory",
                "accepted_resources": ["wood"],
                "initial_gold": 10,
                "dialogue": {"id": "trade_dialogue"},
            }

        cases = (
            (
                "market dialogue required",
                "markets",
                market_record,
                lambda record: record.pop("dialogue"),
            ),
            (
                "market catalog list required",
                "markets",
                market_record,
                lambda record: record.update({"catalog": "wood"}),
            ),
            (
                "market price must be integer",
                "markets",
                market_record,
                lambda record: record["catalog"][0].update({"base_price": True}),
            ),
            (
                "trade accepted resources list required",
                "trade_partners",
                trade_record,
                lambda record: record.update({"accepted_resources": "wood"}),
            ),
            (
                "trade unit prices object required",
                "trade_partners",
                trade_record,
                lambda record: record.update({"unit_prices": []}),
            ),
            (
                "trade buyback rate range",
                "trade_partners",
                trade_record,
                lambda record: record.update({"buyback_rate": 0}),
            ),
            (
                "trade initial gold integer",
                "trade_partners",
                trade_record,
                lambda record: record.update({"initial_gold": True}),
            ),
        )
        for label, section, factory, mutate in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as directory:
                package = Path(directory) / "demo_eldoria"
                shutil.copytree(PACKAGE, package)
                starter_path = package / "starter_content.json"
                payload = json.loads(starter_path.read_text(encoding="utf-8"))
                record = factory()
                mutate(record)
                payload[section] = [record]
                starter_path.write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaises(ContentDefinitionError):
                    load_starter_content(package_path=package)


    def test_starter_content_accepts_valid_optional_market_and_trade_records(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            starter_path = package / "starter_content.json"
            payload = json.loads(starter_path.read_text(encoding="utf-8"))
            payload["markets"] = [{
                "market_id": "village_market",
                "location_id": "village_square",
                "npc_id": "warden_lyra",
                "merchant_id": "village_merchant",
                "inventory_id": "market_inventory",
                "restock_interval": 1,
                "catalog": [{
                    "resource_type": "wood",
                    "base_price": 2,
                    "min_quantity": 1,
                    "max_quantity": 5,
                }],
                "dialogue": {"id": "market_dialogue"},
            }]
            payload["trade_partners"] = [{
                "npc_id": "warden_lyra",
                "merchant_id": "village_trader",
                "inventory_id": "trade_inventory",
                "accepted_resources": ["wood"],
                "initial_gold": 10,
                "dialogue": {"id": "trade_dialogue"},
            }]
            starter_path.write_text(json.dumps(payload), encoding="utf-8")

            loaded = load_starter_content(package_path=package)

            self.assertEqual(loaded["markets"][0]["market_id"], "village_market")
            self.assertEqual(loaded["trade_partners"][0]["merchant_id"], "village_trader")


    def test_quest_item_reward_quantity_must_be_positive(self):
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "demo_eldoria"
            shutil.copytree(PACKAGE, package)
            quests_path = package / "quests.json"
            quests_path.write_text(json.dumps({
                "schema_version": 1,
                "quests": [{
                    "id": "zero_item_reward",
                    "title": "Zero quantity reward",
                    "giver_npc_id": "warden_lyra",
                    "objectives": [{
                        "id": "talk",
                        "description": "Talk to the guard",
                        "type": "talk",
                        "target_id": "warden_lyra",
                    }],
                    "reward": {
                        "items": [{"id": "old_copper_ring", "quantity": 0}],
                    },
                }],
            }), encoding="utf-8")

            with self.assertRaisesRegex(
                ContentDefinitionError, "invalid 'items' reward amount"
            ):
                load_quest_definitions(package_path=package)


if __name__ == "__main__":
    unittest.main()
