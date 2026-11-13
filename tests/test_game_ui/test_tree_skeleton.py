"""Tests for reusable sprite-backed tree skeleton geometry."""

import unittest

from game_ui.world_rendering.tree_skeleton import (
    DEFAULT_TREE_SKELETON,
    TreeBranch,
    TreeLeafCluster,
    TreeSkeleton,
)


class TestTreeSkeleton(unittest.TestCase):
    def test_default_skeleton_exposes_separate_visual_and_physical_regions(self):
        skeleton = DEFAULT_TREE_SKELETON
        self.assertNotEqual(skeleton.canopy_bounds, skeleton.trunk_collision)
        self.assertEqual(skeleton.ground_anchor, (0.5, 0.985))
        self.assertEqual(skeleton.depth_anchor, (0.5, 0.955))
        self.assertEqual(skeleton.trunk_collision, (0.39, 0.82, 0.22, 0.16))
        self.assertEqual(skeleton.canopy_bounds, (0.03, 0.02, 0.94, 0.76))

    def test_default_skeleton_contains_branches_and_leaf_clusters(self):
        skeleton = DEFAULT_TREE_SKELETON
        self.assertGreaterEqual(len(skeleton.branches), 2)
        self.assertGreaterEqual(len(skeleton.leaf_clusters), 3)
        self.assertTrue(all(isinstance(item, TreeBranch) for item in skeleton.branches))
        self.assertTrue(all(isinstance(item, TreeLeafCluster) for item in skeleton.leaf_clusters))

    def test_branch_and_leaf_animation_metadata_is_independent_of_png(self):
        branch = TreeBranch((0.5, 0.8), (0.8, 0.4), sway_weight=0.6, phase=1.25)
        leaves = TreeLeafCluster((0.8, 0.4), radius=0.2, sway_weight=1.0, branch_index=0)
        skeleton = TreeSkeleton(branches=(branch,), leaf_clusters=(leaves,))
        self.assertEqual(skeleton.branches[0].end, (0.8, 0.4))
        self.assertEqual(skeleton.leaf_clusters[0].branch_index, 0)
        self.assertEqual(skeleton.leaf_clusters[0].sway_weight, 1.0)

    def test_rejects_invalid_branch_and_leaf_references(self):
        with self.assertRaises(ValueError):
            TreeSkeleton(branches=(TreeBranch((0.5, 0.8), (0.8, 0.4), parent_index=2),))
        with self.assertRaises(ValueError):
            TreeSkeleton(branches=(), leaf_clusters=(TreeLeafCluster((0.5, 0.4), branch_index=1),))

    def test_rejects_out_of_bounds_branch_geometry(self):
        with self.assertRaises(ValueError):
            TreeBranch((0.5, 0.8), (1.2, 0.4))

    def test_png_is_anchored_to_the_same_world_ground_point_at_any_scale(self):
        skeleton = TreeSkeleton()
        self.assertEqual(skeleton.sprite_top_left((100, 100), (100, 200), 0.5), (75.0, 1.5))
        self.assertEqual(skeleton.sprite_top_left((100, 100), (100, 200), 1.0), (50.0, -97.0))

    def test_depth_anchor_uses_scaled_sprite_dimensions(self):
        skeleton = TreeSkeleton()
        self.assertAlmostEqual(skeleton.depth_y((100, 100), (100, 200), 0.5), 97.0)
        self.assertAlmostEqual(skeleton.depth_y((100, 100), (100, 200), 1.0), 94.0)

    def test_trunk_collision_is_independent_from_canopy_dimensions(self):
        skeleton = TreeSkeleton()
        self.assertEqual(
            skeleton.trunk_collision_bounds((100, 100), (100, 200), 0.5),
            (94.5, 83.5, 11.0, 16.0),
        )

    def test_rejects_out_of_bounds_normalized_geometry(self):
        with self.assertRaises(ValueError):
            TreeSkeleton(trunk_collision=(0.9, 0.8, 0.2, 0.3))

    def test_rejects_invalid_sprite_scale(self):
        with self.assertRaises(ValueError):
            DEFAULT_TREE_SKELETON.depth_y((0, 0), (100, 200), 0)


if __name__ == "__main__":
    unittest.main()
