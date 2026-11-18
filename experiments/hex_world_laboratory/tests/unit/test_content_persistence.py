"""Round-trip, schema rejection, and safe storage tests."""
import json
import pytest
from hex_world_lab.content import (
    CircleElement, ContentCategory, ContentDefinition, ContentLibrary,
    ContentPlacement, DrawingStyle, Layer, Point, PolygonElement, VisualDocument,
)
from hex_world_lab.content.collision import CircleCollider, ConvexPolygonCollider

def make_visual():
    return VisualDocument(
        (32, 40), (0.5, 0.95), (0.5, 0.8),
        {"green": (30, 120, 50, 255), "brown": (90, 55, 30, 255)},
        (Layer("base", 0, (
            PolygonElement("trunk", (Point(12, 35), Point(15, 12), Point(18, 35)), DrawingStyle(fill="brown")),
            CircleElement("crown", Point(15, 10), 8, DrawingStyle(fill="green")),
        )),),
    )

def make_definition(content_id="tree", collider=None):
    return ContentDefinition(content_id, "Tree", ContentCategory.ENVIRONMENTAL_OBJECT, make_visual(), collider, {"biome": "forest"})

def make_library():
    return ContentLibrary("default", (make_definition(collider=CircleCollider(0, 0, 4)),))

from hex_world_lab.content.map_document import MapContentDocument
from hex_world_lab.content.persistence import (
    ContentValidationError, UnsupportedContentVersionError, deserialize_library,
    deserialize_map_content, load_library_file, load_map_content_file,
    save_library_file, save_map_content_file, serialize_library, serialize_map_content,
)
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexMapDefinition, MapId, WorldId

def make_map():
    return HexMapDefinition(WorldId("eldoria"), MapId("valley"), "Valley",
        HexLayout(HexOrientation.POINTY_TOP, 1, WorldPoint(0,0)), {})

def test_library_round_trip_is_deterministic_and_preserves_collider():
    library = make_library()
    text = serialize_library(library)
    assert text == serialize_library(library)
    restored = deserialize_library(json.loads(text))
    assert restored == library
    assert restored.resolve("tree").collider.radius == 4

def test_map_content_round_trip_preserves_base_map_and_placements():
    document = MapContentDocument(make_map(), (ContentPlacement("oak-1", "tree", 4.5, -2),))
    text = serialize_map_content(document)
    assert text == serialize_map_content(document)
    restored = deserialize_map_content(json.loads(text))
    assert restored == document

def test_strict_schemas_reject_unknown_fields_versions_and_duplicate_ids():
    payload = json.loads(serialize_library(make_library()))
    payload["surprise"] = True
    with pytest.raises(ContentValidationError):
        deserialize_library(payload)
    payload = json.loads(serialize_library(make_library()))
    payload["schema_version"] = 2
    with pytest.raises(UnsupportedContentVersionError):
        deserialize_library(payload)
    payload = json.loads(serialize_library(make_library()))
    payload["definitions"].append(payload["definitions"][0])
    with pytest.raises(ContentValidationError):
        deserialize_library(payload)

def test_file_storage_create_replace_and_duplicate_json_key_rejection(tmp_path):
    library = make_library()
    path = tmp_path / "library.json"
    save_library_file(library, path)
    assert load_library_file(path) == library
    with pytest.raises(FileExistsError):
        save_library_file(library, path)
    save_library_file(library, path, mode="replace")
    path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    with pytest.raises(Exception):
        load_library_file(path)

def test_map_content_file_round_trip(tmp_path):
    document = MapContentDocument(make_map(), (ContentPlacement("oak-1", "tree", 1, 2),))
    path = tmp_path / "map-content.json"
    save_map_content_file(document, path)
    assert load_map_content_file(path) == document
