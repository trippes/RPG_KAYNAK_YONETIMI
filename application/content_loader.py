"""Load versioned, data-only content packages.

The loader deliberately has no dependency on gameplay services or UI code.
Content definitions are parsed as JSON and returned as plain data.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping


CONTENT_PACKAGE_SCHEMA_VERSION = 1
class ContentPackageError(ValueError):
    """Raised when a content package is malformed or unsafe to load."""


@dataclass(frozen=True)
class ContentPackage:
    package_id: str
    package_version: str
    schema_version: int
    files: Mapping[str, dict]


def load_content_package(package_dir: str | Path) -> ContentPackage:
    """Load a package manifest and its JSON files without executing content."""
    root = Path(package_dir).resolve()
    manifest_path = root / "manifest.json"

    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ContentPackageError(
            f"Content package manifest could not be loaded: {manifest_path}"
        ) from error

    if not isinstance(manifest, dict):
        raise ContentPackageError("Content package manifest must be a JSON object.")

    allowed_fields = {"schema_version", "package_id", "package_version", "files"}
    unknown_fields = sorted(set(manifest) - allowed_fields)
    if unknown_fields:
        raise ContentPackageError(
            "Content package manifest has unsupported fields: "
            + ", ".join(unknown_fields)
        )

    schema_version = manifest.get("schema_version")
    if (
        type(schema_version) is not int
        or schema_version != CONTENT_PACKAGE_SCHEMA_VERSION
    ):
        raise ContentPackageError("Unsupported content package schema version.")

    package_id = manifest.get("package_id")
    package_version = manifest.get("package_version")
    if not isinstance(package_id, str) or not package_id.strip():
        raise ContentPackageError("Content package id must be a non-empty string.")
    if not isinstance(package_version, str) or not package_version.strip():
        raise ContentPackageError("Content package version must be a non-empty string.")

    file_map = manifest.get("files")
    if not isinstance(file_map, dict) or not file_map:
        raise ContentPackageError("Content package must declare at least one data file.")

    loaded_files: dict[str, dict] = {}
    resolved_paths: set[Path] = set()
    for key, relative_path in file_map.items():
        if not isinstance(key, str) or not key.strip():
            raise ContentPackageError("Content package file keys must be non-empty strings.")
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise ContentPackageError(f"Content file path for '{key}' is invalid.")

        source = (root / relative_path).resolve()
        if not source.is_relative_to(root):
            raise ContentPackageError(
                f"Content file '{key}' resolves outside the package directory."
            )
        if source in resolved_paths:
            raise ContentPackageError(f"Content file is referenced more than once: {key}")
        resolved_paths.add(source)

        try:
            definition = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentPackageError(
                f"Content data file '{key}' could not be loaded: {source}"
            ) from error
        if not isinstance(definition, dict):
            raise ContentPackageError(
                f"Content data file '{key}' must contain a JSON object."
            )
        loaded_files[key] = definition

    return ContentPackage(
        package_id=package_id,
        package_version=package_version,
        schema_version=schema_version,
        files=MappingProxyType(loaded_files),
    )
