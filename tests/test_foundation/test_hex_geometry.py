import math
import unittest

from core.domain.spatial import (
    HexCoord,
    axial_to_pixel,
    fractional_axial_to_hex,
    pixel_to_axial,
)


class TestPointyTopHexGeometry(unittest.TestCase):
    def test_origin_maps_to_pixel_origin(self):
        self.assertEqual(axial_to_pixel(HexCoord(0, 0), 16), (0.0, 0.0))

    def test_axial_to_pixel_known_centers(self):
        size = 10
        self.assertAlmostEqual(axial_to_pixel(HexCoord(1, 0), size)[0], 10 * math.sqrt(3))
        self.assertAlmostEqual(axial_to_pixel(HexCoord(1, 0), size)[1], 0)
        self.assertAlmostEqual(axial_to_pixel(HexCoord(0, 1), size)[0], 5 * math.sqrt(3))
        self.assertAlmostEqual(axial_to_pixel(HexCoord(0, 1), size)[1], 15)

    def test_cell_centers_round_trip_for_multiple_sizes(self):
        coordinates = (
            HexCoord(0, 0),
            HexCoord(1, 0),
            HexCoord(1, -1),
            HexCoord(0, -1),
            HexCoord(-1, 0),
            HexCoord(-1, 1),
            HexCoord(0, 1),
            HexCoord(-12, 8),
            HexCoord(9, -15),
        )
        for size in (1, 8, 16, 37.5):
            for coord in coordinates:
                with self.subTest(size=size, coord=coord):
                    pixel = axial_to_pixel(coord, size)
                    self.assertEqual(pixel_to_axial(*pixel, size), coord)

    def test_fractional_axial_cube_rounding(self):
        self.assertEqual(fractional_axial_to_hex(0.1, -0.1), HexCoord(0, 0))
        self.assertEqual(fractional_axial_to_hex(1.8, -0.9), HexCoord(2, -1))

    def test_shared_edge_tie_is_deterministic(self):
        # The midpoint of cells (0, 0) and (1, 0) resolves to (0, 0).
        midpoint = (math.sqrt(3) / 2, 0.0)
        results = {
            pixel_to_axial(midpoint[0], midpoint[1], 1)
            for _ in range(10)
        }
        self.assertEqual(results, {HexCoord(0, 0)})

    def test_invalid_hex_size(self):
        for size in (0, -1, float("inf"), float("nan"), True, "2"):
            with self.subTest(size=size):
                with self.assertRaises((TypeError, ValueError)):
                    axial_to_pixel(HexCoord(0, 0), size)

    def test_invalid_pixel_values(self):
        for value in (float("inf"), float("nan"), True, "1"):
            with self.subTest(value=value):
                with self.assertRaises((TypeError, ValueError)):
                    pixel_to_axial(value, 0, 1)

    def test_pixel_to_axial_rejects_invalid_size(self):
        with self.assertRaises(ValueError):
            pixel_to_axial(0, 0, 0)

    def test_coordinate_argument_must_be_hex_coord(self):
        with self.assertRaises(TypeError):
            axial_to_pixel((0, 0), 1)


if __name__ == "__main__":
    unittest.main()
