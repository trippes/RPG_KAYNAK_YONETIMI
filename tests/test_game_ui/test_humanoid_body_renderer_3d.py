import unittest

import pygame

from game_ui.world_rendering.humanoid_body_3d import DEFAULT_HUMANOID_BODY
from game_ui.world_rendering.humanoid_body_renderer_3d import HumanoidBodyRenderer3D
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


class TestHumanoidBodyRenderer3D(unittest.TestCase):
    def test_triangle_depth_uses_fixed_isometric_camera_axis(self):
        renderer = HumanoidBodyRenderer3D()
        near = renderer._camera_depth((0.0, 0.0, 1.0), 0.0)
        far = renderer._camera_depth((0.0, 0.0, -1.0), 0.0)
        self.assertGreater(near, far)
        self.assertAlmostEqual(
            renderer._camera_depth((0.0, 1.0, 0.0), 0.0),
            renderer._camera_depth((1.0, 0.0, 0.0), 0.0),
        )

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
        for yaw in (
            0.0,
            0.7853981633974483,
            1.5707963267948966,
            2.356194490192345,
            3.141592653589793,
            3.9269908169872414,
            4.71238898038469,
            5.497787143782138,
        ):
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

    def test_reuses_pose_sprite_for_actors_at_different_positions(self):
        renderer = HumanoidBodyRenderer3D()
        first = pygame.Surface((420, 560), pygame.SRCALPHA)
        second = pygame.Surface((420, 560), pygame.SRCALPHA)

        first_count = renderer.draw(
            first, DEFAULT_HUMANOID_BODY, DEFAULT_HUMANOID_RIG, (180, 500), 300.0,
            yaw=0.7853981633974483,
            local_rotations={"shoulder_left": (0.0, 0.0, 0.12)},
        )
        second_count = renderer.draw(
            second, DEFAULT_HUMANOID_BODY, DEFAULT_HUMANOID_RIG, (240, 500), 300.0,
            yaw=0.7853981633974483,
            local_rotations={"shoulder_left": (0.0, 0.0, 0.12)},
        )

        self.assertEqual(first_count, second_count)
        self.assertEqual(renderer.cache_info()["misses"], 1)
        self.assertEqual(renderer.cache_info()["hits"], 1)
        self.assertEqual(renderer.cache_info()["entries"], 1)
        self.assertGreater(renderer.cache_info()["bytes"], 0)
        self.assertNotEqual(first.get_bounding_rect().size, (0, 0))
        self.assertNotEqual(second.get_bounding_rect().size, (0, 0))

    def test_subpixel_pose_changes_reuse_quantized_sprite_cache(self):
        renderer = HumanoidBodyRenderer3D()
        for rotation, translation in (
            ((0.0, 0.0, 0.1201), (0.0, 0.0, -0.0801)),
            ((0.0, 0.0, 0.1210), (0.0, 0.0, -0.0810)),
        ):
            renderer.draw(
                pygame.Surface((420, 560), pygame.SRCALPHA),
                DEFAULT_HUMANOID_BODY,
                DEFAULT_HUMANOID_RIG,
                (210, 500),
                54.0,
                local_rotations={"shoulder_left": rotation},
                local_translations={"pelvis": translation},
                detail_level="low",
            )
        self.assertEqual(renderer.cache_info()["misses"], 1)
        self.assertEqual(renderer.cache_info()["hits"], 1)
        self.assertEqual(renderer.cache_info()["entries"], 1)

    def test_cache_key_changes_for_pose_direction_detail_and_palette(self):
        renderer = HumanoidBodyRenderer3D()
        options = (
            {},
            {"yaw": 0.5},
            {"local_rotations": {"elbow_left": (0.0, 0.0, -0.4)}},
            {"detail_level": "low"},
            {"palette": {"tunic": (100, 90, 80)}},
        )
        for option in options:
            renderer.draw(
                pygame.Surface((420, 560), pygame.SRCALPHA),
                DEFAULT_HUMANOID_BODY,
                DEFAULT_HUMANOID_RIG,
                (210, 500),
                300.0,
                **option,
            )
        self.assertEqual(renderer.cache_info()["misses"], len(options))
        self.assertEqual(renderer.cache_info()["entries"], len(options))

    def test_draw_accepts_pelvis_translation_and_caches_it(self):
        renderer = HumanoidBodyRenderer3D()
        options = {"local_translations": {"pelvis": (0.0, 0.0, -0.08)}}
        for x in (180, 240):
            renderer.draw(
                pygame.Surface((420, 560), pygame.SRCALPHA),
                DEFAULT_HUMANOID_BODY,
                DEFAULT_HUMANOID_RIG,
                (x, 500),
                300.0,
                **options,
            )
        self.assertEqual(renderer.cache_info()["misses"], 1)
        self.assertEqual(renderer.cache_info()["hits"], 1)

    def test_low_detail_mode_renders_fewer_triangles(self):
        renderer = HumanoidBodyRenderer3D()
        high = pygame.Surface((420, 560))
        low = pygame.Surface((420, 560))
        high_count = renderer.draw(
            high, DEFAULT_HUMANOID_BODY, DEFAULT_HUMANOID_RIG, (210, 500), 300.0
        )
        low_count = renderer.draw(
            low, DEFAULT_HUMANOID_BODY, DEFAULT_HUMANOID_RIG, (210, 500), 300.0,
            detail_level="low",
        )
        self.assertGreater(high_count, low_count)

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
