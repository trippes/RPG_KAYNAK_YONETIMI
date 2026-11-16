"""Sparse mutable cell overrides owned by one hex world."""

from dataclasses import dataclass, replace

from hex_world_lab.geometry import AxialCoord
from hex_world_lab.world.cell import HexCellData
from hex_world_lab.world.identity import CellAddress, MapId, WorldId
from hex_world_lab.world.map_definition import UnknownCellError
from hex_world_lab.world.map_registry import MapNotLoadedError, MapRegistry, UnknownMapError


@dataclass(frozen=True, slots=True)
class RuntimeCellOverride:
    """Immutable snapshot of fields that differ from a cell's base data."""

    terrain_id: str | None = None
    is_walkable: bool | None = None
    has_obstacle: bool | None = None

    @property
    def is_empty(self) -> bool:
        return (
            self.terrain_id is None
            and self.is_walkable is None
            and self.has_obstacle is None
        )


class HexWorldRuntime:
    """Store only changed cell fields for a single world.

    The map registry is consulted for every mutation, so writes are accepted
    only for registered, loaded maps and cells present in their definitions.
    Sparse overrides intentionally survive map unloads.
    """

    __slots__ = ("_world_id", "_map_registry", "_overrides")

    def __init__(self, world_id: WorldId, map_registry: MapRegistry) -> None:
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(map_registry, MapRegistry):
            raise TypeError("map_registry must be a MapRegistry")
        if map_registry.world_id != world_id:
            raise ValueError("map_registry belongs to a different world")
        self._world_id = world_id
        self._map_registry = map_registry
        self._overrides: dict[tuple[MapId, AxialCoord], RuntimeCellOverride] = {}

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def override_count(self) -> int:
        """Number of cells with at least one non-base field override."""
        return len(self._overrides)

    @property
    def field_override_count(self) -> int:
        """Number of stored changed fields across all overridden cells."""
        return sum(
            int(override.terrain_id is not None)
            + int(override.is_walkable is not None)
            + int(override.has_obstacle is not None)
            for override in self._overrides.values()
        )

    def set_cell_state(
        self,
        address: CellAddress,
        *,
        terrain_id: str | None = None,
        is_walkable: bool | None = None,
        has_obstacle: bool | None = None,
    ) -> None:
        """Set one or more fields; None means that field was not supplied."""
        if terrain_id is None and is_walkable is None and has_obstacle is None:
            raise ValueError("at least one cell state field must be supplied")
        base = self._require_loaded_cell(address)
        if terrain_id is not None:
            self._validate_terrain_id(terrain_id)
        if is_walkable is not None and not isinstance(is_walkable, bool):
            raise TypeError("is_walkable must be a boolean")
        if has_obstacle is not None and not isinstance(has_obstacle, bool):
            raise TypeError("has_obstacle must be a boolean")

        key = (address.map_id, address.coord)
        current = self._overrides.get(key, RuntimeCellOverride())
        updated = replace(
            current,
            terrain_id=current.terrain_id if terrain_id is None else terrain_id,
            is_walkable=current.is_walkable if is_walkable is None else is_walkable,
            has_obstacle=current.has_obstacle if has_obstacle is None else has_obstacle,
        )
        self._store_normalized(key, base, updated)

    def set_terrain(self, address: CellAddress, terrain_id: str) -> None:
        self.set_cell_state(address, terrain_id=terrain_id)

    def set_walkable(self, address: CellAddress, is_walkable: bool) -> None:
        self.set_cell_state(address, is_walkable=is_walkable)

    def set_obstacle(self, address: CellAddress, has_obstacle: bool) -> None:
        self.set_cell_state(address, has_obstacle=has_obstacle)

    def reset_terrain(self, address: CellAddress) -> None:
        self._reset_fields(address, terrain_id=None)

    def reset_walkability(self, address: CellAddress) -> None:
        self._reset_fields(address, is_walkable=None)

    def reset_obstacle(self, address: CellAddress) -> None:
        self._reset_fields(address, has_obstacle=None)

    def clear_cell(self, address: CellAddress) -> None:
        """Remove all overrides for a cell, restoring its base data."""
        base = self._require_loaded_cell(address)
        del base  # Validation is intentional; no base data is mutated.
        self._overrides.pop((address.map_id, address.coord), None)

    def has_override(self, address: CellAddress) -> bool:
        self._validate_address_world(address)
        return (address.map_id, address.coord) in self._overrides

    def get_override(self, address: CellAddress) -> RuntimeCellOverride | None:
        """Return an immutable override snapshot, including while unloaded."""
        self._validate_address_world(address)
        return self._overrides.get((address.map_id, address.coord))

    def clear_map(self, map_id: MapId) -> None:
        """Clear a map's sparse state; called when its registration is removed."""
        if not isinstance(map_id, MapId):
            raise TypeError("map_id must be a MapId")
        stale_keys = [key for key in self._overrides if key[0] == map_id]
        for key in stale_keys:
            del self._overrides[key]

    def _reset_fields(self, address: CellAddress, **fields: None) -> None:
        base = self._require_loaded_cell(address)
        key = (address.map_id, address.coord)
        current = self._overrides.get(key)
        if current is None:
            return
        updated = replace(current, **fields)
        self._store_normalized(key, base, updated)

    def _store_normalized(
        self,
        key: tuple[MapId, AxialCoord],
        base: HexCellData,
        candidate: RuntimeCellOverride,
    ) -> None:
        normalized = RuntimeCellOverride(
            terrain_id=(
                candidate.terrain_id
                if candidate.terrain_id is not None
                and candidate.terrain_id != base.terrain_id
                else None
            ),
            is_walkable=(
                candidate.is_walkable
                if candidate.is_walkable is not None
                and candidate.is_walkable != base.is_walkable
                else None
            ),
            has_obstacle=(
                candidate.has_obstacle
                if candidate.has_obstacle is not None
                and candidate.has_obstacle != base.has_obstacle
                else None
            ),
        )
        if normalized.is_empty:
            self._overrides.pop(key, None)
        else:
            self._overrides[key] = normalized

    def _require_loaded_cell(self, address: CellAddress) -> HexCellData:
        self._validate_address_world(address)
        registration = self._map_registry.get_registration(address.map_id)
        if registration is None:
            raise UnknownMapError(f"map '{address.map_id.value}' is not registered")
        definition = self._map_registry.get_map(address.map_id)
        if definition is None:
            raise MapNotLoadedError(f"map '{address.map_id.value}' is not loaded")
        try:
            return definition.require_cell_data(address.coord)
        except UnknownCellError:
            raise

    def _validate_address_world(self, address: CellAddress) -> None:
        if not isinstance(address, CellAddress):
            raise TypeError("address must be a CellAddress")
        if address.world_id != self._world_id:
            raise ValueError(
                f"address belongs to world '{address.world_id.value}', "
                f"not '{self._world_id.value}'"
            )

    @staticmethod
    def _validate_terrain_id(terrain_id: str) -> None:
        if not isinstance(terrain_id, str):
            raise TypeError("terrain_id must be a string")
        if not terrain_id.strip():
            raise ValueError("terrain_id must not be empty or whitespace-only")
