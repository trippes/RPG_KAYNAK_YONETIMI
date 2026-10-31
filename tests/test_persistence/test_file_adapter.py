import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from core.persistence import (
    CANONICAL_PERSISTENCE_SCHEMA,
    FilePersistenceAdapter,
    PersistenceDocument,
    PersistenceFileReadError,
    PersistenceFileWriteError,
    PERSISTENCE_SCHEMA_VERSION,
    UnsupportedPersistenceSchemaError,
)
from core.time import Tick


class TestFilePersistenceAdapter(unittest.TestCase):
    def _document(self, message="Türkçe kayıt 🚀"):
        return PersistenceDocument(
            state={"message": message, "values": [1, 2, 3]},
            simulation_tick=Tick(12),
            snapshot_id="snapshot-1",
        )

    def test_save_new_file_and_load_document(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"

            result = FilePersistenceAdapter.save(self._document(), path)

            self.assertEqual(result, path)
            self.assertEqual(FilePersistenceAdapter.load(path).to_dict(), self._document().to_dict())

    def test_existing_file_is_updated_successfully(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            FilePersistenceAdapter.save(self._document("old"), path)

            FilePersistenceAdapter.save(self._document("new"), path)

            self.assertEqual(FilePersistenceAdapter.load(path).state["message"], "new")

    def test_file_is_utf8_and_unicode_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            document = self._document()

            FilePersistenceAdapter.save(document, path)

            raw = path.read_bytes()
            self.assertIn("Türkçe".encode("utf-8"), raw)
            self.assertEqual(FilePersistenceAdapter.load(path).state["message"], "Türkçe kayıt 🚀")

    def test_missing_file_is_reported_as_file_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(PersistenceFileReadError):
                FilePersistenceAdapter.load(Path(directory) / "missing.json")

    def test_empty_and_malformed_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            empty = Path(directory) / "empty.json"
            malformed = Path(directory) / "malformed.json"
            empty.write_text("", encoding="utf-8")
            malformed.write_text('{"schema":', encoding="utf-8")

            with self.assertRaises(ValueError):
                FilePersistenceAdapter.load(empty)
            with self.assertRaises(ValueError):
                FilePersistenceAdapter.load(malformed)

    def test_unsupported_schema_and_version_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            unknown_schema = Path(directory) / "unknown-schema.json"
            future_version = Path(directory) / "future-version.json"
            base = self._document().to_dict()
            unknown_schema.write_text(
                json.dumps(dict(base, schema="unknown-schema")),
                encoding="utf-8",
            )
            future_version.write_text(
                json.dumps(dict(base, schema_version=PERSISTENCE_SCHEMA_VERSION + 1)),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                FilePersistenceAdapter.load(unknown_schema)
            with self.assertRaises(UnsupportedPersistenceSchemaError):
                FilePersistenceAdapter.load(future_version)

    def test_unreadable_file_is_wrapped_as_file_read_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            path.write_text("{}", encoding="utf-8")

            with mock.patch.object(Path, "read_text", side_effect=PermissionError("denied")):
                with self.assertRaises(PersistenceFileReadError):
                    FilePersistenceAdapter.load(path)

    def test_failed_replace_preserves_existing_target_and_cleans_temp_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            FilePersistenceAdapter.save(self._document("original"), path)
            original_bytes = path.read_bytes()

            with mock.patch("core.persistence.file_adapter.os.replace", side_effect=OSError("replace failed")):
                with self.assertRaises(PersistenceFileWriteError):
                    FilePersistenceAdapter.save(self._document("replacement"), path)

            self.assertEqual(path.read_bytes(), original_bytes)
            self.assertEqual(list(Path(directory).glob(".save.json.*.tmp")), [])

    def test_failed_flush_preserves_existing_target_and_cleans_temp_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            FilePersistenceAdapter.save(self._document("original"), path)
            original_bytes = path.read_bytes()

            with mock.patch("core.persistence.file_adapter.os.fsync", side_effect=OSError("flush failed")):
                with self.assertRaises(PersistenceFileWriteError):
                    FilePersistenceAdapter.save(self._document("replacement"), path)

            self.assertEqual(path.read_bytes(), original_bytes)
            self.assertEqual(list(Path(directory).glob(".save.json.*.tmp")), [])

    def test_deterministic_document_keeps_file_content_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "save.json"
            document = self._document()

            FilePersistenceAdapter.save(document, path)
            first = path.read_bytes()
            FilePersistenceAdapter.save(document, path)
            second = path.read_bytes()

            self.assertEqual(first, second)

    def test_adapter_rejects_non_document_values(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                FilePersistenceAdapter.save({}, Path(directory) / "save.json")


if __name__ == "__main__":
    unittest.main()
