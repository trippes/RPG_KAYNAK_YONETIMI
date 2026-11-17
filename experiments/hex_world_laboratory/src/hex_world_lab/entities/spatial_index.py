"""Map-scoped entity broadphase adapter over the generic UniformGrid."""
from dataclasses import dataclass
from math import hypot
from hex_world_lab.geometry import WorldPoint, MapId
from hex_world_lab.physics.body import ActorBodyTransform
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape
from hex_world_lab.spatial import UniformGrid
from .entity import EntityRecord
from .registry import EntityRegistry

@dataclass(frozen=True, slots=True)
class EntityAABB:
    min_x: float
    min_y: float
    max_x: float
    max_y: float
    def intersects(self, other: object) -> bool:
        return not (self.max_x < other.min_x or self.min_x > other.max_x or
                    self.max_y < other.min_y or self.min_y > other.max_y)

class EntitySpatialIndex:
    def __init__(self, registry: EntityRegistry, cell_size: float = 128.0) -> None:
        self.registry=registry; self.cell_size=cell_size
        self._indexes: dict[MapId,UniformGrid]={}; self._loaded:set[MapId]=set()
    @staticmethod
    def bounds_for(entity: EntityRecord) -> EntityAABB | None:
        position=entity.transform.location.position
        if entity.body is not None:
            shape=ActorBodyTransform(position,entity.transform.rotation_radians).transform_shape(entity.body)
            if isinstance(shape,CircleShape):
                return EntityAABB(shape.center.x-shape.radius,shape.center.y-shape.radius,
                                  shape.center.x+shape.radius,shape.center.y+shape.radius)
            if isinstance(shape,ConvexPolygonShape):
                xs=[v.x for v in shape.vertices]; ys=[v.y for v in shape.vertices]
                return EntityAABB(min(xs),min(ys),max(xs),max(ys))
        profile=entity.interaction_profile
        radius=getattr(profile,"interaction_radius",None)
        if radius is None: return None
        return EntityAABB(position.x-radius,position.y-radius,position.x+radius,position.y+radius)
    def activate_map(self,map_id:MapId)->None:
        self._loaded.add(map_id); self._rebuild(map_id)
    def deactivate_map(self,map_id:MapId)->None:
        self._loaded.discard(map_id); self._indexes.pop(map_id,None)
    def remove_map(self,map_id:MapId)->None: self.deactivate_map(map_id)
    def update_entity(self,entity:EntityRecord)->None:
        for map_id,index in tuple(self._indexes.items()):
            try: index.remove(entity.entity_id.value)
            except KeyError: pass
        if entity.map_id in self._loaded and entity.is_active:
            bounds=self.bounds_for(entity)
            if bounds is not None:
                index=self._indexes.setdefault(entity.map_id,UniformGrid(self.cell_size))
                index.insert(entity.entity_id.value,bounds)
    def remove_entity(self,entity_id)->None:
        for index in self._indexes.values():
            try: index.remove(entity_id.value)
            except KeyError: pass
    def query(self,map_id:MapId,bounds:EntityAABB)->tuple[EntityRecord,...]:
        index=self._indexes.get(map_id)
        if index is None: return ()
        found=[]
        for raw_id in index.query(bounds):
            from .identity import EntityId
            entity=self.registry.get(EntityId(raw_id))
            if entity is not None and entity.is_active and entity.map_id==map_id:
                found.append(entity)
        return tuple(found)
    def _rebuild(self,map_id:MapId)->None:
        index=UniformGrid(self.cell_size)
        for entity in self.registry.entities_for_map(self.registry.world_id,map_id):
            if not entity.is_active: continue
            bounds=self.bounds_for(entity)
            if bounds is not None: index.insert(entity.entity_id.value,bounds)
        self._indexes[map_id]=index
    def differential_candidates(self,map_id:MapId,bounds:EntityAABB)->tuple[str,...]:
        indexed=tuple(e.entity_id.value for e in self.query(map_id,bounds))
        brute=tuple(e.entity_id.value for e in self.registry.entities_for_map(self.registry.world_id,map_id)
                    if e.is_active and (b:=self.bounds_for(e)) is not None and bounds.intersects(b))
        if set(indexed)!=set(brute): raise AssertionError("entity spatial index differs from brute-force reference")
        return indexed
