"""Validated, data-driven presentation asset metadata."""
from __future__ import annotations
import json
import math
from dataclasses import dataclass
from pathlib import Path

class AssetCatalogError(ValueError):
    """Invalid presentation asset metadata."""

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

    def __post_init__(self):
        if not isinstance(self.asset_id, str) or not self.asset_id.strip():
            raise AssetCatalogError("asset_id must be a non-empty string.")
        if not isinstance(self.path, str) or not self.path.strip():
            raise AssetCatalogError("asset path must be a non-empty string.")
        if any(type(v) is not int or v <= 0 for v in (self.width, self.height)):
            raise AssetCatalogError("asset dimensions must be positive integers.")
        if isinstance(self.scale, bool) or not isinstance(self.scale, (int, float)) or not math.isfinite(self.scale) or self.scale <= 0:
            raise AssetCatalogError("asset scale must be a finite positive number.")
        if len(self.anchor) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1 for v in self.anchor):
            raise AssetCatalogError("anchor must contain finite normalized coordinates.")
        if self.collision is not None and (len(self.collision) != 4 or any(not isinstance(v, (int, float)) or isinstance(v, bool) for v in self.collision) or self.collision[2] < 0 or self.collision[3] < 0):
            raise AssetCatalogError("collision must be an x/y/width/height tuple.")
        if not isinstance(self.depth_offset, (int, float)) or isinstance(self.depth_offset, bool) or not math.isfinite(self.depth_offset):
            raise AssetCatalogError("depth_offset must be finite and numeric.")
        terrain_types = tuple(self.terrain_types)
        if any(not isinstance(value, str) or not value.strip() for value in terrain_types):
            raise AssetCatalogError("terrain_types must contain non-empty strings.")
        if self.sheet is not None and not isinstance(self.sheet, dict):
            raise AssetCatalogError("spritesheet metadata must be an object.")
        if self.animations is not None and not isinstance(self.animations, dict):
            raise AssetCatalogError("animation metadata must be an object.")
        if self.placement not in {"ground", "canopy", "overlay", "underlay"}:
            raise AssetCatalogError("unsupported placement layer.")
        object.__setattr__(self, "terrain_types", terrain_types)

class AssetCatalog:
    """Load reusable visual metadata without importing Pygame."""
    SCHEMA_VERSION = 1
    def __init__(self, root, assets, objects=()):
        self.root = Path(root).resolve()
        self.assets = dict(assets)
        self.objects = tuple(objects)
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
            try:
                asset = AssetDefinition(
                    asset_id=record["asset_id"], path=record["path"],
                    width=record["width"], height=record["height"],
                    scale=record.get("scale", 1.0),
                    anchor=tuple(record.get("anchor", (0.5, 1.0))),
                    collision=tuple(record["collision"]) if record.get("collision") is not None else None,
                    depth_offset=record.get("depth_offset", 0.0),
                    terrain_types=tuple(record.get("terrain_types", ())),
                    placement=record.get("placement", "ground"),
                    interaction=record.get("interaction"),
                    sheet=record.get("sheet"), animations=record.get("animations"))
            except (KeyError, TypeError, ValueError) as error:
                raise AssetCatalogError(f"Invalid asset record at index {index}.") from error
            if asset.asset_id in assets:
                raise AssetCatalogError(f"Duplicate asset id: {asset.asset_id}")
            resolved = (source.parent / asset.path).resolve()
            if not resolved.is_relative_to(source.parent):
                raise AssetCatalogError(f"Asset path escapes catalog root: {asset.asset_id}")
            assets[asset.asset_id] = asset
        from game_ui.world_rendering.scene_object import SceneObjectPlacement
        objects = []
        seen_object_ids = set()
        for index, record in enumerate(object_records):
            if not isinstance(record, dict):
                raise AssetCatalogError(f"Object placement at index {index} must be an object.")
            try:
                placement = SceneObjectPlacement(
                    object_id=record["object_id"], asset_id=record["asset_id"],
                    map_id=record["map_id"], q=record["q"], r=record["r"],
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
                raise AssetCatalogError(f"Object placement references unknown asset: {placement.asset_id}")
            seen_object_ids.add(placement.object_id)
            objects.append(placement)
        return cls(source.parent, assets, objects)
    def get(self, asset_id):
        return self.assets.get(asset_id)
    def resolve_path(self, asset_id):
        asset = self.get(asset_id)
        if asset is None:
            return None
        path = (self.root / asset.path).resolve()
        if not path.is_relative_to(self.root):
            raise AssetCatalogError(f"Asset path escapes catalog root: {asset_id}")
        return path
    def available(self, asset_id):
        path = self.resolve_path(asset_id)
        return path is not None and path.is_file()
    def objects_for_map(self, map_id):
        return tuple(item for item in self.objects if item.map_id == map_id)
