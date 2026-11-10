"""Tests for the mutable Position used by the legacy Entity aggregate."""

import unittest

from core.entity.position import Position
from core.domain.spatial import Position as CanonicalPosition


class TestEntityPosition(unittest.TestCase):
    def test_mutable_compatibility_position_is_backed_by_canonical_value(self):
        position = Position(1, 2)
        canonical = position.to_canonical()
        self.assertIsInstance(canonical, CanonicalPosition)
        position.move(3, 4)
        self.assertEqual(canonical.to_dict(), {"x": 1, "y": 2})
        self.assertEqual(position.to_canonical().to_dict(), {"x": 4, "y": 6})

    def test_coordinate_properties_replace_immutable_value(self):
        position = Position(1, 2)
        position.x = 5
        position.y = 8
        self.assertEqual(position.to_canonical(), CanonicalPosition(5, 8))

    def test_default_position(self):
        position = Position()
        self.assertEqual(position.get_position(), (0, 0))

    def test_initial_coordinates(self):
        position = Position(10, 20)
        self.assertEqual(position.get_position(), (10, 20))

    def test_invalid_coordinates_are_rejected(self):
        for value in (True, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    Position(value, 0)

    def test_set_position(self):
        position = Position()
        position.set_position(3, 7)
        self.assertEqual(position.get_position(), (3, 7))

    def test_move(self):
        position = Position(2, 4)
        position.move(3, -1)
        self.assertEqual(position.get_position(), (5, 3))

    def test_distance_to(self):
        first = Position(0, 0)
        second = Position(3, 4)
        self.assertEqual(first.distance_to(second), 5.0)

    def test_same_as(self):
        self.assertTrue(Position(2, 5).same_as(Position(2, 5)))
        self.assertFalse(Position(2, 5).same_as(Position(5, 2)))

    def test_copy_is_independent(self):
        original = Position(1, 2)
        copied = original.copy()
        copied.move(3, 4)
        self.assertEqual(original.get_position(), (1, 2))
        self.assertEqual(copied.get_position(), (4, 6))

    def test_to_dict(self):
        self.assertEqual(Position(8, 9).to_dict(), {"x": 8, "y": 9})


if __name__ == "__main__":
    unittest.main()
