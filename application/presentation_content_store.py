"""Safe persistence and explicit migration for presentation content packages.

This module is deliberately independent of Pygame and editor UI. It validates a
complete staged package before replacing source files, writes UTF-8 JSON
atomically, and retains the previous bytes in a sidecar backup.
"""
from __future__ import annotations

import json
import math
import os
import shutil
import tempfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Mapping

from .save_lock import save_path_lock


class PresentationContentStoreError(RuntimeError):
    """Base error for presentation-content persistence."""


class ContentWriteError(PresentationContentStoreError):
    """A validated content update could not be committed safely."""


class ContentMigrationError(PresentationContentStoreError):
    """A legacy presentation document could not be migrated safely."""


@dataclass(frozen=True, slots=True)
class ContentWriteResult:
    written_paths: tuple[Path, ...]
    backup_paths: tuple[Path, ...]


@dataclass(frozen=True, slots=True)
class ContentMigrationResult:
    migrated: bool
    written_paths: tuple[Path, ...] = ()


class PresentationContentStore:
    """Validate and safely persist split presentation content for one package."""

    MANIFEST_NAME = "manifest.json"
    ASSET_CATALOG_FIELD = "asset_catalog"
    PLACEMENTS_FIELD = "map_placements"
    LEGACY_PRESENTATION_FIELD = "presentation_assets"

    def __init__(self, package_root: str | os.PathLike[str]) -> None:
        self.package_root = Path(package_root).resolve()
        if not self.package_root.is_dir():
            raise PresentationContentStoreError(
                f"Content package directory does not exist: {self.package_root}"
            )

    def save_asset_catalog(self, payload: Mapping[str, Any]) -> ContentWriteResult:
        """Validate and atomically replace the package's split asset catalog."""
        with save_path_lock(self.package_root / self.MANIFEST_NAME):
            with self._staged_package() as stage_root:
                manifest = self._read_manifest(stage_root)
                relative = manifest.get(self.ASSET_CATALOG_FIELD)
                if relative is None:
                    raise ContentWriteError(
                        "Package has no split asset_catalog source; migrate legacy content first."
                    )
                self._write_staged_json(stage_root, relative, payload)
                self._validate_staged_package(stage_root)
                return self._commit_staged_files(stage_root, (relative,))

    def save_map_placements(
        self,
        map_id: str,
        payload: Mapping[str, Any],
    ) -> ContentWriteResult:
        """Validate and atomically replace one map's placement document."""
        if not isinstance(map_id, str) or not map_id.strip():
            raise ContentWriteError("map_id must be a non-empty string.")
        with save_path_lock(self.package_root / self.MANIFEST_NAME):
            with self._staged_package() as stage_root:
                manifest = self._read_manifest(stage_root)
                relative_directory = manifest.get(self.PLACEMENTS_FIELD)
                if relative_directory is None:
                    raise ContentWriteError(
                        "Package has no split map_placements source; migrate legacy content first."
                    )
                if not isinstance(payload, Mapping) or payload.get("map_id") != map_id:
                    raise ContentWriteError(
                        "Placement payload map_id must match the requested map_id."
                    )
                placements_directory = self._resolve_package_path(
                    stage_root, relative_directory
                )
                if not placements_directory.is_dir():
                    raise ContentWriteError(
                        f"Placement directory does not exist: {relative_directory}"
                    )
                relative = self._placement_relative_path(
                    stage_root, relative_directory, map_id
                )
                self._write_staged_json(stage_root, relative, payload)
                self._validate_staged_package(stage_root)
                return self._commit_staged_files(stage_root, (relative,))

    def migrate_legacy_combined_presentation(self) -> ContentMigrationResult:
        """Split a validated legacy presentation_assets.json without deleting it.

        The migration is explicit and idempotent. It writes the new catalog,
        per-map placement documents, and manifest pointers only after the
        complete staged package passes the normal content loader.
        """
        with save_path_lock(self.package_root / self.MANIFEST_NAME):
            with self._staged_package() as stage_root:
                manifest = self._read_manifest(stage_root)
                has_assets = self.ASSET_CATALOG_FIELD in manifest
                has_placements = self.PLACEMENTS_FIELD in manifest
                if has_assets and has_placements:
                    try:
                        self._validate_staged_package(stage_root)
                    except ContentWriteError as error:
                        raise ContentMigrationError(
                            f"Existing split presentation content is invalid: {error}"
                        ) from error
                    return ContentMigrationResult(migrated=False)
                if has_assets != has_placements:
                    raise ContentMigrationError(
                        "Manifest contains only one split presentation source; refusing partial migration."
                    )

                legacy_relative = manifest.get(self.LEGACY_PRESENTATION_FIELD)
                if legacy_relative is None:
                    raise ContentMigrationError(
                        "Package has no legacy presentation_assets source to migrate."
                    )
                try:
                    self._validate_staged_package(stage_root)
                except ContentWriteError as error:
                    raise ContentMigrationError(
                        f"Legacy presentation content is invalid: {error}"
                    ) from error
                legacy_path = self._resolve_package_path(stage_root, legacy_relative)
                try:
                    legacy_payload = json.loads(
                        legacy_path.read_text(encoding="utf-8"),
                        parse_constant=self._reject_json_constant,
                    )
                except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
                    raise ContentMigrationError(
                        f"Legacy presentation file could not be read: {legacy_path}"
                    ) from error
                if not isinstance(legacy_payload, dict):
                    raise ContentMigrationError(
                        "Legacy presentation document must be a JSON object."
                    )
                unknown_root = set(legacy_payload) - {"schema_version", "assets", "objects"}
                if unknown_root:
                    raise ContentMigrationError(
                        "Legacy presentation document has unsupported fields: "
                        + ", ".join(sorted(unknown_root))
                    )
                assets = legacy_payload.get("assets")
                objects = legacy_payload.get("objects", [])
                if not isinstance(assets, list) or not isinstance(objects, list):
                    raise ContentMigrationError(
                        "Legacy presentation assets and objects must be lists."
                    )

                from game_ui.assets.placement_catalog import ScenePlacementCatalog

                allowed_object_fields = ScenePlacementCatalog.ALLOWED_OBJECT_FIELDS | {"map_id"}
                grouped: dict[str, list[dict[str, Any]]] = {}
                for index, record in enumerate(objects):
                    if not isinstance(record, dict):
                        raise ContentMigrationError(
                            f"Legacy objects[{index}] must be an object."
                        )
                    unknown = set(record) - allowed_object_fields
                    if unknown:
                        raise ContentMigrationError(
                            f"Legacy objects[{index}] has unsupported fields: "
                            + ", ".join(sorted(unknown))
                        )
                    target_map = record.get("map_id")
                    if not isinstance(target_map, str) or not target_map.strip():
                        raise ContentMigrationError(
                            f"Legacy objects[{index}] requires a non-empty map_id."
                        )
                    self._validate_filename_component(target_map, "map_id")
                    grouped.setdefault(target_map, []).append(
                        {key: value for key, value in record.items() if key != "map_id"}
                    )

                asset_relative = "asset_catalog.json"
                placements_relative = "placements"
                asset_payload = {"schema_version": 1, "assets": assets}
                asset_target = self._resolve_package_path(stage_root, asset_relative)
                asset_encoded = self._encode_json(asset_payload)
                if asset_target.exists() and asset_target.read_text(encoding="utf-8") != asset_encoded:
                    raise ContentMigrationError(
                        "An unmanaged asset_catalog.json conflicts with the legacy migration."
                    )
                self._write_staged_json(stage_root, asset_relative, asset_payload)

                placements_directory = self._resolve_package_path(
                    stage_root, placements_relative
                )
                expected_placement_names = {
                    f"{target_map}.json" for target_map in grouped
                }
                if placements_directory.exists():
                    existing_names = {
                        source.name for source in placements_directory.glob("*.json")
                    }
                    unexpected = existing_names - expected_placement_names
                    if unexpected:
                        raise ContentMigrationError(
                            "Unmanaged placement files conflict with the legacy migration: "
                            + ", ".join(sorted(unexpected))
                        )
                for target_map, records in sorted(grouped.items()):
                    placement_relative = (
                        f"{placements_relative}/{target_map}.json"
                    )
                    placement_payload = {
                        "schema_version": 1,
                        "map_id": target_map,
                        "objects": records,
                    }
                    placement_target = self._resolve_package_path(
                        stage_root, placement_relative
                    )
                    placement_encoded = self._encode_json(placement_payload)
                    if (
                        placement_target.exists()
                        and placement_target.read_text(encoding="utf-8")
                        != placement_encoded
                    ):
                        raise ContentMigrationError(
                            f"An unmanaged placement file conflicts with map '{target_map}'."
                        )
                    self._write_staged_json(
                        stage_root, placement_relative, placement_payload
                    )

                manifest[self.ASSET_CATALOG_FIELD] = asset_relative
                manifest[self.PLACEMENTS_FIELD] = placements_relative
                self._write_staged_json(stage_root, self.MANIFEST_NAME, manifest)
                try:
                    self._validate_staged_package(stage_root)
                except ContentWriteError as error:
                    raise ContentMigrationError(
                        f"Migrated presentation content failed validation: {error}"
                    ) from error

                changed = [
                    asset_relative,
                    *(
                        f"{placements_relative}/{target_map}.json"
                        for target_map in sorted(grouped)
                    ),
                    self.MANIFEST_NAME,
                ]
                result = self._commit_staged_files(stage_root, tuple(changed))
                return ContentMigrationResult(
                    migrated=True,
                    written_paths=result.written_paths,
                )

    @contextmanager
    def _staged_package(self):
        """Yield a temporary package copy, preserving symlinks for boundary checks."""
        with tempfile.TemporaryDirectory(
            prefix=f".{self.package_root.name}.content-stage-",
            dir=self.package_root.parent,
        ) as temporary_directory:
            stage_root = Path(temporary_directory) / self.package_root.name
            shutil.copytree(self.package_root, stage_root, symlinks=True)
            yield stage_root

    def _read_manifest(self, stage_root: Path) -> dict[str, Any]:
        path = self._resolve_package_path(stage_root, self.MANIFEST_NAME)
        try:
            payload = json.loads(
                path.read_text(encoding="utf-8"),
                parse_constant=self._reject_json_constant,
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            raise ContentWriteError(
                f"Content package manifest could not be read: {path}"
            ) from error
        if not isinstance(payload, dict):
            raise ContentWriteError("Content package manifest must be a JSON object.")
        return payload

    def _validate_staged_package(self, stage_root: Path) -> None:
        from .content_loader import ContentPackageError, load_content_package

        try:
            load_content_package(stage_root)
        except (ContentPackageError, OSError, ValueError, TypeError) as error:
            raise ContentWriteError(
                f"Staged presentation content failed package validation: {error}"
            ) from error

    def _placement_relative_path(
        self,
        stage_root: Path,
        relative_directory: str,
        map_id: str,
    ) -> str:
        self._validate_filename_component(map_id, "map_id")
        directory = self._resolve_package_path(stage_root, relative_directory)
        matches = []
        for source in sorted(directory.glob("*.json")):
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict) and payload.get("map_id") == map_id:
                matches.append(source)
        if len(matches) > 1:
            raise ContentWriteError(
                f"Multiple placement files declare map_id '{map_id}'."
            )
        if matches:
            return matches[0].relative_to(stage_root).as_posix()
        return f"{PurePosixPath(relative_directory).as_posix()}/{map_id}.json"

    @staticmethod
    def _validate_filename_component(value: str, label: str) -> None:
        posix = PurePosixPath(value)
        windows = PureWindowsPath(value)
        if (
            value in {"", ".", ".."}
            or posix.name != value
            or windows.name != value
            or "/" in value
            or "\\" in value
            or any(ord(char) < 32 for char in value)
        ):
            raise ContentWriteError(f"{label} must be a safe filename component.")

    @classmethod
    def _resolve_package_path(cls, root: Path, relative: str) -> Path:
        if not isinstance(relative, str) or not relative.strip():
            raise ContentWriteError("Content path must be a non-empty relative path.")
        posix = PurePosixPath(relative)
        windows = PureWindowsPath(relative)
        if (
            posix.is_absolute()
            or windows.is_absolute()
            or windows.drive
            or "\\" in relative
            or ".." in posix.parts
        ):
            raise ContentWriteError(f"Unsafe content path: {relative}")
        candidate = root.joinpath(*posix.parts)
        current = root
        for part in posix.parts:
            current = current / part
            if current.is_symlink():
                raise ContentWriteError(f"Content path contains a symlink: {relative}")
        resolved = candidate.resolve()
        if not resolved.is_relative_to(root.resolve()):
            raise ContentWriteError(f"Content path escapes package root: {relative}")
        return candidate

    def _write_staged_json(
        self,
        stage_root: Path,
        relative: str,
        payload: Mapping[str, Any],
    ) -> None:
        if not isinstance(payload, Mapping):
            raise ContentWriteError("Content JSON root must be an object.")
        try:
            encoded = self._encode_json(payload)
            target = self._resolve_package_path(stage_root, relative)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(encoded, encoding="utf-8", newline="\n")
        except (OSError, TypeError, ValueError) as error:
            if isinstance(error, PresentationContentStoreError):
                raise
            raise ContentWriteError(
                f"Could not stage content JSON '{relative}': {error}"
            ) from error

    @classmethod
    def _encode_json(cls, payload: Mapping[str, Any]) -> str:
        cls._validate_json_value(payload, "$")
        try:
            return json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                indent=2,
            ) + "\n"
        except (TypeError, ValueError) as error:
            raise ContentWriteError("Content payload is not valid JSON data.") from error

    @classmethod
    def _validate_json_value(cls, value: Any, path: str) -> None:
        if value is None or isinstance(value, (str, bool)):
            return
        if type(value) is int:
            return
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ContentWriteError(f"Non-finite number at {path}.")
            return
        if isinstance(value, list):
            for index, item in enumerate(value):
                cls._validate_json_value(item, f"{path}[{index}]")
            return
        if isinstance(value, dict):
            for key, item in value.items():
                if not isinstance(key, str):
                    raise ContentWriteError(f"JSON object key at {path} must be a string.")
                cls._validate_json_value(item, f"{path}.{key}")
            return
        raise ContentWriteError(
            f"Unsupported JSON value at {path}: {type(value).__name__}."
        )

    @staticmethod
    def _reject_json_constant(value: str):
        raise ValueError(f"Non-standard JSON number is not allowed: {value}")

    def _commit_staged_files(
        self,
        stage_root: Path,
        relative_paths: tuple[str, ...],
    ) -> ContentWriteResult:
        prepared = []
        backups = []
        for relative in relative_paths:
            staged = self._resolve_package_path(stage_root, relative)
            target = self._resolve_package_path(self.package_root, relative)
            if not staged.is_file():
                raise ContentWriteError(f"Staged content file is missing: {relative}")
            if target.exists() and not target.is_file():
                raise ContentWriteError(f"Content target is not a regular file: {target}")
            old_bytes = target.read_bytes() if target.is_file() else None
            new_bytes = staged.read_bytes()
            backup = target.with_name(target.name + ".bak")
            prepared.append((relative, target, new_bytes, old_bytes, backup))

        # Backups are complete before the first live target is replaced.
        try:
            for _, target, _, old_bytes, backup in prepared:
                if old_bytes is not None:
                    self._atomic_write_bytes(backup, old_bytes)
                    backups.append(backup)
        except OSError as error:
            raise ContentWriteError(
                f"Could not preserve existing content before commit: {error}"
            ) from error

        replaced = []
        existing_parent_directories = {
            target.parent for _, target, _, _, _ in prepared if target.parent.exists()
        }
        try:
            for relative, target, new_bytes, old_bytes, backup in prepared:
                target.parent.mkdir(parents=True, exist_ok=True)
                temporary = self._write_temporary_bytes(target, new_bytes)
                try:
                    self._replace_target(temporary, target)
                    temporary = None
                finally:
                    if temporary is not None:
                        temporary.unlink(missing_ok=True)
                replaced.append((target, old_bytes))
            for directory in {item[1].parent for item in prepared}:
                self._fsync_directory(directory)
        except OSError as error:
            rollback_errors = []
            for target, old_bytes in reversed(replaced):
                try:
                    if old_bytes is None:
                        target.unlink(missing_ok=True)
                    else:
                        self._atomic_write_bytes(target, old_bytes)
                except OSError as rollback_error:
                    rollback_errors.append(f"{target}: {rollback_error}")
            created_directories = {
                target.parent for _, target, _, _, _ in prepared
            } - existing_parent_directories
            for directory in sorted(created_directories, key=lambda item: len(item.parts), reverse=True):
                try:
                    directory.rmdir()
                except OSError:
                    pass
            detail = (
                " Rollback also failed for: " + "; ".join(rollback_errors)
                if rollback_errors else ""
            )
            backup_detail = (
                " Recovery backups: " + ", ".join(str(path) for path in backups)
                if backups else ""
            )
            raise ContentWriteError(
                f"Content commit failed; previously replaced files were rolled back.{detail}{backup_detail}"
            ) from error

        return ContentWriteResult(
            written_paths=tuple(self.package_root / item[0] for item in prepared),
            backup_paths=tuple(backups),
        )

    @staticmethod
    def _write_temporary_bytes(target: Path, payload: bytes) -> Path:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
            return Path(temporary.name)

    @staticmethod
    def _replace_target(source: Path, target: Path) -> None:
        os.replace(source, target)

    @classmethod
    def _atomic_write_bytes(cls, target: Path, payload: bytes) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = cls._write_temporary_bytes(target, payload)
        try:
            os.replace(temporary, target)
            temporary = None
            cls._fsync_directory(target.parent)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    @staticmethod
    def _fsync_directory(directory: Path) -> None:
        if os.name != "posix":
            return
        flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        descriptor = os.open(directory, flags)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
