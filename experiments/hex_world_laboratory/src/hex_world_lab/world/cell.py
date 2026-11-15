"""Immutable data stored for a single hex cell."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import TypeAlias


JSONScalar: TypeAlias = str | int | float | bool | None
FrozenJSONValue: TypeAlias = JSONScalar | tuple["FrozenJSONValue", ...] | Mapping[str, "FrozenJSONValue"]


def _freeze_json_value(value: object, active_containers: set[int]) -> FrozenJSONValue:
    """Copy a JSON-compatible value into a deeply immutable representation."""
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("metadata numbers must be finite")
        return value

    if isinstance(value, Mapping):
        container_id = id(value)
        if container_id in active_containers:
            raise ValueError("metadata must not contain circular references")
        active_containers.add(container_id)
        try:
            frozen_items: dict[str, FrozenJSONValue] = {}
            for key, item in value.items():
                if not isinstance(key, str):
                    raise TypeError("metadata mapping keys must be strings")
                frozen_items[key] = _freeze_json_value(item, active_containers)
            return MappingProxyType(frozen_items)
        finally:
            active_containers.remove(container_id)

    if isinstance(value, (list, tuple)):
        container_id = id(value)
        if container_id in active_containers:
            raise ValueError("metadata must not contain circular references")
        active_containers.add(container_id)
        try:
            return tuple(_freeze_json_value(item, active_containers) for item in value)
        finally:
            active_containers.remove(container_id)

    raise TypeError(
        "metadata values must be JSON-compatible: "
        "null, string, boolean, integer, finite float, mapping, list, or tuple"
    )


def _hashable_json_value(value: FrozenJSONValue) -> object:
    """Return a stable hash input for an already frozen metadata value."""
    if isinstance(value, Mapping):
        return ("mapping", tuple(sorted((key, _hashable_json_value(item)) for key, item in value.items())))
    if isinstance(value, tuple):
        return ("sequence", tuple(_hashable_json_value(item) for item in value))
    return (type(value).__name__, value)


@dataclass(frozen=True, slots=True, eq=True)
class HexCellData:
    """Immutable initial terrain and gameplay data for one hex cell.

    Metadata accepts JSON-compatible values. Mappings are defensively copied
    and exposed as read-only mappings; lists and tuples become tuples.
    """

    terrain_id: str
    is_walkable: bool
    has_obstacle: bool
    metadata: Mapping[str, FrozenJSONValue] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.terrain_id, str):
            raise TypeError("terrain_id must be a string")
        if not self.terrain_id.strip():
            raise ValueError("terrain_id must not be empty or whitespace-only")
        if not isinstance(self.is_walkable, bool):
            raise TypeError("is_walkable must be a boolean")
        if not isinstance(self.has_obstacle, bool):
            raise TypeError("has_obstacle must be a boolean")

        if self.metadata is not None:
            if not isinstance(self.metadata, Mapping):
                raise TypeError("metadata must be a mapping or None")
            frozen_metadata = _freeze_json_value(self.metadata, set())
            object.__setattr__(self, "metadata", frozen_metadata)

    def __hash__(self) -> int:
        """Hash all fields, including nested metadata mappings."""
        metadata_hash = (
            None
            if self.metadata is None
            else _hashable_json_value(self.metadata)
        )
        return hash(
            (
                self.terrain_id,
                self.is_walkable,
                self.has_obstacle,
                metadata_hash,
            )
        )
