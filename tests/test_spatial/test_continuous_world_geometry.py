"""Tests for Eldoria-native continuous point and pointy-top hex transforms."""

import math
import unittest

from core.domain.spatial import (
    ContinuousEntityPosition,
    HexCoord,
    WorldPoint,
    axial_to_world_point,
    world_point_to_fractional_axial,
    world_point_to_hex,
)


class WorldPointTests(unittest.TestCase):
    def test_world_point_is_finite_and_immutable(self):
        point = WorldPoint(2, -3)
        self.assertEqual(point.to_dict(), {"x": 2.0, "y": -3.0})
        with self.assertRaises((AttributeError, TypeError)):
            point.x = 5
        with self.assertRaises(ValueError):
            WorldPoint(math.nan, 0)
        with self.assertRaises(ValueError):
            WorldPoint(0, math.inf)
        with self.assertRaises(TypeError):
            WorldPoint(True, 0)

    def test_continuous_position_is_map_scoped(self):
        position = ContinuousEntityPosition.from_xy("forest", 12.5, 24)
        self.assertEqual((position.map_id, position.x, position.y), ("forest", 12.5, 24.0))
        with self.assertRaises(ValueError):
            ContinuousEntityPosition.from_xy("", 0, 0)


class ContinuousHexGeometryTests(unittest.TestCase):
    HEX_SIZE = 32.0

    def test_axial_center_uses_eldoria_y_down_pointy_top_basis(self):
        point = axial_to_world_point(HexCoord(1, 2), self.HEX_SIZE)
        self.assertAlmostEqual(point.x, self.HEX_SIZE * math.sqrt(3.0) * 2.0)
        self.assertAlmostEqual(point.y, self.HEX_SIZE * 3.0)

    def test_world_to_fractional_axial_is_inverse_of_center_transform(self):
        cell = HexCoord(-3, 2)
        point = axial_to_world_point(cell, self.HEX_SIZE)
        q, r = world_point_to_fractional_axial(point, self.HEX_SIZE)
        self.assertAlmostEqual(q, cell.q)
        self.assertAlmostEqual(r, cell.r)

    def test_world_point_round_trip_to_cell_center(self):
        for cell in (HexCoord(0, 0), HexCoord(1, 0), HexCoord(-2, 3), HexCoord(4, -3)):
            point = axial_to_world_point(cell, self.HEX_SIZE)
            self.assertEqual(world_point_to_hex(point, self.HEX_SIZE), cell)

    def test_previous_cell_wins_only_on_equal_distance_boundary(self):
        left = HexCoord(0, 0)
        right = HexCoord(1, 0)
        left_center = axial_to_world_point(left, self.HEX_SIZE)
        right_center = axial_to_world_point(right, self.HEX_SIZE)
        midpoint = WorldPoint(
            (left_center.x + right_center.x) / 2.0,
            (left_center.y + right_center.y) / 2.0,
        )
        self.assertEqual(world_point_to_hex(midpoint, self.HEX_SIZE), left)
        self.assertEqual(world_point_to_hex(midpoint, self.HEX_SIZE, previous_cell=right), right)
        self.assertEqual(
            world_point_to_hex(WorldPoint(left_center.x + 1.0, left_center.y), self.HEX_SIZE, previous_cell=right),
            left,
        )

    def test_invalid_hex_size_is_rejected(self):
        with self.assertRaises(ValueError):
            axial_to_world_point(HexCoord(0, 0), 0)
        with self.assertRaises(ValueError):
            world_point_to_fractional_axial(WorldPoint(0, 0), math.inf)


if __name__ == "__main__":
    unittest.main()
