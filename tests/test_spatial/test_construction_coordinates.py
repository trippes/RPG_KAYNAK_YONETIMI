"""Tests for map-scoped construction coordinates and snapping."""
import math
import unittest

from core.domain.spatial import (
    ConstructionPosition,
    ConstructionSnapPolicy,
    ConstructionSpaceTransform,
    HexCoord,
    WorldPoint,
)


class ConstructionPositionTests(unittest.TestCase):
    def test_position_is_map_scoped_and_normalizes_rotation(self):
        position = ConstructionPosition("village", WorldPoint(12.5, -4), 2.0, 450)
        self.assertEqual(position.map_id, "village")
        self.assertEqual(position.point, WorldPoint(12.5, -4))
        self.assertEqual(position.elevation, 2.0)
        self.assertEqual(position.rotation_degrees, 90.0)

    def test_position_rejects_invalid_map_point_and_non_finite_values(self):
        with self.assertRaises(ValueError):
            ConstructionPosition("", WorldPoint(0, 0))
        with self.assertRaises(TypeError):
            ConstructionPosition("village", (0, 0))
        with self.assertRaises(ValueError):
            ConstructionPosition("village", WorldPoint(0, 0), math.inf)

    def test_translation_and_rotation_return_new_positions(self):
        original = ConstructionPosition("village", WorldPoint(1, 2), 1, 350)
        moved = original.translated(3, -2, dz=0.5).rotated(20)
        self.assertEqual(original.point, WorldPoint(1, 2))
        self.assertEqual(moved.point, WorldPoint(4, 0))
        self.assertEqual(moved.elevation, 1.5)
        self.assertEqual(moved.rotation_degrees, 10.0)


class ConstructionSnapPolicyTests(unittest.TestCase):
    def test_position_and_rotation_snap_deterministically(self):
        policy = ConstructionSnapPolicy(10, 5, 90)
        position = ConstructionPosition("village", WorldPoint(14, -13), 2, 46)
        snapped = policy.apply(position)
        self.assertEqual(snapped.point, WorldPoint(10, -15))
        self.assertEqual(snapped.elevation, 2)
        self.assertEqual(snapped.rotation_degrees, 90)

    def test_zero_steps_preserve_values_and_negative_steps_are_rejected(self):
        position = ConstructionPosition("village", WorldPoint(-2.25, 3.75), 1, 17)
        self.assertEqual(ConstructionSnapPolicy().apply(position), position)
        with self.assertRaises(ValueError):
            ConstructionSnapPolicy(step_x=-1)

    def test_half_steps_round_away_from_zero(self):
        policy = ConstructionSnapPolicy(step_x=2, step_y=2)
        snapped = policy.apply(
            ConstructionPosition("village", WorldPoint(1, -1))
        )
        self.assertEqual(snapped.point, WorldPoint(2, -2))


class ConstructionSpaceTransformTests(unittest.TestCase):
    def test_hex_cell_center_round_trips_to_same_construction_position(self):
        transform = ConstructionSpaceTransform(
            "village", 32, WorldPoint(100, 200)
        )
        for cell in (HexCoord(0, 0), HexCoord(1, -2), HexCoord(-3, 4)):
            position = transform.hex_to_position(cell)
            self.assertEqual(position.map_id, "village")
            self.assertEqual(transform.position_to_hex(position), cell)

    def test_transform_rejects_positions_from_other_maps(self):
        transform = ConstructionSpaceTransform("village", 32)
        other = ConstructionPosition("forest", WorldPoint(0, 0))
        with self.assertRaises(ValueError):
            transform.position_to_hex(other)

    def test_transform_rejects_invalid_hex_size_and_origin(self):
        with self.assertRaises(ValueError):
            ConstructionSpaceTransform("village", 0)
        with self.assertRaises(TypeError):
            ConstructionSpaceTransform("village", 32, (0, 0))


if __name__ == "__main__":
    unittest.main()
