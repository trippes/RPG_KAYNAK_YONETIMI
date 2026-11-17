"""Application-level orchestration of map and entity lifecycles."""
from hex_world_lab.world.world import HexWorld
from hex_world_lab.world.map_definition import HexMapDefinition
from hex_world_lab.world.identity import MapId
from hex_world_lab.entities import EntityRecord, EntityId, EntityRegistry
from hex_world_lab.entities.spatial_index import EntitySpatialIndex
from hex_world_lab.companions import CompanionRoster
class EntityWorldCoordinator:
    def __init__(self,world:HexWorld,registry:EntityRegistry|None=None,
                 spatial_index:EntitySpatialIndex|None=None,companions:CompanionRoster|None=None)->None:
        if not isinstance(world,HexWorld): raise TypeError("world must be a HexWorld")
        self.world=world
        self.registry=registry or EntityRegistry(world.world_id,world.map_registry)
        self.spatial_index=spatial_index or EntitySpatialIndex(self.registry)
        self.companions=companions or CompanionRoster(self.registry)
        self._validate_dependencies()
    def _validate_dependencies(self)->None:
        if self.registry.world_id!=self.world.world_id: raise ValueError("registry belongs to another world")
        if self.spatial_index.registry is not self.registry: raise ValueError("spatial index must use coordinator registry")
        if self.companions.registry is not self.registry: raise ValueError("companion roster must use coordinator registry")
    def register_entity(self,entity:EntityRecord)->None:
        self.registry.register(entity)
        if self.world.is_loaded(entity.map_id): self.spatial_index.update_entity(entity)
    def load_map(self,definition:HexMapDefinition)->None:
        self.world.load_map(definition)
        self.spatial_index.activate_map(definition.map_id)
    def unload_map(self,map_id:MapId)->None:
        self.world.unload_map(map_id)
        self.spatial_index.deactivate_map(map_id)
    def remove_map(self,map_id:MapId)->tuple[EntityRecord,...]:
        removed=[]
        for entity in self.registry.entities_for_map(self.world.world_id,map_id):
            self.spatial_index.remove_entity(entity.entity_id)
            self.companions.remove_entity(entity.entity_id)
            removed.append(self.registry.remove(entity.entity_id))
        self.spatial_index.remove_map(map_id)
        self.world.remove_map(map_id)
        return tuple(removed)
    def update_transform(self,entity_id:EntityId,transform)->EntityRecord:
        previous=self.registry.require(entity_id)
        updated=self.registry.update_transform(entity_id,transform)
        try:self.spatial_index.update_entity(updated)
        except Exception:
            restored=self.registry.update_transform(entity_id,previous.transform)
            self.spatial_index.update_entity(restored)
            raise
        return updated
    def set_active(self,entity_id:EntityId,active:bool)->EntityRecord:
        updated=self.registry.set_active(entity_id,active)
        self.spatial_index.update_entity(updated)
        return updated
    def remove_entity(self,entity_id:EntityId)->EntityRecord:
        self.spatial_index.remove_entity(entity_id); self.companions.remove_entity(entity_id)
        return self.registry.remove(entity_id)
