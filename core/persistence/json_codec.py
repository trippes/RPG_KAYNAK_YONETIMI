"""Pure JSON codec for persistence documents.

This module performs no file I/O and does not construct runtime objects. JSON
structure is decoded here; persistence schema validation remains owned by
``PersistenceDocument.from_dict``.
"""

import json
from typing import Any

from .contracts import PersistenceDocument, PersistenceSchemaError


class JsonPersistenceCodec:
    """Deterministic, standard-library JSON codec for PersistenceDocument."""

    @staticmethod
    def encode(document: PersistenceDocument) -> str:
        if not isinstance(document, PersistenceDocument):
            raise TypeError("document must be PersistenceDocument.")
        try:
            return json.dumps(
                document.to_dict(),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as error:
            raise PersistenceSchemaError(
                "Persistence document is not JSON-compatible."
            ) from error

    @staticmethod
    def decode(payload: str) -> PersistenceDocument:
        if not isinstance(payload, str):
            raise TypeError("JSON payload must be a string.")
        try:
            data: Any = json.loads(payload, parse_constant=_reject_non_json_number)
        except json.JSONDecodeError as error:
            raise PersistenceSchemaError("Invalid JSON persistence document.") from error

        if not isinstance(data, dict):
            raise PersistenceSchemaError("JSON persistence document must be an object.")
        return PersistenceDocument.from_dict(data)


def _reject_non_json_number(value: str):
    raise PersistenceSchemaError(f"Non-standard JSON number is not allowed: {value}")


def encode_document(document: PersistenceDocument) -> str:
    """Encode a persistence document as deterministic JSON text."""
    return JsonPersistenceCodec.encode(document)


def decode_document(payload: str) -> PersistenceDocument:
    """Decode deterministic JSON text into a validated persistence document."""
    return JsonPersistenceCodec.decode(payload)
