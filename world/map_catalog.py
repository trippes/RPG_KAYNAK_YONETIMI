"""Deterministic mixed-schema map discovery for content packages."""
import json
from pathlib import Path
from .map_definition import MapDefinitionError
from .map_loader import load_map_definition
from .hex_map_definition import load_hex_map_definition

def load_map_catalog(directory):
    root=Path(directory)
    if not root.is_dir(): raise MapDefinitionError(f"Map directory could not be loaded: {root}")
    square={}; hexes={}; transition_ids=set()
    for source in sorted(root.glob("*.json")):
        try: raw=json.loads(source.read_text(encoding="utf-8"))
        except (OSError,json.JSONDecodeError) as e: raise MapDefinitionError(f"Map JSON could not be read: {source}") from e
        if not isinstance(raw,dict) or type(raw.get("schema_version")) is not int:
            raise MapDefinitionError(f"Map file '{source}' has an invalid schema_version.")
        version=raw["schema_version"]
        if version==1: definition=load_map_definition(source); target=square
        elif version==2: definition=load_hex_map_definition(source); target=hexes
        else: raise MapDefinitionError(f"Map file '{source}' uses unsupported schema_version '{version}'.")
        if definition.map_id in square or definition.map_id in hexes:
            raise MapDefinitionError(f"Duplicate map ID in package: {definition.map_id}")
        target[definition.map_id]=definition
        for transition in definition.transitions:
            transition_id=transition.transition_id
            if transition_id in transition_ids: raise MapDefinitionError(f"Duplicate transition ID in map package: {transition_id}")
            transition_ids.add(transition_id)
    if not square and not hexes: raise MapDefinitionError(f"Map directory contains no JSON map definitions: {root}")
    # Preserve the established v1 transition contract; v2 transitions remain structural only until Stage 3.
    for definition in square.values():
        for transition in definition.transitions:
            target=square.get(transition.target_map_id)
            if target is None: raise MapDefinitionError(f"Legacy transition '{transition.transition_id}' references missing square map '{transition.target_map_id}'.")
            for x,y in transition.target_tiles:
                if not (0<=x<target.size.width and 0<=y<target.size.height):
                    raise MapDefinitionError(f"Legacy transition '{transition.transition_id}' target ({x}, {y}) is outside map '{target.map_id}'.")
            if transition.bidirectional:
                opposite={"north":"south","south":"north","east":"west","west":"east"}.get(transition.direction)
                reciprocal=any(c.bidirectional and c.target_map_id==definition.map_id and c.direction==opposite and set(c.from_tiles)==set(transition.target_tiles) and set(c.target_tiles)==set(transition.from_tiles) for c in target.transitions)
                if not reciprocal: raise MapDefinitionError(f"Bidirectional legacy transition '{transition.transition_id}' requires a reciprocal transition.")
    return square,hexes
