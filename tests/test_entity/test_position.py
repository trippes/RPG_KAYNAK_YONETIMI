"""Tests for legacy and canonical Position value objects."""

import math
import unittest
from dataclasses import FrozenInstanceError

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


class TestCanonicalPosition(unittest.TestCase):
    def test_defaults_to_origin(self):
        self.assertEqual(CanonicalPosition(), CanonicalPosition(x=0, y=0))

    def test_stores_integer_and_float_coordinates(self):
        for x, y in ((3, 4), (-2, 7), (1.5, -0.25)):
            with self.subTest(x=x, y=y):
                position = CanonicalPosition(x=x, y=y)
                self.assertEqual((position.x, position.y), (x, y))

    def test_rejects_non_numeric_coordinates(self):
        for value in (True, False, "1", None, object()):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    CanonicalPosition(x=value, y=0)
                with self.assertRaises(TypeError):
                    CanonicalPosition(x=0, y=value)

    def test_rejects_non_finite_coordinates(self):
        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    CanonicalPosition(x=value, y=0)
                with self.assertRaises(ValueError):
                    CanonicalPosition(x=0, y=value)

    def test_is_immutable_and_orderable(self):
        position = CanonicalPosition(2, 5)
        with self.assertRaises(FrozenInstanceError):
            position.x = 10
        self.assertEqual(
            sorted((CanonicalPosition(2, 0), CanonicalPosition(1, 5), CanonicalPosition(1, 2))),
            [CanonicalPosition(1, 2), CanonicalPosition(1, 5), CanonicalPosition(2, 0)],
        )

    def test_translation_returns_new_position(self):
        original = CanonicalPosition(2, 3)
        translated = original.translated(dx=-1, dy=4)
        self.assertEqual(translated, CanonicalPosition(1, 7))
        self.assertEqual(original, CanonicalPosition(2, 3))
        self.assertIsNot(translated, original)

    def test_translation_rejects_invalid_offsets(self):
        position = CanonicalPosition(1, 2)
        for value in (True, "1", None, math.nan, math.inf):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    position.translated(dx=value)
                with self.assertRaises((TypeError, ValueError)):
                    position.translated(dy=value)

    def test_distance_to_uses_euclidean_metric(self):
        self.assertEqual(CanonicalPosition(0, 0).distance_to(CanonicalPosition(3, 4)), 5.0)

    def test_distance_to_rejects_non_position_values(self):
        with self.assertRaisesRegex(TypeError, "other must be a Position"):
            CanonicalPosition().distance_to((0, 0))

    def test_serialization_round_trip(self):
        position = CanonicalPosition(2.5, -4)
        expected = {"x": 2.5, "y": -4}
        self.assertEqual(position.to_dict(), expected)
        self.assertEqual(position.to_persistence(), expected)
        self.assertEqual(CanonicalPosition.from_dict(expected), position)
        self.assertEqual(CanonicalPosition.from_persistence(expected), position)

    def test_deserialization_rejects_invalid_data(self):
        with self.assertRaisesRegex(TypeError, "Position data must be a dictionary"):
            CanonicalPosition.from_dict([1, 2])
        for data in ({"x": 1}, {"y": 2}, {}):
            with self.subTest(data=data):
                with self.assertRaisesRegex(ValueError, "Missing position field"):
                    CanonicalPosition.from_dict(data)


if __name__ == "__main__":
    unittest.main()
