"""Map-scoped presentation placements, stored separately from reusable assets."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from game_ui.world_rendering.scene_object import SceneObjectPlacement


class ScenePlacementCatalogError(ValueError):
    """Invalid map placement data or unresolved asset reference."""


@dataclass(frozen=True, slots=True, init=False)
class ScenePlacementCatalog:
    """Immutable, UI-independent collection of map-authored scene placements."""

    placements: tuple[SceneObjectPlacement, ...]
    _by_map: Mapping[str, tuple[SceneObjectPlacement, ...]] = field(
        repr=False, compare=False, hash=False
    )

    SCHEMA_VERSION = 1
    ALLOWED_ROOT_FIELDS = {"schema_version", "map_id", "objects"}
    ALLOWED_OBJECT_FIELDS = {
        "object_id", "asset_id", "q", "r", "offset_x", "offset_y",
        "footprint", "collision_box", "depth_offset", "layer", "kind",
    }

    def __init__(self, placements=()):
        normalized = tuple(placements)
        by_map = {}
        for placement in normalized:
            by_map.setdefault(placement.map_id, []).append(placement)
        object.__setattr__(self, "placements", normalized)
        object.__setattr__(self, "_by_map", MappingProxyType({
            map_id: tuple(items) for map_id, items in by_map.items()
        }))

    @classmethod
    def load_directory(cls, directory, asset_catalog):
        """Load one JSON document per map and resolve every asset_id reference."""
        root = Path(directory).resolve()
        if not root.is_dir():
            raise ScenePlacementCatalogError(
                f"Placement directory could not be loaded: {root}"
            )

        placements = []
        seen_ids = set()
        for source in sorted(root.glob("*.json")):
            if not source.resolve().is_relative_to(root):
                raise ScenePlacementCatalogError(
                    f"Placement file escapes content directory: {source.name}"
                )
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as error:
                raise ScenePlacementCatalogError(
                    f"Placement file could not be read: {source.name}"
                ) from error
            if not isinstance(payload, dict):
                raise ScenePlacementCatalogError(
                    f"Placement file '{source.name}' must contain an object."
                )
            unknown = sorted(set(payload) - cls.ALLOWED_ROOT_FIELDS)
            if unknown:
                raise ScenePlacementCatalogError(
                    f"Placement file '{source.name}' has unsupported fields: {', '.join(unknown)}"
                )
            if type(payload.get("schema_version")) is not int or payload["schema_version"] != cls.SCHEMA_VERSION:
                raise ScenePlacementCatalogError(
                    f"Placement file '{source.name}' has an unsupported schema_version."
                )
            map_id = payload.get("map_id")
            if not isinstance(map_id, str) or not map_id.strip():
                raise ScenePlacementCatalogError(
                    f"Placement file '{source.name}' requires a non-empty map_id."
                )
            records = payload.get("objects")
            if not isinstance(records, list):
                raise ScenePlacementCatalogError(
                    f"Placement file '{source.name}' objects must be a list."
                )

            for index, record in enumerate(records):
                label = f"{source.name} objects[{index}]"
                if not isinstance(record, dict):
                    raise ScenePlacementCatalogError(f"{label} must be an object.")
                unknown = sorted(set(record) - cls.ALLOWED_OBJECT_FIELDS)
                if unknown:
                    raise ScenePlacementCatalogError(
                        f"{label} has unsupported fields: {', '.join(unknown)}"
                    )
                try:
                    placement = SceneObjectPlacement(
                        object_id=record["object_id"],
                        asset_id=record["asset_id"],
                        map_id=map_id,
                        q=record["q"],
                        r=record["r"],
                        offset_x=record.get("offset_x", 0.0),
                        offset_y=record.get("offset_y", 0.0),
                        footprint=tuple(record.get("footprint", (1, 1))),
                        collision_box=(
                            tuple(record["collision_box"])
                            if record.get("collision_box") is not None else None
                        ),
                        depth_offset=record.get("depth_offset", 0.0),
                        layer=record.get("layer", "ground"),
                        kind=record.get("kind", "prop"),
                    )
                except (KeyError, TypeError, ValueError) as error:
                    raise ScenePlacementCatalogError(
                        f"Invalid {label}: {error}"
                    ) from error
                if placement.object_id in seen_ids:
                    raise ScenePlacementCatalogError(
                        f"Duplicate scene object id: {placement.object_id}"
                    )
                if asset_catalog.get(placement.asset_id) is None:
                    raise ScenePlacementCatalogError(
                        f"Placement '{placement.object_id}' references unknown asset: "
                        f"{placement.asset_id}"
                    )
                seen_ids.add(placement.object_id)
                placements.append(placement)

        return cls(placements)

    @property
    def map_ids(self):
        return tuple(sorted(self._by_map))

    def objects_for_map(self, map_id):
        return self._by_map.get(map_id, ())
