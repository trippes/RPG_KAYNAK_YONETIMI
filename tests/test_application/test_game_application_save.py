import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from application import (
    GameApplication,
    GameSaveFileAdapter,
    SessionBundle,
    SessionHolder,
    WorldActor,
)
from application.save_file_adapter import SaveFileWriteError
from character import CharacterFactory, Race, CharacterClass
from economy import Currency, Money
from application import GameplayService
from core.application import GameSession
from npc import NPC
from core.time import Tick
from resources import (
    GameplaySnapshot,
    Inventory,
    ProductionJobManager,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


class TestGameApplicationSave(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.tool = ResourceType("tool")
        self.recipe = Recipe(
            "tool_recipe",
            ((self.wood, Quantity(3, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
        )
        self.extra_recipe = Recipe(
            "unused_recipe",
            ((self.wood, Quantity(1, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
        )

    def _application_with_gameplay(self):
        session = GameSession()
        session.worlds.create("Main", world_id="world_main")
        session.worlds.set_active("world_main")
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        jobs = ProductionJobManager(session.simulation)
        jobs.start(self.recipe, inventory, 4, job_id="job_main")
        jobs.advance_to(0)

        nodes = WorldResourceNodeManager()
        nodes.add(WorldResourceNode(
            "node_main",
            "world_main",
            self.wood,
            Quantity(2, ResourceUnit.ITEM),
            Quantity(5, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
            Tick(0),
        ))
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=jobs,
            resource_nodes=nodes,
            inventories={"main": inventory},
            recipes={
                self.recipe.recipe_id: self.recipe,
                self.extra_recipe.recipe_id: self.extra_recipe,
            },
        )
        return GameApplication(SessionHolder(bundle))

    def test_save_creates_readable_unified_document(self):
        application = self._application_with_gameplay()
        active = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            result = application.save(path)
            document = GameSaveFileAdapter.load(result)

        self.assertEqual(document.schema, "rpg-game-save")
        self.assertEqual(document.schema_version, 3)
        self.assertEqual(document.core.simulation_tick.value, document.gameplay.simulation_tick)
        self.assertEqual(document.gameplay.inventories[0].inventory_id, "main")
        self.assertEqual(document.gameplay.nodes[0].node_id, "node_main")
        self.assertEqual(document.gameplay.jobs[0].job_id, "job_main")
        self.assertIs(application.holder.current, active)

    def test_save_uses_one_active_bundle_and_preserves_registries(self):
        application = self._application_with_gameplay()
        active = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            application.save(path)
            document = GameSaveFileAdapter.load(path)

        self.assertEqual(
            document.core.to_state().simulation_tick,
            document.gameplay.simulation_tick,
        )
        self.assertEqual(document.gameplay.inventories[0].inventory_id, "main")
        self.assertEqual(document.gameplay.recipes[0].recipe_id, "tool_recipe")
        self.assertEqual(
            {record.recipe_id for record in document.gameplay.recipes},
            {"tool_recipe", "unused_recipe"},
        )
        self.assertIs(application.holder.current, active)

    def test_save_load_round_trip_restores_active_job_and_completes_once(self):
        application = self._application_with_gameplay()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            application.save(path)
            application.load(path)

        bundle = application.holder.current
        inventory = bundle.inventories["main"]
        self.assertIsNone(inventory.get(self.wood))
        self.assertEqual(bundle.simulation.current_tick.value, 0)
        self.assertEqual(bundle.production_jobs.get("job_main").state.value, "running")

        bundle.production_jobs.advance_to(4)
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        bundle.production_jobs.advance_to(4)
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_tick_or_snapshot_failure_happens_before_file_write(self):
        application = self._application_with_gameplay()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            with mock.patch(
                "application.game_application.GameSaveFileAdapter.save"
            ) as file_save:
                bad_snapshot = GameplaySnapshot(
                    simulation_tick=99,
                    inventories=(),
                    nodes=(),
                    recipes=(),
                    jobs=(),
                )
                with mock.patch(
                    "application.game_application.GameplaySnapshot.from_runtime",
                    return_value=bad_snapshot,
                ):
                    with self.assertRaises(ValueError):
                        application.save(path)
                file_save.assert_not_called()

            with mock.patch(
                "application.game_application.GameplaySnapshot.from_runtime",
                side_effect=ValueError("snapshot failed"),
            ), mock.patch(
                "application.game_application.GameSaveFileAdapter.save"
            ) as file_save:
                with self.assertRaises(ValueError):
                    application.save(path)
                file_save.assert_not_called()

    def test_load_rejects_legacy_actor_square_map_positions(self):
        application = self._application_with_gameplay()
        application.holder.current.actors.add(
            WorldActor("legacy_actor", "world_main", "player")
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-actor-save.json"
            application.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["actors"]["actors"][0]["location_id"] = "legacy_village"
            data["actors"]["actors"][0]["position"] = {"x": 3, "y": 4}
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "legacy square-map positions or placements"):
                application.load(path)

    def test_load_rejects_legacy_resource_node_square_map_locations(self):
        application = self._application_with_gameplay()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-resource-save.json"
            application.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["gameplay"]["nodes"][0]["location_id"] = "legacy_village"
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "legacy square-map positions or placements"):
                application.load(path)

    def test_load_rejects_legacy_npc_square_map_positions(self):
        application = self._application_with_gameplay()
        application.holder.current.social.npcs.add(
            NPC("legacy_npc", "Legacy NPC")
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "legacy-npc-save.json"
            application.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["social"]["npcs"][0]["location_id"] = "legacy_village"
            data["social"]["npcs"][0]["position"] = {"x": 3, "y": 4}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "legacy square-map positions"):
                application.load(path)

    def test_file_write_error_is_reported(self):
        application = self._application_with_gameplay()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            with mock.patch(
                "application.game_application.GameSaveFileAdapter.save",
                side_effect=SaveFileWriteError("write failed"),
            ):
                with self.assertRaises(SaveFileWriteError):
                    application.save(path)

    def test_save_does_not_replace_active_bundle(self):
        application = self._application_with_gameplay()
        active = application.holder.current
        runtime = active.simulation
        with tempfile.TemporaryDirectory() as directory:
            application.save(Path(directory) / "save.json")

        self.assertIs(application.holder.current, active)
        self.assertIs(application.holder.current.simulation, runtime)


    def test_save_load_round_trip_preserves_alternate_player_identity_links(self):
        session = GameSession()
        session.worlds.create("Main", world_id="world_main")
        session.worlds.set_active("world_main")
        inventory = Inventory()
        inventory.add(self.wood, Quantity(7, ResourceUnit.ITEM))
        jobs = ProductionJobManager(session.simulation)
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=jobs,
            resource_nodes=WorldResourceNodeManager(),
            inventories={"inventory_custom": inventory},
            recipes={self.recipe.recipe_id: self.recipe},
        )
        application = GameApplication(SessionHolder(bundle))
        factory = CharacterFactory(
            races={"race_custom": Race("race_custom", "Human")},
            classes={"class_custom": CharacterClass("class_custom", "Warrior")},
        )
        character = application.karakter_olustur(
            factory, "character_custom", "Test Hero",
            "race_custom", "class_custom", actor_id="actor_custom",
        )
        bundle.actors.bind_inventory("actor_custom", "inventory_custom")
        currency = Currency("gold")
        bundle.economy.ledger.credit(
            "account_custom", Money(125, currency), "test seed",
        )

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "alternate-player.json"
            application.save(path)
            application.load(path)

        restored = application.holder.current
        restored_service = GameplayService(application)
        restored_service.configure_player_context(
            "actor_custom", "inventory_custom", "account_custom",
        )

        self.assertEqual(restored_service.player_actor_id, "actor_custom")
        self.assertEqual(restored_service.player_inventory_id, "inventory_custom")
        self.assertEqual(restored_service.player_account_id, "account_custom")
        self.assertEqual(
            restored_service.actor_character("actor_custom").character_id,
            "character_custom",
        )
        self.assertEqual(
            restored.actors.get("actor_custom").character_id,
            "character_custom",
        )
        self.assertEqual(
            restored.actors.get("actor_custom").inventory_id,
            "inventory_custom",
        )
        self.assertEqual(
            restored.inventories["inventory_custom"].get(self.wood),
            Quantity(7, ResourceUnit.ITEM),
        )
        self.assertEqual(
            restored.economy.ledger.balance("account_custom", currency),
            Money(125, currency),
        )
        self.assertNotIn("player", restored.inventories)
        self.assertNotIn("actor_custom", restored.characters)

    def test_load_rejects_alternate_actor_with_unknown_inventory_reference(self):
        session = GameSession()
        session.worlds.create("Main", world_id="world_main")
        session.worlds.set_active("world_main")
        inventory = Inventory()
        jobs = ProductionJobManager(session.simulation)
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=jobs,
            resource_nodes=WorldResourceNodeManager(),
            inventories={"inventory_custom": inventory},
            recipes={},
        )
        application = GameApplication(SessionHolder(bundle))
        bundle.actors.add(
            WorldActor(
                "actor_custom", "world_main", "player",
                inventory_id="inventory_custom",
            )
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken-player-reference.json"
            application.save(path)
            data = json.loads(path.read_text(encoding="utf-8"))
            data["actors"]["actors"][0]["inventory_id"] = "missing_inventory"
            path.write_text(json.dumps(data), encoding="utf-8")
            active_before_load = application.holder.current

            with self.assertRaises(ValueError):
                application.load(path)

        self.assertIs(application.holder.current, active_before_load)


if __name__ == "__main__":
    unittest.main()
