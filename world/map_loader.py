"""Load and validate content-defined local maps from JSON files."""

from __future__ import annotations

import json
from pathlib import Path

from .map_definition import MapDefinition, MapDefinitionError


def load_map_definition(path: str | Path) -> MapDefinition:
    """Load a local map JSON file and validate it against the map contract."""
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MapDefinitionError(f"Map definition could not be loaded: {source}") from error
    return MapDefinition.from_dict(data)


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
    return definitions
