"""Map-authored gameplay entity placements, separate from presentation objects."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from types import MappingProxyType
from typing import Mapping

from core.domain.spatial import EntityPosition, LocalHexPosition


class GameplayPlacementCatalogError(ValueError):
    """Invalid gameplay placement data or unresolved map reference."""


@dataclass(frozen=True, slots=True)
class GameplayPlacement:
    """One domain-owned entity's explicit axial placement and occupancy policy."""

    domain_id: str
    kind: str
    map_id: str
    q: int
    r: int
    blocks_movement: bool
    blocks_occupancy: bool

    def __post_init__(self) -> None:
        for field_name in ("domain_id", "kind", "map_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")
        if self.kind not in {"npc", "resource_node", "container"}:
            raise ValueError("kind must be npc, resource_node, or container.")
        if type(self.q) is not int or type(self.r) is not int:
            raise TypeError("Gameplay placement q/r coordinates must be integers.")
        if not isinstance(self.blocks_movement, bool):
            raise TypeError("blocks_movement must be a boolean.")
        if not isinstance(self.blocks_occupancy, bool):
            raise TypeError("blocks_occupancy must be a boolean.")
        if self.kind == "resource_node" and (
            self.blocks_movement or self.blocks_occupancy
        ):
            raise ValueError("Resource-node placements must be non-blocking.")

    @property
    def position(self) -> EntityPosition:
        return EntityPosition(self.map_id, LocalHexPosition(self.q, self.r))


@dataclass(frozen=True, slots=True, init=False)
class GameplayPlacementCatalog:
    """Immutable gameplay placement snapshot grouped by axial local map."""

    placements: tuple[GameplayPlacement, ...]
    _by_map: Mapping[str, tuple[GameplayPlacement, ...]] = field(
        repr=False, compare=False, hash=False
    )

    SCHEMA_VERSION = 1
    ALLOWED_ROOT_FIELDS = {"schema_version", "map_id", "placements"}
    ALLOWED_PLACEMENT_FIELDS = {
        "domain_id", "kind", "q", "r", "blocks_movement", "blocks_occupancy",
    }

    def __init__(self, placements=()):
        normalized = tuple(placements)
        if any(not isinstance(item, GameplayPlacement) for item in normalized):
            raise TypeError("placements must contain GameplayPlacement records.")
        domain_ids = [item.domain_id for item in normalized]
        if len(domain_ids) != len(set(domain_ids)):
            raise GameplayPlacementCatalogError(
                "Gameplay placement domain_id values must be unique."
            )
        by_map: dict[str, list[GameplayPlacement]] = {}
        for placement in normalized:
            by_map.setdefault(placement.map_id, []).append(placement)
        object.__setattr__(self, "placements", normalized)
        object.__setattr__(
            self,
            "_by_map",
            MappingProxyType({
                map_id: tuple(items) for map_id, items in by_map.items()
            }),
        )

    @classmethod
    def load_directory(
        cls,
        directory: str | Path,
        *,
        map_definitions: Mapping[str, object],
    ) -> GameplayPlacementCatalog:
        root = Path(directory).resolve()
        if not root.is_dir():
            raise GameplayPlacementCatalogError(
                f"Gameplay placement directory could not be loaded: {root}"
            )
        if not isinstance(map_definitions, Mapping) or not map_definitions:
            raise GameplayPlacementCatalogError(
                "Gameplay placements require at least one validated hex map."
            )

        placements: list[GameplayPlacement] = []
        seen_ids: set[str] = set()
        for source in sorted(root.glob("*.json")):
            if not source.resolve().is_relative_to(root):
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file escapes its directory: {source.name}"
                )
            try:
                payload = json.loads(source.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file could not be read: {source.name}"
                ) from error
            if not isinstance(payload, dict):
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file '{source.name}' must contain an object."
                )
            unknown_root = sorted(set(payload) - cls.ALLOWED_ROOT_FIELDS)
            if unknown_root:
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file '{source.name}' has unsupported fields: "
                    + ", ".join(unknown_root)
                )
            if (
                type(payload.get("schema_version")) is not int
                or payload["schema_version"] != cls.SCHEMA_VERSION
            ):
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file '{source.name}' has an unsupported schema_version."
                )
            map_id = payload.get("map_id")
            if not isinstance(map_id, str) or not map_id.strip():
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file '{source.name}' requires a non-empty map_id."
                )
            map_definition = map_definitions.get(map_id)
            if map_definition is None:
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file '{source.name}' references unknown map: {map_id}"
                )
            records = payload.get("placements")
            if not isinstance(records, list):
                raise GameplayPlacementCatalogError(
                    f"Gameplay placement file '{source.name}' placements must be a list."
                )

            for index, record in enumerate(records):
                label = f"{source.name} placements[{index}]"
                if not isinstance(record, dict):
                    raise GameplayPlacementCatalogError(f"{label} must be an object.")
                unknown = sorted(set(record) - cls.ALLOWED_PLACEMENT_FIELDS)
                missing = sorted(cls.ALLOWED_PLACEMENT_FIELDS - record.keys())
                if unknown or missing:
                    details = []
                    if missing:
                        details.append("missing fields: " + ", ".join(missing))
                    if unknown:
                        details.append("unsupported fields: " + ", ".join(unknown))
                    raise GameplayPlacementCatalogError(
                        f"{label} has " + "; ".join(details)
                    )
                try:
                    placement = GameplayPlacement(map_id=map_id, **record)
                except (TypeError, ValueError) as error:
                    raise GameplayPlacementCatalogError(
                        f"Invalid {label}: {error}"
                    ) from error
                if placement.domain_id in seen_ids:
                    raise GameplayPlacementCatalogError(
                        f"Duplicate gameplay placement domain_id: {placement.domain_id}"
                    )
                if not map_definition.has_cell(placement.position.cell):
                    raise GameplayPlacementCatalogError(
                        f"Gameplay placement '{placement.domain_id}' uses a cell outside "
                        f"map '{map_id}': q={placement.q}, r={placement.r}"
                    )
                seen_ids.add(placement.domain_id)
                placements.append(placement)

        return cls(placements)

    @property
    def map_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_map))

    def placements_for_map(self, map_id: str) -> tuple[GameplayPlacement, ...]:
        return self._by_map.get(map_id, ())


__all__ = [
    "GameplayPlacement",
    "GameplayPlacementCatalog",
    "GameplayPlacementCatalogError",
]
