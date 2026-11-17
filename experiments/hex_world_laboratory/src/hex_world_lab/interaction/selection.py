"""Small functional facade for deterministic target selection."""
from hex_world_lab.entities import EntityId
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.world.identity import MapId
from .target_query import TargetQuery

def select_target(query: TargetQuery, point: WorldPoint, map_id: MapId,
                  tags: frozenset[str] | None = None) -> EntityId | None:
    if not isinstance(query, TargetQuery): raise TypeError("query must be a TargetQuery")
    return query.select_target(point,map_id,tags)
