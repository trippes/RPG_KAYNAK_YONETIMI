import json
import unittest

from core.persistence import (
    CANONICAL_PERSISTENCE_SCHEMA,
    JsonPersistenceCodec,
    PersistenceDocument,
    PersistenceSchemaError,
    PERSISTENCE_SCHEMA_VERSION,
    UnsupportedPersistenceSchemaError,
)
from core.time import Tick


class TestJsonPersistenceCodec(unittest.TestCase):
    def _document(self):
        return PersistenceDocument(
            state={"message": "Türkçe karakterler: ğüşöçı İ, emoji: 🚀"},
            simulation_tick=Tick(12),
            snapshot_id="snapshot-1",
        )

    def test_document_json_document_round_trip(self):
        original = self._document()

        encoded = JsonPersistenceCodec.encode(original)
        restored = JsonPersistenceCodec.decode(encoded)

        self.assertEqual(restored.to_dict(), original.to_dict())

    def test_encoding_is_deterministic(self):
        document = self._document()

        self.assertEqual(
            JsonPersistenceCodec.encode(document),
            JsonPersistenceCodec.encode(document),
        )

    def test_unicode_is_preserved_in_json_text(self):
        encoded = JsonPersistenceCodec.encode(self._document())

        self.assertIn("Türkçe", encoded)
        self.assertIn("🚀", encoded)
        self.assertEqual(JsonPersistenceCodec.decode(encoded).state["message"], "Türkçe karakterler: ğüşöçı İ, emoji: 🚀")

    def test_malformed_and_truncated_json_are_rejected(self):
        for payload in ('{"schema":', '{"schema":"rpg-core"'):
            with self.subTest(payload=payload):
                with self.assertRaises(PersistenceSchemaError):
                    JsonPersistenceCodec.decode(payload)

    def test_json_root_must_be_an_object(self):
        for payload in ('[]', '"text"', '42'):
            with self.subTest(payload=payload):
                with self.assertRaises(PersistenceSchemaError):
                    JsonPersistenceCodec.decode(payload)

    def test_missing_and_wrong_type_fields_use_document_validation(self):
        missing = {
            "schema": CANONICAL_PERSISTENCE_SCHEMA,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
        }
        wrong_type = {
            "schema": CANONICAL_PERSISTENCE_SCHEMA,
            "schema_version": PERSISTENCE_SCHEMA_VERSION,
            "core_version": "2.0",
            "simulation_tick": "12",
            "state": {},
        }

        with self.assertRaises(PersistenceSchemaError):
            JsonPersistenceCodec.decode('{"schema":')
        with self.assertRaises(PersistenceSchemaError):
            JsonPersistenceCodec.decode(json.dumps(missing))
        with self.assertRaises(PersistenceSchemaError):
            JsonPersistenceCodec.decode(json.dumps(wrong_type))

    def test_unknown_schema_and_unsupported_version_are_rejected(self):
        base = self._document().to_dict()
        unknown_schema = dict(base, schema="unknown-schema")
        unsupported_version = dict(base, schema_version=PERSISTENCE_SCHEMA_VERSION + 1)

        with self.assertRaises(PersistenceSchemaError):
            JsonPersistenceCodec.decode(json.dumps(unknown_schema))
        with self.assertRaises(UnsupportedPersistenceSchemaError):
            JsonPersistenceCodec.decode(json.dumps(unsupported_version))

    def test_non_standard_json_numbers_are_rejected(self):
        for payload in ('{"value":NaN}', '{"value":Infinity}', '{"value":-Infinity}'):
            with self.subTest(payload=payload):
                with self.assertRaises(PersistenceSchemaError):
                    JsonPersistenceCodec.decode(payload)

        for value in (float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                with self.assertRaises(PersistenceSchemaError):
                    JsonPersistenceCodec.encode(
                        PersistenceDocument({"value": value}, Tick(0))
                    )

    def test_unknown_fields_remain_tolerated(self):
        data = self._document().to_dict()
        data["future_field"] = {"enabled": True}

        restored = JsonPersistenceCodec.decode(json.dumps(data))

        self.assertEqual(restored.to_dict(), self._document().to_dict())

    def test_codec_does_not_accept_runtime_or_non_document_values(self):
        with self.assertRaises(TypeError):
            JsonPersistenceCodec.encode({"state": {}})
        with self.assertRaises(TypeError):
            JsonPersistenceCodec.decode(b"{}")


if __name__ == "__main__":
    unittest.main()
