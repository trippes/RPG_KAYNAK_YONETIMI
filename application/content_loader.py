"""Load versioned, data-only content packages with parallel map models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from .hex_map_definition import load_hex_map_definition
from .world_map_definition import parse_world_map, validate_world_map

CONTENT_PACKAGE_SCHEMA_VERSION = 1


class ContentPackageError(ValueError):
    """Malformed or unsafe content package."""


@dataclass(frozen=True)
class ContentPackage:
    package_id: str
    package_version: str
    schema_version: int
    files: Mapping[str, dict]
    map_definitions: Mapping[str, object]
    hex_map_definitions: Mapping[str, object]
    world_map_definition: object | None = None
    presentation_assets_path: Path | None = None


def _load_hex_maps(maps_root: Path, square_maps: Mapping[str, object]) -> dict[str, object]:
    hex_maps: dict[str, object] = {}
    transition_ids = {
        transition.transition_id
        for definition in square_maps.values()
        for transition in definition.transitions
    }
    for source in sorted(maps_root.glob("*.json")):
        try:
            raw = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentPackageError(f"Map file could not be loaded: {source}") from error
        if not isinstance(raw, dict):
            raise ContentPackageError(f"Map file '{source}' must contain a JSON object.")
        version = raw.get("schema_version")
        if type(version) is not int:
            raise ContentPackageError(f"Map file '{source}' has an invalid schema_version.")
        if version == 1:
            continue
        if version != 2:
            raise ContentPackageError(
                f"Map file '{source}' uses unsupported schema_version '{version}'."
            )
        try:
            definition = load_hex_map_definition(source)
        except (OSError, ValueError) as error:
            raise ContentPackageError(f"Invalid hex map '{source}': {error}") from error
        if definition.map_id in square_maps or definition.map_id in hex_maps:
            raise ContentPackageError(f"Duplicate map ID in package: {definition.map_id}")
        hex_maps[definition.map_id] = definition
        for transition in definition.transitions:
            if transition.transition_id in transition_ids:
                raise ContentPackageError(
                    f"Duplicate transition ID in map package: {transition.transition_id}"
                )
            transition_ids.add(transition.transition_id)
    return hex_maps


def load_content_package(package_dir: str | Path) -> ContentPackage:
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
    allowed = {"schema_version", "package_id", "package_version", "files", "maps", "world_map", "presentation_assets"}
    extra = sorted(set(manifest) - allowed)
    if extra:
        raise ContentPackageError(
            "Content package manifest has unsupported fields: " + ", ".join(extra)
        )
    version = manifest.get("schema_version")
    if type(version) is not int or version != CONTENT_PACKAGE_SCHEMA_VERSION:
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

    files = {}
    resolved = set()
    for key, relative in file_map.items():
        if not isinstance(key, str) or not key.strip():
            raise ContentPackageError("Content package file keys must be non-empty strings.")
        if not isinstance(relative, str) or not relative.strip():
            raise ContentPackageError(f"Content file path for '{key}' is invalid.")
        source = (root / relative).resolve()
        if not source.is_relative_to(root):
            raise ContentPackageError(
                f"Content file '{key}' resolves outside the package directory."
            )
        if source in resolved:
            raise ContentPackageError(f"Content file is referenced more than once: {key}")
        resolved.add(source)
        try:
            value = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentPackageError(
                f"Content data file '{key}' could not be loaded: {source}"
            ) from error
        if not isinstance(value, dict):
            raise ContentPackageError(
                f"Content data file '{key}' must contain a JSON object."
            )
        files[key] = value

    square = {}
    hexes = {}
    world_map = None
    maps_dir = manifest.get("maps")
    if maps_dir is not None:
        if not isinstance(maps_dir, str) or not maps_dir.strip():
            raise ContentPackageError(
                "Content package maps directory must be a non-empty relative path."
            )
        maps_root = (root / maps_dir).resolve()
        if not maps_root.is_relative_to(root):
            raise ContentPackageError(
                "Content package maps directory resolves outside the package directory."
            )
        if not maps_root.is_dir():
            raise ContentPackageError(
                f"Content package maps directory could not be loaded: {maps_root}"
            )
        try:
            from world.map_catalog import load_map_catalog

            square, _ = load_map_catalog(maps_root)
            hexes = _load_hex_maps(maps_root, square)
            world_map_path = manifest.get("world_map")
            if world_map_path is not None:
                if not isinstance(world_map_path, str) or not world_map_path.strip():
                    raise ContentPackageError(
                        "Content package world_map path must be a non-empty relative path."
                    )
                world_map_source = (root / world_map_path).resolve()
                if not world_map_source.is_relative_to(root):
                    raise ContentPackageError(
                        "Content package world_map path resolves outside the package directory."
                    )
                try:
                    world_map_data = json.loads(world_map_source.read_text(encoding="utf-8"))
                    world_map = parse_world_map(world_map_data)
                    validate_world_map(world_map, hexes)
                except (OSError, json.JSONDecodeError, ValueError) as error:
                    raise ContentPackageError(
                        f"Invalid content package world map '{world_map_source}': {error}"
                    ) from error
        except (OSError, ValueError) as error:
            raise ContentPackageError(
                f"Content package maps could not be loaded from '{maps_root}': {error}"
            ) from error
    elif manifest.get("world_map") is not None:
        raise ContentPackageError("Content package world_map requires a maps directory.")

    presentation_assets_path = None
    presentation_assets_relative = manifest.get("presentation_assets")
    if presentation_assets_relative is not None:
        if not isinstance(presentation_assets_relative, str) or not presentation_assets_relative.strip():
            raise ContentPackageError("Presentation asset catalog path must be a non-empty relative path.")
        candidate = (root / presentation_assets_relative).resolve()
        if not candidate.is_relative_to(root):
            raise ContentPackageError("Presentation asset catalog path resolves outside the package directory.")
        if not candidate.is_file():
            raise ContentPackageError(f"Presentation asset catalog could not be loaded: {candidate}")
        try:
            presentation_data = json.loads(candidate.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentPackageError("Presentation asset catalog could not be parsed.") from error
        if (
            not isinstance(presentation_data, dict)
            or presentation_data.get("schema_version") != 1
            or not isinstance(presentation_data.get("assets"), list)
            or not isinstance(presentation_data.get("objects", []), list)
        ):
            raise ContentPackageError("Presentation asset catalog has an invalid schema.")
        presentation_assets_path = candidate

    return ContentPackage(
        package_id,
        package_version,
        version,
        MappingProxyType(files),
        MappingProxyType(square),
        MappingProxyType(hexes),
        world_map,
        presentation_assets_path,
    )
