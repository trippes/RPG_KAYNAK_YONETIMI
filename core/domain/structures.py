"""Immutable domain contracts for modular structure content definitions.

These objects describe catalog definitions only. They do not represent placed
world structures and do not own coordinates, physics, entity identity or
runtime lifecycle.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from types import MappingProxyType
from typing import Mapping

from core.domain.spatial import WorldPoint


STRUCTURE_DEFINITION_SCHEMA_VERSION = 1
STRUCTURE_PART_DEFINITION_SCHEMA_VERSION = 1


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string.")
    return value


def _require_positive_finite(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{field_name} must be a real number.")
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{field_name} must be finite and greater than zero.")
    return float(value)


def _normalize_unique_texts(values: object, field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{field_name} must be an iterable of strings, not a string.")
    try:
        normalized = tuple(values)
    except TypeError as error:
        raise TypeError(f"{field_name} must be an iterable of strings.") from error
    for value in normalized:
        _require_text(value, field_name)
    if len(set(normalized)) != len(normalized):
        raise ValueError(f"{field_name} cannot contain duplicates.")
    return tuple(sorted(normalized))


@dataclass(frozen=True, slots=True)
class StructureGeometryDefinition:
    """Catalog geometry envelope; dimensions use canonical world units.

    The geometry kind is descriptive metadata. Concrete construction-space
    placement, local anchors and collider projection are defined in later
    roadmap stages and are deliberately not encoded here.
    """

    shape_kind: str
    width: float
    depth: float
    height: float
    footprint_local_points: tuple[WorldPoint, ...] = ()

    def __post_init__(self) -> None:
        _require_text(self.shape_kind, "shape_kind")
        for name in ("width", "depth", "height"):
            object.__setattr__(
                self, name, _require_positive_finite(getattr(self, name), name)
            )
        points = tuple(self.footprint_local_points)
        if any(not isinstance(point, WorldPoint) for point in points):
            raise TypeError("footprint_local_points must contain WorldPoint values.")
        if len(set(points)) != len(points):
            raise ValueError("footprint_local_points cannot contain duplicates.")
        object.__setattr__(self, "footprint_local_points", points)


@dataclass(frozen=True, slots=True)
class StructureConnectionPort:
    """Semantic connection port; no world/local coordinate is assigned yet."""

    port_id: str
    connection_kind: str
    compatibility_key: str
    max_connections: int = 1
    required: bool = False

    def __post_init__(self) -> None:
        _require_text(self.port_id, "port_id")
        _require_text(self.connection_kind, "connection_kind")
        _require_text(self.compatibility_key, "compatibility_key")
        if type(self.max_connections) is not int or self.max_connections < 1:
            raise ValueError("max_connections must be a positive integer.")
        if not isinstance(self.required, bool):
            raise TypeError("required must be boolean.")

    def is_compatible_with(self, other: StructureConnectionPort) -> bool:
        if not isinstance(other, StructureConnectionPort):
            raise TypeError("other must be a StructureConnectionPort.")
        return (
            self.connection_kind == other.connection_kind
            and self.compatibility_key == other.compatibility_key
        )


@dataclass(frozen=True, slots=True)
class StructurePartDefinition:
    """Immutable catalog definition for one reusable construction component."""

    part_definition_id: str
    category: str
    geometry: StructureGeometryDefinition
    connection_ports: tuple[StructureConnectionPort, ...] = ()
    orientation_policy: str = "quarter_turn"
    vertical_policy: str = "ground"
    material_profile_id: str | None = None
    durability: float = 100.0
    placement_rule_ids: tuple[str, ...] = ()
    visual_asset_id: str | None = None
    schema_version: int = STRUCTURE_PART_DEFINITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text(self.part_definition_id, "part_definition_id")
        _require_text(self.category, "category")
        if not isinstance(self.geometry, StructureGeometryDefinition):
            raise TypeError("geometry must be a StructureGeometryDefinition.")
        if type(self.schema_version) is not int or self.schema_version != STRUCTURE_PART_DEFINITION_SCHEMA_VERSION:
            raise ValueError("Unsupported structure part definition schema version.")
        if self.orientation_policy not in {"fixed", "quarter_turn", "free"}:
            raise ValueError("orientation_policy must be fixed, quarter_turn or free.")
        if self.vertical_policy not in {"ground", "stackable", "elevated"}:
            raise ValueError("vertical_policy must be ground, stackable or elevated.")
        if self.material_profile_id is not None:
            _require_text(self.material_profile_id, "material_profile_id")
        if self.visual_asset_id is not None:
            _require_text(self.visual_asset_id, "visual_asset_id")
        object.__setattr__(
            self, "durability", _require_positive_finite(self.durability, "durability")
        )
        ports = tuple(self.connection_ports)
        if any(not isinstance(port, StructureConnectionPort) for port in ports):
            raise TypeError("connection_ports must contain StructureConnectionPort values.")
        port_ids = tuple(port.port_id for port in ports)
        if len(set(port_ids)) != len(port_ids):
            raise ValueError("connection port IDs must be unique within a part definition.")
        object.__setattr__(self, "connection_ports", tuple(sorted(ports, key=lambda p: p.port_id)))
        object.__setattr__(
            self, "placement_rule_ids",
            _normalize_unique_texts(self.placement_rule_ids, "placement_rule_ids"),
        )


@dataclass(frozen=True, slots=True)
class StructureDefinition:
    """Immutable catalog/archetype definition, not a placed structure instance."""

    structure_definition_id: str
    name: str
    allowed_part_definition_ids: tuple[str, ...]
    category: str = "general"
    tags: tuple[str, ...] = ()
    schema_version: int = STRUCTURE_DEFINITION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_text(self.structure_definition_id, "structure_definition_id")
        _require_text(self.name, "name")
        _require_text(self.category, "category")
        if type(self.schema_version) is not int or self.schema_version != STRUCTURE_DEFINITION_SCHEMA_VERSION:
            raise ValueError("Unsupported structure definition schema version.")
        part_ids = _normalize_unique_texts(
            self.allowed_part_definition_ids, "allowed_part_definition_ids"
        )
        if not part_ids:
            raise ValueError("A structure definition must allow at least one part definition.")
        object.__setattr__(self, "allowed_part_definition_ids", part_ids)
        object.__setattr__(self, "tags", _normalize_unique_texts(self.tags, "tags"))


class StructureDefinitionCatalog:
    """Validated, immutable lookup of structure and part catalog definitions."""

    def __init__(
        self,
        structures: tuple[StructureDefinition, ...] = (),
        parts: tuple[StructurePartDefinition, ...] = (),
    ) -> None:
        structure_map: dict[str, StructureDefinition] = {}
        part_map: dict[str, StructurePartDefinition] = {}
        for part in parts:
            if not isinstance(part, StructurePartDefinition):
                raise TypeError("parts must contain StructurePartDefinition values.")
            if part.part_definition_id in part_map:
                raise ValueError(f"Duplicate structure part definition ID: {part.part_definition_id}")
            part_map[part.part_definition_id] = part
        for structure in structures:
            if not isinstance(structure, StructureDefinition):
                raise TypeError("structures must contain StructureDefinition values.")
            if structure.structure_definition_id in structure_map:
                raise ValueError(f"Duplicate structure definition ID: {structure.structure_definition_id}")
            missing = sorted(set(structure.allowed_part_definition_ids) - part_map.keys())
            if missing:
                raise ValueError(
                    f"Structure definition '{structure.structure_definition_id}' "
                    f"references unknown part definitions: {missing}"
                )
            structure_map[structure.structure_definition_id] = structure
        self._structures: Mapping[str, StructureDefinition] = MappingProxyType(structure_map)
        self._parts: Mapping[str, StructurePartDefinition] = MappingProxyType(part_map)

    def structure(self, structure_definition_id: str) -> StructureDefinition | None:
        _require_text(structure_definition_id, "structure_definition_id")
        return self._structures.get(structure_definition_id)

    def part(self, part_definition_id: str) -> StructurePartDefinition | None:
        _require_text(part_definition_id, "part_definition_id")
        return self._parts.get(part_definition_id)

    def structures(self) -> tuple[StructureDefinition, ...]:
        return tuple(self._structures[key] for key in sorted(self._structures))

    def parts(self) -> tuple[StructurePartDefinition, ...]:
        return tuple(self._parts[key] for key in sorted(self._parts))


__all__ = [
    "STRUCTURE_DEFINITION_SCHEMA_VERSION",
    "STRUCTURE_PART_DEFINITION_SCHEMA_VERSION",
    "StructureGeometryDefinition",
    "StructureConnectionPort",
    "StructurePartDefinition",
    "StructureDefinition",
    "StructureDefinitionCatalog",
]
