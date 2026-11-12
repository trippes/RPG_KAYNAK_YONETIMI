"""Load versioned, data-only content packages with parallel map models."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

CONTENT_PACKAGE_SCHEMA_VERSION=1

class ContentPackageError(ValueError):
    """Malformed or unsafe content package."""

@dataclass(frozen=True)
class ContentPackage:
    package_id: str
    package_version: str
    schema_version: int
    files: Mapping[str,dict]
    map_definitions: Mapping[str,object]
    hex_map_definitions: Mapping[str,object]

def load_content_package(package_dir: str | Path) -> ContentPackage:
    root=Path(package_dir).resolve(); manifest_path=root/"manifest.json"
    try: manifest=json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError,json.JSONDecodeError) as e: raise ContentPackageError(f"Content package manifest could not be loaded: {manifest_path}") from e
    if not isinstance(manifest,dict): raise ContentPackageError("Content package manifest must be a JSON object.")
    allowed={"schema_version","package_id","package_version","files","maps"}
    extra=sorted(set(manifest)-allowed)
    if extra: raise ContentPackageError("Content package manifest has unsupported fields: "+", ".join(extra))
    version=manifest.get("schema_version")
    if type(version) is not int or version!=CONTENT_PACKAGE_SCHEMA_VERSION: raise ContentPackageError("Unsupported content package schema version.")
    package_id=manifest.get("package_id"); package_version=manifest.get("package_version")
    if not isinstance(package_id,str) or not package_id.strip(): raise ContentPackageError("Content package id must be a non-empty string.")
    if not isinstance(package_version,str) or not package_version.strip(): raise ContentPackageError("Content package version must be a non-empty string.")
    file_map=manifest.get("files")
    if not isinstance(file_map,dict) or not file_map: raise ContentPackageError("Content package must declare at least one data file.")
    files={}; resolved=set()
    for key,relative in file_map.items():
        if not isinstance(key,str) or not key.strip(): raise ContentPackageError("Content package file keys must be non-empty strings.")
        if not isinstance(relative,str) or not relative.strip(): raise ContentPackageError(f"Content file path for '{key}' is invalid.")
        source=(root/relative).resolve()
        if not source.is_relative_to(root): raise ContentPackageError(f"Content file '{key}' resolves outside the package directory.")
        if source in resolved: raise ContentPackageError(f"Content file is referenced more than once: {key}")
        resolved.add(source)
        try: value=json.loads(source.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as e: raise ContentPackageError(f"Content data file '{key}' could not be loaded: {source}") from e
        if not isinstance(value,dict): raise ContentPackageError(f"Content data file '{key}' must contain a JSON object.")
        files[key]=value
    square={}; hexes={}
    maps_dir=manifest.get("maps")
    if maps_dir is not None:
        if not isinstance(maps_dir,str) or not maps_dir.strip(): raise ContentPackageError("Content package maps directory must be a non-empty relative path.")
        maps_root=(root/maps_dir).resolve()
        if not maps_root.is_relative_to(root): raise ContentPackageError("Content package maps directory resolves outside the package directory.")
        if not maps_root.is_dir(): raise ContentPackageError(f"Content package maps directory could not be loaded: {maps_root}")
        try:
            from world.map_catalog import load_map_catalog
            square,hexes=load_map_catalog(maps_root)
        except (OSError,ValueError) as e: raise ContentPackageError(f"Content package maps could not be loaded from '{maps_root}': {e}") from e
    return ContentPackage(package_id,package_version,version,MappingProxyType(files),MappingProxyType(square),MappingProxyType(hexes))
