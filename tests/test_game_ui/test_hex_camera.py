import unittest

from game_ui.world_rendering.camera import HexCamera


class TestHexCamera(unittest.TestCase):
    def setUp(self):
        self.camera = HexCamera()
        self.bounds = (-2000.0, -2000.0, 2000.0, 2000.0)

    def test_initial_camera_starts_on_player(self):
        self.camera.update((120, -40), None, (800, 600), self.bounds, 1.0, 1 / 60)
        self.assertEqual((self.camera.x, self.camera.y), (120.0, -40.0))

    def test_follow_is_smooth_and_time_based(self):
        self.camera.update((0, 0), None, (800, 600), self.bounds, 1.0, 1 / 60)
        before = self.camera.x
        self.camera.update((500, 0), None, (800, 600), self.bounds, 1.0, 1 / 60)
        self.assertGreater(self.camera.x, before)
        self.assertLess(self.camera.x, 500)

    def test_edge_scroll_is_free_and_leaving_edge_returns_to_follow(self):
        self.camera.update((0, 0), None, (800, 600), self.bounds, 1.0, 1 / 60)
        self.camera.update((0, 0), (799, 300), (800, 600), self.bounds, 1.0, 0.1)
        self.assertTrue(self.camera.free_look)
        free_x = self.camera.x
        self.camera.update((0, 0), (400, 300), (800, 600), self.bounds, 1.0, 0.1)
        self.assertFalse(self.camera.free_look)
        self.assertLess(self.camera.x, free_x)

    def test_camera_is_clamped_to_small_world(self):
        self.camera.update((900, 900), None, (800, 600), (-100, -100, 100, 100), 1.0, 1 / 60)
        self.assertEqual((self.camera.x, self.camera.y), (0.0, 0.0))

    def test_isometric_edge_scroll_moves_in_the_projected_world_direction(self):
        self.camera.update(
            (0, 0), None, (800, 600), self.bounds, 1.0, 1 / 60,
            projection="isometric",
        )
        self.camera.update(
            (0, 0), (799, 300), (800, 600), self.bounds, 1.0, 0.1,
            projection="isometric",
        )
        self.assertGreater(self.camera.x, 0.0)
        self.assertLess(self.camera.y, 0.0)

    def test_isometric_camera_uses_conservative_world_viewport_bounds(self):
        self.camera.update(
            (0, 0), None, (800, 600), (-300, -300, 300, 300), 1.0, 1 / 60,
            projection="isometric",
        )
        self.assertEqual((self.camera.x, self.camera.y), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
