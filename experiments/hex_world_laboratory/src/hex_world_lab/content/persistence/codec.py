"""Strict JSON codecs for content libraries and map-content documents."""
from __future__ import annotations
import json
from collections.abc import Mapping
from typing import Any
from hex_world_lab.world.persistence.map_serializer import map_to_payload
from hex_world_lab.world.persistence.map_deserializer import deserialize_map_payload
from .collision import CircleCollider, ConvexPolygonCollider
from .definition import ContentCategory, ContentDefinition
from .drawing import (
    CircleElement, DrawingStyle, EllipseElement, Layer, Point,
    PolygonElement, PolylineElement, VisualDocument,
)
from .library import ContentLibrary
from .map_document import MapContentDocument
from .placement import ContentPlacement
from .errors import ContentValidationError, UnsupportedContentVersionError
from .values import thaw_json

def _keys(value, allowed, required, path):
    if not isinstance(value, dict):
        raise ContentValidationError("must be an object", path)
    unknown = set(value) - set(allowed)
    missing = set(required) - set(value)
    if unknown:
        raise ContentValidationError(f"unknown field {sorted(unknown)[0]!r}", path)
    if missing:
        raise ContentValidationError(f"missing field {sorted(missing)[0]!r}", path)
    return value

def _pair(value, path):
    if not isinstance(value, list) or len(value) != 2:
        raise ContentValidationError("must be a two-number array", path)
    return tuple(value)

def _style_payload(style):
    return {"fill": style.fill, "stroke": style.stroke, "stroke_width": style.stroke_width}

def _element_payload(element):
    base = {"element_id": element.element_id, "style": _style_payload(element.style)}
    if isinstance(element, PolygonElement):
        return {**base, "shape": {"type": "polygon", "points": [[p.x, p.y] for p in element.points]}}
    if isinstance(element, EllipseElement):
        return {**base, "shape": {"type": "ellipse", "x": element.x, "y": element.y, "width": element.width, "height": element.height}}
    if isinstance(element, CircleElement):
        return {**base, "shape": {"type": "circle", "center": [element.center.x, element.center.y], "radius": element.radius}}
    return {**base, "shape": {"type": "polyline", "points": [[p.x, p.y] for p in element.points], "closed": element.closed}}

def _visual_payload(doc):
    return {
        "document_version": doc.document_version,
        "logical_size": list(doc.logical_size),
        "ground_anchor": list(doc.ground_anchor),
        "depth_anchor": list(doc.depth_anchor),
        "palette": thaw_json(doc.palette),
        "layers": [{"layer_id": layer.layer_id, "order": layer.order, "elements": [_element_payload(e) for e in layer.elements]} for layer in doc.layers],
        "generator": thaw_json(doc.generator),
    }

def _collider_payload(collider):
    if collider is None:
        return None
    if isinstance(collider, CircleCollider):
        return {"type": "circle", "center": [collider.center_x, collider.center_y], "radius": collider.radius}
    return {"type": "convex_polygon", "vertices": [list(v) for v in collider.vertices]}

def _definition_payload(item):
    return {
        "content_id": item.content_id, "name": item.name, "category": item.category.value,
        "visual_document": _visual_payload(item.visual_document),
        "collider": _collider_payload(item.collider), "metadata": thaw_json(item.metadata),
    }

def library_to_payload(library: ContentLibrary):
    if not isinstance(library, ContentLibrary):
        raise TypeError("library must be ContentLibrary")
    return {"schema_version": 1, "kind": "eldoria_content_library", "library_id": library.library_id,
            "definitions": [_definition_payload(item) for item in library.definitions]}

def map_content_to_payload(document: MapContentDocument):
    if not isinstance(document, MapContentDocument):
        raise TypeError("document must be MapContentDocument")
    return {"schema_version": 1, "kind": "eldoria_map_document",
            "map": map_to_payload(document.map_definition),
            "placements": [{"instance_id": p.instance_id, "content_id": p.content_id, "position": {"x": p.x, "y": p.y}} for p in document.placements]}

