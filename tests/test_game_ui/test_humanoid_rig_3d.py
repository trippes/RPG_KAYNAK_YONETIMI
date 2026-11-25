import math
import unittest

from game_ui.world_transform import WorldTransform

from game_ui.world_rendering.humanoid_rig_3d import (
    DEFAULT_HUMANOID_RIG,
    project_point_orthographic,
    BoneDefinition,
    HumanoidRig,
    JointDefinition,
    JointLimit,
)


class TestHumanoidRig3D(unittest.TestCase):
    def test_default_rig_has_unique_hierarchical_anatomical_joints(self):
        rig = DEFAULT_HUMANOID_RIG
        self.assertEqual(rig.root_joint, "pelvis")
        self.assertGreaterEqual(len(rig.joints), 25)
        self.assertEqual(len(rig.joint_names), len(set(rig.joint_names)))
        self.assertIn("clavicle_left", rig.joint_names)
        self.assertIn("clavicle_right", rig.joint_names)
        self.assertIn("scapula_left_control", rig.control_joint_names)
        self.assertIn("heel_left", rig.joint_names)
        self.assertIn("toe_right", rig.joint_names)

    def test_coordinate_contract_uses_positive_y_forward_and_positive_z_up(self):
        rig = DEFAULT_HUMANOID_RIG
        self.assertEqual(rig.forward_axis, (0.0, 1.0, 0.0))
        positions = rig.joint_positions()
        self.assertGreater(positions["head"][2], positions["pelvis"][2])
        self.assertGreater(positions["toe_left"][1], positions["heel_left"][1])

    def test_left_and_right_rest_pose_is_mirrored_across_x(self):
        positions = DEFAULT_HUMANOID_RIG.joint_positions()
        pairs = (
            ("shoulder_left", "shoulder_right"),
            ("elbow_left", "elbow_right"),
            ("wrist_left", "wrist_right"),
            ("hip_left", "hip_right"),
            ("knee_left", "knee_right"),
            ("ankle_left", "ankle_right"),
            ("toe_left", "toe_right"),
        )
        for left, right in pairs:
            self.assertAlmostEqual(positions[left][0], -positions[right][0])
            self.assertAlmostEqual(positions[left][1], positions[right][1])
            self.assertAlmostEqual(positions[left][2], positions[right][2])

    def test_a_pose_has_outward_and_downward_arm_segments(self):
        positions = DEFAULT_HUMANOID_RIG.joint_positions()
        for side in ("left", "right"):
            shoulder = positions[f"shoulder_{side}"]
            elbow = positions[f"elbow_{side}"]
            outward_distance = abs(elbow[0] - shoulder[0])
            downward_distance = shoulder[2] - elbow[2]
            self.assertGreater(outward_distance, 0.0)
            self.assertGreater(downward_distance, 0.0)
            self.assertAlmostEqual(
                math.degrees(math.atan2(downward_distance, outward_distance)),
                30.0,
                delta=0.5,
            )

    def test_rest_pose_has_a_small_elbow_flexion(self):
        positions = DEFAULT_HUMANOID_RIG.joint_positions()
        for side in ("left", "right"):
            shoulder = positions[f"shoulder_{side}"]
            elbow = positions[f"elbow_{side}"]
            wrist = positions[f"wrist_{side}"]
            upper_angle = math.degrees(
                math.atan2(shoulder[2] - elbow[2], abs(elbow[0] - shoulder[0]))
            )
            forearm_angle = math.degrees(
                math.atan2(elbow[2] - wrist[2], abs(wrist[0] - elbow[0]))
            )
            self.assertAlmostEqual(forearm_angle - upper_angle, 5.0, delta=0.5)

    def test_ground_anchor_is_at_heel_height_in_rest_pose(self):
        positions = DEFAULT_HUMANOID_RIG.joint_positions()
        anchor_z = DEFAULT_HUMANOID_RIG.ground_anchor[2]
        self.assertAlmostEqual(positions["heel_left"][2], anchor_z)
        self.assertAlmostEqual(positions["heel_right"][2], anchor_z)

    def test_clavicles_connect_chest_to_shoulder_girdle(self):
        rig = DEFAULT_HUMANOID_RIG
        by_name = {joint.name: joint for joint in rig.joints}
        self.assertEqual(by_name["clavicle_left"].parent, "chest")
        self.assertEqual(by_name["shoulder_left"].parent, "clavicle_left")
        self.assertEqual(by_name["clavicle_right"].parent, "chest")
        self.assertEqual(by_name["shoulder_right"].parent, "clavicle_right")
        bone_names = {bone.name for bone in rig.bones}
        self.assertIn("clavicle_left", bone_names)
        self.assertIn("clavicle_right", bone_names)

    def test_scapula_controls_are_non_deforming_auxiliary_joints(self):
        rig = DEFAULT_HUMANOID_RIG
        controls = {joint.name: joint for joint in rig.joints if joint.is_control}
        self.assertEqual(
            set(controls),
            {"scapula_left_control", "scapula_right_control"},
        )
        for control_name in controls:
            self.assertFalse(
                any(
                    control_name in (bone.start_joint, bone.end_joint)
                    for bone in rig.bones
                )
            )

    def test_parent_rotation_is_inherited_by_descendant_offsets(self):
        rest = DEFAULT_HUMANOID_RIG.joint_positions()
        posed = DEFAULT_HUMANOID_RIG.joint_positions({"pelvis": (0.0, 0.0, math.pi / 2)})
        self.assertAlmostEqual(posed["spine_lower"][0], rest["spine_lower"][0])
        self.assertAlmostEqual(posed["spine_lower"][1], rest["spine_lower"][1])
        self.assertAlmostEqual(posed["hip_left"][0], -rest["hip_left"][1])
        self.assertAlmostEqual(posed["hip_left"][1], rest["hip_left"][0])

    def test_child_rotation_does_not_move_its_joint_origin(self):
        rest = DEFAULT_HUMANOID_RIG.joint_positions()
        posed = DEFAULT_HUMANOID_RIG.joint_positions({"shoulder_left": (0.0, 0.0, 0.7)})
        self.assertEqual(posed["shoulder_left"], rest["shoulder_left"])
        self.assertNotEqual(posed["elbow_left"], rest["elbow_left"])
        self.assertEqual(posed["elbow_right"], rest["elbow_right"])

    def test_joint_limits_clamp_local_euler_rotation(self):
        posed = DEFAULT_HUMANOID_RIG.resolve_pose({"knee_left": (-10.0, 0.0, 0.0)})
        rest = DEFAULT_HUMANOID_RIG.resolve_pose()
        self.assertNotEqual(posed["ankle_left"].position, rest["ankle_left"].position)

    def test_bone_lengths_are_positive_and_deterministic(self):
        lengths = DEFAULT_HUMANOID_RIG.bone_lengths()
        self.assertEqual(set(lengths), {bone.name for bone in DEFAULT_HUMANOID_RIG.bones})
        self.assertTrue(all(length > 0 for length in lengths.values()))
        self.assertEqual(lengths, DEFAULT_HUMANOID_RIG.bone_lengths())

    def test_local_joint_translation_moves_descendants_without_mutating_rest_pose(self):
        rig = DEFAULT_HUMANOID_RIG
        rest = rig.joint_positions()
        posed = rig.joint_positions(local_translations={"pelvis": (0.0, 0.0, -0.08)})
        self.assertAlmostEqual(posed["pelvis"][2], -0.08)
        self.assertAlmostEqual(posed["head"][2], rest["head"][2] - 0.08)
        self.assertAlmostEqual(posed["heel_left"][2], rest["heel_left"][2] - 0.08)
        self.assertEqual(rig.joint_positions(), rest)

    def test_unknown_joint_translation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown joints"):
            DEFAULT_HUMANOID_RIG.joint_positions(
                local_translations={"tail": (0.0, 0.0, 0.1)}
            )

    def test_pose_does_not_mutate_rest_geometry(self):
        before = DEFAULT_HUMANOID_RIG.joint_positions()
        DEFAULT_HUMANOID_RIG.joint_positions({"hip_left": (0.4, 0.0, 0.0)})
        after = DEFAULT_HUMANOID_RIG.joint_positions()
        self.assertEqual(before, after)

    def test_isometric_projection_matches_world_transform_basis(self):
        point = (0.25, 0.4, 0.75)
        front = project_point_orthographic(point)
        side = project_point_orthographic(point, yaw=math.pi / 2)
        self.assertAlmostEqual(front[0], -0.15)
        self.assertAlmostEqual(front[1], -0.425)
        self.assertAlmostEqual(side[0], 0.65)
        self.assertAlmostEqual(side[1], -0.675)

    def test_character_forward_projection_matches_all_world_octants(self):
        transform = WorldTransform()
        screen_vectors = (
            (1.0, 0.0), (math.sqrt(0.5), math.sqrt(0.5)),
            (0.0, 1.0), (-math.sqrt(0.5), math.sqrt(0.5)),
            (-1.0, 0.0), (-math.sqrt(0.5), -math.sqrt(0.5)),
            (0.0, -1.0), (math.sqrt(0.5), -math.sqrt(0.5)),
        )
        for screen_vector in screen_vectors:
            with self.subTest(screen_vector=screen_vector):
                world_dx, world_dy = transform.unproject_vector(*screen_vector)
                yaw = math.atan2(world_dx, world_dy)
                projected_forward = project_point_orthographic(
                    (0.0, 1.0, 0.0), yaw=yaw,
                )
                world_length = math.hypot(world_dx, world_dy)
                expected = transform.project_vector(
                    world_dx / world_length, world_dy / world_length,
                )
                self.assertAlmostEqual(projected_forward[0], expected[0])
                self.assertAlmostEqual(projected_forward[1], expected[1])

    def test_projection_rejects_vertical_camera_pitch(self):
        with self.assertRaisesRegex(ValueError, "pitch must not be vertical"):
            project_point_orthographic((0.0, 0.0, 0.0), pitch=math.pi / 2)

    def test_projection_rejects_invalid_scale_and_coordinates(self):
        with self.assertRaisesRegex(ValueError, "greater than zero"):
            project_point_orthographic((0.0, 0.0, 0.0), scale=0)
        with self.assertRaisesRegex(ValueError, "three coordinates"):
            project_point_orthographic((0.0, 1.0))

    def test_unknown_joint_rotation_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown joints"):
            DEFAULT_HUMANOID_RIG.joint_positions({"tail": (0.0, 0.0, 0.0)})

    def test_invalid_vectors_and_limits_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "three coordinates"):
            JointDefinition("root", None, (0.0, 0.0))
        with self.assertRaisesRegex(ValueError, "minimum must be"):
            JointLimit((1.0, 0.0, 0.0), (0.0, 1.0, 1.0))
        with self.assertRaisesRegex(ValueError, "finite"):
            JointDefinition("root", None, (0.0, 0.0, float("nan")))

    def test_invalid_hierarchy_and_bones_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "cycles"):
            HumanoidRig(
                joints=(
                    JointDefinition("root", None, (0.0, 0.0, 0.0)),
                    JointDefinition("a", "b", (0.0, 0.0, 1.0)),
                    JointDefinition("b", "a", (0.0, 0.0, -1.0)),
                ),
                bones=(),
                root_joint="root",
                ground_anchor=(0.0, 0.0, -1.0),
            )
        with self.assertRaisesRegex(ValueError, "missing joint"):
            HumanoidRig(
                joints=(JointDefinition("root", None, (0.0, 0.0, 0.0)),),
                bones=(BoneDefinition("bad", "root", "missing"),),
                root_joint="root",
                ground_anchor=(0.0, 0.0, 0.0),
            )


if __name__ == "__main__":
    unittest.main()
