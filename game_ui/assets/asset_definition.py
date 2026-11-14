"""Validated, data-driven presentation asset metadata.

The catalog deliberately has no Pygame dependency. PNG files are inspected with
the standard library; the presentation layer remains responsible for decoding
surfaces and retaining its existing deterministic fallback behavior.
"""
from __future__ import annotations

import json
import math
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType


MIN_DRAW_SCALE = 0.01
MAX_DRAW_SCALE = 8.0


class AssetCatalogError(ValueError):
    """Invalid presentation asset metadata or unsafe asset reference."""


@dataclass(frozen=True, slots=True)
class AssetValidationIssue:
    """A non-fatal source-file problem that presentation code can report."""

    asset_id: str
    code: str
    message: str


@dataclass(frozen=True, slots=True)
class AssetDefinition:
    asset_id: str
    path: str
    width: int
    height: int
    scale: float = 1.0
    anchor: tuple[float, float] = (0.5, 1.0)
    collision: tuple[float, float, float, float] | None = None
    depth_offset: float = 0.0
    terrain_types: tuple[str, ...] = ()
    placement: str = "ground"
    interaction: str | None = None
    sheet: dict | None = None
    animations: dict | None = None
    category: str | None = None

    def __post_init__(self):
        if (
            not isinstance(self.asset_id, str)
            or not self.asset_id
            or self.asset_id != self.asset_id.strip()
            or any(ord(char) < 32 for char in self.asset_id)
            or "/" in self.asset_id
            or "\\" in self.asset_id
        ):
            raise AssetCatalogError("asset_id must be a stable, non-empty identifier.")
        if not isinstance(self.path, str) or not self.path.strip():
            raise AssetCatalogError("asset path must be a non-empty string.")
        if any(type(v) is not int or v < 0 for v in (self.width, self.height)) or (
            (self.width == 0) != (self.height == 0)
        ):
            raise AssetCatalogError(
                "asset dimensions must be positive integers, or both zero for source-image dimensions."
            )
        if (
            isinstance(self.scale, bool)
            or not isinstance(self.scale, (int, float))
            or not math.isfinite(self.scale)
            or not MIN_DRAW_SCALE <= self.scale <= MAX_DRAW_SCALE
        ):
            raise AssetCatalogError(
                f"asset scale must be finite and between {MIN_DRAW_SCALE} and {MAX_DRAW_SCALE}."
            )
        if (
            len(self.anchor) != 2
            or any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                or not 0 <= v <= 1
                for v in self.anchor
            )
        ):
            raise AssetCatalogError("anchor must contain finite normalized coordinates.")
        if self.collision is not None and (
            len(self.collision) != 4
            or any(
                isinstance(v, bool)
                or not isinstance(v, (int, float))
                or not math.isfinite(v)
                for v in self.collision
            )
            or self.collision[2] <= 0
            or self.collision[3] <= 0
        ):
            raise AssetCatalogError(
                "collision must be a finite local-pixel x/y/width/height box with positive area."
            )
        if (
            not isinstance(self.depth_offset, (int, float))
            or isinstance(self.depth_offset, bool)
            or not math.isfinite(self.depth_offset)
        ):
            raise AssetCatalogError("depth_offset must be finite and numeric.")
        if isinstance(self.terrain_types, str):
            raise AssetCatalogError("terrain_types must be a list of strings.")
        terrain_types = tuple(self.terrain_types)
        if any(not isinstance(value, str) or not value.strip() for value in terrain_types):
            raise AssetCatalogError("terrain_types must contain non-empty strings.")
        if self.sheet is not None and not isinstance(self.sheet, dict):
            raise AssetCatalogError("spritesheet metadata must be an object.")
        if self.animations is not None and not isinstance(self.animations, dict):
            raise AssetCatalogError("animation metadata must be an object.")
        if self.category is not None and (
            not isinstance(self.category, str) or not self.category.strip()
        ):
            raise AssetCatalogError("asset category must be a non-empty string when provided.")
        if self.placement not in {"ground", "canopy", "overlay", "underlay"}:
            raise AssetCatalogError("unsupported placement layer.")
        object.__setattr__(self, "anchor", tuple(float(value) for value in self.anchor))
        if self.collision is not None:
            object.__setattr__(self, "collision", tuple(float(value) for value in self.collision))
        object.__setattr__(self, "scale", float(self.scale))
        object.__setattr__(self, "depth_offset", float(self.depth_offset))
        object.__setattr__(self, "terrain_types", terrain_types)


