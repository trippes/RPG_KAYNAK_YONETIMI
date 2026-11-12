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
