"""JSON loading helpers for content-defined local maps."""

from __future__ import annotations

import json
from pathlib import Path

from .map_definition import MapDefinition, MapDefinitionError


class MapContentError(ValueError):
    """Raised when a map content file cannot be loaded safely."""


def load_map_definition(path: str | Path) -> MapDefinition:
    source = Path(path)
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MapContentError(f"Map definition could not be loaded: {source}") from error
    try:
        return MapDefinition.from_dict(data)
    except MapDefinitionError as error:
        raise MapContentError(f"Invalid map definition: {source}") from error