class AssetCatalog:
    """Load reusable visual metadata without importing Pygame."""

    SCHEMA_VERSION = 1
    PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

    def __init__(self, root, assets, objects=()):
        self.root = Path(root).resolve()
        self.assets = MappingProxyType(dict(assets))
        self.objects = tuple(objects)
        self._source_sizes = {}
        self._validation_issues = self._inspect_asset_files()

    @classmethod
    def _resolve_safe_path(cls, root: Path, relative_path: str, asset_id: str) -> Path:
        windows_path = PureWindowsPath(relative_path)
        posix_path = PurePosixPath(relative_path)
        if (
            windows_path.is_absolute()
            or windows_path.drive
            or posix_path.is_absolute()
            or "\\" in relative_path
            or ".." in posix_path.parts
        ):
            raise AssetCatalogError(f"Asset path must stay inside catalog root: {asset_id}")
        resolved = (root / Path(*posix_path.parts)).resolve()
        if not resolved.is_relative_to(root):
            raise AssetCatalogError(f"Asset path escapes catalog root: {asset_id}")
        return resolved

    @classmethod
    def _read_png_size(cls, path: Path) -> tuple[int, int]:
        """Validate PNG container chunks/CRCs and its compressed image stream."""
        try:
            with path.open("rb") as stream:
                if stream.read(8) != cls.PNG_SIGNATURE:
                    raise ValueError("file does not have a PNG signature")
                width = height = None
                saw_idat = False
                saw_iend = False
                compressed_data = bytearray()
                first_chunk = True
                while True:
                    raw_length = stream.read(4)
                    if len(raw_length) != 4:
                        raise ValueError("PNG ended before IEND")
                    length = struct.unpack(">I", raw_length)[0]
                    chunk_type = stream.read(4)
                    if len(chunk_type) != 4:
                        raise ValueError("truncated PNG chunk header")
                    data = stream.read(length)
                    raw_crc = stream.read(4)
                    if len(data) != length or len(raw_crc) != 4:
                        raise ValueError("truncated PNG chunk")
                    expected_crc = struct.unpack(">I", raw_crc)[0]
                    actual_crc = zlib.crc32(chunk_type + data) & 0xFFFFFFFF
                    if actual_crc != expected_crc:
                        raise ValueError("PNG chunk checksum mismatch")
                    if first_chunk:
                        if chunk_type != b"IHDR" or length != 13:
                            raise ValueError("PNG must begin with a 13-byte IHDR chunk")
                        width, height = struct.unpack(">II", data[:8])
                        if width <= 0 or height <= 0:
                            raise ValueError("PNG dimensions must be positive")
                        first_chunk = False
                    elif chunk_type == b"IHDR":
                        raise ValueError("PNG contains more than one IHDR chunk")
                    if chunk_type == b"IDAT":
                        saw_idat = True
                        compressed_data.extend(data)
                    elif chunk_type == b"IEND":
                        if length != 0 or not saw_idat:
                            raise ValueError("PNG has an invalid IEND or no image data")
                        saw_iend = True
                        break
                if not saw_iend or not compressed_data:
                    raise ValueError("PNG image data is incomplete")
                if stream.read(1):
                    raise ValueError("unexpected data after PNG IEND")
                try:
                    decoded = zlib.decompress(compressed_data)
                except zlib.error as error:
                    raise ValueError("PNG image data cannot be decompressed") from error
                if not decoded:
                    raise ValueError("PNG image data is empty")
                return width, height
        except OSError as error:
            raise ValueError("PNG file cannot be read") from error

    def _inspect_asset_files(self) -> tuple[AssetValidationIssue, ...]:
        issues = []
        for asset_id, asset in self.assets.items():
            path = self._resolve_safe_path(self.root, asset.path, asset_id)
            if not path.is_file():
                issues.append(
                    AssetValidationIssue(asset_id, "missing_file", f"PNG file is missing: {asset.path}")
                )
                continue
            try:
                source_size = self._read_png_size(path)
            except ValueError as error:
                issues.append(
                    AssetValidationIssue(asset_id, "invalid_png", f"PNG is invalid: {error}")
                )
                continue
            self._source_sizes[asset_id] = source_size
            if asset.width and (asset.width, asset.height) != source_size:
                issues.append(
                    AssetValidationIssue(
                        asset_id,
                        "dimension_mismatch",
                        f"Metadata size {asset.width}x{asset.height} does not match PNG size "
                        f"{source_size[0]}x{source_size[1]}.",
                    )
                )
        return tuple(issues)

    @classmethod
    def load(cls, source):
        source = Path(source).resolve()
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise AssetCatalogError("Presentation asset catalog could not be read.") from error
        if not isinstance(payload, dict) or payload.get("schema_version") != cls.SCHEMA_VERSION:
            raise AssetCatalogError("Unsupported presentation asset catalog schema.")
        records = payload.get("assets")
        object_records = payload.get("objects", [])
        if not isinstance(records, list) or not isinstance(object_records, list):
            raise AssetCatalogError("Catalog assets and objects must be lists.")
        assets = {}
        for index, record in enumerate(records):
            if not isinstance(record, dict):
                raise AssetCatalogError(f"Asset at index {index} must be an object.")
            terrain_values = record.get("terrain_types", ())
            if isinstance(terrain_values, str) or not isinstance(terrain_values, (list, tuple)):
                raise AssetCatalogError("terrain_types must be a list of strings.")
            try:
                asset = AssetDefinition(
                    asset_id=record["asset_id"],
                    path=record["path"],
                    width=record["width"],
                    height=record["height"],
                    scale=record.get("scale", 1.0),
                    anchor=tuple(record.get("anchor", (0.5, 1.0))),
                    collision=tuple(record["collision"]) if record.get("collision") is not None else None,
                    depth_offset=record.get("depth_offset", 0.0),
                    terrain_types=tuple(terrain_values),
                    placement=record.get("placement", "ground"),
                    interaction=record.get("interaction"),
                    sheet=record.get("sheet"),
                    animations=record.get("animations"),
                    category=record.get("category"),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise AssetCatalogError(f"Invalid asset record at index {index}.") from error
            if asset.asset_id in assets:
                raise AssetCatalogError(f"Duplicate asset id: {asset.asset_id}")
            cls._resolve_safe_path(source.parent, asset.path, asset.asset_id)
            assets[asset.asset_id] = asset

        # Legacy schema-v1 presentation_assets.json may still embed placements.
        # The split asset_catalog.json format intentionally contains assets only.
        objects = []
        if object_records:
            from game_ui.world_rendering.scene_object import SceneObjectPlacement

        seen_object_ids = set()
        for index, record in enumerate(object_records):
            if not isinstance(record, dict):
                raise AssetCatalogError(f"Object placement at index {index} must be an object.")
            try:
                placement = SceneObjectPlacement(
                    object_id=record["object_id"],
                    asset_id=record["asset_id"],
                    map_id=record["map_id"],
                    q=record["q"],
                    r=record["r"],
                    offset_x=record.get("offset_x", 0.0),
                    offset_y=record.get("offset_y", 0.0),
                    footprint=tuple(record.get("footprint", (1, 1))),
                    collision_box=tuple(record["collision_box"]) if record.get("collision_box") is not None else None,
                    depth_offset=record.get("depth_offset", 0.0),
                    layer=record.get("layer", "ground"),
                    kind=record.get("kind", "prop"),
                )
            except (KeyError, TypeError, ValueError) as error:
                raise AssetCatalogError(f"Invalid object placement at index {index}.") from error
            if placement.object_id in seen_object_ids:
                raise AssetCatalogError(f"Duplicate scene object id: {placement.object_id}")
            if placement.asset_id not in assets:
                raise AssetCatalogError(
                    f"Object placement references unknown asset: {placement.asset_id}"
                )
            seen_object_ids.add(placement.object_id)
            objects.append(placement)
        return cls(source.parent, assets, objects)

    @property
    def asset_ids(self) -> tuple[str, ...]:
        return tuple(self.assets)

    @property
    def categories(self) -> tuple[str, ...]:
        return tuple(sorted({asset.category for asset in self.assets.values() if asset.category}))

    def get(self, asset_id):
        """Return an asset or None; retained for existing runtime callers."""
        return self.assets.get(asset_id)

    def require(self, asset_id: str) -> AssetDefinition:
        """Return an asset or raise a clear catalog error for an unknown ID."""
        asset = self.get(asset_id)
        if asset is None:
            raise AssetCatalogError(f"Unknown asset id: {asset_id}")
        return asset

    def list_assets(self, category: str | None = None) -> tuple[AssetDefinition, ...]:
        """Return immutable asset definitions, optionally filtered by category."""
        assets = self.assets.values()
        if category is not None:
            assets = (asset for asset in assets if asset.category == category)
        return tuple(assets)

    def resolve_path(self, asset_id):
        asset = self.get(asset_id)
        if asset is None:
            return None
        return self._resolve_safe_path(self.root, asset.path, asset_id)

    def source_size(self, asset_id: str) -> tuple[int, int] | None:
        """Return validated source PNG dimensions without reopening the file."""
        self.require(asset_id)
        return self._source_sizes.get(asset_id)

    def validate_assets(self) -> tuple[AssetValidationIssue, ...]:
        """Return cached file validation findings; no image is loaded per query."""
        return self._validation_issues

    def available(self, asset_id):
        """Return whether the referenced file exists (legacy runtime semantics)."""
        path = self.resolve_path(asset_id)
        return path is not None and path.is_file()

    def is_valid(self, asset_id: str) -> bool:
        """Return whether the source PNG passed the cached catalog checks."""
        self.require(asset_id)
        return not any(issue.asset_id == asset_id for issue in self._validation_issues)

    def objects_for_map(self, map_id):
        return tuple(item for item in self.objects if item.map_id == map_id)
