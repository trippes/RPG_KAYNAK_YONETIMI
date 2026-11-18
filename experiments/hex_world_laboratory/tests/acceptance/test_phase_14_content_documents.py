"""Acceptance-level round-trip and reference integrity for Phase 14 documents."""
import json
from hex_world_lab.content import ContentPlacement
from hex_world_lab.content.map_document import MapContentDocument
from hex_world_lab.content.persistence import (
    deserialize_library, deserialize_map_content, serialize_library, serialize_map_content,
)
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering.procedural import build_builtin_content_library
from hex_world_lab.world import HexMapDefinition, MapId, WorldId

def test_five_profile_library_and_map_document_round_trip_as_editor_ready_data():
    library = build_builtin_content_library(seed="phase-14-acceptance")
    map_definition = HexMapDefinition(
        WorldId("eldoria"), MapId("content_acceptance"), "Content Acceptance",
        HexLayout(HexOrientation.POINTY_TOP, 24, WorldPoint(0, 0)), {},
    )
    placements = tuple(
        ContentPlacement(f"instance-{index}", item.content_id, index * 12.5, index * -7.0)
        for index, item in enumerate(library.definitions)
    )
    document = MapContentDocument(map_definition, placements)
    restored_library = deserialize_library(json.loads(serialize_library(library)))
    restored_document = deserialize_map_content(json.loads(serialize_map_content(document)))
    restored_document.validate_references(restored_library)
    assert restored_library == library
    assert restored_document == document
    assert len(restored_document.placements) == 5
