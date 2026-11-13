"""Tests for reusable sprite-backed tree skeleton geometry."""

import unittest

from game_ui.world_rendering.tree_skeleton import (
    DEFAULT_TREE_SKELETON,
    TreeSkeleton,
)


class TestTreeSkeleton(unittest.TestCase):
    def test_default_skeleton_exposes_separate_visual_and_physical_regions(self):
        skeleton = DEFAULT_TREE_SKELETON
        self.assertNotEqual(skeleton.canopy_bounds, skeleton.trunk_collision)
        self.assertEqual(skeleton.ground_anchor, (0.5, 1.0))
        self.assertEqual(skeleton.depth_anchor, (0.5, 0.96))

    def test_png_is_anchored_to_the_same_world_ground_point_at_any_scale(self):
        skeleton = TreeSkeleton()
        self.assertEqual(skeleton.sprite_top_left((100, 100), (100, 200), 0.5), (75.0, 0.0))
        self.assertEqual(skeleton.sprite_top_left((100, 100), (100, 200), 1.0), (50.0, -100.0))

    def test_depth_anchor_uses_scaled_sprite_dimensions(self):
        skeleton = TreeSkeleton()
        self.assertAlmostEqual(skeleton.depth_y((100, 100), (100, 200), 0.5), 96.0)
        self.assertAlmostEqual(skeleton.depth_y((100, 100), (100, 200), 1.0), 92.0)

    def test_trunk_collision_is_independent_from_canopy_dimensions(self):
        skeleton = TreeSkeleton()
        self.assertEqual(
            skeleton.trunk_collision_bounds((100, 100), (100, 200), 0.5),
            (95.0, 78.0, 10.0, 20.0),
        )

    def test_rejects_out_of_bounds_normalized_geometry(self):
        with self.assertRaises(ValueError):
            TreeSkeleton(trunk_collision=(0.9, 0.8, 0.2, 0.3))

    def test_rejects_invalid_sprite_scale(self):
        with self.assertRaises(ValueError):
            DEFAULT_TREE_SKELETON.depth_y((0, 0), (100, 200), 0)


if __name__ == "__main__":
    unittest.main()
