import unittest

from core.domain.spatial import HexCoord
from game_ui.world_transform import WorldTransform


class TestWorldTransform(unittest.TestCase):
    def test_axial_origin_maps_to_viewport_center(self):
        transform = WorldTransform(hex_size=32, viewport_center=(400, 300))
        self.assertEqual(transform.axial_to_screen(HexCoord(0, 0)), (400.0, 300.0))

    def test_world_screen_round_trip_with_camera_and_zoom(self):
        transform = WorldTransform(
            hex_size=24, camera_x=17.5, camera_y=-8,
            viewport_center=(640, 360), zoom=1.75,
        )
        point = (123.25, -41.5)
        screen = transform.world_to_screen(*point)
        restored = transform.screen_to_world(*screen)
        self.assertAlmostEqual(restored[0], point[0])
        self.assertAlmostEqual(restored[1], point[1])

    def test_axial_screen_round_trip_with_camera_and_zoom(self):
        transform = WorldTransform(
            hex_size=31, camera_x=12, camera_y=-19,
            viewport_center=(500, 350), zoom=1.4,
        )
        for coord in (HexCoord(0, 0), HexCoord(3, -2), HexCoord(-7, 5)):
            self.assertEqual(
                transform.screen_to_axial(*transform.axial_to_screen(coord)),
                coord,
            )

    def test_rejects_non_positive_zoom_and_hex_size(self):
        transform = WorldTransform()
        with self.assertRaises(ValueError):
            transform.configure(zoom=0)
        with self.assertRaises(ValueError):
            transform.configure(hex_size=-1)

    def test_rejects_non_finite_camera_values(self):
        transform = WorldTransform()
        with self.assertRaises(ValueError):
            transform.configure(camera_x=float("inf"))


if __name__ == "__main__":
    unittest.main()
