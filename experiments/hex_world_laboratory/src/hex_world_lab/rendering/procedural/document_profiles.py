"""Built-in vector documents for the five established environmental profiles."""

from __future__ import annotations
import math
from hex_world_lab.content.drawing import (
    CircleElement,
    DrawingStyle,
    EllipseElement,
    Layer,
    Point,
    PolygonElement,
    PolylineElement,
    VisualDocument,
)
from hex_world_lab.rendering.procedural.variation import normalize_seed


def _doc(key, size, anchor, palette, layers, seed=0):
    return VisualDocument(
        size,
        anchor,
        anchor,
        palette,
        tuple(layers),
        1,
        {"profile_id": key, "profile_version": 1, "seed": seed},
    )


def build_profile_document(profile_key: str, *, seed: int | str = 0) -> VisualDocument:
    if profile_key not in {"tree", "rock", "bush", "grass", "flower"}:
        raise KeyError(f"unknown procedural profile: {profile_key}")
    normalized = normalize_seed(seed)
    if profile_key == "tree":
        palette = {
            "bark": (91, 57, 38, 255),
            "bark_light": (125, 82, 51, 255),
            "leaf_shadow": (34, 83, 48, 255),
            "leaf": (54, 112, 57, 255),
            "leaf_light": (91, 145, 72, 255),
        }
        trunk = PolygonElement(
            "trunk-main",
            (Point(49, 151), Point(56, 102), Point(72, 48), Point(87, 151)),
            DrawingStyle(fill="bark"),
        )
        trunk_light = PolylineElement(
            "trunk-highlight",
            (Point(60, 137), Point(65, 95), Point(74, 57)),
            DrawingStyle(stroke="bark_light", stroke_width=3),
        )
        canopy = PolygonElement(
            "canopy-main",
            (
                Point(66, 12),
                Point(100, 34),
                Point(126, 79),
                Point(105, 112),
                Point(34, 112),
                Point(8, 76),
                Point(31, 35),
            ),
            DrawingStyle(fill="leaf"),
        )
        leaves = (
            CircleElement("leaf-left", Point(34, 64), 25, DrawingStyle(fill="leaf_shadow")),
            CircleElement("leaf-right", Point(99, 63), 27, DrawingStyle(fill="leaf_shadow")),
            CircleElement("leaf-crown", Point(66, 36), 31, DrawingStyle(fill="leaf_light")),
        )
        return _doc(
            "tree",
            (132, 168),
            (0.5, 0.94),
            palette,
            (Layer("trunk", 0, (trunk, trunk_light)), Layer("canopy", 10, (canopy, *leaves))),
            normalized,
        )
    if profile_key == "rock":
        palette = {
            "shadow": (48, 53, 57, 255),
            "stone": (111, 119, 124, 255),
            "light": (164, 171, 171, 255),
        }
        shapes = (
            PolygonElement(
                "rock-body",
                (
                    Point(4, 39),
                    Point(12, 15),
                    Point(29, 4),
                    Point(53, 10),
                    Point(64, 34),
                    Point(55, 45),
                    Point(15, 47),
                ),
                DrawingStyle(fill="stone"),
            ),
            PolygonElement(
                "rock-highlight",
                (Point(12, 16), Point(29, 4), Point(44, 11), Point(28, 18), Point(18, 31)),
                DrawingStyle(fill="light"),
            ),
        )
        return _doc("rock", (66, 48), (0.5, 0.92), palette, (Layer("rock", 0, shapes),), normalized)
    if profile_key == "bush":
        palette = {
            "shadow": (35, 78, 42, 255),
            "leaf": (57, 119, 61, 255),
            "light": (94, 151, 74, 255),
        }
        elements = (
            EllipseElement("bush-base", 8, 23, 72, 32, DrawingStyle(fill="shadow")),
            CircleElement("bush-left", Point(26, 28), 19, DrawingStyle(fill="leaf")),
            CircleElement("bush-center", Point(46, 20), 22, DrawingStyle(fill="light")),
            CircleElement("bush-right", Point(65, 30), 18, DrawingStyle(fill="leaf")),
        )
        return _doc(
            "bush", (88, 58), (0.5, 0.92), palette, (Layer("foliage", 0, elements),), normalized
        )
    if profile_key == "grass":
        palette = {
            "shadow": (48, 76, 43, 150),
            "blade": (47, 103, 54, 255),
            "light": (91, 145, 72, 255),
        }
        elements = [EllipseElement("ground-shadow", 7, 27, 50, 8, DrawingStyle(fill="shadow"))]
        # A local deterministic sequence derived from the normalized seed.
        state = (normalized ^ 0x9E3779B9) & 0xFFFFFFFF
        for index in range(17):
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            x = 5 + (state % 5400) / 100
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            height = 9 + (state % 1500) / 100
            state = (1664525 * state + 1013904223) & 0xFFFFFFFF
            lean = -5 + (state % 1000) / 100
            token = "light" if index % 4 == 0 else "blade"
            elements.append(
                PolygonElement(
                    f"blade-{index}",
                    (
                        Point(x, 31),
                        Point(x - 1, 31 - height * 0.42),
                        Point(x + lean, 31 - height),
                        Point(x + 1, 31 - height * 0.42),
                    ),
                    DrawingStyle(fill=token),
                )
            )
        return _doc(
            "grass",
            (64, 36),
            (0.5, 0.94),
            palette,
            (Layer("grass", 0, tuple(elements)),),
            normalized,
        )
    palette = {
        "stem": (55, 112, 59, 255),
        "leaf": (54, 112, 57, 255),
        "pink": (225, 125, 115, 255),
        "gold": (238, 190, 90, 255),
        "violet": (178, 145, 218, 255),
        "center": (245, 215, 105, 255),
    }
    elements = []
    for index, x in enumerate((14, 28, 42)):
        top_y = 10 + ((normalized >> (index * 5)) & 7)
        top_x = x + ((normalized >> (index * 3)) % 5) - 2
        elements.append(
            PolylineElement(
                f"stem-{index}",
                (Point(x, 41), Point((x + top_x) / 2, 28), Point(top_x, top_y)),
                DrawingStyle(stroke="stem", stroke_width=1),
            )
        )
        elements.append(
            EllipseElement(
                f"leaf-{index}",
                x - 5 if index % 2 == 0 else x + 1,
                30,
                7,
                3,
                DrawingStyle(fill="leaf"),
            )
        )
        token = ("pink", "gold", "violet")[index]
        for petal in range(5):
            angle = petal * math.tau / 5
            elements.append(
                CircleElement(
                    f"petal-{index}-{petal}",
                    Point(top_x + 3.2 * math.cos(angle), top_y + 3.2 * math.sin(angle)),
                    2.2,
                    DrawingStyle(fill=token),
                )
            )
        elements.append(
            CircleElement(f"center-{index}", Point(top_x, top_y), 1.5, DrawingStyle(fill="center"))
        )
    return _doc(
        "flower",
        (56, 48),
        (0.5, 0.94),
        palette,
        (Layer("flowers", 0, tuple(elements)),),
        normalized,
    )
