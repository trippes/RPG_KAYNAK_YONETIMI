import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from application import GameSaveDocument, GameSaveFileAdapter, SaveJsonCodec
from application.save_file_adapter import SaveFileReadError, SaveFileWriteError
from application.save_document import (
    SaveDocumentError,
    UnsupportedSaveSchemaError,
)
from core.application import GameSession
from core.persistence import CanonicalSessionState, PersistenceDocument
from core.simulation import SimulationRuntime
from core.time import Tick
from resources import (
    GameplayPersistenceError,
    GameplaySnapshot,
    Inventory,
    ProductionJobManager,
    Quantity,
    Recipe,
    ResourceType,
    ResourceUnit,
    WorldResourceNodeManager,
)
from core.foundation import EntityId


class TestUnifiedSaveDocument(unittest.TestCase):
    def _document(self):
        session = GameSession()
        session.simulation.advance_to(3)
        core = PersistenceDocument.from_state(CanonicalSessionState.from_session(session))

        wood = ResourceType("wood")
        inventory = Inventory()
        inventory.add(wood, Quantity(2, ResourceUnit.ITEM))
        jobs = ProductionJobManager(SimulationRuntime(start_tick=3))
        gameplay = GameplaySnapshot.from_runtime(
            {"main": inventory}, WorldResourceNodeManager(), jobs
        )
        return GameSaveDocument(core=core, gameplay=gameplay)

    def test_valid_document_preserves_inner_schemas(self):
        document = self._document()
        data = document.to_dict()

        self.assertEqual(data["schema"], "rpg-game-save")
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(data["core"]["schema"], "rpg-core")
        self.assertEqual(data["gameplay"]["schema"], "rpg-gameplay")

    def test_schema_and_versions_are_validated(self):
        data = self._document().to_dict()
        data["schema"] = "other"
        with self.assertRaises(SaveDocumentError):
            GameSaveDocument.from_dict(data)

        data = self._document().to_dict()
        data["schema_version"] = 2
        with self.assertRaises(UnsupportedSaveSchemaError):
            GameSaveDocument.from_dict(data)

        data = self._document().to_dict()
        data["core"]["schema_version"] = 2
        with self.assertRaises(Exception):
            GameSaveDocument.from_dict(data)

        data = self._document().to_dict()
        data["gameplay"]["schema_version"] = 2
        with self.assertRaises(GameplayPersistenceError):
            GameSaveDocument.from_dict(data)

    def test_tick_mismatch_and_missing_outer_fields_are_rejected(self):
        document = self._document()
        data = document.to_dict()
        data["gameplay"]["simulation_tick"] = 4
        with self.assertRaises(SaveDocumentError):
            GameSaveDocument.from_dict(data)

        data = document.to_dict()
        del data["gameplay"]
        with self.assertRaises(SaveDocumentError):
            GameSaveDocument.from_dict(data)

        data = document.to_dict()
        data["unexpected"] = True
        with self.assertRaises(SaveDocumentError):
            GameSaveDocument.from_dict(data)

    def test_codec_round_trip_is_deterministic(self):
        document = self._document()
        encoded = SaveJsonCodec.encode(document)
        decoded = SaveJsonCodec.decode(encoded)

        self.assertEqual(encoded, SaveJsonCodec.encode(decoded))
        self.assertEqual(encoded, SaveJsonCodec.encode(document))

    def test_codec_rejects_invalid_json_and_inner_documents(self):
        with self.assertRaises(SaveDocumentError):
            SaveJsonCodec.decode('{"schema":')

        data = self._document().to_dict()
        data["core"]["state"] = None
        with self.assertRaises(Exception):
            SaveJsonCodec.decode(json.dumps(data))

        data = self._document().to_dict()
        data["gameplay"] = {"schema": "rpg-gameplay", "schema_version": 1}
        with self.assertRaises(GameplayPersistenceError):
            SaveJsonCodec.decode(json.dumps(data))

    def test_file_adapter_round_trip(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            result = GameSaveFileAdapter.save(document, path)
            loaded = GameSaveFileAdapter.load(result)

        self.assertEqual(SaveJsonCodec.encode(document), SaveJsonCodec.encode(loaded))

    def test_existing_valid_save_is_backed_up_before_replacement(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            GameSaveFileAdapter.save(document, path)

            GameSaveFileAdapter.save(document, path)

            backup = GameSaveFileAdapter.backup_path(path)
            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(backup)),
                SaveJsonCodec.encode(document),
            )
            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(path)),
                SaveJsonCodec.encode(document),
            )

    def test_corrupt_primary_recovers_from_valid_backup_and_repairs_primary(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            backup = GameSaveFileAdapter.backup_path(path)
            backup.write_text(SaveJsonCodec.encode(document), encoding="utf-8")
            path.write_text('{"broken":', encoding="utf-8")

            loaded = GameSaveFileAdapter.load(path)

            self.assertEqual(
                SaveJsonCodec.encode(loaded),
                SaveJsonCodec.encode(document),
            )
            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(path)),
                SaveJsonCodec.encode(document),
            )
            self.assertTrue(backup.is_file())

    def test_save_does_not_overwrite_valid_backup_with_corrupt_primary(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            backup = GameSaveFileAdapter.backup_path(path)
            backup.write_text(SaveJsonCodec.encode(document), encoding="utf-8")
            path.write_text('{"broken":', encoding="utf-8")

            GameSaveFileAdapter.save(document, path)

            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(backup)),
                SaveJsonCodec.encode(document),
            )
            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(path)),
                SaveJsonCodec.encode(document),
            )

    def test_invalid_primary_and_backup_raise_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text('{"broken":', encoding="utf-8")
            GameSaveFileAdapter.backup_path(path).write_text(
                "also broken", encoding="utf-8"
            )

            with self.assertRaises(SaveDocumentError):
                GameSaveFileAdapter.load(path)

    def test_write_failure_preserves_existing_target_and_cleans_temp(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            GameSaveFileAdapter.save(document, path)
            previous = path.read_text(encoding="utf-8")

            with mock.patch(
                "application.save_file_adapter.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaises(OSError):
                    GameSaveFileAdapter.save(document, path)

            self.assertEqual(path.read_text(encoding="utf-8"), previous)
            self.assertEqual(list(Path(directory).glob(".save.json.*.tmp")), [])


    def test_interrupted_final_replace_keeps_primary_and_recovery_copy(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            backup = GameSaveFileAdapter.backup_path(path)
            GameSaveFileAdapter.save(document, path)
            original_payload = path.read_text(encoding="utf-8")

            real_replace = __import__("os").replace
            replace_calls = 0

            def interrupt_primary_replace(source, target):
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise OSError("simulated interruption before primary replace")
                return real_replace(source, target)

            with mock.patch(
                "application.save_file_adapter.os.replace",
                side_effect=interrupt_primary_replace,
            ):
                with self.assertRaises(SaveFileWriteError):
                    GameSaveFileAdapter.save(document, path)

            self.assertEqual(replace_calls, 2)
            self.assertEqual(path.read_text(encoding="utf-8"), original_payload)
            self.assertTrue(backup.is_file())
            self.assertEqual(
                SaveJsonCodec.encode(GameSaveFileAdapter.load(backup)),
                original_payload,
            )
            self.assertEqual(list(Path(directory).glob(".save.json.*.tmp")), [])
            self.assertEqual(list(Path(directory).glob(".save.json.bak.*.tmp")), [])

    def test_legacy_version_zero_envelope_migrates_without_mutating_input(self):
        data = self._document().to_dict()
        data["schema_version"] = 0

        migrated = GameSaveDocument.from_dict(data)

        self.assertEqual(data["schema_version"], 0)
        self.assertEqual(migrated.schema_version, 1)
        self.assertEqual(
            SaveJsonCodec.encode(migrated),
            SaveJsonCodec.encode(self._document()),
        )


if __name__ == "__main__":
    unittest.main()
