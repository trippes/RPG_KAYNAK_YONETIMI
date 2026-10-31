import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from application import GameSaveDocument, GameSaveFileAdapter, SaveJsonCodec
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

    def test_existing_save_is_backed_up_before_replacement(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text("previous-valid-save", encoding="utf-8")

            GameSaveFileAdapter.save(document, path)

            backup = GameSaveFileAdapter.backup_path(path)
            self.assertEqual(backup.read_text(encoding="utf-8"), "previous-valid-save")
            self.assertNotEqual(path.read_text(encoding="utf-8"), "previous-valid-save")

    def test_write_failure_preserves_existing_target_and_cleans_temp(self):
        document = self._document()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text("previous-valid-save", encoding="utf-8")

            with mock.patch(
                "application.save_file_adapter.os.replace",
                side_effect=OSError("replace failed"),
            ):
                with self.assertRaises(OSError):
                    GameSaveFileAdapter.save(document, path)

            self.assertEqual(path.read_text(encoding="utf-8"), "previous-valid-save")
            self.assertEqual(list(Path(directory).glob(".save.json.*.tmp")), [])


if __name__ == "__main__":
    unittest.main()
