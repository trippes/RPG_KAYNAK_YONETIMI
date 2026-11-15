"""World aggregate that owns a map registry."""

from hex_world_lab.world.identity import MapId, WorldId
from hex_world_lab.world.map_definition import HexMapDefinition
from hex_world_lab.world.map_registry import MapRegistration, MapRegistry


class HexWorld:
    """A world identity and the map catalog scoped to that identity."""

    __slots__ = ("_world_id", "_map_registry")

    def __init__(self, world_id: WorldId) -> None:
        if not isinstance(world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        object.__setattr__(self, "_world_id", world_id)
        object.__setattr__(self, "_map_registry", MapRegistry(world_id))

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("HexWorld attributes are immutable")

    @property
    def world_id(self) -> WorldId:
        return self._world_id

    @property
    def map_registry(self) -> MapRegistry:
        """Return the registry API, never its internal mutable dictionaries."""
        return self._map_registry

    def register_map(self, map_id: MapId, name: str) -> MapRegistration:
        return self._map_registry.register_map(map_id, name)

    def load_map(self, definition: HexMapDefinition) -> None:
        self._map_registry.load_map(definition)

    def unload_map(self, map_id: MapId) -> None:
        self._map_registry.unload_map(map_id)

    def remove_map(self, map_id: MapId) -> None:
        self._map_registry.remove_map(map_id)

    def get_map(self, map_id: MapId) -> HexMapDefinition | None:
        return self._map_registry.get_map(map_id)

    def is_registered(self, map_id: MapId) -> bool:
        return self._map_registry.is_registered(map_id)

    def is_loaded(self, map_id: MapId) -> bool:
        return self._map_registry.is_loaded(map_id)
