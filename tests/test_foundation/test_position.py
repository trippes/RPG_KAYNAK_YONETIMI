import unittest

from core.domain.spatial import Position


class TestCanonicalPosition(unittest.TestCase):
    def test_creation_equality_and_hashing(self):
        first = Position(1, 2)
        second = Position(1, 2)
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))

    def test_position_is_immutable(self):
        position = Position(1, 2)
        with self.assertRaises(AttributeError):
            position.x = 3

    def test_translation_returns_new_position(self):
        original = Position(1, 2)
        translated = original.translated(3, -1)
        self.assertEqual(original, Position(1, 2))
        self.assertEqual(translated, Position(4, 1))

    def test_serialization_round_trip(self):
        position = Position(1.5, 2)
        self.assertEqual(Position.from_dict(position.to_dict()), position)

    def test_invalid_coordinates(self):
        for value in (True, "1", float("inf"), float("nan")):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    Position(value, 0)

    def test_bounds_are_not_position_responsibility(self):
        self.assertEqual(Position(-100, 100), Position(-100, 100))
