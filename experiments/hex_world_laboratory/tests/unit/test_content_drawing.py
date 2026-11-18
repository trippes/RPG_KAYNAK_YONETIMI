"""Immutable visual document contract tests."""

import pytest
from hex_world_lab.content import (
    CircleElement,
    ContentCategory,
    ContentDefinition,
    ContentLibrary,
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


def test_visual_document_sorts_layers_and_freezes_palette_and_generator():
    palette = {"green": [30, 120, 50, 255], "brown": [90, 55, 30, 255]}
    doc = make_visual()
    assert [layer.layer_id for layer in doc.layers] == ["base"]
    assert doc.palette["green"] == (30, 120, 50, 255)
    with pytest.raises(TypeError):
        doc.palette["green"] = (0, 0, 0)
    with pytest.raises(ValueError):
        VisualDocument((0, 20), (0.5, 1), (0.5, 1), palette, (), 1)


def test_visual_document_rejects_duplicate_layer_and_element_ids():
    layer = Layer("same", 0, ())
    with pytest.raises(ValueError):
        VisualDocument((10, 10), (0.5, 1), (0.5, 1), {"x": (1, 2, 3)}, (layer, layer))
    element = PolygonElement(
        "same", (Point(0, 0), Point(1, 0), Point(0, 1)), DrawingStyle(fill="x")
    )
    with pytest.raises(ValueError):
        VisualDocument(
            (10, 10),
            (0.5, 1),
            (0.5, 1),
            {"x": (1, 2, 3)},
            (Layer("a", 0, (element,)), Layer("b", 1, (element,))),
        )


def test_visual_document_rejects_unknown_palette_tokens_and_nonfinite_geometry():
    with pytest.raises(ValueError):
        VisualDocument(
            (10, 10),
            (0.5, 1),
            (0.5, 1),
            {"x": (1, 2, 3)},
            (
                Layer(
                    "a",
                    0,
                    (
                        PolygonElement(
                            "p",
                            (Point(0, 0), Point(1, 0), Point(0, 1)),
                            DrawingStyle(fill="missing"),
                        ),
                    ),
                ),
            ),
        )
    with pytest.raises(ValueError):
        Point(float("nan"), 0)


def test_explicit_collider_types_validate_independently_of_visual_shapes():
    definition = make_definition(CircleCollider(1, 2, 3))
    assert definition.collider.radius == 3
    assert make_definition().collider is None
    with pytest.raises(ValueError):
        CircleCollider(0, 0, 0)
    with pytest.raises(ValueError):
        ConvexPolygonCollider(((0, 0), (1, 1), (0, 0)))
