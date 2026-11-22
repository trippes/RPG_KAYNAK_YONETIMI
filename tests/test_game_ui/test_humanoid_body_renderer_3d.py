import unittest

import pygame

from game_ui.world_rendering.humanoid_body_3d import DEFAULT_HUMANOID_BODY
from game_ui.world_rendering.humanoid_body_renderer_3d import HumanoidBodyRenderer3D
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


class TestHumanoidBodyRenderer3D(unittest.TestCase):
    def test_draws_mesh_triangles_to_surface(self):
        surface = pygame.Surface((420, 560))
        surface.fill((0, 0, 0))
        renderer = HumanoidBodyRenderer3D()

        count = renderer.draw(
            surface,
            DEFAULT_HUMANOID_BODY,
            DEFAULT_HUMANOID_RIG,
            (210, 500),
            300.0,
        )

        self.assertGreater(count, 300)
        self.assertNotEqual(surface.get_at((210, 300))[:3], (0, 0, 0))

    def test_all_three_reference_yaws_render_without_mutating_rig(self):
        renderer = HumanoidBodyRenderer3D()
        rest = DEFAULT_HUMANOID_RIG.joint_positions()
        for yaw in (0.0, 0.7853981633974483, 1.5707963267948966):
            with self.subTest(yaw=yaw):
                surface = pygame.Surface((420, 560))
                count = renderer.draw(
                    surface,
                    DEFAULT_HUMANOID_BODY,
                    DEFAULT_HUMANOID_RIG,
                    (210, 500),
                    300.0,
                    yaw=yaw,
                )
                self.assertGreater(count, 300)
        self.assertEqual(rest, DEFAULT_HUMANOID_RIG.joint_positions())

    def test_invalid_scale_and_material_are_rejected(self):
        renderer = HumanoidBodyRenderer3D()
        surface = pygame.Surface((20, 20))
        with self.assertRaisesRegex(ValueError, "positive"):
            renderer.draw(
                surface, DEFAULT_HUMANOID_BODY, DEFAULT_HUMANOID_RIG, (10, 10), 0
            )
        with self.assertRaisesRegex(ValueError, "Unknown body materials"):
            renderer.draw(
                surface,
                DEFAULT_HUMANOID_BODY,
                DEFAULT_HUMANOID_RIG,
                (10, 10),
                10,
                palette={"unknown": (1, 2, 3)},
            )


if __name__ == "__main__":
    unittest.main()