def serialize_library(library):
    return json.dumps(library_to_payload(library), ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"

def serialize_map_content(document):
    return json.dumps(map_content_to_payload(document), ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n"

def _decode_style(raw, path):
    _keys(raw, {"fill", "stroke", "stroke_width"}, {"fill", "stroke", "stroke_width"}, path)
    return DrawingStyle(raw["fill"], raw["stroke"], raw["stroke_width"])

def _decode_visual(raw, path):
    _keys(raw, {"document_version", "logical_size", "ground_anchor", "depth_anchor", "palette", "layers", "generator"},
          {"document_version", "logical_size", "ground_anchor", "depth_anchor", "palette", "layers", "generator"}, path)
    version = raw["document_version"]
    if isinstance(version, bool) or version != 1:
        raise UnsupportedContentVersionError("unsupported visual document version", path + ".document_version")
    layers = []
    if not isinstance(raw["layers"], list):
        raise ContentValidationError("must be an array", path + ".layers")
    for li, layer in enumerate(raw["layers"]):
        lp = f"{path}.layers[{li}]"
        _keys(layer, {"layer_id", "order", "elements"}, {"layer_id", "order", "elements"}, lp)
        elements = []
        if not isinstance(layer["elements"], list):
            raise ContentValidationError("must be an array", lp + ".elements")
        for ei, element in enumerate(layer["elements"]):
            ep = f"{lp}.elements[{ei}]"
            _keys(element, {"element_id", "shape", "style"}, {"element_id", "shape", "style"}, ep)
            shape = element["shape"]
            if not isinstance(shape, dict) or "type" not in shape:
                raise ContentValidationError("shape requires a type", ep + ".shape")
            kind = shape["type"]
            style = _decode_style(element["style"], ep + ".style")
            eid = element["element_id"]
            if kind == "polygon":
                _keys(shape, {"type", "points"}, {"type", "points"}, ep + ".shape")
                points = tuple(Point(*_pair(p, ep + ".shape.points")) for p in shape["points"])
                item = PolygonElement(eid, points, style)
            elif kind == "ellipse":
                _keys(shape, {"type", "x", "y", "width", "height"}, {"type", "x", "y", "width", "height"}, ep + ".shape")
                item = EllipseElement(eid, shape["x"], shape["y"], shape["width"], shape["height"], style)
            elif kind == "circle":
                _keys(shape, {"type", "center", "radius"}, {"type", "center", "radius"}, ep + ".shape")
                item = CircleElement(eid, Point(*_pair(shape["center"], ep + ".shape.center")), shape["radius"], style)
            elif kind == "polyline":
                _keys(shape, {"type", "points", "closed"}, {"type", "points", "closed"}, ep + ".shape")
                points = tuple(Point(*_pair(p, ep + ".shape.points")) for p in shape["points"])
                item = PolylineElement(eid, points, style, shape["closed"])
            else:
                raise ContentValidationError(f"unknown drawing primitive {kind!r}", ep + ".shape.type")
            elements.append(item)
        layers.append(Layer(layer["layer_id"], layer["order"], tuple(elements)))
    try:
        return VisualDocument(tuple(raw["logical_size"]), tuple(raw["ground_anchor"]), tuple(raw["depth_anchor"]),
                              raw["palette"], tuple(layers), version, raw["generator"])
    except (TypeError, ValueError, KeyError) as exc:
        raise ContentValidationError(str(exc), path) from exc

def _decode_collider(raw, path):
    if raw is None:
        return None
    if not isinstance(raw, dict) or "type" not in raw:
        raise ContentValidationError("collider requires a type", path)
    if raw["type"] == "circle":
        _keys(raw, {"type", "center", "radius"}, {"type", "center", "radius"}, path)
        center = _pair(raw["center"], path + ".center")
        return CircleCollider(center[0], center[1], raw["radius"])
    if raw["type"] == "convex_polygon":
        _keys(raw, {"type", "vertices"}, {"type", "vertices"}, path)
        return ConvexPolygonCollider(tuple(_pair(v, path + ".vertices") for v in raw["vertices"]))
    raise ContentValidationError("unknown collider type", path + ".type")

def deserialize_library(payload: Any):
    _keys(payload, {"schema_version", "kind", "library_id", "definitions"},
          {"schema_version", "kind", "library_id", "definitions"}, "$")
    if isinstance(payload["schema_version"], bool) or payload["schema_version"] != 1:
        raise UnsupportedContentVersionError("unsupported content library schema version", "$.schema_version")
    if payload["kind"] != "eldoria_content_library":
        raise ContentValidationError("unexpected document kind", "$.kind")
    if not isinstance(payload["definitions"], list):
        raise ContentValidationError("must be an array", "$.definitions")
    definitions = []
    for index, raw in enumerate(payload["definitions"]):
        path = f"$.definitions[{index}]"
        _keys(raw, {"content_id", "name", "category", "visual_document", "collider", "metadata"},
              {"content_id", "name", "category", "visual_document", "collider", "metadata"}, path)
        try:
            definitions.append(ContentDefinition(raw["content_id"], raw["name"], ContentCategory(raw["category"]),
                _decode_visual(raw["visual_document"], path + ".visual_document"),
                _decode_collider(raw["collider"], path + ".collider"), raw["metadata"]))
        except (TypeError, ValueError, KeyError) as exc:
            raise ContentValidationError(str(exc), path) from exc
    try:
        return ContentLibrary(payload["library_id"], tuple(definitions))
    except (TypeError, ValueError) as exc:
        raise ContentValidationError(str(exc), "$") from exc

def deserialize_map_content(payload: Any):
    _keys(payload, {"schema_version", "kind", "map", "placements"}, {"schema_version", "kind", "map", "placements"}, "$")
    if isinstance(payload["schema_version"], bool) or payload["schema_version"] != 1:
        raise UnsupportedContentVersionError("unsupported map-content schema version", "$.schema_version")
    if payload["kind"] != "eldoria_map_document":
        raise ContentValidationError("unexpected document kind", "$.kind")
    if not isinstance(payload["placements"], list):
        raise ContentValidationError("must be an array", "$.placements")
    placements = []
    for index, raw in enumerate(payload["placements"]):
        path = f"$.placements[{index}]"
        _keys(raw, {"instance_id", "content_id", "position"}, {"instance_id", "content_id", "position"}, path)
        position = _keys(raw["position"], {"x", "y"}, {"x", "y"}, path + ".position")
        try:
            placements.append(ContentPlacement(raw["instance_id"], raw["content_id"], position["x"], position["y"]))
        except (TypeError, ValueError) as exc:
            raise ContentValidationError(str(exc), path) from exc
    try:
        return MapContentDocument(deserialize_map_payload(payload["map"]), tuple(placements))
    except (TypeError, ValueError, KeyError) as exc:
        raise ContentValidationError(str(exc), "$") from exc
