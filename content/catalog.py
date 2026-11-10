"""Load, validate, and index editor-authored content packs.

This layer deliberately handles data only. Runtime systems remain responsible for
turning validated records into NPCs, items, quests, enemies, maps, and other
domain objects.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping


CONTENT_CATALOG_SCHEMA_VERSION = 1
CONTENT_PACK_SCHEMA_VERSION = 1
_KIND_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]*$")


class ContentCatalogError(ValueError):
    """Raised when a content catalog or pack is unsafe or inconsistent."""


@dataclass(frozen=True)
class ContentRecord:
    """One catalog entry; authored data is exposed read-only at the top level."""

    kind: str
    content_id: str
    pack_id: str
    source_path: str
    data: Mapping[str, Any]


@dataclass(frozen=True)
class ContentPackInfo:
    """Validated metadata for one enabled content pack."""

    pack_id: str
    version: str
    dependencies: tuple[str, ...]


class ContentCatalog:
    """A deterministic, read-only index of records in enabled content packs."""

    def __init__(
        self,
        records: tuple[ContentRecord, ...],
        packs: tuple[ContentPackInfo, ...],
    ) -> None:
        self._records = records
        self._packs = packs
        self._by_key = MappingProxyType(
            {(record.kind, record.content_id): record for record in records}
        )

    @property
    def records(self) -> tuple[ContentRecord, ...]:
        return self._records

    @property
    def packs(self) -> tuple[ContentPackInfo, ...]:
        return self._packs

    def get(self, kind: str, content_id: str) -> ContentRecord | None:
        """Return one record by its type-scoped ID."""
        return self._by_key.get((kind, content_id))

    def all(self, kind: str | None = None) -> tuple[ContentRecord, ...]:
        """Return records in deterministic pack/manifest order, optionally by kind."""
        if kind is None:
            return self._records
        return tuple(record for record in self._records if record.kind == kind)

    def pack_ids(self) -> tuple[str, ...]:
        return tuple(pack.pack_id for pack in self._packs)


def load_content_catalog(
    root: str | Path,
    *,
    enabled_pack_ids: set[str] | frozenset[str] | None = None,
) -> ContentCatalog:
    """Load a catalog directory containing a manifest.json file.

    Catalog manifest example:
        {"schema_version": 1, "packs": [
            {"id": "world_base", "manifest": "packs/world_base/pack.json", "enabled": True}
        ]}

    Pack manifest example:
        {"schema_version": 1, "id": "world_base", "version": "1.0.0",
         "dependencies": [], "files": [{"kind": "npc", "path": "npcs/warden.json"}]}

    Each listed file contains one JSON object with a non-empty id. Optional
    cross-content references use references: [{"kind": "item", "id": "iron_sword"}].
    """
    catalog_root = Path(root).resolve()
    manifest_path = _resolve_inside(catalog_root, "manifest.json", catalog_root)
    manifest = _read_json(manifest_path, "catalog manifest")
    if manifest.get("schema_version") != CONTENT_CATALOG_SCHEMA_VERSION:
        raise ContentCatalogError("Unsupported content catalog schema version.")

    raw_packs = manifest.get("packs")
    if not isinstance(raw_packs, list):
        raise ContentCatalogError("Catalog manifest 'packs' must be a list.")

    pack_entries: dict[str, dict[str, Any]] = {}
    manifest_order: list[str] = []
    for index, entry in enumerate(raw_packs):
        if not isinstance(entry, dict):
            raise ContentCatalogError(f"Pack entry at index {index} must be an object.")
        pack_id = _valid_id(entry.get("id"), f"pack id at index {index}")
        if pack_id in pack_entries:
            raise ContentCatalogError(f"Duplicate content pack id: {pack_id}")
        manifest_ref = entry.get("manifest")
        if not isinstance(manifest_ref, str) or not manifest_ref.strip():
            raise ContentCatalogError(f"Pack {pack_id} has no manifest path.")
        enabled = entry.get("enabled", True)
        if not isinstance(enabled, bool):
            raise ContentCatalogError(f"Pack {pack_id} enabled flag must be boolean.")
        pack_entries[pack_id] = {"manifest": manifest_ref, "enabled": enabled}
        manifest_order.append(pack_id)

    if enabled_pack_ids is None:
        selected = {key for key, entry in pack_entries.items() if entry["enabled"]}
    else:
        selected = set(enabled_pack_ids)
        unknown = selected - set(pack_entries)
        if unknown:
            raise ContentCatalogError(
                "Unknown enabled content packs: " + ", ".join(sorted(unknown))
            )

    pack_definitions: dict[str, dict[str, Any]] = {}
    for pack_id in manifest_order:
        if pack_id not in selected:
            continue
        pack_manifest_path = _resolve_inside(
            catalog_root, pack_entries[pack_id]["manifest"], catalog_root
        )
        definition = _read_json(pack_manifest_path, f"manifest for pack {pack_id}")
        if definition.get("schema_version") != CONTENT_PACK_SCHEMA_VERSION:
            raise ContentCatalogError(f"Unsupported schema version in pack {pack_id}.")
        if definition.get("id") != pack_id:
            raise ContentCatalogError(f"Pack manifest id does not match catalog id: {pack_id}")
        version = definition.get("version")
        if not isinstance(version, str) or not version.strip():
            raise ContentCatalogError(f"Pack {pack_id} must declare a version.")
        dependencies = definition.get("dependencies", [])
        if not isinstance(dependencies, list) or any(
            not isinstance(value, str) or not value.strip() for value in dependencies
        ):
            raise ContentCatalogError(f"Pack {pack_id} dependencies must be a list of IDs.")
        if len(dependencies) != len(set(dependencies)):
            raise ContentCatalogError(f"Pack {pack_id} has duplicate dependencies.")
        files = definition.get("files")
        if not isinstance(files, list):
            raise ContentCatalogError(f"Pack {pack_id} files must be a list.")
        pack_definitions[pack_id] = {
            "version": version,
            "dependencies": tuple(dependencies),
            "files": files,
            "directory": pack_manifest_path.parent,
        }

    for pack_id, definition in pack_definitions.items():
        missing = set(definition["dependencies"]) - selected
        if missing:
            raise ContentCatalogError(
                f"Pack {pack_id} requires disabled or missing packs: "
                + ", ".join(sorted(missing))
            )

    ordered_pack_ids = _dependency_order(pack_definitions, manifest_order)
    records: list[ContentRecord] = []
    seen: set[tuple[str, str]] = set()

    for pack_id in ordered_pack_ids:
        definition = pack_definitions[pack_id]
        for index, file_entry in enumerate(definition["files"]):
            if not isinstance(file_entry, dict):
                raise ContentCatalogError(
                    f"File entry {index} in pack {pack_id} must be an object."
                )
            kind = file_entry.get("kind")
            if not isinstance(kind, str) or not _KIND_PATTERN.fullmatch(kind):
                raise ContentCatalogError(
                    f"File entry {index} in pack {pack_id} has an invalid content kind."
                )
            relative_path = file_entry.get("path")
            if not isinstance(relative_path, str) or not relative_path.strip():
                raise ContentCatalogError(
                    f"File entry {index} in pack {pack_id} has no path."
                )
            record_path = _resolve_inside(
                definition["directory"], relative_path, catalog_root
            )
            data = _read_json(record_path, f"{kind} record in pack {pack_id}")
            content_id = _valid_id(data.get("id"), f"{kind} record id in pack {pack_id}")
            key = (kind, content_id)
            if key in seen:
                raise ContentCatalogError(
                    f"Duplicate {kind} content id across enabled packs: {content_id}"
                )
            _validate_references(data, kind, content_id)
            seen.add(key)
            records.append(
                ContentRecord(
                    kind=kind,
                    content_id=content_id,
                    pack_id=pack_id,
                    source_path=record_path.relative_to(catalog_root).as_posix(),
                    data=MappingProxyType(dict(data)),
                )
            )

    record_keys = {(record.kind, record.content_id) for record in records}
    for record in records:
        for reference in record.data.get("references", ()):
            key = (reference["kind"], reference["id"])
            if key not in record_keys:
                raise ContentCatalogError(
                    f"{record.kind} {record.content_id} references missing "
                    f"{reference['kind']} content {reference['id']}."
                )

    packs = tuple(
        ContentPackInfo(
            pack_id=pack_id,
            version=pack_definitions[pack_id]["version"],
            dependencies=pack_definitions[pack_id]["dependencies"],
        )
        for pack_id in ordered_pack_ids
    )
    return ContentCatalog(tuple(records), packs)


def _dependency_order(
    definitions: Mapping[str, Mapping[str, Any]],
    manifest_order: list[str],
) -> tuple[str, ...]:
    ordered: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(pack_id: str) -> None:
        if pack_id in visited:
            return
        if pack_id in visiting:
            raise ContentCatalogError(f"Content pack dependency cycle includes {pack_id}.")
        visiting.add(pack_id)
        for dependency in definitions[pack_id]["dependencies"]:
            if dependency not in definitions:
                raise ContentCatalogError(
                    f"Pack {pack_id} depends on unknown pack {dependency}."
                )
            visit(dependency)
        visiting.remove(pack_id)
        visited.add(pack_id)
        ordered.append(pack_id)

    for pack_id in manifest_order:
        if pack_id in definitions:
            visit(pack_id)
    return tuple(ordered)


def _validate_references(data: Mapping[str, Any], kind: str, content_id: str) -> None:
    references = data.get("references", [])
    if not isinstance(references, list):
        raise ContentCatalogError(f"{kind} {content_id} references must be a list.")
    for index, reference in enumerate(references):
        if not isinstance(reference, dict):
            raise ContentCatalogError(
                f"Reference {index} in {kind} {content_id} must be an object."
            )
        ref_kind = reference.get("kind")
        ref_id = reference.get("id")
        if not isinstance(ref_kind, str) or not _KIND_PATTERN.fullmatch(ref_kind):
            raise ContentCatalogError(
                f"Reference {index} in {kind} {content_id} has an invalid kind."
            )
        _valid_id(ref_id, f"reference id in {kind} {content_id}")


def _valid_id(value: Any, description: str) -> str:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise ContentCatalogError(f"Invalid {description}.")
    return value


def _resolve_inside(base: Path, relative_path: str, allowed_root: Path) -> Path:
    candidate = (base / relative_path).resolve()
    try:
        candidate.relative_to(allowed_root)
    except ValueError as error:
        raise ContentCatalogError(
            f"Content path escapes catalog root: {relative_path}"
        ) from error
    if not candidate.is_file():
        raise ContentCatalogError(f"Content file does not exist: {relative_path}")
    return candidate


def _read_json(path: Path, description: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentCatalogError(f"Could not read {description}: {path}") from error
    if not isinstance(value, dict):
        raise ContentCatalogError(f"{description} must be a JSON object.")
    return value
