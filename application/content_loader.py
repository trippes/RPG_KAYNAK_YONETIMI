"""Load versioned, data-only content packages with parallel map models."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from core.domain.spatial import LocalHexPosition

from .hex_map_definition import load_hex_map_definition
from .world_map_definition import parse_world_map, validate_world_map
from .gameplay_placement_catalog import (
    GameplayPlacementCatalog,
    GameplayPlacementCatalogError,
)

CONTENT_PACKAGE_SCHEMA_VERSION = 1


class ContentPackageError(ValueError):
    """Malformed or unsafe content package."""


@dataclass(frozen=True)
class ContentPackage:
    package_id: str
    package_version: str
    schema_version: int
    files: Mapping[str, dict]
    hex_map_definitions: Mapping[str, object]
    world_map_definition: object | None = None
    presentation_assets_path: Path | None = None
    asset_catalog_path: Path | None = None
    map_placements_path: Path | None = None
    presentation_catalog: object | None = None
    scene_placements: object | None = None
    gameplay_placements_path: Path | None = None
    gameplay_placements: GameplayPlacementCatalog | None = None


def _load_hex_maps(maps_root: Path) -> dict[str, object]:
    hex_maps: dict[str, object] = {}
    transition_ids = set()
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
            raise ContentPackageError(
                f"Legacy square-map schema is no longer supported: {source}"
            )
        if version != 2:
            raise ContentPackageError(
                f"Map file '{source}' uses unsupported schema_version '{version}'."
            )
        try:
            definition = load_hex_map_definition(source)
        except (OSError, ValueError) as error:
            raise ContentPackageError(f"Invalid hex map '{source}': {error}") from error
        if definition.map_id in hex_maps:
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
    allowed = {
        "schema_version", "package_id", "package_version", "files", "maps",
        "world_map", "presentation_assets", "asset_catalog", "map_placements",
        "gameplay_placements",
    }
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
            hexes = _load_hex_maps(maps_root)
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

    asset_catalog_path = None
    map_placements_path = None
    asset_catalog_relative = manifest.get("asset_catalog")
    map_placements_relative = manifest.get("map_placements")
    if (asset_catalog_relative is None) != (map_placements_relative is None):
        raise ContentPackageError(
            "Split presentation content requires both asset_catalog and map_placements."
        )
    if asset_catalog_relative is not None:
        if not isinstance(asset_catalog_relative, str) or not asset_catalog_relative.strip():
            raise ContentPackageError("Asset catalog path must be a non-empty relative path.")
        asset_catalog_path = (root / asset_catalog_relative).resolve()
        if not asset_catalog_path.is_relative_to(root):
            raise ContentPackageError("Asset catalog path resolves outside the package directory.")
        if not asset_catalog_path.is_file():
            raise ContentPackageError(f"Asset catalog could not be loaded: {asset_catalog_path}")
        try:
            asset_payload = json.loads(asset_catalog_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ContentPackageError("Asset catalog could not be parsed.") from error
        if (
            not isinstance(asset_payload, dict)
            or type(asset_payload.get("schema_version")) is not int
            or asset_payload.get("schema_version") != 1
            or not isinstance(asset_payload.get("assets"), list)
            or "objects" in asset_payload
        ):
            raise ContentPackageError(
                "Unsupported split asset catalog schema; expected schema_version 1 and assets only."
            )

        if not isinstance(map_placements_relative, str) or not map_placements_relative.strip():
            raise ContentPackageError("Map placements path must be a non-empty relative path.")
        map_placements_path = (root / map_placements_relative).resolve()
        if not map_placements_path.is_relative_to(root):
            raise ContentPackageError("Map placements path resolves outside the package directory.")
        if not map_placements_path.is_dir():
            raise ContentPackageError(f"Map placements directory could not be loaded: {map_placements_path}")

    # Build a complete presentation snapshot before exposing the package.
    # Missing/corrupt PNGs remain non-fatal catalog diagnostics so the existing
    # deterministic renderer fallback can operate; malformed metadata and broken
    # placement references reject the package as a whole.
    presentation_catalog = None
    scene_placements = None
    if asset_catalog_path is not None or presentation_assets_path is not None:
        from game_ui.assets.asset_definition import AssetCatalog, AssetCatalogError
        from game_ui.assets.placement_catalog import (
            ScenePlacementCatalog,
            ScenePlacementCatalogError,
        )

        try:
            if asset_catalog_path is not None:
                presentation_catalog = AssetCatalog.load(asset_catalog_path)
                scene_placements = ScenePlacementCatalog.load_directory(
                    map_placements_path,
                    presentation_catalog,
                    valid_map_ids=set(hexes) if hexes else None,
                    map_definitions=hexes if hexes else None,
                )
            else:
                presentation_catalog = AssetCatalog.load(presentation_assets_path)
                if hexes:
                    known_map_ids = set(hexes)
                    unknown_maps = sorted({
                        item.map_id for item in presentation_catalog.objects
                        if item.map_id not in known_map_ids
                    })
                    if unknown_maps:
                        raise ValueError(
                            "Legacy placements reference unknown hex maps: "
                            + ", ".join(unknown_maps)
                        )
                    from core.domain.spatial import LocalHexPosition

                    for placement in presentation_catalog.objects:
                        map_definition = hexes[placement.map_id]
                        if not map_definition.has_cell(
                            LocalHexPosition(placement.q, placement.r)
                        ):
                            raise ValueError(
                                f"Legacy placement '{placement.object_id}' uses a cell "
                                f"outside map '{placement.map_id}': "
                                f"q={placement.q}, r={placement.r}"
                            )
        except (AssetCatalogError, ScenePlacementCatalogError, OSError, ValueError) as error:
            raise ContentPackageError(
                f"Invalid presentation content in package '{package_id}': {error}"
            ) from error

    gameplay_placements_path = None
    gameplay_placements = None
    gameplay_placements_relative = manifest.get("gameplay_placements")
    if gameplay_placements_relative is not None:
        if (
            not isinstance(gameplay_placements_relative, str)
            or not gameplay_placements_relative.strip()
        ):
            raise ContentPackageError(
                "Gameplay placements path must be a non-empty relative path."
            )
        gameplay_placements_path = (
            root / gameplay_placements_relative
        ).resolve()
        if not gameplay_placements_path.is_relative_to(root):
            raise ContentPackageError(
                "Gameplay placements path resolves outside the package directory."
            )
        if not gameplay_placements_path.is_dir():
            raise ContentPackageError(
                f"Gameplay placements directory could not be loaded: "
                f"{gameplay_placements_path}"
            )
        if not hexes:
            raise ContentPackageError(
                "Gameplay placements require a package with validated hex maps."
            )
        try:
            gameplay_placements = GameplayPlacementCatalog.load_directory(
                gameplay_placements_path,
                map_definitions=hexes,
            )
        except (GameplayPlacementCatalogError, OSError, ValueError) as error:
            raise ContentPackageError(
                f"Invalid gameplay placements in package '{package_id}': {error}"
            ) from error

        npc_records = files.get("npcs", {}).get("npcs", [])
        resource_records = files.get("resources", {}).get("nodes", [])
        if not isinstance(npc_records, list):
            raise ContentPackageError(
                "NPC definitions must contain an 'npcs' list when gameplay placements are declared."
            )
        if not isinstance(resource_records, list):
            raise ContentPackageError(
                "Resource definitions must contain a 'nodes' list when gameplay placements are declared."
            )
        npc_ids = {
            record.get("id")
            for record in npc_records
            if isinstance(record, dict)
        }
        resource_ids = {
            record.get("id")
            for record in resource_records
            if isinstance(record, dict)
        }
        npc_by_id = {
            record["id"]: record
            for record in npc_records
            if isinstance(record, dict) and isinstance(record.get("id"), str)
        }
        for placement in gameplay_placements.placements:
            if placement.kind == "npc" and placement.domain_id not in npc_ids:
                raise ContentPackageError(
                    f"Gameplay placement references unknown NPC: {placement.domain_id}"
                )
            if placement.kind == "npc":
                npc_record = npc_by_id[placement.domain_id]
                route = npc_record.get("patrol_route", [])
                if not isinstance(route, list):
                    raise ContentPackageError(
                        f"NPC '{placement.domain_id}' patrol_route must be a list."
                    )
                map_definition = hexes[placement.map_id]
                for waypoint in route:
                    if (
                        not isinstance(waypoint, list) or len(waypoint) != 2
                        or type(waypoint[0]) is not int
                        or type(waypoint[1]) is not int
                    ):
                        raise ContentPackageError(
                            f"NPC '{placement.domain_id}' patrol waypoints must be integer [q, r] pairs."
                        )
                    q, r = waypoint
                    if not map_definition.has_cell(LocalHexPosition(q, r)):
                        raise ContentPackageError(
                            f"NPC '{placement.domain_id}' patrol route references a cell "
                            f"outside map '{placement.map_id}': q={q}, r={r}"
                        )
            if (
                placement.kind == "resource_node"
                and placement.domain_id not in resource_ids
            ):
                raise ContentPackageError(
                    "Gameplay placement references unknown resource node: "
                    f"{placement.domain_id}"
                )
            if (
                placement.kind == "container"
                and placement.domain_id not in container_ids
            ):
                raise ContentPackageError(
                    "Gameplay placement references unknown container: "
                    f"{placement.domain_id}"
                )

    return ContentPackage(
        package_id,
        package_version,
        version,
        MappingProxyType(files),
        MappingProxyType(hexes),
        world_map,
        presentation_assets_path,
        asset_catalog_path,
        map_placements_path,
        presentation_catalog,
        scene_placements,
        gameplay_placements_path,
        gameplay_placements,
    )
