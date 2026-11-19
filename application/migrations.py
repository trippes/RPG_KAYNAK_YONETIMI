"""Explicit migrations for application save envelopes."""
from __future__ import annotations

from copy import deepcopy

CURRENT_SAVE_SCHEMA_VERSION = 3


def migrate_save_data(data: dict) -> dict:
    """Return a normalized copy of a legacy save without mutating its input.

    v0 is the original Core/gameplay envelope. v1 added optional gameplay
    sections. v2 adds the optional container section. v3 adds an optional,
    independently versioned HexWorldRuntime snapshot. Old saves migrate with
    no hex-world snapshot; no square coordinates are converted.
    """
    if not isinstance(data, dict):
        raise TypeError("save data must be a dict.")
    normalized = deepcopy(data)
    version = normalized.get("schema_version")
    if isinstance(version, bool) or not isinstance(version, int):
        return normalized
    if version == 0:
        normalized["schema_version"] = 1
        version = 1
    if version == 1:
        normalized.setdefault("containers", None)
        normalized["schema_version"] = 2
        version = 2
    if version == 2:
        normalized.setdefault("hex_world", None)
        normalized["schema_version"] = 3
    return normalized


__all__ = ["CURRENT_SAVE_SCHEMA_VERSION", "migrate_save_data"]
