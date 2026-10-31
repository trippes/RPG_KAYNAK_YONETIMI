import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from application import (
    GameApplication,
    GameSaveDocument,
    GameSaveFileAdapter,
    SessionBundle,
    SessionHolder,
)
from application.save_file_adapter import SaveFileReadError
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


class TestCandidateRestore(unittest.TestCase):
    def setUp(self):
        self.wood = ResourceType("wood")
        self.tool = ResourceType("tool")
        self.recipe = Recipe(
            "tool_recipe",
            ((self.wood, Quantity(3, ResourceUnit.ITEM)),),
            ((self.tool, Quantity(1, ResourceUnit.ITEM)),),
        )

    def _document(self, node_world_id="world_main"):
        source = GameSession()
        source.worlds.create("Main", world_id="world_main")
        source.worlds.set_active("world_main")
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        jobs = ProductionJobManager(source.simulation)
        jobs.start(self.recipe, inventory, 4, job_id="job_main")
        jobs.advance_to(0)

        nodes = WorldResourceNodeManager()
        nodes.add(WorldResourceNode(
            "node_main",
            node_world_id,
            self.wood,
            Quantity(2, ResourceUnit.ITEM),
            Quantity(5, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
            Tick(0),
        ))
        core = PersistenceDocument.from_state(CanonicalSessionState.from_session(source))
        gameplay = GameplaySnapshot.from_runtime(
            {"main": inventory}, nodes, jobs
        )
        return GameSaveDocument(core=core, gameplay=gameplay)

    def _write(self, directory, document):
        path = Path(directory) / "save.json"
        GameSaveFileAdapter.save(document, path)
        return path

    def test_valid_load_publishes_candidate_using_one_runtime(self):
        application = GameApplication.create_default()
        old = application.holder.current

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            candidate = application.load(path)

        self.assertIs(application.holder.current, candidate)
        self.assertIsNot(candidate, old)
        self.assertIs(candidate.simulation, candidate.session.simulation)
        self.assertIs(candidate.production_jobs.runtime, candidate.simulation)
        self.assertEqual(candidate.session.simulation.current_tick.value, 0)
        self.assertEqual(candidate.resource_nodes.get("node_main").world_id, "world_main")
        self.assertEqual(candidate.production_jobs.runtime.dispatcher.consumer_count(), 1)
        self.assertIs(candidate.recipes["tool_recipe"], candidate.production_jobs.get("job_main").recipe)

    def test_active_job_continues_without_second_input_consumption_or_duplicate_output(self):
        application = GameApplication.create_default()
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            application.load(path)

        bundle = application.holder.current
        inventory = bundle.inventories["main"]
        self.assertIsNone(inventory.get(self.wood))

        bundle.production_jobs.advance_to(4)
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))
        bundle.production_jobs.advance_to(4)
        self.assertEqual(inventory.get(self.tool), Quantity(1, ResourceUnit.ITEM))

    def test_invalid_node_world_keeps_existing_bundle_and_runtime(self):
        application = GameApplication.create_default()
        old = application.holder.current
        old_runtime = old.simulation

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document("missing_world"))
            with self.assertRaises(ValueError):
                application.load(path)

        self.assertIs(application.holder.current, old)
        self.assertIs(application.holder.current.simulation, old_runtime)

    def test_invalid_gameplay_document_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            data = json.loads(path.read_text(encoding="utf-8"))
            data["gameplay"]["jobs"][0]["inventory_id"] = "missing"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                application.load(path)

        self.assertIs(application.holder.current, old)

    def test_missing_or_broken_file_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / "missing.json"
            with self.assertRaises(OSError):
                application.load(missing)
            broken = Path(directory) / "broken.json"
            broken.write_text('{"schema":', encoding="utf-8")
            with self.assertRaises(ValueError):
                application.load(broken)

        self.assertIs(application.holder.current, old)

    def test_file_read_failure_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text("unreadable-in-practice", encoding="utf-8")
            with mock.patch(
                "application.save_file_adapter.Path.read_text",
                side_effect=OSError("read failed"),
            ):
                with self.assertRaises(SaveFileReadError):
                    application.load(path)

        self.assertIs(application.holder.current, old)

    def test_schema_and_tick_failures_keep_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            data = json.loads(path.read_text(encoding="utf-8"))

            data["schema_version"] = 99
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                application.load(path)
            self.assertIs(application.holder.current, old)

            data = json.loads(self._write(directory, self._document()).read_text(encoding="utf-8"))
            data["gameplay"]["simulation_tick"] = 1
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                application.load(path)
            self.assertIs(application.holder.current, old)

    def test_core_validation_failure_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            data = json.loads(path.read_text(encoding="utf-8"))
            data["core"]["state"]["active_world_id"] = "missing_world"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(ValueError):
                application.load(path)

        self.assertIs(application.holder.current, old)

    def test_gameplay_restore_failure_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            with mock.patch(
                "application.game_application.GameplaySnapshot.restore",
                side_effect=ValueError("restore failed"),
            ):
                with self.assertRaises(ValueError):
                    application.load(path)

        self.assertIs(application.holder.current, old)

    def test_failed_load_preserves_existing_runtime_and_world_state(self):
        application = GameApplication.create_default()
        old = application.holder.current
        world = application.dunya_olustur("Existing", world_id="existing_world")
        node = WorldResourceNode(
            "existing_node",
            world.world_id,
            self.wood,
            Quantity(2, ResourceUnit.ITEM),
            Quantity(5, ResourceUnit.ITEM),
            Quantity(1, ResourceUnit.ITEM),
            Tick(0),
        )
        old.resource_nodes.add(node)
        old.simulation.advance_to(3)
        before_quantity = node.quantity

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document("missing_world"))
            with self.assertRaises(ValueError):
                application.load(path)

        self.assertIs(application.holder.current, old)
        self.assertEqual(old.simulation.current_tick.value, 3)
        self.assertIs(old.resource_nodes.get("existing_node"), node)
        self.assertEqual(node.quantity, before_quantity)

    def test_failed_load_preserves_existing_job_scheduler_and_dispatcher(self):
        session = GameSession()
        session.worlds.create("Existing", world_id="existing_world")
        inventory = Inventory()
        inventory.add(self.wood, Quantity(3, ResourceUnit.ITEM))
        jobs = ProductionJobManager(session.simulation)
        jobs.start(self.recipe, inventory, 4, job_id="existing_job")
        jobs.advance_to(0)
        bundle = SessionBundle(
            session=session,
            simulation=session.simulation,
            production_jobs=jobs,
            resource_nodes=WorldResourceNodeManager(),
            inventories={"main": inventory},
            recipes={self.recipe.recipe_id: self.recipe},
        )
        application = GameApplication(SessionHolder(bundle))
        old_runtime = bundle.simulation
        old_job = bundle.production_jobs.get("existing_job")
        old_pending = old_runtime.actions.scheduler.pending_count
        old_consumers = old_runtime.dispatcher.consumer_count()

        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document("missing_world"))
            with self.assertRaises(ValueError):
                application.load(path)

        self.assertIs(application.holder.current, bundle)
        self.assertIs(application.holder.current.simulation, old_runtime)
        self.assertEqual(old_runtime.actions.scheduler.pending_count, old_pending)
        self.assertEqual(old_runtime.dispatcher.consumer_count(), old_consumers)
        self.assertIs(bundle.production_jobs.get("existing_job"), old_job)
        self.assertEqual(old_job.state.value, "running")
        self.assertIsNone(inventory.get(self.wood))

    def test_publish_failure_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            with mock.patch.object(
                application.holder, "publish", side_effect=RuntimeError("publish failed")
            ):
                with self.assertRaises(RuntimeError):
                    application.load(path)

        self.assertIs(application.holder.current, old)

    def test_candidate_bundle_validation_failure_keeps_existing_bundle(self):
        application = GameApplication.create_default()
        old = application.holder.current
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            with mock.patch(
                "application.game_application.SessionBundle",
                side_effect=ValueError("candidate invariant failed"),
            ):
                with self.assertRaises(ValueError):
                    application.load(path)

        self.assertIs(application.holder.current, old)

    def test_facade_uses_published_bundle_after_load(self):
        application = GameApplication.create_default()
        with tempfile.TemporaryDirectory() as directory:
            path = self._write(directory, self._document())
            application.load(path)

        self.assertEqual(application.aktif_dunya().world_id, "world_main")
        application.advance_simulation(2)
        self.assertEqual(application.holder.current.simulation.current_tick.value, 2)


if __name__ == "__main__":
    unittest.main()
