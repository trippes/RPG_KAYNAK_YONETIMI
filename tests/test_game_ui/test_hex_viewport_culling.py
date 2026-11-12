import unittest
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer

class TestHexViewportCulling(unittest.TestCase):
    def test_intersecting_hex_is_visible(self):
        self.assertTrue(HexTerrainRenderer.is_visible((-5, 50), 10, 100, 100))
    def test_fully_outside_hex_is_culled(self):
        self.assertFalse(HexTerrainRenderer.is_visible((-20, 50), 10, 100, 100))
        self.assertFalse(HexTerrainRenderer.is_visible((120, 50), 10, 100, 100))
        self.assertFalse(HexTerrainRenderer.is_visible((50, -20), 10, 100, 100))
        self.assertFalse(HexTerrainRenderer.is_visible((50, 120), 10, 100, 100))
    def test_edge_touching_hex_is_visible(self):
        self.assertTrue(HexTerrainRenderer.is_visible((110, 50), 10, 100, 100))

if __name__ == "__main__": unittest.main()
