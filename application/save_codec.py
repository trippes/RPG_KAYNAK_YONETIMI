"""Deterministic JSON codec for the application-level game save envelope."""

import json
from typing import Any

from .save_document import GameSaveDocument, SaveDocumentError


class SaveJsonCodec:
    """Encode and decode GameSaveDocument without filesystem access."""

    @staticmethod
    def encode(document: GameSaveDocument) -> str:
        if not isinstance(document, GameSaveDocument):
            raise TypeError("document must be GameSaveDocument.")
        try:
            return json.dumps(
                document.to_dict(),
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        except (TypeError, ValueError) as error:
            raise SaveDocumentError(
                "Game save document is not JSON-compatible."
            ) from error

    @staticmethod
    def decode(payload: str) -> GameSaveDocument:
        if not isinstance(payload, str):
            raise TypeError("JSON payload must be a string.")
        try:
            data: Any = json.loads(payload, parse_constant=_reject_constant)
        except json.JSONDecodeError as error:
            raise SaveDocumentError("Invalid game save JSON.") from error
        return GameSaveDocument.from_dict(data)


def _reject_constant(value: str):
    raise SaveDocumentError(f"Non-standard JSON number is not allowed: {value}")


def encode_document(document: GameSaveDocument) -> str:
    return SaveJsonCodec.encode(document)


def decode_document(payload: str) -> GameSaveDocument:
    return SaveJsonCodec.decode(payload)
