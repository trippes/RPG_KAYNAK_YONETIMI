"""Explicit migrations for application save envelopes."""
from __future__ import annotations
from copy import deepcopy

CURRENT_SAVE_SCHEMA_VERSION = 1


def migrate_save_data(data: dict) -> dict:
    """Return a normalized copy of a legacy save without mutating input.

    Version 0 was the pre-extension envelope: it used the same core/gameplay
    payloads but had no optional character, economy, social or combat sections.
    """
    if not isinstance(data, dict):
        raise TypeError("save data must be a dict.")
    normalized = deepcopy(data)
    version = normalized.get("schema_version")
    if version == 0:
        normalized["schema_version"] = CURRENT_SAVE_SCHEMA_VERSION
        return normalized
    return normalized


__all__ = ["CURRENT_SAVE_SCHEMA_VERSION", "migrate_save_data"]
