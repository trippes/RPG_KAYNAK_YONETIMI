"""Vector-document equivalents of all five accepted procedural art profiles."""

from __future__ import annotations

import math

from hex_world_lab.content.definition import ContentCategory, ContentDefinition
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
from hex_world_lab.content.library import ContentLibrary
from hex_world_lab.rendering._procedural_environment_legacy import (
    DEFAULT_PALETTE,
    EnvironmentArtPalette,
)

from .variation import create_rng, normalize_seed


class _DocumentBuilder:
    """Collect ordered vector elements and a stable color-token table."""

    def __init__(self):
        self.palette = {}
        self._tokens = {}
        self._layers = {}

    def _token(self, color):
        color = tuple(color)
        if color not in self._tokens:
            token = f"color_{len(self._tokens):03d}"
            self._tokens[color] = token
            self.palette[token] = color
        return self._tokens[color]

    def _add(self, layer_id, order, element):
        self._layers.setdefault((order, layer_id), []).append(element)

    def ellipse(self, layer, order, element_id, color, rect):
        x, y, width, height = rect
        self._add(
            layer,
            order,
            EllipseElement(element_id, x, y, width, height, DrawingStyle(fill=self._token(color))),
        )

    def polygon(self, layer, order, element_id, color, points, width=0):
        points = tuple(Point(x, y) for x, y in points)
        if width:
            style = DrawingStyle(stroke=self._token(color), stroke_width=width)
        else:
            style = DrawingStyle(fill=self._token(color))
        self._add(layer, order, PolygonElement(element_id, points, style))

    def line(self, layer, order, element_id, color, points, width=1):
        self._add(
            layer,
            order,
            PolylineElement(
                element_id,
                tuple(Point(x, y) for x, y in points),
                DrawingStyle(stroke=self._token(color), stroke_width=width),
            ),
        )

    def circle(self, layer, order, element_id, color, center, radius):
        self._add(
            layer,
            order,
            CircleElement(
                element_id, Point(*center), radius, DrawingStyle(fill=self._token(color))
            ),
        )

    def finish(self, key, size, ground_anchor, depth_anchor, seed):
        layers = tuple(
            Layer(layer_id, order, tuple(elements))
            for (order, layer_id), elements in sorted(self._layers.items())
        )
        return VisualDocument(
            size,
            ground_anchor,
            depth_anchor,
            self.palette,
            layers,
            1,
            {"profile_id": key, "profile_version": 1, "seed": seed},
        )


