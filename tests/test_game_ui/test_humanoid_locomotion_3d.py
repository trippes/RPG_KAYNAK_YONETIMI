import math
import unittest

from game_ui.world_rendering.humanoid_locomotion_3d import (
    HumanoidFootLockSolver3D,
    solve_two_bone_ik,
)


class TestTwoBoneIK(unittest.TestCase):
    def test_forward_kinematics_reaches_a_reachable_target(self):
        target_forward, target_down = 0.12, 0.38
        result = solve_two_bone_ik(target_forward, target_down, 0.22, 0.228)
        self.assertTrue(result.reachable)
        self.assertAlmostEqual(result.end_forward, target_forward, places=6)
        self.assertAlmostEqual(result.end_down, target_down, places=6)
        self.assertLess(result.knee_angle, 0.0)

    def test_unreachable_target_is_clamped_and_reported(self):
        result = solve_two_bone_ik(0.5, 0.5, 0.22, 0.228)
        self.assertFalse(result.reachable)
        self.assertAlmostEqual(result.solved_distance, 0.448, places=6)
        self.assertGreater(result.target_distance, result.solved_distance)

    def test_invalid_inputs_are_rejected(self):
        for args in (
            (float("nan"), 0.2, 0.22, 0.22),
            (0.1, 0.2, 0.0, 0.22),
            (True, 0.2, 0.22, 0.22),
        ):
            with self.subTest(args=args), self.assertRaises(ValueError):
                solve_two_bone_ik(*args)


class TestHumanoidFootLockSolver3D(unittest.TestCase):
    def test_stance_anchor_remains_fixed_while_root_moves(self):
        solver = HumanoidFootLockSolver3D()
        solver.update(
            phase=0.0, state="walk", world_position=(100.0, 200.0),
            yaw=0.0, world_scale=54.0,
        )
        initial = solver.anchors["left"]
        self.assertIsNotNone(initial)
        solver.update(
            phase=0.25, state="walk", world_position=(104.0, 200.0),
            yaw=0.0, world_scale=54.0,
        )
        self.assertEqual(solver.anchors["left"], initial)

    def test_subpixel_motion_reuses_the_same_quantized_ik_pose(self):
        solver = HumanoidFootLockSolver3D()
        first, _ = solver.update(
            phase=0.2, state="walk", world_position=(0.0, 0.0),
            yaw=0.0, world_scale=54.0,
        )
        second, _ = solver.update(
            phase=0.2, state="walk", world_position=(0.1, 0.1),
            yaw=0.0, world_scale=54.0,
        )
        self.assertEqual(first, second)

    def test_turning_keeps_anchor_in_world_space(self):
        solver = HumanoidFootLockSolver3D()
        solver.update(
            phase=0.0, state="walk", world_position=(20.0, 30.0),
            yaw=0.4, world_scale=54.0,
        )
        anchor = solver.anchors["left"]
        solver.update(
            phase=0.2, state="walk", world_position=(21.0, 31.0),
            yaw=0.8, world_scale=54.0,
        )
        self.assertEqual(solver.anchors["left"], anchor)

    def test_idle_releases_all_world_foot_anchors(self):
        solver = HumanoidFootLockSolver3D()
        solver.update(
            phase=0.0, state="walk", world_position=(0.0, 0.0),
            yaw=0.0, world_scale=54.0,
        )
        solver.update(
            phase=0.0, state="idle", world_position=(0.0, 0.0),
            yaw=0.0, world_scale=54.0,
        )
        self.assertEqual(solver.anchors, {"left": None, "right": None})
        self.assertEqual(solver.diagnostics, {})

    def test_stance_outputs_both_hip_and_knee_rotations(self):
        solver = HumanoidFootLockSolver3D()
        rotations, translations = solver.update(
            phase=0.0, state="walk", world_position=(0.0, 0.0),
            yaw=0.0, world_scale=54.0,
        )
        self.assertIn("hip_left", rotations)
        self.assertIn("knee_left", rotations)
        self.assertIn("pelvis", translations)
        self.assertTrue(all(math.isfinite(v) for r in rotations.values() for v in r))


if __name__ == "__main__":
    unittest.main()
