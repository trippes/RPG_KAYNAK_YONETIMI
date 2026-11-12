import unittest
from types import SimpleNamespace
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer

class TestHexTerrainRenderer(unittest.TestCase):
    def setUp(self): self.renderer = HexTerrainRenderer()
    def test_pointy_top_polygon_has_six_vertices(self):
        polygon = self.renderer.polygon_for((100, 80), 20)
        self.assertEqual(len(polygon), 6)
        self.assertEqual(polygon[0], (100, 60))
    def test_polygon_rejects_non_positive_radius(self):
        with self.assertRaises(ValueError): self.renderer.polygon_for((0, 0), 0)
    def test_selected_and_blocked_colors(self):
        cell = SimpleNamespace(terrain_id="grass", blocked=True)
        self.assertEqual(self.renderer.color_for(cell, True), self.renderer.SELECTED_COLOR)
        self.assertEqual(self.renderer.color_for(cell), self.renderer.BLOCKED_COLOR)
    def test_unknown_terrain_fallback(self):
        cell = SimpleNamespace(terrain_id="unknown", blocked=False)
        self.assertEqual(self.renderer.color_for(cell), (91, 105, 79))

if __name__ == "__main__": unittest.main()
