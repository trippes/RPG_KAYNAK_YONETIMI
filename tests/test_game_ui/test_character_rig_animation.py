import math
import unittest

from game_ui.world_rendering.character_rig_animation import CharacterRigAnimator


class TestCharacterRigAnimator(unittest.TestCase):
    def test_idle_pose_contains_only_subtle_body_motion(self):
        animator = CharacterRigAnimator(state="idle")
        pose = animator.update(0.4)

        self.assertIn("spine", pose)
        self.assertIn("chest", pose)
        self.assertLess(abs(pose["spine"]), 0.02)
        self.assertLess(abs(pose["chest"]), 0.02)
        self.assertNotIn("left_knee", pose)

    def test_walk_pose_moves_opposite_legs_and_arms(self):
        animator = CharacterRigAnimator(state="walk")
        pose = animator.update(0.18)

        self.assertAlmostEqual(pose["left_hip"], -pose["right_hip"])
        self.assertNotAlmostEqual(pose["left_hip"], 0.0)
        self.assertNotAlmostEqual(pose["left_shoulder"], pose["right_shoulder"])

    def test_run_has_greater_stride_than_walk_at_same_normalized_phase(self):
        walk = CharacterRigAnimator(state="walk")
        run = CharacterRigAnimator(state="run")
        walk.update(CharacterRigAnimator.CYCLE_SECONDS["walk"] * 0.25)
        run.update(CharacterRigAnimator.CYCLE_SECONDS["run"] * 0.25)

        self.assertGreater(abs(run.pose["left_hip"]), abs(walk.pose["left_hip"]))
        self.assertGreater(
            abs(run.pose["left_shoulder"] - run.pose["right_shoulder"]),
            abs(walk.pose["left_shoulder"] - walk.pose["right_shoulder"]),
        )

    def test_cycle_returns_to_same_pose_after_one_period(self):
        animator = CharacterRigAnimator(state="walk")
        first = animator.update(0.0)
        second = animator.update(CharacterRigAnimator.CYCLE_SECONDS["walk"])

        self.assertEqual(first, second)

    def test_delta_time_is_independent_of_update_chunking(self):
        first = CharacterRigAnimator(state="run")
        second = CharacterRigAnimator(state="run")
        first.update(0.31)
        second.update(0.10)
        second.update(0.21)

        for joint, angle in first.pose.items():
            self.assertAlmostEqual(angle, second.pose[joint])

    def test_direction_change_preserves_gait_phase(self):
        animator = CharacterRigAnimator(direction="south", state="walk")
        animator.update(0.23)
        phase_before = animator.phase
        animator.select(direction="north_west")

        self.assertEqual(animator.direction, "north_west")
        self.assertAlmostEqual(animator.phase, phase_before)
        self.assertEqual(animator.pose, animator._build_pose())

    def test_state_change_preserves_normalized_cycle_phase(self):
        animator = CharacterRigAnimator(state="walk")
        animator.update(0.18)
        normalized_before = animator.elapsed / CharacterRigAnimator.CYCLE_SECONDS["walk"]
        animator.select(state="run")
        normalized_after = animator.elapsed / CharacterRigAnimator.CYCLE_SECONDS["run"]

        self.assertAlmostEqual(normalized_before, normalized_after)

    def test_instances_do_not_share_phase_or_pose(self):
        first = CharacterRigAnimator(state="walk")
        second = CharacterRigAnimator(state="walk")
        first.update(0.2)

        self.assertNotEqual(first.pose, second.pose)
        self.assertEqual(second.elapsed, 0.0)

    def test_pose_property_returns_a_copy(self):
        animator = CharacterRigAnimator(state="run")
        pose = animator.pose
        pose["left_hip"] = 999.0

        self.assertNotEqual(animator.pose["left_hip"], 999.0)

    def test_all_eight_directions_are_accepted(self):
        for direction in CharacterRigAnimator.DIRECTIONS:
            with self.subTest(direction=direction):
                animator = CharacterRigAnimator(direction=direction, state="walk")
                self.assertEqual(animator.direction, direction)
                self.assertIn("left_hip", animator.update(0.1))

    def test_invalid_direction_state_and_delta_time_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "direction"):
            CharacterRigAnimator(direction="up")
        with self.assertRaisesRegex(ValueError, "state"):
            CharacterRigAnimator(state="attack")
        animator = CharacterRigAnimator()
        for delta in (-0.1, float("nan"), float("inf"), True):
            with self.subTest(delta=delta):
                with self.assertRaisesRegex(ValueError, "delta_seconds"):
                    animator.update(delta)

    def test_ankle_compensation_keeps_foot_local_orientation_level(self):
        animator = CharacterRigAnimator(state="run")
        pose = animator.update(0.13)

        self.assertAlmostEqual(
            pose["left_hip"] + pose["left_knee"] + pose["left_ankle"], 0.0
        )
        self.assertAlmostEqual(
            pose["right_hip"] + pose["right_knee"] + pose["right_ankle"], 0.0
        )


if __name__ == "__main__":
    unittest.main()
