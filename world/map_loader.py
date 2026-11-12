"""Load and validate content-defined local maps from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from .map_definition import MapDefinition, MapDefinitionError
from .location import Location
from .map import WorldMap
from .local_map import LocalMapDefinition


def load_map_definition(path: str | Path) -> MapDefinition:
    """Load a local map JSON file and validate it against the map contract."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except OSError as error:
        raise MapDefinitionError(f"Map definition file could not be read: {source}") from error
    except json.JSONDecodeError as error:
        raise MapDefinitionError(
            f"Invalid map JSON in '{source}' at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    try:
        return MapDefinition.from_dict(data)
    except MapDefinitionError as error:
        raise MapDefinitionError(f"Invalid map definition in '{source}': {error}") from error


def load_map_definitions(directory: str | Path) -> dict[str, MapDefinition]:
    """Load a map package and validate all cross-map transition references."""
    root = Path(directory)
    if not root.is_dir():
        raise MapDefinitionError(f"Map directory could not be loaded: {root}")
    definitions: dict[str, MapDefinition] = {}
    transition_ids: set[str] = set()
    for source in sorted(root.glob("*.json")):
        definition = load_map_definition(source)
        if definition.map_id in definitions:
            raise MapDefinitionError(f"Duplicate map ID: {definition.map_id}")
        definitions[definition.map_id] = definition
        for transition in definition.transitions:
            if transition.transition_id in transition_ids:
                raise MapDefinitionError(
                    f"Duplicate transition ID in map package: {transition.transition_id}"
                )
            transition_ids.add(transition.transition_id)

    for definition in definitions.values():
        for transition in definition.transitions:
            target = definitions.get(transition.target_map_id)
            if target is None:
                raise MapDefinitionError(
                    f"Transition '{transition.transition_id}' references missing map "
                    f"'{transition.target_map_id}'."
                )
            for x, y in transition.target_tiles:
                if not (0 <= x < target.size.width and 0 <= y < target.size.height):
                    raise MapDefinitionError(
                        f"Transition '{transition.transition_id}' target coordinate "
                        f"({x}, {y}) is outside map '{target.map_id}' bounds."
                    )
            if transition.bidirectional:
                reciprocal = any(
                    candidate.bidirectional
                    and candidate.target_map_id == definition.map_id
                    and candidate.direction == {
                        "north": "south", "south": "north",
                        "east": "west", "west": "east",
                    }.get(transition.direction)
                    and set(candidate.from_tiles) == set(transition.target_tiles)
                    and set(candidate.target_tiles) == set(transition.from_tiles)
                    for candidate in target.transitions
                )
                if not reciprocal:
                    raise MapDefinitionError(
                        f"Bidirectional transition '{transition.transition_id}' from "
                        f"'{definition.map_id}' requires a reciprocal transition in "
                        f"'{target.map_id}'. Set bidirectional=false for a one-way exit."
                    )
    return definitions


def build_world_map(definitions: dict[str, MapDefinition], world_id: str) -> WorldMap:
    """Build the world graph exclusively from local map metadata and exits."""
    world_map = WorldMap(world_id)
    for definition in definitions.values():
        if definition.world_position is None:
            raise MapDefinitionError(
                f"Map '{definition.map_id}' is missing required world_position metadata."
            )
        landmarks = tuple(
            (
                item.landmark_id, item.name, item.position, item.activities,
                item.description, item.visual_type,
            )
            for item in definition.landmarks
        )
        location_type = (definition.metadata or {}).get("location_type", "unknown")
        world_map.add_location(Location(
            definition.map_id, definition.name, definition.world_position,
            definition.description, location_type, definition.activities, landmarks,
        ))

    connected_pairs = set()
    for definition in definitions.values():
        for transition in definition.transitions:
            pair = (definition.map_id, transition.target_map_id)
            if transition.bidirectional:
                key = tuple(sorted(pair))
                if key not in connected_pairs:
                    world_map.connect(*pair)
                    connected_pairs.add(key)
            else:
                world_map.connect_one_way(*pair)
    return world_map


def build_local_map_definitions(
    definitions: dict[str, MapDefinition], world_id: str,
) -> tuple[LocalMapDefinition, ...]:
    """Create dynamic local-map dimensions from the content catalog."""
    return tuple(
        LocalMapDefinition(
            world_id, definition.map_id,
            definition.size.width, definition.size.height,
        )
        for definition in definitions.values()
    )
