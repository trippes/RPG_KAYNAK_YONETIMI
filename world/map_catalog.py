"""Legacy square-map catalog. Hex map discovery belongs to application content loading."""

from pathlib import Path

from .map_definition import MapDefinitionError
from .map_loader import load_map_definitions


def load_map_catalog(directory):
    """Return the v1 square-map catalog and an empty legacy hex collection.

    Schema-v2 maps are parsed by application.content_loader so the legacy
    world package never imports core.domain spatial types.
    """
    root = Path(directory)
    if not root.is_dir():
        raise MapDefinitionError(f"Map directory could not be loaded: {root}")
    if not any(root.glob("*.json")):
        raise MapDefinitionError(f"Map directory contains no JSON map definitions: {root}")
    return load_map_definitions(root), {}
