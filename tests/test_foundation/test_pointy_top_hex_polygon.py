import math
import unittest

from core.domain.spatial import (
    HexCoord,
    WorldPoint,
    axial_to_world_point,
    pointy_top_hex_corners,
)


class TestPointyTopHexPolygon(unittest.TestCase):
    def test_corners_start_at_top_and_follow_clockwise_order(self):
        corners = pointy_top_hex_corners(HexCoord(0, 0), 10.0)
        self.assertEqual(len(corners), 6)
        expected = (
            (0.0, -10.0),
            (math.sqrt(3.0) * 5.0, -5.0),
            (math.sqrt(3.0) * 5.0, 5.0),
            (0.0, 10.0),
            (-math.sqrt(3.0) * 5.0, 5.0),
            (-math.sqrt(3.0) * 5.0, -5.0),
        )
        for point, (x, y) in zip(corners, expected):
            self.assertAlmostEqual(point.x, x)
            self.assertAlmostEqual(point.y, y)

    def test_polygon_uses_existing_hex_world_origin_and_center_geometry(self):
        origin = WorldPoint(17.0, -23.0)
        corners = pointy_top_hex_corners(HexCoord(1, -2), 12, origin)
        center = axial_to_world_point(HexCoord(1, -2), 12, origin)
        self.assertAlmostEqual(sum(point.x for point in corners) / 6.0, center.x)
        self.assertAlmostEqual(sum(point.y for point in corners) / 6.0, center.y)

    def test_invalid_polygon_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            pointy_top_hex_corners((0, 0), 32)
        with self.assertRaises(TypeError):
            pointy_top_hex_corners(HexCoord(0, 0), 32, (0, 0))


if __name__ == "__main__":
    unittest.main()
