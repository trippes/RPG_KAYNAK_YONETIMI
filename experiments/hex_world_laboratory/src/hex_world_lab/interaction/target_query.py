"""Spatially accelerated target candidates with exact world-distance filtering."""
from dataclasses import dataclass
from hex_world_lab.entities import EntityId, EntityRecord, EntityRegistry
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.world.identity import MapId
from hex_world_lab.interaction.profile import InteractionProfile
from hex_world_lab.interaction.range import world_distance
from hex_world_lab.entities.spatial_index import EntityAABB, EntitySpatialIndex

@dataclass(frozen=True, slots=True)
class TargetCandidate:
    entity: EntityRecord
    distance: float
    selection_priority: int

class TargetQuery:
    def __init__(self, registry: EntityRegistry, spatial_index: EntitySpatialIndex) -> None:
        self.registry, self.spatial_index = registry, spatial_index
    def query_targets(self, origin: WorldPoint, map_id: MapId, radius: float,
                      tags: frozenset[str] | None = None) -> tuple[TargetCandidate, ...]:
        if not isinstance(origin, WorldPoint): raise TypeError("origin must be a WorldPoint")
        if isinstance(radius, bool) or not isinstance(radius, (int,float)) or radius < 0:
            raise ValueError("radius must be non-negative")
        profiles = [getattr(e.interaction_profile, "interaction_radius", 0.0)
                    for e in self.registry.entities_for_map(self.registry.world_id, map_id)]
        padding = max(profiles, default=0.0)
        extent = radius + padding
        area = EntityAABB(origin.x-extent, origin.y-extent, origin.x+extent, origin.y+extent)
        candidates=[]
        for entity in self.spatial_index.query(map_id, area):
            profile=entity.interaction_profile
            if not isinstance(profile, InteractionProfile) or not profile.targetable: continue
            if tags is not None and not (profile.interaction_tags & tags): continue
            distance=world_distance(origin, entity.transform.location.position)
            if distance <= radius + profile.interaction_radius:
                candidates.append(TargetCandidate(entity, distance, profile.selection_priority))
        return tuple(sorted(candidates, key=lambda c:(-c.selection_priority,c.distance,c.entity.entity_id.value)))
    def select_target(self, point: WorldPoint, map_id: MapId,
                      tags: frozenset[str] | None = None) -> EntityId | None:
        found=self.query_targets(point,map_id,0.0,tags)
        return found[0].entity.entity_id if found else None
    def is_in_interaction_range(self, actor_id: EntityId, target_id: EntityId,
                                interaction_kind: str) -> bool:
        actor=self.registry.get(actor_id); target=self.registry.get(target_id)
        if actor is None or target is None or not actor.is_active or not target.is_active: return False
        if actor.world_id != target.world_id or actor.map_id != target.map_id: return False
        actor_profile=actor.interaction_profile; target_profile=target.interaction_profile
        if not isinstance(actor_profile,InteractionProfile) or not isinstance(target_profile,InteractionProfile): return False
        if not target_profile.targetable or interaction_kind not in target_profile.interaction_tags: return False
        return world_distance(actor.transform.location.position,target.transform.location.position) <= actor_profile.interaction_radius + target_profile.interaction_radius
