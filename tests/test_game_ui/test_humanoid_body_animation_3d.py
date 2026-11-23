"""Regression tests for world-aware humanoid locomotion and idle motion."""

import math
import unittest

from game_ui.world_rendering.humanoid_body_animation_3d import HumanoidBodyAnimator3D
from game_ui.world_rendering.humanoid_locomotion_3d import HumanoidFootLockSolver3D
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


class HumanoidBodyAnimator3DTests(unittest.TestCase):
    def test_idle_pose_contains_breathing_and_full_body_joints(self):
        animator = HumanoidBodyAnimator3D()
        animator.advance(0.0, 0.4)
        pose = animator.pose
        self.assertIn("chest", pose)
        self.assertIn("head", pose)
        self.assertIn("elbow_left", pose)
        self.assertIn("wrist_right", pose)
        self.assertIn("hand_left", pose)
        self.assertIn("clavicle_right", pose)
        self.assertIn("toe_right", pose)
        self.assertIn("hip_left", pose)
        self.assertLess(pose["shoulder_left"][1], 0.0)
        self.assertGreater(pose["shoulder_right"][1], 0.0)
        self.assertLess(pose["elbow_left"][2], 0.0)
        self.assertNotEqual(pose, {})

    def test_walk_phase_advances_from_traveled_distance(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        quarter_cycle = animator.WALK_CYCLE_SECONDS / 4.0
        animator.advance(animator.WALK_CYCLE_DISTANCE / 4.0, quarter_cycle)
        self.assertAlmostEqual(animator.phase, math.pi / 2.0)
        self.assertEqual(animator.phase_index, 4)

    def test_full_walk_cycle_returns_to_same_phase(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(animator.WALK_CYCLE_DISTANCE, animator.WALK_CYCLE_SECONDS)
        self.assertAlmostEqual(animator.phase, 0.0)

    def test_run_uses_longer_distance_per_cycle_than_walk(self):
        self.assertGreater(
            HumanoidBodyAnimator3D.RUN_CYCLE_DISTANCE,
            HumanoidBodyAnimator3D.WALK_CYCLE_DISTANCE,
        )
        self.assertGreater(HumanoidFootLockSolver3D.WALK_STANCE_FRACTION, 0.5)
        self.assertLess(HumanoidFootLockSolver3D.RUN_STANCE_FRACTION, 0.5)

    def test_stationary_frame_preserves_gait_phase(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(4.0)
        phase = animator.phase
        animator.advance(0.0)
        self.assertEqual(animator.phase, phase)

    def test_direction_change_preserves_gait_phase(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(4.0)
        phase = animator.phase
        animator.select(direction="north_west")
        self.assertEqual(animator.phase, phase)

    def test_state_change_blends_from_previous_pose(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(8.0)
        previous = animator.pose
        animator.select(state="idle")
        animator.advance(0.0, 1.0 / 60.0)
        self.assertNotEqual(animator.pose, {})
        self.assertNotEqual(animator.pose, previous)

    def test_pose_and_translations_are_valid_for_the_anatomical_rig(self):
        for state in ("idle", "walk", "run"):
            with self.subTest(state=state):
                animator = HumanoidBodyAnimator3D(state=state)
                animator.advance(
                    4.0, world_position=(10.0, 20.0), yaw=0.0, world_scale=54.0,
                )
                self.assertTrue(
                    set(animator.pose).issubset(set(DEFAULT_HUMANOID_RIG.joint_names))
                )
                self.assertTrue(
                    set(animator.translations).issubset(set(DEFAULT_HUMANOID_RIG.joint_names))
                )
                DEFAULT_HUMANOID_RIG.resolve_pose(
                    animator.pose, animator.translations
                )

    def test_world_foot_lock_produces_stance_targets(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(
            0.0, world_position=(10.0, 20.0), yaw=0.0, world_scale=54.0,
        )
        self.assertIn("left", animator.foot_lock_diagnostics)
        self.assertIn("pelvis", animator.translations)

    def test_walk_pose_interpolates_between_phase_samples(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(0.5)
        first_index = animator.phase_index
        first_pose = animator.pose
        animator.advance(0.5)
        self.assertEqual(animator.phase_index, first_index)
        self.assertNotEqual(animator.pose, first_pose)
        self.assertLess(
            max(
                abs(animator.pose[name][axis] - first_pose[name][axis])
                for name in first_pose
                for axis in range(3)
            ),
            0.1,
        )

    def test_invalid_distance_and_delta_are_rejected(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        for value in (True, -1.0, float("nan"), float("inf"), "1"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                animator.advance(value)
        with self.assertRaises(ValueError):
            animator.advance(0.0, -0.1)

    def test_invalid_selection_is_rejected(self):
        with self.assertRaises(ValueError):
            HumanoidBodyAnimator3D(direction="up")
        with self.assertRaises(ValueError):
            HumanoidBodyAnimator3D(state="jump")

    def test_walk_and_run_share_locomotion_stance_contract(self):
        self.assertAlmostEqual(HumanoidBodyAnimator3D.WALK_STANCE_FRACTION,
                               HumanoidFootLockSolver3D.WALK_STANCE_FRACTION)
        self.assertAlmostEqual(HumanoidBodyAnimator3D.RUN_STANCE_FRACTION,
                               HumanoidFootLockSolver3D.RUN_STANCE_FRACTION)

    def test_zero_distance_does_not_advance_walk_or_run_phase(self):
        for state in ("walk", "run"):
            animator = HumanoidBodyAnimator3D(state=state)
            animator.advance(3.25)
            phase = animator.phase
            animator.advance(0.0, 0.25)
            self.assertEqual(animator.phase, phase)

    def test_run_phase_is_distance_driven_and_distinct_from_walk(self):
        walk = HumanoidBodyAnimator3D(state="walk")
        run = HumanoidBodyAnimator3D(state="run")
        walk.advance(5.0)
        run.advance(5.0)
        self.assertNotAlmostEqual(walk.phase, run.phase)

    def test_foot_lock_solves_stance_and_swing_legs(self):
        solver = HumanoidFootLockSolver3D()
        rotations, translations = solver.update(
            phase=math.pi * 0.5, state="walk",
            world_position=(0.0, 0.0), yaw=0.0, world_scale=54.0,
        )
        self.assertEqual(set(rotations), {
            "hip_left", "knee_left", "ankle_left",
            "hip_right", "knee_right", "ankle_right",
        })
        self.assertIn("pelvis", translations)
        self.assertTrue(all(math.isfinite(value)
                            for rotation in rotations.values() for value in rotation))

    def test_transition_blending_is_continuous_not_quantized_in_steps(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(3.0)
        animator.select(state="run")
        previous = animator.pose
        deltas = []
        for _ in range(5):
            animator.advance(0.0, 1.0 / 60.0)
            current = animator.pose
            deltas.append(max(
                abs(current[name][axis] - previous[name][axis])
                for name in current.keys() & previous.keys()
                for axis in range(3)
            ))
            previous = current
        self.assertTrue(all(delta < 0.2 for delta in deltas))



if __name__ == "__main__":
    unittest.main()
