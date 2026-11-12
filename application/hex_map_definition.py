"""Immutable masked axial local-map domain model and strict JSON loader."""
from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from core.domain.spatial import HexDirection, LocalHexPosition

class HexMapDefinitionError(ValueError):
    """Invalid schema-v2 hex map."""

def _text(v, field):
    if not isinstance(v, str) or not v.strip():
        raise HexMapDefinitionError(f"{field} must be a non-empty string.")
    return v

@dataclass(frozen=True, slots=True)
class HexCell:
    position: LocalHexPosition
    terrain_id: str
    blocked: bool = False
    def __post_init__(self):
        if not isinstance(self.position, LocalHexPosition): raise TypeError("position must be LocalHexPosition.")
        _text(self.terrain_id, "terrain_id")
        if not isinstance(self.blocked, bool): raise TypeError("blocked must be boolean.")

@dataclass(frozen=True, slots=True)
class HexMapFeature:
    feature_id: str
    feature_type: str
    cells: tuple[LocalHexPosition, ...]
    def __post_init__(self):
        _text(self.feature_id, "feature_id"); _text(self.feature_type, "feature_type")
        values=tuple(self.cells)
        if not values or any(not isinstance(p,LocalHexPosition) for p in values):
            raise HexMapDefinitionError("Feature cells must be non-empty LocalHexPosition values.")
        if len(set(values))!=len(values): raise HexMapDefinitionError("Feature cells must be unique.")
        object.__setattr__(self,"cells",values)

@dataclass(frozen=True, slots=True)
class HexLandmarkDefinition:
    landmark_id: str
    name: str
    position: LocalHexPosition
    landmark_type: str = "generic"
    visual_type: str = "generic"
    walkable: bool = True
    interactable: bool = False
    activities: tuple[str, ...] = ()
    resource_node_id: str | None = None
    description: str = ""
    def __post_init__(self):
        _text(self.landmark_id,"landmark_id"); _text(self.name,"name")
        if not isinstance(self.position,LocalHexPosition): raise TypeError("position must be LocalHexPosition.")
        _text(self.landmark_type,"landmark_type"); _text(self.visual_type,"visual_type")
        if not isinstance(self.walkable,bool) or not isinstance(self.interactable,bool): raise TypeError("landmark flags must be booleans.")
        acts=tuple(self.activities)
        if any(not isinstance(v,str) or not v.strip() for v in acts): raise HexMapDefinitionError("activities must be non-empty strings.")
        if self.resource_node_id is not None: _text(self.resource_node_id,"resource_node_id")
        if not isinstance(self.description,str): raise TypeError("description must be a string.")
        object.__setattr__(self,"activities",acts)

@dataclass(frozen=True, slots=True)
class HexMapTransition:
    transition_id: str
    source_cells: tuple[LocalHexPosition, ...]
    exit_direction: HexDirection
    target_map_id: str
    target_entry_direction: HexDirection | None = None
    target_cells: tuple[LocalHexPosition, ...] = ()
    active: bool = True
    traversal_mode: str = "one_way"
    def __post_init__(self):
        _text(self.transition_id,"transition_id"); _text(self.target_map_id,"target_map_id")
        sources=tuple(self.source_cells); targets=tuple(self.target_cells)
        if not sources or any(not isinstance(p,LocalHexPosition) for p in sources): raise HexMapDefinitionError("source_cells must contain LocalHexPosition values.")
        if len(set(sources))!=len(sources) or len(set(targets))!=len(targets): raise HexMapDefinitionError("transition cells must be unique.")
        if any(not isinstance(p,LocalHexPosition) for p in targets): raise TypeError("target_cells must contain LocalHexPosition values.")
        if not isinstance(self.exit_direction,HexDirection): raise TypeError("exit_direction must be HexDirection.")
        if self.target_entry_direction is not None and not isinstance(self.target_entry_direction,HexDirection): raise TypeError("target_entry_direction must be HexDirection or None.")
        if not isinstance(self.active,bool): raise TypeError("active must be boolean.")
        if self.traversal_mode not in {"one_way","bidirectional"}: raise HexMapDefinitionError("Invalid traversal_mode.")
        object.__setattr__(self,"source_cells",sources); object.__setattr__(self,"target_cells",targets)

