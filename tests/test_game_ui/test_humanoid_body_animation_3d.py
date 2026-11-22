"""Tests for distance-driven 3D humanoid gait sampling."""

import math
import unittest

from game_ui.world_rendering.humanoid_body_animation_3d import (
    HumanoidBodyAnimator3D,
)
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


class HumanoidBodyAnimator3DTests(unittest.TestCase):
    def test_idle_pose_is_static_and_does_not_advance(self):
        animator = HumanoidBodyAnimator3D()
        initial_phase = animator.phase
        self.assertEqual(animator.pose, {})
        animator.advance(24.0)
        self.assertEqual(animator.phase, initial_phase)
        self.assertEqual(animator.pose, {})

    def test_walk_phase_advances_from_traveled_distance(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(animator.WALK_CYCLE_DISTANCE / 4.0)
        self.assertAlmostEqual(animator.phase, math.pi / 2.0)
        self.assertEqual(animator.phase_index, 2)

    def test_full_walk_cycle_returns_to_same_phase(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        initial = animator.pose
        animator.advance(animator.WALK_CYCLE_DISTANCE)
        self.assertAlmostEqual(animator.phase, 0.0)
        self.assertEqual(animator.pose, initial)

    def test_run_uses_longer_distance_per_cycle_than_walk(self):
        walk = HumanoidBodyAnimator3D(state="walk")
        run = HumanoidBodyAnimator3D(state="run")
        walk.advance(21.0)
        run.advance(21.0)
        self.assertGreater(walk.phase, run.phase)

    def test_stationary_frame_preserves_current_gait_pose(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(17.0)
        phase = animator.phase
        pose = animator.pose
        animator.advance(0.0)
        self.assertEqual(animator.phase, phase)
        self.assertEqual(animator.pose, pose)

    def test_direction_change_preserves_gait_phase(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(13.0)
        phase = animator.phase
        animator.select(direction="north_west")
        self.assertEqual(animator.phase, phase)

    def test_idle_transition_holds_phase_and_hides_gait_pose(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(13.0)
        phase = animator.phase
        animator.select(state="idle")
        self.assertEqual(animator.phase, phase)
        self.assertEqual(animator.pose, {})

    def test_gait_pose_is_mirrored_and_joint_names_match_rig(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(14.0)
        pose = animator.pose
        self.assertAlmostEqual(pose["hip_left"][0], -pose["hip_right"][0])
        self.assertLessEqual(pose["knee_left"][0], 0.0)
        self.assertLessEqual(pose["knee_right"][0], 0.0)
        self.assertEqual(
            set(pose),
            {
                "pelvis", "spine_upper", "chest",
                "hip_left", "hip_right", "knee_left", "knee_right",
                "ankle_left", "ankle_right",
                "shoulder_left", "shoulder_right",
            },
        )

    def test_phase_is_quantized_for_sprite_cache_reuse(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        animator.advance(1.0)
        first_pose = animator.pose
        animator.advance(0.1)
        self.assertEqual(animator.phase_index, 0)
        self.assertEqual(animator.pose, first_pose)
        animator.advance(8.0)
        self.assertNotEqual(animator.phase_index, 0)

    def test_walk_and_run_poses_are_valid_for_the_anatomical_rig(self):
        for state in ("walk", "run"):
            with self.subTest(state=state):
                animator = HumanoidBodyAnimator3D(state=state)
                animator.advance(18.0)
                transforms = DEFAULT_HUMANOID_RIG.resolve_pose(animator.pose)
                self.assertEqual(
                    set(transforms), set(DEFAULT_HUMANOID_RIG.joint_names)
                )

    def test_invalid_distance_is_rejected(self):
        animator = HumanoidBodyAnimator3D(state="walk")
        for value in (True, -1.0, float("nan"), float("inf"), "1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    animator.advance(value)

    def test_invalid_selection_is_rejected(self):
        with self.assertRaises(ValueError):
            HumanoidBodyAnimator3D(direction="up")
        with self.assertRaises(ValueError):
            HumanoidBodyAnimator3D(state="jump")


if __name__ == "__main__":
    unittest.main()
