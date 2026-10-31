import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.application import GameSession, SessionPersistenceService
from core.domain.spatial import Position
from core.entity import Entity, EntityType
from core.persistence import (
    CanonicalEntityRecord,
    CanonicalSessionState,
    EntityRepositoryState,
    FilePersistenceAdapter,
    MembershipRecord,
    PersistenceDocument,
    PersistenceFileReadError,
    PersistenceSchemaError,
    RestoreContract,
    RestoreValidationError,
    WorldMembershipState,
)
from core.foundation import EntityId, WorldId
from core.time import Tick


def session_snapshot(session):
    return CanonicalSessionState.from_session(session).to_dict()


def make_source_session():
    source = GameSession()
    first = source.worlds.create("First", width=20, height=30, world_id="world_a")
    second = source.worlds.create("Second", width=40, height=50, world_id="world_b")
    source.worlds.set_active(second.world_id)
    source.add_entity(Entity(EntityType.NPC, "Guard", entity_id="entity_a"), first.world_id)
    source.add_entity(Entity(EntityType.KARAKTER, "Hero", entity_id="entity_b"), second.world_id)
    source.simulation.advance_to(11)
    return source


class TestSessionPersistenceService(unittest.TestCase):
    def setUp(self):
        Entity._id_generator.reset()

    def _write_document(self, directory, state, tick):
        path = Path(directory) / "session.json"
        FilePersistenceAdapter.save(
            PersistenceDocument(state=state, simulation_tick=Tick(tick)),
            path,
        )
        return path

    def _make_existing_target(self):
        target = GameSession()
        world = target.worlds.create("Existing", world_id="existing")
        target.worlds.set_active(world.world_id)
        target.add_entity(Entity(EntityType.NPC, "Existing", entity_id="existing_entity"), world.world_id)
        target.simulation.advance_to(100)
        return target

    def test_valid_file_restores_complete_session(self):
        source = make_source_session()
        target = self._make_existing_target()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "session.json"
            document = PersistenceDocument.from_state(CanonicalSessionState.from_session(source))
            FilePersistenceAdapter.save(document, path)

            result = SessionPersistenceService.load_into(target, path)

        self.assertIs(result, target)
        self.assertEqual(session_snapshot(target), session_snapshot(source))
        self.assertEqual([world.world_id for world in target.worlds.get_all()], ["world_a", "world_b"])
        self.assertEqual(target.membership.world_id_for("entity_a"), "world_a")
        self.assertEqual(target.membership.world_id_for("entity_b"), "world_b")
        self.assertEqual(target.worlds.get_active_id(), "world_b")
        self.assertEqual(target.simulation.current_tick.value, 11)

    def test_missing_file_preserves_session_and_session_can_continue(self):
        target = self._make_existing_target()
        before = session_snapshot(target)

        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PersistenceFileReadError):
                SessionPersistenceService.load_into(target, Path(directory) / "missing.json")

        self.assertEqual(session_snapshot(target), before)
        target.simulation.advance_to(101)
        self.assertEqual(target.simulation.current_tick.value, 101)

    def test_file_read_error_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)

        with tempfile.TemporaryDirectory() as directory:
            with mock.patch(
                "core.application.persistence.FilePersistenceAdapter.load",
                side_effect=PersistenceFileReadError("denied"),
            ):
                with self.assertRaises(PersistenceFileReadError):
                    SessionPersistenceService.load_into(target, Path(directory) / "session.json")

        self.assertEqual(session_snapshot(target), before)

    def test_malformed_json_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.json"
            path.write_text('{"schema":', encoding="utf-8")

            with self.assertRaises(PersistenceSchemaError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)

    def test_unsupported_schema_version_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)
        source = make_source_session()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "future.json"
            data = PersistenceDocument.from_state(CanonicalSessionState.from_session(source)).to_dict()
            data["schema_version"] = 2
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(PersistenceSchemaError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)

    def test_unknown_schema_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)
        source = make_source_session()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "unknown-schema.json"
            data = PersistenceDocument.from_state(CanonicalSessionState.from_session(source)).to_dict()
            data["schema"] = "unknown-schema"
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(PersistenceSchemaError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)

    def test_envelope_state_tick_mismatch_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)
        source = make_source_session()

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tick-mismatch.json"
            data = PersistenceDocument.from_state(CanonicalSessionState.from_session(source)).to_dict()
            data["simulation_tick"] = 12
            path.write_text(json.dumps(data), encoding="utf-8")

            with self.assertRaises(PersistenceSchemaError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)

    def test_invalid_membership_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)
        source = make_source_session()
        state = CanonicalSessionState.from_session(source).to_dict()
        state["memberships"] = {
            "records": [{"entity_id": "missing", "world_id": "world_a"}],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_document(directory, state, 11)

            with self.assertRaises(RestoreValidationError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)

    def test_invalid_active_world_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)
        source = make_source_session()
        state = CanonicalSessionState.from_session(source).to_dict()
        state["active_world_id"] = "missing-world"

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_document(directory, state, 11)

            with self.assertRaises(RestoreValidationError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)

    def test_activation_failure_preserves_session(self):
        target = self._make_existing_target()
        before = session_snapshot(target)
        source = make_source_session()
        state = CanonicalSessionState.from_session(source).to_dict()
        state["entities"]["records"][0]["state"] = {"durum": "invalid", "canli": True}

        with tempfile.TemporaryDirectory() as directory:
            path = self._write_document(directory, state, 11)

            with self.assertRaises(ValueError):
                SessionPersistenceService.load_into(target, path)

        self.assertEqual(session_snapshot(target), before)
        target.simulation.advance_to(101)
        self.assertEqual(target.simulation.current_tick.value, 101)

    def test_session_type_is_required(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                SessionPersistenceService.load_into({}, Path(directory) / "session.json")


if __name__ == "__main__":
    unittest.main()
