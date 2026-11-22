import unittest

from game_ui.world_rendering.humanoid_body_3d import (
    DEFAULT_HUMANOID_BODY,
    BodyPartDefinition,
)
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


class TestHumanoidBody3D(unittest.TestCase):
    def test_default_body_contains_anatomical_core_and_bilateral_limbs(self):
        names = {part.name for part in DEFAULT_HUMANOID_BODY.parts}
        for expected in (
            "pelvis_volume",
            "abdomen_volume",
            "waist_volume",
            "chest_volume",
            "upper_back_volume",
            "left_clavicle_volume",
            "right_clavicle_volume",
            "neck_volume",
            "head_volume",
            "shoulder_left_volume",
            "shoulder_right_volume",
            "left_upper_arm_volume",
            "right_upper_arm_volume",
            "left_thigh_volume",
            "right_thigh_volume",
            "left_foot_volume",
            "right_foot_volume",
        ):
            self.assertIn(expected, names)

    def test_mesh_is_deterministic_and_has_triangles(self):
        first = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        second = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        self.assertGreater(len(first), 300)
        self.assertEqual(first, second)
        self.assertIs(first, second)

    def test_mesh_follows_rig_pose_without_mutating_rest_geometry(self):
        rest_positions = DEFAULT_HUMANOID_RIG.joint_positions()
        rest_mesh = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        posed_mesh = DEFAULT_HUMANOID_BODY.build_mesh(
            DEFAULT_HUMANOID_RIG,
            {"shoulder_left": (0.0, 0.0, 0.55)},
        )
        self.assertNotEqual(rest_mesh, posed_mesh)
        self.assertEqual(rest_positions, DEFAULT_HUMANOID_RIG.joint_positions())

    def test_left_and_right_limb_part_inventory_is_balanced(self):
        names = {part.name for part in DEFAULT_HUMANOID_BODY.parts}
        for suffix in ("upper_arm", "elbow", "forearm", "hand", "thigh", "knee", "shin", "foot"):
            self.assertIn(f"left_{suffix}_volume", names)
            self.assertIn(f"right_{suffix}_volume", names)

    def test_limb_segments_use_anatomical_taper_profiles(self):
        parts = {part.name: part for part in DEFAULT_HUMANOID_BODY.parts}
        for name in (
            "left_upper_arm_volume",
            "right_upper_arm_volume",
            "left_forearm_volume",
            "right_forearm_volume",
            "left_thigh_volume",
            "right_thigh_volume",
            "left_shin_volume",
            "right_shin_volume",
        ):
            self.assertIsNotNone(parts[name].profile)
            self.assertGreaterEqual(len(parts[name].profile), 7)
            self.assertGreater(
                max(width for _, width in parts[name].profile),
                min(width for _, width in parts[name].profile),
            )

    def test_unit_mesh_samples_are_cached(self):
        from game_ui.world_rendering.humanoid_body_3d import (
            _latitude_samples,
            _unit_circle,
        )

        self.assertIs(_unit_circle(10), _unit_circle(10))
        self.assertIs(_latitude_samples(7), _latitude_samples(7))

    def test_invalid_segment_profile_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "strictly increasing"):
            BodyPartDefinition(
                "bad_profile",
                "shoulder_left",
                "elbow_left",
                (0.04, 0.04, 0.04),
                "skin",
                "segment",
                ((0.0, 0.5), (0.5, 0.8), (0.4, 0.7)),
            )

    def test_invalid_body_part_geometry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            BodyPartDefinition("bad", "pelvis", "pelvis", (0.1, 0.0, 0.1), "skin")
        with self.assertRaisesRegex(ValueError, "shape"):
            BodyPartDefinition(
                "bad", "pelvis", "pelvis", (0.1, 0.1, 0.1), "skin", "box"
            )

    def test_unknown_joint_reference_is_rejected_when_building_mesh(self):
        invalid = BodyPartDefinition(
            "bad", "unknown", "unknown", (0.1, 0.1, 0.1), "skin"
        )
        from game_ui.world_rendering.humanoid_body_3d import HumanoidBodyModel

        with self.assertRaisesRegex(ValueError, "unknown rig joint"):
            HumanoidBodyModel((invalid,)).build_mesh(DEFAULT_HUMANOID_RIG)


if __name__ == "__main__":
    unittest.main()
