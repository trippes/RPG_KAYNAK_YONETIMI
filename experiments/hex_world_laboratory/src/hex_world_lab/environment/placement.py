"""Immutable map placement for a static environmental object instance."""
from dataclasses import dataclass

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.world.identity import MapId, WorldId


@dataclass(frozen=True, slots=True)
class EnvironmentalObjectPlacement:
    instance_id: str
    definition_id: str
    world_id: WorldId
    map_id: MapId
    ground_position: WorldPoint

    def __post_init__(self) -> None:
        for name, value in (("instance_id", self.instance_id), ("definition_id", self.definition_id)):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        if not isinstance(self.ground_position, WorldPoint):
            raise TypeError("ground_position must be a WorldPoint")