def _tree(builder, palette):
    # Ground contact, roots, trunk, branches and bark details.
    builder.ellipse("ground-trunk", 0, "ground-shadow", palette.ground_shadow, (22, 145, 88, 15))
    builder.polygon(
        "ground-trunk",
        0,
        "root-left",
        (73, 45, 31),
        [(54, 147), (43, 158), (31, 159), (42, 151), (48, 143)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "root-right",
        (92, 58, 36),
        [(65, 147), (77, 157), (94, 159), (81, 150), (74, 142)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "root-center",
        (111, 73, 43),
        [(58, 145), (51, 155), (44, 157), (55, 148)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "trunk-base",
        palette.bark_base,
        [
            (49, 151),
            (54, 111),
            (52, 82),
            (45, 57),
            (55, 48),
            (66, 74),
            (72, 48),
            (82, 54),
            (76, 89),
            (81, 119),
            (87, 151),
            (72, 156),
            (63, 151),
        ],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "trunk-light",
        palette.bark_light,
        [(53, 149), (58, 111), (57, 81), (50, 58), (56, 53), (64, 83), (67, 119), (68, 151)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "trunk-shadow",
        (83, 47, 31),
        [(68, 151), (70, 115), (68, 82), (74, 56), (81, 57), (77, 91), (81, 121), (87, 151)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "branch-left",
        (83, 48, 30),
        [(61, 103), (53, 79), (36, 64), (31, 51), (39, 61), (58, 73), (68, 95)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "branch-right",
        (100, 59, 34),
        [(70, 96), (82, 74), (99, 61), (104, 47), (101, 64), (84, 84), (77, 105)],
    )
    builder.polygon(
        "ground-trunk",
        0,
        "branch-top",
        (91, 51, 31),
        [(62, 83), (61, 59), (51, 43), (55, 37), (68, 59), (70, 82)],
    )
    builder.line(
        "ground-trunk",
        0,
        "bark-line-light",
        (183, 119, 65),
        [(57, 137), (61, 119), (60, 103), (64, 91)],
        2,
    )
    builder.line(
        "ground-trunk", 0, "bark-line-shadow", (47, 31, 25), [(76, 137), (73, 119), (76, 105)], 2
    )
    builder.line(
        "ground-trunk", 0, "root-line-left", (151, 91, 49), [(54, 151), (45, 156), (39, 156)], 2
    )
    builder.line(
        "ground-trunk", 0, "root-line-right", (57, 35, 27), [(78, 151), (87, 157), (92, 157)], 2
    )
    builder.ellipse("ground-trunk", 0, "bark-knot-shadow", (54, 31, 25), (61, 116, 5, 8))
    builder.ellipse("ground-trunk", 0, "bark-knot-light", (179, 112, 61), (62, 118, 2, 3))

    shadows = [
        (15, 54, 47, 48, palette.tree_leaf_shadow),
        (37, 27, 55, 57, palette.tree_leaf_shadow),
        (67, 18, 49, 53, palette.tree_leaf_shadow),
        (88, 43, 34, 46, palette.tree_leaf_shadow),
        (7, 83, 48, 43, palette.tree_leaf_shadow),
        (39, 75, 58, 57, palette.tree_leaf_shadow),
        (78, 82, 47, 47, palette.tree_leaf_shadow),
        (26, 112, 45, 28, palette.tree_leaf_shadow),
    ]
    for index, (x, y, w, h, color) in enumerate(shadows):
        builder.ellipse("canopy-shadow", 10, f"leaf-shadow-{index}", color, (x, y, w, h))
    lit = [
        (23, 60, 31, 29, palette.tree_leaf_mid),
        (45, 34, 35, 35, palette.tree_leaf_light),
        (75, 29, 29, 31, palette.tree_leaf_mid),
        (91, 55, 22, 27, palette.tree_leaf_mid),
        (14, 88, 29, 25, palette.tree_leaf_mid),
        (45, 83, 35, 34, palette.tree_leaf_light),
        (78, 91, 29, 27, palette.tree_leaf_mid),
    ]
    for index, (x, y, w, h, color) in enumerate(lit):
        builder.ellipse("canopy-light", 20, f"leaf-lit-{index}", color, (x, y, w, h))
    for index, (x, y, w, h) in enumerate(
        (
            (31, 67, 8, 5),
            (48, 47, 10, 6),
            (68, 35, 8, 5),
            (89, 57, 7, 5),
            (21, 95, 8, 5),
            (52, 91, 9, 5),
            (78, 102, 8, 5),
            (39, 119, 7, 4),
        )
    ):
        builder.ellipse(
            "canopy-detail", 30, f"leaf-glint-{index}", palette.leaf_glint, (x, y, w, h)
        )
    for index, (x, y) in enumerate(((39, 76), (69, 68), (93, 83), (55, 112))):
        builder.ellipse("canopy-detail", 30, f"leaf-deep-{index}", (25, 65, 38), (x, y, 9, 7))


def _rock(builder, palette):
    builder.ellipse("ground", 0, "ground-shadow", palette.ground_shadow, (5, 34, 57, 10))
    silhouette = [
        (5, 31),
        (9, 18),
        (20, 8),
        (34, 5),
        (47, 12),
        (61, 25),
        (57, 37),
        (43, 42),
        (17, 40),
    ]
    builder.polygon("rock-body", 10, "rock-silhouette", palette.rock_base, silhouette)
    builder.polygon(
        "rock-body",
        10,
        "rock-upper-left",
        palette.rock_light,
        [(9, 20), (20, 8), (34, 5), (29, 22), (18, 30), (5, 31)],
    )
    builder.polygon(
        "rock-body",
        10,
        "rock-upper-right",
        (105, 119, 132),
        [(34, 5), (47, 12), (61, 25), (43, 27), (29, 22)],
    )
    builder.polygon(
        "rock-body",
        10,
        "rock-lower",
        (72, 84, 99),
        [(5, 31), (18, 30), (29, 22), (43, 27), (57, 37), (43, 42), (17, 40)],
    )
    builder.polygon(
        "rock-detail",
        20,
        "rock-highlight",
        palette.rock_light,
        [(20, 8), (34, 5), (29, 14), (17, 18)],
    )
    builder.polygon(
        "rock-detail",
        20,
        "rock-shadow",
        palette.rock_shadow,
        [(43, 27), (61, 25), (57, 37), (43, 42), (38, 33)],
    )
    builder.polygon("rock-detail", 20, "rock-outline", (33, 40, 51), silhouette, 1)
    builder.line(
        "rock-detail", 20, "rock-edge-dark", (74, 87, 102), [(29, 22), (38, 33), (43, 42)], 2
    )
    builder.line(
        "rock-detail", 20, "rock-edge-light", (192, 200, 205), [(12, 20), (21, 12), (28, 10)], 1
    )
    builder.line("rock-detail", 20, "rock-crack", (58, 69, 82), [(17, 31), (26, 35)], 1)
    builder.circle("rock-detail", 20, "rock-speck-light", (205, 211, 210), (23, 17), 1)
    builder.circle("rock-detail", 20, "rock-speck-mid", (120, 132, 143), (49, 28), 1)


def _bush(builder, palette):
    builder.ellipse("ground", 0, "ground-shadow", palette.ground_shadow, (8, 43, 72, 12))
    builder.ellipse("foliage-base", 10, "bush-base-shadow", (25, 68, 39), (7, 19, 72, 34))
    masses = [
        (8, 21, 31, 29, palette.bush_base),
        (20, 10, 34, 36, palette.bush_base),
        (43, 13, 35, 35, palette.bush_base),
        (54, 26, 27, 25, palette.bush_base),
        (27, 27, 34, 27, palette.bush_light),
        (4, 32, 29, 20, palette.bush_base),
    ]
    for index, (x, y, w, h, color) in enumerate(masses):
        builder.ellipse("foliage-masses", 20, f"bush-mass-{index}", color, (x, y, w, h))
    for index, (x, y, w, h) in enumerate(
        (
            (17, 23, 12, 8),
            (31, 15, 13, 8),
            (51, 19, 10, 7),
            (29, 34, 12, 7),
            (62, 31, 8, 6),
            (10, 38, 9, 5),
        )
    ):
        builder.ellipse(
            "foliage-highlights", 30, f"bush-highlight-{index}", palette.bush_light, (x, y, w, h)
        )
    for index, (x, y) in enumerate(((27, 30), (48, 38), (65, 28))):
        builder.ellipse("foliage-highlights", 30, f"bush-deep-{index}", (24, 65, 37), (x, y, 5, 4))


def _grass(builder, seed, palette):
    rng = create_rng(f"grass:{seed}")
    builder.ellipse("ground", 0, "ground-shadow", palette.ground_shadow, (7, 27, 50, 8))
    base, mid, light = palette.tree_leaf_shadow, palette.tree_leaf_mid, palette.tree_leaf_light
    for index in range(17):
        x = rng.uniform(5, 59)
        height = rng.uniform(9, 24)
        lean = rng.uniform(-5, 5)
        blade_width = rng.uniform(1.0, 2.8)
        points = (
            (x, 31),
            (x - blade_width, 31 - height * 0.42),
            (x + lean, 31 - height),
            (x + blade_width, 31 - height * 0.42),
        )
        color = rng.choice((base, mid, light))
        builder.polygon("grass-blades", 10, f"blade-{index}", color, points)


def _flower(builder, seed, palette):
    rng = create_rng(f"flower:{seed}")
    builder.ellipse("ground", 0, "ground-shadow", palette.ground_shadow, (5, 38, 46, 8))
    stem_color = (55, 112, 59)
    leaf_color = palette.tree_leaf_mid
    flower_colors = ((225, 125, 115), (238, 190, 90), (178, 145, 218))
    for index, x in enumerate((14.0, 28.0, 42.0)):
        height = rng.uniform(20, 29)
        top = (x + rng.uniform(-2, 2), 39 - height)
        root = (x, 41)
        bend = ((x + top[0]) / 2 + rng.uniform(-2, 2), 28)
        builder.line("flower-parts", 10, f"stem-{index}", stem_color, (root, bend, top), 1)
        leaf_y = rng.uniform(29, 34)
        builder.ellipse(
            "flower-parts",
            10,
            f"leaf-{index}",
            leaf_color,
            (x - 7 if index % 2 == 0 else x + 1, leaf_y, 7, 3),
        )
        color = flower_colors[index]
        for petal in range(5):
            angle = petal * math.tau / 5
            center = (top[0] + 3.2 * math.cos(angle), top[1] + 3.2 * math.sin(angle))
            builder.circle("flower-parts", 10, f"petal-{index}-{petal}", color, center, 2.2)
        builder.circle("flower-parts", 10, f"center-{index}", (245, 215, 105), top, 1.5)


def build_profile_document(
    profile_key: str,
    *,
    seed: int | str = 0,
    palette: EnvironmentArtPalette | None = None,
) -> VisualDocument:
    """Build the editable vector source of a profile using the legacy pixel geometry."""
    if profile_key not in {"tree", "rock", "bush", "grass", "flower"}:
        raise KeyError(f"unknown procedural profile: {profile_key}")
    normalized = normalize_seed(seed)
    selected_palette = DEFAULT_PALETTE if palette is None else palette
    if not isinstance(selected_palette, EnvironmentArtPalette):
        raise TypeError("palette must be an EnvironmentArtPalette")
    builder = _DocumentBuilder()
    if profile_key == "tree":
        size, ground, depth = (132, 168), (0.5, 0.94), (0.5, 0.80)
        _tree(builder, selected_palette)
    elif profile_key == "rock":
        size, ground, depth = (66, 48), (0.5, 0.92), (0.5, 0.86)
        _rock(builder, selected_palette)
    elif profile_key == "bush":
        size, ground, depth = (88, 58), (0.5, 0.92), (0.5, 0.84)
        _bush(builder, selected_palette)
    elif profile_key == "grass":
        size, ground, depth = (64, 36), (0.5, 0.94), (0.5, 0.94)
        _grass(builder, normalized, selected_palette)
    else:
        size, ground, depth = (56, 48), (0.5, 0.94), (0.5, 0.94)
        _flower(builder, normalized, selected_palette)
    return builder.finish(profile_key, size, ground, depth, normalized)


def build_builtin_content_library(*, seed: int | str = 0) -> ContentLibrary:
    """Create the stable five-profile library used by Phase 14 examples and tests."""
    definitions = tuple(
        ContentDefinition(
            content_id=f"environment.{key}",
            name=key.replace("_", " ").title(),
            category=ContentCategory.ENVIRONMENTAL_OBJECT,
            visual_document=build_profile_document(key, seed=seed),
            collider=None,
            metadata={"source": "procedural_profile", "profile_id": key},
        )
        for key in ("tree", "rock", "bush", "grass", "flower")
    )
    return ContentLibrary("eldoria.environment.v1", definitions)