@dataclass(frozen=True, slots=True)
class HexMapDefinition:
    schema_version: int
    map_id: str
    name: str
    description: str
    default_terrain: str
    valid_cells: frozenset[LocalHexPosition]
    cells: object
    terrain_ids: frozenset[str]
    features: tuple[HexMapFeature, ...] = ()
    landmarks: tuple[HexLandmarkDefinition, ...] = ()
    transitions: tuple[HexMapTransition, ...] = ()
    orientation: str = "pointy_top"
    coordinate_system: str = "axial"

    def __post_init__(self):
        if type(self.schema_version) is not int or self.schema_version != 2:
            raise HexMapDefinitionError("Unsupported hex map schema version.")
        _text(self.map_id, "map_id"); _text(self.name, "name"); _text(self.default_terrain, "default_terrain")
        if not isinstance(self.description, str): raise TypeError("description must be a string.")
        if self.orientation != "pointy_top" or self.coordinate_system != "axial":
            raise HexMapDefinitionError("Only pointy_top axial geometry is supported.")
        if not self.valid_cells: raise HexMapDefinitionError("valid_cells must not be empty.")
        if any(not isinstance(p, LocalHexPosition) for p in self.valid_cells):
            raise TypeError("valid_cells must contain LocalHexPosition values.")
        if self.default_terrain not in self.terrain_ids:
            raise HexMapDefinitionError("default_terrain references an unknown terrain ID.")
        if any(not isinstance(t, str) or not t.strip() for t in self.terrain_ids):
            raise HexMapDefinitionError("terrain_ids must contain non-empty strings.")
        cells = dict(self.cells)
        if set(cells) != set(self.valid_cells):
            raise HexMapDefinitionError("Cell records must exactly match valid_cells.")
        if any(not isinstance(c, HexCell) or c.position != p for p, c in cells.items()):
            raise HexMapDefinitionError("Cell records must match their mapping coordinates.")
        if any(c.terrain_id not in self.terrain_ids for c in cells.values()):
            raise HexMapDefinitionError("A cell references an unknown terrain ID.")
        for label, values, attr in (
            ("feature", self.features, "feature_id"),
            ("landmark", self.landmarks, "landmark_id"),
            ("transition", self.transitions, "transition_id"),
        ):
            ids = [getattr(v, attr) for v in values]
            if len(ids) != len(set(ids)): raise HexMapDefinitionError(f"Duplicate {label} IDs are not allowed.")
        for f in self.features:
            _text(f.feature_id, "feature.id"); _text(f.feature_type, "feature.type")
            if not f.cells or len(set(f.cells)) != len(f.cells): raise HexMapDefinitionError(f"Feature '{f.feature_id}' has empty or duplicate cells.")
            if any(p not in self.valid_cells for p in f.cells): raise HexMapDefinitionError(f"Feature '{f.feature_id}' references a cell outside valid_cells.")
        for item in self.landmarks:
            _text(item.landmark_id, "landmark.id"); _text(item.name, "landmark.name")
            if item.position not in self.valid_cells: raise HexMapDefinitionError(f"Landmark '{item.landmark_id}' is outside valid_cells.")
            if not isinstance(item.walkable, bool) or not isinstance(item.interactable, bool): raise HexMapDefinitionError("Landmark flags must be booleans.")
            if item.resource_node_id is not None: _text(item.resource_node_id, "resource_node_id")
        for tr in self.transitions:
            _text(tr.transition_id, "transition.id"); _text(tr.target_map_id, "transition.target_map_id")
            if not tr.source_cells or len(set(tr.source_cells)) != len(tr.source_cells): raise HexMapDefinitionError(f"Transition '{tr.transition_id}' has empty or duplicate source cells.")
            if any(p not in self.valid_cells for p in tr.source_cells): raise HexMapDefinitionError(f"Transition '{tr.transition_id}' source is outside valid_cells.")
            if not isinstance(tr.exit_direction, HexDirection): raise HexMapDefinitionError("Invalid transition exit direction.")
            if tr.target_entry_direction is not None and not isinstance(tr.target_entry_direction, HexDirection): raise HexMapDefinitionError("Invalid target entry direction.")
            if not isinstance(tr.active, bool) or tr.traversal_mode not in {"one_way", "bidirectional"}: raise HexMapDefinitionError("Invalid transition active/traversal_mode.")
        object.__setattr__(self, "valid_cells", frozenset(self.valid_cells))
        object.__setattr__(self, "terrain_ids", frozenset(self.terrain_ids))
        object.__setattr__(self, "cells", MappingProxyType(cells))
        object.__setattr__(self, "features", tuple(self.features))
        object.__setattr__(self, "landmarks", tuple(self.landmarks))
        object.__setattr__(self, "transitions", tuple(self.transitions))

    def has_cell(self, position):
        if not isinstance(position, LocalHexPosition): raise TypeError("position must be LocalHexPosition.")
        return position in self.valid_cells
    def get_cell(self, position):
        if not isinstance(position, LocalHexPosition): raise TypeError("position must be LocalHexPosition.")
        return self.cells.get(position)
    def is_blocked(self, position):
        cell = self.get_cell(position)
        return cell.blocked if cell is not None else False
    @property
    def bounds(self):
        return (min(p.q for p in self.valid_cells), min(p.r for p in self.valid_cells),
                max(p.q for p in self.valid_cells), max(p.r for p in self.valid_cells))

