import unittest

from core.domain.spatial import (
    SquareGridCoord,
    WorldPoint,
    square_grid_cell_bounds,
    square_grid_cell_corners,
    square_grid_to_world_point,
    world_point_to_square_grid,
)


class TestSquareGridGeometry(unittest.TestCase):
    def test_cell_centers_round_trip_for_positive_and_negative_coordinates(self):
        coordinates = (
            SquareGridCoord(0, 0),
            SquareGridCoord(1, 2),
            SquareGridCoord(-1, -2),
            SquareGridCoord(-19, 7),
            SquareGridCoord(23, -11),
        )
        for size in (8, 16, 32.5):
            for coord in coordinates:
                with self.subTest(size=size, coord=coord):
                    center = square_grid_to_world_point(coord, size)
                    self.assertEqual(world_point_to_square_grid(center, size), coord)

    def test_origin_is_the_center_of_grid_cell_zero_zero(self):
        origin = WorldPoint(125.0, -80.0)
        coord = world_point_to_square_grid(origin, 8, origin=origin)
        self.assertEqual(coord, SquareGridCoord(0, 0))
        self.assertEqual(
            square_grid_to_world_point(coord, 8, origin=origin),
            origin,
        )

    def test_half_open_boundaries_have_deterministic_ownership(self):
        self.assertEqual(
            world_point_to_square_grid(WorldPoint(4, 4), 8),
            SquareGridCoord(1, 1),
        )
        self.assertEqual(
            world_point_to_square_grid(WorldPoint(-4, -4), 8),
            SquareGridCoord(0, 0),
        )
        self.assertEqual(
            world_point_to_square_grid(WorldPoint(-4.000001, -4.000001), 8),
            SquareGridCoord(-1, -1),
        )

    def test_bounds_and_corners_describe_the_same_cell(self):
        coord = SquareGridCoord(-2, 3)
        self.assertEqual(
            square_grid_cell_bounds(coord, 8),
            (-20.0, 20.0, -12.0, 28.0),
        )
        self.assertEqual(
            square_grid_cell_corners(coord, 8),
            (
                WorldPoint(-20, 20),
                WorldPoint(-12, 20),
                WorldPoint(-12, 28),
                WorldPoint(-20, 28),
            ),
        )

    def test_invalid_coordinates_and_sizes_are_rejected(self):
        for invalid in (True, 1.5, "2"):
            with self.subTest(invalid=invalid):
                with self.assertRaises(TypeError):
                    SquareGridCoord(invalid, 0)
        for invalid in (0, -1, float("inf"), float("nan"), True, "8"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    square_grid_to_world_point(SquareGridCoord(0, 0), invalid)

    def test_non_world_point_inputs_are_rejected(self):
        with self.assertRaises(TypeError):
            world_point_to_square_grid((0, 0), 8)
        with self.assertRaises(TypeError):
            square_grid_to_world_point(SquareGridCoord(0, 0), 8, origin=(0, 0))


if __name__ == "__main__":
    unittest.main()
