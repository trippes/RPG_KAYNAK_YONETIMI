"""Content library, reference integrity, and immutable placement operations."""

import pytest
from hex_world_lab.content import (
    CircleElement,
    ContentCategory,
    ContentDefinition,
    ContentLibrary,
    ContentPlacement,
    DrawingStyle,
    Layer,
    Point,
    PolygonElement,
    VisualDocument,
)
from hex_world_lab.content.collision import CircleCollider, ConvexPolygonCollider


def make_visual():
    return VisualDocument(
        (32, 40),
        (0.5, 0.95),
        (0.5, 0.8),
        {"green": (30, 120, 50, 255), "brown": (90, 55, 30, 255)},
        (
            Layer(
                "base",
                0,
                (
                    PolygonElement(
                        "trunk",
                        (Point(12, 35), Point(15, 12), Point(18, 35)),
                        DrawingStyle(fill="brown"),
                    ),
                    CircleElement("crown", Point(15, 10), 8, DrawingStyle(fill="green")),
                ),
            ),
        ),
    )


def make_definition(content_id="tree", collider=None):
    return ContentDefinition(
        content_id,
        "Tree",
        ContentCategory.ENVIRONMENTAL_OBJECT,
        make_visual(),
        collider,
        {"biome": "forest"},
    )


def make_library():
    return ContentLibrary("default", (make_definition(collider=CircleCollider(0, 0, 4)),))


from hex_world_lab.content.map_document import MapContentDocument
from hex_world_lab.rendering.procedural import build_builtin_content_library
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexMapDefinition, MapId, WorldId


def make_map():
    return HexMapDefinition(
        WorldId("eldoria"),
        MapId("valley"),
        "Valley",
        HexLayout(HexOrientation.POINTY_TOP, 1, WorldPoint(0, 0)),
        {},
    )


def test_builtin_content_library_exposes_all_five_stable_profile_ids():
    library = build_builtin_content_library(seed=42)
    assert {item.content_id for item in library.definitions} == {
        "environment.tree", "environment.rock", "environment.bush",
        "environment.grass", "environment.flower",
    }
    assert all(item.collider is None for item in library.definitions)

def test_library_resolves_stable_ids_and_rejects_duplicates():
    library = make_library()
    assert library.resolve("tree").name == "Tree"
    with pytest.raises(KeyError):
        library.resolve("missing")
    with pytest.raises(ValueError):
        ContentLibrary("duplicate", (make_definition(), make_definition()))


def test_map_document_add_update_remove_are_immutable_and_reference_checked():
    library = make_library()
    empty = MapContentDocument(make_map())
    placed = empty.add_placement(ContentPlacement("tree-1", "tree", 10, 20), library)
    assert empty.placements == ()
    assert placed.placements[0].x == 10
    moved = placed.update_placement("tree-1", x=25, y=30)
    assert (moved.placements[0].x, moved.placements[0].y) == (25, 30)
    removed = moved.remove_placement("tree-1")
    assert removed.placements == ()
    assert moved.placements
    with pytest.raises(KeyError):
        empty.add_placement(ContentPlacement("bad", "unknown", 0, 0), library)


def test_map_document_rejects_duplicate_instance_ids_and_missing_reference():
    library = make_library()
    with pytest.raises(ValueError):
        MapContentDocument(
            make_map(),
            (ContentPlacement("same", "tree", 0, 0), ContentPlacement("same", "tree", 1, 1)),
        )
    document = MapContentDocument(make_map(), (ContentPlacement("one", "missing", 0, 0),))
    with pytest.raises(KeyError):
        document.validate_references(library)
    with pytest.raises(KeyError):
        document.remove_placement("not-there")