def _pos(raw, field):
    if not isinstance(raw, (list, tuple)) or len(raw) != 2 or type(raw[0]) is not int or type(raw[1]) is not int:
        raise HexMapDefinitionError(f"{field} must be a [q, r] pair of integers; bool and float are invalid.")
    return LocalHexPosition(raw[0], raw[1])
def _positions(raw, field, required=False):
    if not isinstance(raw, list): raise HexMapDefinitionError(f"{field} must be a list.")
    result = tuple(_pos(v, f"{field}[{i}]") for i, v in enumerate(raw))
    if required and not result: raise HexMapDefinitionError(f"{field} must not be empty.")
    return result
def _unknown(data, allowed, field):
    extra = sorted(set(data) - set(allowed))
    if extra: raise HexMapDefinitionError(f"{field} has unsupported fields: {', '.join(extra)}")
def _direction(value, field, optional=False):
    if optional and value is None: return None
    if not isinstance(value, str): raise HexMapDefinitionError(f"{field} must name one of six directions.")
    try: return HexDirection[value.upper()]
    except KeyError as e: raise HexMapDefinitionError(f"{field} has unknown direction '{value}'.") from e

def parse_hex_map(data):
    if not isinstance(data, dict): raise HexMapDefinitionError("hex map must be an object.")
    allowed={"schema_version","map_id","name","description","geometry","terrain_ids","default_terrain","valid_cells","cell_overrides","features","landmarks","transitions"}
    _unknown(data, allowed, "hex map")
    required=allowed-{"description","cell_overrides","features","landmarks","transitions"}
    missing=sorted(required-set(data))
    if missing: raise HexMapDefinitionError("hex map missing fields: "+", ".join(missing))
    if type(data["schema_version"]) is not int or data["schema_version"] != 2: raise HexMapDefinitionError("Unsupported hex map schema_version; expected 2.")
    geometry=data["geometry"]
    if not isinstance(geometry,dict): raise HexMapDefinitionError("geometry must be an object.")
    _unknown(geometry,{"type","orientation","coordinate_system"},"geometry")
    if geometry != {"type":"hex_axial","orientation":"pointy_top","coordinate_system":"axial"}:
        raise HexMapDefinitionError("geometry must declare hex_axial, pointy_top, axial.")
    terrains=data["terrain_ids"]
    if not isinstance(terrains,list) or not terrains: raise HexMapDefinitionError("terrain_ids must be a non-empty list.")
    terrain_ids=frozenset(_text(v,"terrain_ids item") for v in terrains)
    if len(terrain_ids)!=len(terrains): raise HexMapDefinitionError("terrain_ids contains duplicate IDs.")
    default=_text(data["default_terrain"],"default_terrain")
    if default not in terrain_ids: raise HexMapDefinitionError(f"Unknown default terrain '{default}'.")
    valid_list=_positions(data["valid_cells"],"valid_cells",True)
    if len(set(valid_list))!=len(valid_list): raise HexMapDefinitionError("valid_cells contains duplicate coordinates.")
    valid=frozenset(valid_list)
    cells={p:HexCell(p,default) for p in valid}
    overrides=data.get("cell_overrides",[])
    if not isinstance(overrides,list): raise HexMapDefinitionError("cell_overrides must be a list.")
    seen=set()
    for i,item in enumerate(overrides):
        if not isinstance(item,dict): raise HexMapDefinitionError(f"cell_overrides[{i}] must be an object.")
        _unknown(item,{"q","r","terrain","blocked"},f"cell_overrides[{i}]")
        if "q" not in item or "r" not in item: raise HexMapDefinitionError(f"cell_overrides[{i}] requires q and r.")
        p=_pos([item["q"],item["r"]],f"cell_overrides[{i}]")
        if p in seen: raise HexMapDefinitionError(f"Duplicate cell override at ({p.q}, {p.r}).")
        seen.add(p)
        if p not in valid: raise HexMapDefinitionError(f"Cell override ({p.q}, {p.r}) is outside valid_cells.")
        terrain=item.get("terrain",default)
        if not isinstance(terrain,str) or terrain not in terrain_ids: raise HexMapDefinitionError(f"cell_overrides[{i}] references unknown terrain '{terrain}'.")
        blocked=item.get("blocked",False)
        if not isinstance(blocked,bool): raise HexMapDefinitionError(f"cell_overrides[{i}].blocked must be boolean.")
        cells[p]=HexCell(p,terrain,blocked)
    raw_features=data.get("features",[])
    raw_landmarks=data.get("landmarks",[])
    raw_transitions=data.get("transitions",[])
    if not isinstance(raw_features,list) or not isinstance(raw_landmarks,list) or not isinstance(raw_transitions,list):
        raise HexMapDefinitionError("features, landmarks and transitions must be lists.")
    features=[]
    for i,item in enumerate(raw_features):
        if not isinstance(item,dict): raise HexMapDefinitionError(f"features[{i}] must be an object.")
        _unknown(item,{"id","type","cells"},f"features[{i}]")
        features.append(HexMapFeature(_text(item.get("id"),f"features[{i}].id"),_text(item.get("type"),f"features[{i}].type"),_positions(item.get("cells",[]),f"features[{i}].cells",True)))
    landmarks=[]
    for i,item in enumerate(raw_landmarks):
        if not isinstance(item,dict): raise HexMapDefinitionError(f"landmarks[{i}] must be an object.")
        _unknown(item,{"id","name","position","description","type","visual_type","walkable","interactable","activities","resource_node_id"},f"landmarks[{i}]")
        acts=item.get("activities",[])
        if not isinstance(acts,list) or any(not isinstance(v,str) or not v.strip() for v in acts): raise HexMapDefinitionError(f"landmarks[{i}].activities must be strings.")
        landmarks.append(HexLandmarkDefinition(_text(item.get("id"),f"landmarks[{i}].id"),_text(item.get("name"),f"landmarks[{i}].name"),_pos(item.get("position"),f"landmarks[{i}].position"),_text(item.get("type","generic"),f"landmarks[{i}].type"),_text(item.get("visual_type","generic"),f"landmarks[{i}].visual_type"),item.get("walkable",True),item.get("interactable",False),tuple(acts),item.get("resource_node_id"),item.get("description","")))
    transitions=[]
    for i,item in enumerate(raw_transitions):
        if not isinstance(item,dict): raise HexMapDefinitionError(f"transitions[{i}] must be an object.")
        _unknown(item,{"id","source_cells","exit_direction","target_map_id","target_entry_direction","target_cells","active","traversal_mode"},f"transitions[{i}]")
        transitions.append(HexMapTransition(_text(item.get("id"),f"transitions[{i}].id"),_positions(item.get("source_cells",[]),f"transitions[{i}].source_cells",True),_direction(item.get("exit_direction"),f"transitions[{i}].exit_direction"),_text(item.get("target_map_id"),f"transitions[{i}].target_map_id"),_direction(item.get("target_entry_direction"),f"transitions[{i}].target_entry_direction",True),_positions(item.get("target_cells",[]),f"transitions[{i}].target_cells"),item.get("active",True),item.get("traversal_mode","one_way")))
    try:
        return HexMapDefinition(2,_text(data["map_id"],"map_id"),_text(data["name"],"name"),data.get("description",""),default,valid,cells,terrain_ids,tuple(features),tuple(landmarks),tuple(transitions),geometry["orientation"],geometry["coordinate_system"])
    except (TypeError,ValueError) as e:
        if isinstance(e,HexMapDefinitionError): raise
        raise HexMapDefinitionError(str(e)) from e

def load_hex_map_definition(path):
    source=Path(path)
    try: raw=json.loads(source.read_text(encoding="utf-8"))
    except OSError as e: raise HexMapDefinitionError(f"Hex map file could not be read: {source}") from e
    except json.JSONDecodeError as e: raise HexMapDefinitionError(f"Invalid hex map JSON in '{source}' line {e.lineno}, column {e.colno}: {e.msg}") from e
    try: return parse_hex_map(raw)
    except (TypeError,ValueError) as e: raise HexMapDefinitionError(f"Invalid hex map definition in '{source}': {e}") from e
