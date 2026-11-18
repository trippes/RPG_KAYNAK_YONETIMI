"""Validated immutable collection of environmental definitions and placements."""
from dataclasses import dataclass

from hex_world_lab.world.identity import MapId, WorldId
from .definition import EnvironmentalObjectDefinition
from .placement import EnvironmentalObjectPlacement


@dataclass(frozen=True, slots=True)
class EnvironmentalObjectScene:
    world_id: WorldId
    map_id: MapId
    definitions: tuple[EnvironmentalObjectDefinition, ...]
    placements: tuple[EnvironmentalObjectPlacement, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.world_id, WorldId):
            raise TypeError("world_id must be a WorldId")
        if not isinstance(self.map_id, MapId):
            raise TypeError("map_id must be a MapId")
        definitions = tuple(self.definitions)
        placements = tuple(self.placements)
        if any(not isinstance(item, EnvironmentalObjectDefinition) for item in definitions):
            raise TypeError("definitions must contain EnvironmentalObjectDefinition values")
        if any(not isinstance(item, EnvironmentalObjectPlacement) for item in placements):
            raise TypeError("placements must contain EnvironmentalObjectPlacement values")
        definition_ids = [item.definition_id for item in definitions]
        instance_ids = [item.instance_id for item in placements]
        if len(definition_ids) != len(set(definition_ids)):
            raise ValueError("definition_id values must be unique within a scene")
        if len(instance_ids) != len(set(instance_ids)):
            raise ValueError("instance_id values must be unique within a scene")
        known = set(definition_ids)
        for placement in placements:
            if placement.definition_id not in known:
                raise ValueError(f"unknown environmental definition: {placement.definition_id}")
            if placement.world_id != self.world_id or placement.map_id != self.map_id:
                raise ValueError("all placements must belong to the scene world and map")
        object.__setattr__(self, "definitions", tuple(sorted(definitions, key=lambda item: item.definition_id)))
        object.__setattr__(self, "placements", tuple(sorted(placements, key=lambda item: item.instance_id)))

    def definition_for(self, placement: EnvironmentalObjectPlacement) -> EnvironmentalObjectDefinition:
        for definition in self.definitions:
            if definition.definition_id == placement.definition_id:
                return definition
        raise KeyError(placement.definition_id)
