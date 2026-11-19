"""World-scoped entity registry with immutable snapshots."""
from hex_world_lab.world.identity import WorldId, MapId
from hex_world_lab.world.map_registry import MapRegistry
from .entity import EntityRecord
from .identity import EntityId
from .transform import EntityTransform
class EntityRegistryError(Exception): pass
class DuplicateEntityError(EntityRegistryError): pass
class UnknownEntityError(EntityRegistryError, LookupError): pass
class EntityWorldMismatchError(EntityRegistryError, ValueError): pass
class EntityMapUnknownError(EntityRegistryError, LookupError): pass
class EntityRegistry:
    __slots__ = ("_world_id", "_maps", "_entities")
    def __init__(self, world_id: WorldId, map_registry: MapRegistry) -> None:
        if not isinstance(world_id, WorldId): raise TypeError("world_id must be a WorldId")
        if not isinstance(map_registry, MapRegistry): raise TypeError("map_registry must be a MapRegistry")
        if map_registry.world_id != world_id: raise EntityWorldMismatchError("map registry belongs to another world")
        self._world_id, self._maps, self._entities = world_id, map_registry, {}
    @property
    def world_id(self) -> WorldId: return self._world_id
    def register(self, entity: EntityRecord) -> None:
        if not isinstance(entity, EntityRecord): raise TypeError("entity must be an EntityRecord")
        if entity.world_id != self._world_id: raise EntityWorldMismatchError("entity belongs to another world")
        if not self._maps.is_registered(entity.map_id): raise EntityMapUnknownError(entity.map_id.value)
        if entity.entity_id in self._entities: raise DuplicateEntityError(entity.entity_id.value)
        self._entities[entity.entity_id] = entity
    def get(self, entity_id: EntityId) -> EntityRecord | None:
        self._validate_id(entity_id); return self._entities.get(entity_id)
    def require(self, entity_id: EntityId) -> EntityRecord:
        entity = self.get(entity_id)
        if entity is None: raise UnknownEntityError(entity_id.value)
        return entity
    def update_transform(self, entity_id: EntityId, transform: EntityTransform) -> EntityRecord:
        entity = self.require(entity_id)
        if not isinstance(transform, EntityTransform): raise TypeError("transform must be an EntityTransform")
        if transform.location.world_id != self._world_id: raise EntityWorldMismatchError("transform belongs to another world")
        if not self._maps.is_registered(transform.location.map_id): raise EntityMapUnknownError(transform.location.map_id.value)
        updated = entity.with_transform(transform); self._entities[entity_id] = updated
        return updated
    def set_active(self, entity_id: EntityId, active: bool) -> EntityRecord:
        if not isinstance(active, bool): raise TypeError("active must be a bool")
        entity = self.require(entity_id); updated = entity.with_active(active)
        self._entities[entity_id] = updated; return updated
    def remove(self, entity_id: EntityId) -> EntityRecord:
        self._validate_id(entity_id)
        try: return self._entities.pop(entity_id)
        except KeyError: raise UnknownEntityError(entity_id.value) from None
    def entities_for_map(self, world_id: WorldId, map_id: MapId) -> tuple[EntityRecord, ...]:
        if world_id != self._world_id: raise EntityWorldMismatchError("query belongs to another world")
        if not self._maps.is_registered(map_id): raise EntityMapUnknownError(map_id.value)
        return tuple(sorted((e for e in self._entities.values() if e.map_id == map_id), key=lambda e:e.entity_id.value))
    def all_entities(self) -> tuple[EntityRecord, ...]:
        return tuple(sorted(self._entities.values(), key=lambda e:e.entity_id.value))
    @staticmethod
    def _validate_id(entity_id: EntityId) -> None:
        if not isinstance(entity_id, EntityId): raise TypeError("entity_id must be an EntityId")
