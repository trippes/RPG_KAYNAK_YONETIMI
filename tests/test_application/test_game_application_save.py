import tempfile
import unittest
from pathlib import Path
from unittest import mock

from application import (
    GameApplication,
    GameSaveFileAdapter,
    SaveJsonCodec,
    SessionBundle,
    SessionHolder,
)
from application.save_file_adapter import SaveFileWriteError
from core.application import GameSession
from core.persistence import CanonicalSessionState, PersistenceDocument
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
        self.assertEqual(document.schema_version, 1)
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


if __name__ == "__main__":
    unittest.main()
