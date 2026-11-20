import unittest

from core.domain.spatial import HexCoord, WorldPoint
from game_ui.world_transform import WorldTransform


class TestIsometricProjection(unittest.TestCase):
    def test_projection_uses_two_to_one_vertical_ratio(self):
        transform = WorldTransform(viewport_center=(100, 100))
        self.assertEqual(transform.world_to_screen(2, 0), (102.0, 101.0))
        self.assertEqual(transform.world_to_screen(0, 2), (98.0, 101.0))

    def test_projection_and_inverse_round_trip_with_camera_zoom(self):
        transform = WorldTransform(
            camera_x=125.5,
            camera_y=-42.25,
            viewport_center=(640, 360),
            zoom=1.75,
        )
        for point in (
            (0.0, 0.0), (123.25, -41.5), (-512.75, 99.125),
        ):
            self.assertAlmostEqual(
                transform.screen_to_world(*transform.world_to_screen(*point))[0],
                point[0],
            )
            self.assertAlmostEqual(
                transform.screen_to_world(*transform.world_to_screen(*point))[1],
                point[1],
            )

    def test_axial_hit_test_round_trips_after_projection(self):
        transform = WorldTransform(
            hex_size=32,
            camera_x=17,
            camera_y=-11,
            viewport_center=(500, 300),
            zoom=1.25,
        )
        for coord in (
            HexCoord(0, 0), HexCoord(1, 0), HexCoord(0, 1),
            HexCoord(-4, 3), HexCoord(7, -5),
        ):
            self.assertEqual(
                transform.screen_to_axial(*transform.axial_to_screen(coord)),
                coord,
            )

    def test_world_point_api_preserves_canonical_coordinates(self):
        transform = WorldTransform(viewport_center=(400, 300))
        point = WorldPoint(64.0, 32.0)
        screen = transform.world_point_to_screen(point)
        self.assertEqual(transform.screen_to_world_point(*screen), point)

    def test_cartesian_projection_remains_available_for_legacy_adapters(self):
        transform = WorldTransform(
            projection="cartesian", viewport_center=(10, 20),
        )
        self.assertEqual(transform.world_to_screen(4, 6), (14.0, 26.0))
        self.assertEqual(transform.screen_to_world(14, 26), (4.0, 6.0))

    def test_invalid_projection_is_rejected(self):
        with self.assertRaises(ValueError):
            WorldTransform(projection="oblique")


if __name__ == "__main__":
    unittest.main()
