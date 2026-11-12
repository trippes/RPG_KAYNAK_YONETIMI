import unittest

from core.domain.spatial import HexCoord, HexDirection


class TestHexDirection(unittest.TestCase):
    def test_canonical_offsets(self):
        expected = {
            HexDirection.EAST: (1, 0),
            HexDirection.NORTH_EAST: (1, -1),
            HexDirection.NORTH_WEST: (0, -1),
            HexDirection.WEST: (-1, 0),
            HexDirection.SOUTH_WEST: (-1, 1),
            HexDirection.SOUTH_EAST: (0, 1),
        }
        self.assertEqual(
            {direction: direction.offset for direction in HexDirection},
            expected,
        )

    def test_opposites_are_involutive(self):
        for direction in HexDirection:
            with self.subTest(direction=direction):
                self.assertIs(direction.opposite.opposite, direction)

    def test_opposite_offsets_cancel(self):
        origin = HexCoord(4, -7)
        for direction in HexDirection:
            with self.subTest(direction=direction):
                neighbor = origin.neighbor(direction)
                self.assertEqual(neighbor.neighbor(direction.opposite), origin)


class TestHexCoord(unittest.TestCase):
    def test_creation_equality_hash_and_order(self):
        first = HexCoord(2, -3)
        second = HexCoord(2, -3)
        self.assertEqual(first, second)
        self.assertEqual(hash(first), hash(second))
        self.assertLess(HexCoord(-1, 0), HexCoord(0, 0))

    def test_coordinate_is_immutable(self):
        coord = HexCoord(1, 2)
        with self.assertRaises(AttributeError):
            coord.q = 9

    def test_integer_components_only(self):
        for value in (True, False, 1.0, "1", None):
            with self.subTest(value=value):
                with self.assertRaises(TypeError):
                    HexCoord(value, 0)

    def test_negative_coordinates_are_valid(self):
        self.assertEqual(HexCoord(-12, -4), HexCoord(-12, -4))

    def test_addition_subtraction_and_translation(self):
        first = HexCoord(3, -5)
        second = HexCoord(-2, 7)
        self.assertEqual(first + second, HexCoord(1, 2))
        self.assertEqual(first - second, HexCoord(5, -12))
        self.assertEqual(first.translated(-4, 2), HexCoord(-1, -3))

    def test_translation_rejects_non_integer_delta(self):
        with self.assertRaises(TypeError):
            HexCoord(0, 0).translated(dq=1.5)

    def test_six_neighbors_follow_canonical_order(self):
        origin = HexCoord(0, 0)
        self.assertEqual(
            origin.neighbors(),
            (
                HexCoord(1, 0),
                HexCoord(1, -1),
                HexCoord(0, -1),
                HexCoord(-1, 0),
                HexCoord(-1, 1),
                HexCoord(0, 1),
            ),
        )

    def test_each_neighbor_has_distance_one(self):
        coord = HexCoord(-8, 13)
        for neighbor in coord.neighbors():
            with self.subTest(neighbor=neighbor):
                self.assertEqual(coord.distance_to(neighbor), 1)

    def test_distance_examples_and_symmetry(self):
        examples = (
            (HexCoord(0, 0), HexCoord(0, 0), 0),
            (HexCoord(0, 0), HexCoord(2, -1), 2),
            (HexCoord(0, 0), HexCoord(-3, 2), 3),
            (HexCoord(-4, 7), HexCoord(5, -2), 9),
        )
        for first, second, expected in examples:
            with self.subTest(first=first, second=second):
                self.assertEqual(first.distance_to(second), expected)
                self.assertEqual(second.distance_to(first), expected)

    def test_distance_triangle_inequality(self):
        first = HexCoord(-5, 2)
        middle = HexCoord(3, -4)
        last = HexCoord(8, 7)
        self.assertLessEqual(
            first.distance_to(last),
            first.distance_to(middle) + middle.distance_to(last),
        )

    def test_invalid_neighbor_direction(self):
        with self.assertRaises(TypeError):
            HexCoord(0, 0).neighbor("east")


if __name__ == "__main__":
    unittest.main()
