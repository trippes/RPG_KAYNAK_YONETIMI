"""Lightweight map catalog separated from loaded map definitions."""

from dataclasses import dataclass

from hex_world_lab.world.identity import MapId, WorldId
from hex_world_lab.world.map_definition import HexMapDefinition


@dataclass(frozen=True, slots=True)
class MapRegistration:
    """Small catalog entry; deliberately contains no cell data."""

    map_id: MapId
    name: str

    def __post_init__(self) -> None:
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.name, str):
            raise TypeError("name must be a string")
        if not self.name.strip():
            raise ValueError("name must not be empty or whitespace-only")


class MapRegistryError(Exception):
    """Base class for map registry errors."""


class DuplicateMapError(MapRegistryError):
    """Raised when a map ID is already registered or loaded."""


class UnknownMapError(MapRegistryError, LookupError):
    """Raised when an operation requires an unknown map ID."""


class MapNotLoadedError(MapRegistryError, LookupError):
    """Raised when an unload operation targets a registered but unloaded map."""


class MapAlreadyLoadedError(MapRegistryError):
    """Raised when a map is loaded more than once."""


class MapWorldMismatchError(MapRegistryError, ValueError):
    """Raised when a map definition belongs to another world."""


class MapNameMismatchError(MapRegistryError, ValueError):
    """Raised when loaded map name differs from its catalog entry."""


class MapRegistry:
    """Manage lightweight registrations and separately held loaded maps."""

    __slots__ = ("_world_id", "_registrations", "_loaded_maps")

    def __init__(self, world_id: WorldId) -> None:
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        self._world_id = world_id
        self._registrations: dict[MapId, MapRegistration] = {}
        self._loaded_maps: dict[MapId, HexMapDefinition] = {}

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def map_ids(self) -> tuple[MapId, ...]:
        return tuple(self._registrations)

    @property
    def loaded_map_ids(self) -> tuple[MapId, ...]:
        return tuple(self._loaded_maps)

    @property
    def registrations(self) -> tuple[MapRegistration, ...]:
        return tuple(self._registrations.values())

    def register_map(self, map_id: MapId, name: str) -> MapRegistration:
        registration = MapRegistration(map_id, name)
        if map_id in self._registrations:
            raise DuplicateMapError(f"map '{map_id.value}' is already registered")
        self._registrations[map_id] = registration
        return registration

    def load_map(self, definition: HexMapDefinition) -> None:
        if not isinstance(definition, HexMapDefinition):
            raise TypeError("definition must be a HexMapDefinition")
        if definition.world_id != self._world_id:
            raise MapWorldMismatchError(
                f"map '{definition.map_id.value}' belongs to world "
                f"'{definition.world_id.value}', not '{self._world_id.value}'"
            )
        registration = self._registrations.get(definition.map_id)
        if registration is None:
            raise UnknownMapError(f"map '{definition.map_id.value}' is not registered")
        if registration.name != definition.name:
            raise MapNameMismatchError(
                f"registered name '{registration.name}' does not match "
                f"definition name '{definition.name}'"
            )
        if definition.map_id in self._loaded_maps:
            raise MapAlreadyLoadedError(
                f"map '{definition.map_id.value}' is already loaded"
            )
        self._loaded_maps[definition.map_id] = definition

    def unload_map(self, map_id: MapId) -> None:
        self._require_registration(map_id)
        if map_id not in self._loaded_maps:
            raise MapNotLoadedError(f"map '{map_id.value}' is not loaded")
        del self._loaded_maps[map_id]

    def remove_map(self, map_id: MapId) -> None:
        self._require_registration(map_id)
        self._loaded_maps.pop(map_id, None)
        del self._registrations[map_id]

    def get_registration(self, map_id: MapId) -> MapRegistration | None:
        self._validate_map_id(map_id)
        return self._registrations.get(map_id)

    def get_map(self, map_id: MapId) -> HexMapDefinition | None:
        self._validate_map_id(map_id)
        return self._loaded_maps.get(map_id)

    def is_registered(self, map_id: MapId) -> bool:
        self._validate_map_id(map_id)
        return map_id in self._registrations

    def is_loaded(self, map_id: MapId) -> bool:
        self._validate_map_id(map_id)
        return map_id in self._loaded_maps

    def _require_registration(self, map_id: MapId) -> MapRegistration:
        self._validate_map_id(map_id)
        try:
            return self._registrations[map_id]
        except KeyError:
            raise UnknownMapError(f"map '{map_id.value}' is not registered") from None

    @staticmethod
    def _validate_map_id(map_id: MapId) -> None:
        if not isinstance(map_id, MapId):
            raise TypeError("map_id must be a MapId")
