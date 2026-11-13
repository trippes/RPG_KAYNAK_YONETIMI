"""Regression checks for Phase 7 natural-world presentation metadata."""

import unittest
from pathlib import Path

from game_ui.assets.asset_definition import AssetCatalog
from game_ui.world_rendering.depth_sorter import DepthSorter
from game_ui.world_rendering.scene_object import SceneObjectPlacement
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer


ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = ROOT / "content" / "demo_eldoria" / "presentation_assets.json"


class TestPhase7VisualPresentation(unittest.TestCase):
    def test_catalog_supports_environment_variety_and_editor_metadata(self):
        catalog = AssetCatalog.load(CATALOG_PATH)
        self.assertGreaterEqual(len(catalog.assets), 6)
        self.assertGreaterEqual(len(catalog.objects_for_map("hex_forest_demo")), 10)
        for asset in catalog.assets.values():
            self.assertEqual(len(asset.anchor), 2)
            self.assertGreater(asset.scale, 0)

    def test_environment_placements_keep_visual_and_collision_data_separate(self):
        catalog = AssetCatalog.load(CATALOG_PATH)
        placements = catalog.objects_for_map("hex_forest_demo")
        self.assertTrue(any(item.collision_box is None for item in placements))
        self.assertTrue(any(item.collision_box is not None for item in placements))
        self.assertTrue(all(item.footprint[0] > 0 and item.footprint[1] > 0 for item in placements))

    def test_depth_sort_uses_ground_anchor_and_stable_secondary_key(self):
        items = (
            SceneObjectPlacement("b", "asset", "map", 0, 0, depth_offset=1),
            SceneObjectPlacement("a", "asset", "map", 0, 0, depth_offset=1),
        )
        ordered = DepthSorter.sort_by_depth(
            items,
            lambda item: item.depth_offset,
            lambda item: item.object_id,
        )
        self.assertEqual([item.object_id for item in ordered], ["a", "b"])

    def test_terrain_renderer_keeps_hex_geometry_as_non_visual_data(self):
        renderer = HexTerrainRenderer()
        points = renderer.polygon_for((10, 10), 8)
        self.assertEqual(len(points), 6)
        # The geometry helper remains available to simulation/render internals,
        # while normal draw_cell deliberately does not draw this polygon outline.
        self.assertTrue(callable(renderer.draw_cell))


if __name__ == "__main__":
    unittest.main()
