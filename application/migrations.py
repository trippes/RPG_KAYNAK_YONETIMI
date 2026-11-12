"""Explicit migrations for application save envelopes."""
from __future__ import annotations

from copy import deepcopy

CURRENT_SAVE_SCHEMA_VERSION = 2


def migrate_save_data(data: dict, *, npc_definitions=None) -> dict:
    """Return a normalized copy of a legacy save without mutating its input.

    v0 is the original Core/gameplay envelope. v1 added optional gameplay
    sections. v2 adds the optional, independently versioned container section.
    Old saves deliberately migrate with no container data.
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
    _restore_legacy_npc_positions(normalized, npc_definitions)
    return normalized

def _restore_legacy_npc_positions(data: dict, npc_definitions) -> None:
    """Backfill absent/default NPC positions from the active content package."""
    if not npc_definitions:
        return
    social = data.get("social")
    if not isinstance(social, dict):
        return
    saved_npcs = social.get("npcs")
    if not isinstance(saved_npcs, list):
        return
    saved_by_id = {
        item.get("npc_id"): item
        for item in saved_npcs
        if isinstance(item, dict) and isinstance(item.get("npc_id"), str)
    }
    for definition in npc_definitions:
        if not isinstance(definition, dict):
            continue
        npc_id = definition.get("id")
        coordinates = definition.get("position")
        if (
            not isinstance(npc_id, str)
            or not isinstance(coordinates, (list, tuple))
            or len(coordinates) != 2
            or any(isinstance(value, bool) or not isinstance(value, (int, float)) for value in coordinates)
        ):
            continue
        saved = saved_by_id.get(npc_id)
        if saved is None:
            continue
        position = saved.get("position")
        if position is None or position == {"x": 0, "y": 0}:
            saved["position"] = {"x": coordinates[0], "y": coordinates[1]}


__all__ = ["CURRENT_SAVE_SCHEMA_VERSION", "migrate_save_data"]
