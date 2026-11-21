import math
import unittest

from game_ui.world_rendering.character_skeleton import (
    BoneDefinition,
    CharacterSkeleton,
    DEFAULT_CHARACTER_SKELETON,
    JointDefinition,
)


class TestCharacterSkeleton(unittest.TestCase):
    def test_default_skeleton_has_unique_hierarchical_joints_and_bones(self):
        skeleton = DEFAULT_CHARACTER_SKELETON

        self.assertEqual(skeleton.root_joint, "pelvis")
        self.assertEqual(len(skeleton.joints), 19)
        self.assertEqual(len(skeleton.bones), 14)
        self.assertEqual(len(skeleton.joint_names), len(set(skeleton.joint_names)))
        self.assertIn("left_knee", skeleton.joint_names)
        self.assertIn("right_elbow", skeleton.joint_names)

    def test_default_rest_pose_resolves_joint_positions_and_ground_anchor(self):
        positions = DEFAULT_CHARACTER_SKELETON.joint_positions()

        self.assertEqual(positions["pelvis"], (0.0, 0.0))
        self.assertEqual(positions["head"], (0.0, 0.59))
        self.assertAlmostEqual(positions["left_foot"][1], -0.53)
        self.assertAlmostEqual(positions["right_foot"][1], -0.53)
        self.assertEqual(DEFAULT_CHARACTER_SKELETON.ground_anchor, (0.0, -0.53))

    def test_parent_rotation_is_inherited_by_descendant_joint_offsets(self):
        positions = DEFAULT_CHARACTER_SKELETON.joint_positions(
            {"pelvis": math.pi / 2}
        )

        self.assertAlmostEqual(positions["spine"][0], -0.16)
        self.assertAlmostEqual(positions["spine"][1], 0.0)
        self.assertAlmostEqual(positions["chest"][0], -0.34)
        self.assertAlmostEqual(positions["chest"][1], 0.0)

    def test_local_rotation_changes_descendant_positions_without_moving_parent(self):
        rest = DEFAULT_CHARACTER_SKELETON.joint_positions()
        posed = DEFAULT_CHARACTER_SKELETON.joint_positions(
            {"left_shoulder": math.pi / 2}
        )

        self.assertEqual(posed["left_shoulder"], rest["left_shoulder"])
        self.assertNotEqual(posed["left_elbow"], rest["left_elbow"])
        self.assertNotEqual(posed["left_hand"], rest["left_hand"])
        self.assertEqual(posed["right_elbow"], rest["right_elbow"])

    def test_pose_overrides_are_independent_between_calls(self):
        first = DEFAULT_CHARACTER_SKELETON.joint_positions(
            {"left_hip": math.pi / 4}
        )
        second = DEFAULT_CHARACTER_SKELETON.joint_positions()

        self.assertNotEqual(first["left_knee"], second["left_knee"])
        self.assertAlmostEqual(second["left_knee"][0], -0.075)
        self.assertAlmostEqual(second["left_knee"][1], -0.26)

    def test_duplicate_joint_names_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unique"):
            CharacterSkeleton(
                joints=(
                    JointDefinition("root", None, (0.0, 0.0)),
                    JointDefinition("root", "root", (0.0, 1.0)),
                ),
                bones=(),
                root_joint="root",
                ground_anchor=(0.0, 0.0),
            )

    def test_missing_parent_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "missing parent"):
            CharacterSkeleton(
                joints=(
                    JointDefinition("root", None, (0.0, 0.0)),
                    JointDefinition("child", "missing", (0.0, 1.0)),
                ),
                bones=(),
                root_joint="root",
                ground_anchor=(0.0, 0.0),
            )

    def test_cyclic_hierarchy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycles"):
            CharacterSkeleton(
                joints=(
                    JointDefinition("root", None, (0.0, 0.0)),
                    JointDefinition("left", "right", (0.0, 1.0)),
                    JointDefinition("right", "left", (0.0, -1.0)),
                ),
                bones=(),
                root_joint="root",
                ground_anchor=(0.0, 0.0),
            )

    def test_bones_must_reference_existing_distinct_joints(self):
        with self.assertRaisesRegex(ValueError, "missing joint"):
            CharacterSkeleton(
                joints=(JointDefinition("root", None, (0.0, 0.0)),),
                bones=(BoneDefinition("invalid", "root", "missing"),),
                root_joint="root",
                ground_anchor=(0.0, 0.0),
            )

        with self.assertRaisesRegex(ValueError, "different joints"):
            CharacterSkeleton(
                joints=(JointDefinition("root", None, (0.0, 0.0)),),
                bones=(BoneDefinition("invalid", "root", "root"),),
                root_joint="root",
                ground_anchor=(0.0, 0.0),
            )

    def test_invalid_vectors_angles_and_bone_thickness_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "finite"):
            JointDefinition("root", None, (0.0, float("nan")))

        with self.assertRaisesRegex(ValueError, "finite"):
            JointDefinition("root", None, (0.0, 0.0), rest_angle=float("inf"))

        with self.assertRaisesRegex(ValueError, "greater than zero"):
            BoneDefinition("invalid", "a", "b", thickness=0)

    def test_unknown_or_non_finite_pose_rotations_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown joints"):
            DEFAULT_CHARACTER_SKELETON.joint_positions({"tail": 0.2})

        with self.assertRaisesRegex(ValueError, "finite"):
            DEFAULT_CHARACTER_SKELETON.joint_positions({"head": float("nan")})


if __name__ == "__main__":
    unittest.main()
