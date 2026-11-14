"""Executable contract tests for presentation geometry metadata."""

import math
import unittest

from game_ui.assets.asset_definition import (
    MAX_DRAW_SCALE,
    MIN_DRAW_SCALE,
    AssetCatalogError,
    AssetDefinition,
)
from game_ui.world_rendering.scene_object import (
    SCENE_LAYER_ORDER,
    SceneObject,
    SceneObjectPlacement,
)


class TestSceneObjectPlacementGeometryContract(unittest.TestCase):
    def make_placement(self, **overrides):
        values = {
            "object_id": "tree-01",
            "asset_id": "flora.tree",
            "map_id": "hex_forest",
            "q": 2,
            "r": -1,
        }
        values.update(overrides)
        return SceneObjectPlacement(**values)

    def test_offsets_and_depth_are_finite_world_pixel_values(self):
        placement = self.make_placement(offset_x=-7.5, offset_y=4, depth_offset=-1.25)
        self.assertEqual(
            (placement.offset_x, placement.offset_y, placement.depth_offset),
            (-7.5, 4.0, -1.25),
        )
        for field in ("offset_x", "offset_y", "depth_offset"):
            with self.subTest(field=field):
                with self.assertRaises((TypeError, ValueError)):
                    self.make_placement(**{field: math.inf})

    def test_axial_cell_coordinates_are_integers_not_booleans(self):
        with self.assertRaises(TypeError):
            self.make_placement(q=True)

    def test_footprint_is_positive_map_cell_dimensions(self):
        placement = self.make_placement(footprint=(2, 3))
        self.assertEqual(placement.footprint, (2, 3))
        with self.assertRaises(ValueError):
            self.make_placement(footprint=(1, 0))

    def test_collision_box_is_local_pixel_aabb_with_positive_area(self):
        placement = self.make_placement(collision_box=(-8, -14, 16, 14))
        self.assertEqual(placement.collision_box, (-8.0, -14.0, 16.0, 14.0))
        self.assertIsNone(self.make_placement(collision_box=None).collision_box)
        for box in ((0, 0, 0, 2), (0, 0, 2, -1), (0, 0, math.nan, 2)):
            with self.subTest(box=box):
                with self.assertRaises(ValueError):
                    self.make_placement(collision_box=box)

    def test_only_declared_scene_layers_are_accepted(self):
        for layer in SCENE_LAYER_ORDER:
            self.assertEqual(self.make_placement(layer=layer).layer, layer)
        with self.assertRaises(ValueError):
            self.make_placement(layer="background")


class TestResolvedSceneObjectGeometryContract(unittest.TestCase):
    def make_object(self, **overrides):
        values = {
            "object_id": "tree-01",
            "asset_id": "flora.tree",
            "world_x": 100,
            "world_y": 200,
            "visual_width": 80,
            "visual_height": 120,
            "anchor_x": 0.5,
            "anchor_y": 1.0,
        }
        values.update(overrides)
        return SceneObject(**values)

    def test_anchor_is_normalized_and_visual_bounds_use_scaled_dimensions(self):
        obj = self.make_object()
        self.assertEqual(obj.visual_bounds, (60.0, 80.0, 140.0, 200.0))
        with self.assertRaises(ValueError):
            self.make_object(anchor_x=1.01)

    def test_collision_box_is_independent_from_visual_bounds(self):
        obj = self.make_object(collision_box=(-8, -14, 16, 14))
        self.assertEqual(obj.visual_bounds, (60.0, 80.0, 140.0, 200.0))
        self.assertEqual(obj.collision_box, (-8.0, -14.0, 16.0, 14.0))
        with self.assertRaises(ValueError):
            self.make_object(collision_box=(0, 0, 0, 10))

    def test_visual_geometry_rejects_non_finite_values(self):
        with self.assertRaises(TypeError):
            self.make_object(world_y=math.nan)
        with self.assertRaises(TypeError):
            self.make_object(depth_offset=math.inf)


class TestAssetMetadataGeometryContract(unittest.TestCase):
    def make_asset(self, **overrides):
        values = {
            "asset_id": "flora.tree",
            "path": "assets/tree.png",
            "width": 0,
            "height": 0,
            "scale": 1.0,
            "anchor": (0.5, 1.0),
        }
        values.update(overrides)
        return AssetDefinition(**values)

    def test_draw_scale_has_documented_inclusive_technical_bounds(self):
        self.assertEqual(self.make_asset(scale=MIN_DRAW_SCALE).scale, MIN_DRAW_SCALE)
        self.assertEqual(self.make_asset(scale=MAX_DRAW_SCALE).scale, MAX_DRAW_SCALE)
        for scale in (0, -1, MIN_DRAW_SCALE / 10, MAX_DRAW_SCALE * 2, math.inf):
            with self.subTest(scale=scale):
                with self.assertRaises(AssetCatalogError):
                    self.make_asset(scale=scale)

    def test_anchor_is_normalized_and_stored_as_immutable_float_pair(self):
        asset = self.make_asset(anchor=(0, 1))
        self.assertEqual(asset.anchor, (0.0, 1.0))
        with self.assertRaises(AssetCatalogError):
            self.make_asset(anchor=(0.5, 1.1))

    def test_collision_is_optional_but_must_have_positive_pixel_area(self):
        self.assertIsNone(self.make_asset(collision=None).collision)
        self.assertEqual(
            self.make_asset(collision=(-8, -14, 16, 14)).collision,
            (-8.0, -14.0, 16.0, 14.0),
        )
        with self.assertRaises(AssetCatalogError):
            self.make_asset(collision=(0, 0, 0, 14))


class TestPresentationLayerOrder(unittest.TestCase):
    def test_layer_order_is_explicit_and_stable(self):
        self.assertEqual(
            dict(SCENE_LAYER_ORDER),
            {"underlay": 0, "ground": 1, "canopy": 2, "overlay": 3},
        )


if __name__ == "__main__":
    unittest.main()
