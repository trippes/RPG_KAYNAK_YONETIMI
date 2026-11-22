import math
import unittest

from game_ui.world_rendering.humanoid_body_3d import (
    DEFAULT_HUMANOID_BODY,
    BodyPartDefinition,
    BodySurfaceDefinition,
)
from game_ui.world_rendering.humanoid_rig_3d import DEFAULT_HUMANOID_RIG


class TestHumanoidBody3D(unittest.TestCase):
    def test_default_body_contains_anatomical_core_and_bilateral_limbs(self):
        names = {part.name for part in DEFAULT_HUMANOID_BODY.parts}
        for expected in (
            "left_clavicle_volume",
            "right_clavicle_volume",
            "head_volume",
            "shoulder_left_volume",
            "shoulder_right_volume",
            "left_hand_volume",
            "right_hand_volume",
        ):
            self.assertIn(expected, names)
        surface_names = {surface.name for surface in DEFAULT_HUMANOID_BODY.surfaces}
        self.assertIn("connected_torso", surface_names)
        self.assertIn("connected_foot_left", surface_names)
        self.assertIn("connected_foot_right", surface_names)

    def test_torso_is_one_connected_surface_with_ordered_anatomical_landmarks(self):
        surfaces = {surface.name: surface for surface in DEFAULT_HUMANOID_BODY.surfaces}
        self.assertIn("connected_torso", surfaces)
        torso = surfaces["connected_torso"]
        self.assertEqual(torso.name, "connected_torso")
        self.assertEqual(
            tuple(station[0] for station in torso.stations),
            ("pelvis", "spine_lower", "spine_upper", "chest", "neck"),
        )
        self.assertEqual(torso.sides, 8)
        self.assertEqual(torso.subdivisions, 3)

    def test_connected_surfaces_cover_torso_arms_and_legs(self):
        names = {surface.name for surface in DEFAULT_HUMANOID_BODY.surfaces}
        self.assertEqual(
            names,
            {
                "connected_torso",
                "connected_arm_left",
                "connected_arm_right",
                "connected_hand_left",
                "connected_hand_right",
                "connected_leg_left",
                "connected_leg_right",
                "connected_foot_left",
                "connected_foot_right",
            },
        )

    def test_connected_torso_surface_has_shared_ring_topology(self):
        mesh = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        torso = next(
            surface for surface in DEFAULT_HUMANOID_BODY.surfaces
            if surface.name == "connected_torso"
        )
        expected_torso_triangles = (
            (len(torso.stations) - 1) * torso.subdivisions * torso.sides * 2
        )
        self.assertGreaterEqual(len(mesh), expected_torso_triangles)

    def test_surface_rejects_invalid_station_width(self):
        with self.assertRaisesRegex(ValueError, "positive"):
            BodySurfaceDefinition(
                "invalid",
                (("pelvis", 0.1, 0.1, "skin"), ("chest", 0.0, 0.1, "skin")),
            )

    def test_mesh_is_deterministic_and_has_triangles(self):
        first = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        second = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        self.assertGreater(len(first), 300)
        self.assertLessEqual(len(first), 1300)
        self.assertEqual(first, second)
        self.assertIs(first, second)

    def test_all_mesh_vertices_have_normalized_skin_weights(self):
        mesh = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        joint_names = set(DEFAULT_HUMANOID_RIG.joint_names)
        for triangle in mesh:
            self.assertEqual(len(triangle.vertex_weights), 3)
            for influences in triangle.vertex_weights:
                self.assertGreaterEqual(len(influences), 1)
                self.assertLessEqual(len(influences), 2)
                self.assertAlmostEqual(sum(weight for _, weight in influences), 1.0)
                for joint_name, weight in influences:
                    self.assertIn(joint_name, joint_names)
                    self.assertGreaterEqual(weight, 0.0)

    def test_elbow_pose_deforms_the_weighted_arm_surface(self):
        rest_mesh = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        posed_mesh = DEFAULT_HUMANOID_BODY.build_mesh(
            DEFAULT_HUMANOID_RIG,
            {"elbow_left": (0.0, 0.0, -1.0)},
        )
        self.assertNotEqual(rest_mesh, posed_mesh)
        rest_left_arm = [
            triangle for triangle in rest_mesh
            if any(
                joint_name in {"shoulder_left", "elbow_left", "wrist_left"}
                for influences in triangle.vertex_weights
                for joint_name, _ in influences
            )
        ]
        posed_left_arm = [
            triangle for triangle in posed_mesh
            if any(
                joint_name in {"shoulder_left", "elbow_left", "wrist_left"}
                for influences in triangle.vertex_weights
                for joint_name, _ in influences
            )
        ]
        self.assertEqual(len(rest_left_arm), len(posed_left_arm))
        self.assertTrue(
            any(first.vertices != second.vertices for first, second in zip(rest_left_arm, posed_left_arm))
        )

    def test_zero_pose_rotation_preserves_bind_mesh(self):
        rest_mesh = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        zero_pose_mesh = DEFAULT_HUMANOID_BODY.build_mesh(
            DEFAULT_HUMANOID_RIG,
            {"elbow_left": (0.0, 0.0, 0.0)},
        )
        for rest_triangle, posed_triangle in zip(rest_mesh, zero_pose_mesh, strict=True):
            for rest_vertex, posed_vertex in zip(
                rest_triangle.vertices, posed_triangle.vertices, strict=True
            ):
                for rest_value, posed_value in zip(rest_vertex, posed_vertex, strict=True):
                    self.assertAlmostEqual(rest_value, posed_value, places=10)

    def test_bind_geometry_cache_is_reused_across_different_poses(self):
        from game_ui.world_rendering.humanoid_body_3d import _build_bind_mesh_cached

        DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        before = _build_bind_mesh_cached.cache_info().hits
        DEFAULT_HUMANOID_BODY.build_mesh(
            DEFAULT_HUMANOID_RIG,
            {"elbow_left": (0.0, 0.0, -0.8)},
        )
        after = _build_bind_mesh_cached.cache_info().hits
        self.assertGreater(after, before)

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
        self.assertIn("left_hand_volume", names)
        self.assertIn("right_hand_volume", names)
        surfaces = {surface.name for surface in DEFAULT_HUMANOID_BODY.surfaces}
        for name in (
            "connected_arm_left", "connected_arm_right",
            "connected_hand_left", "connected_hand_right",
            "connected_leg_left", "connected_leg_right",
            "connected_foot_left", "connected_foot_right",
        ):
            self.assertIn(name, surfaces)

    def test_surface_topology_uses_compact_consistent_rings(self):
        parts = {part.name: part for part in DEFAULT_HUMANOID_BODY.parts}
        self.assertIn("left_clavicle_volume", parts)
        self.assertIn("right_clavicle_volume", parts)
        for surface in DEFAULT_HUMANOID_BODY.surfaces:
            self.assertGreaterEqual(len(surface.stations), 2)
            self.assertEqual(surface.sides, 8)
            self.assertIn(surface.subdivisions, (2, 3))

    def test_triangle_normals_are_precomputed_and_finite(self):
        mesh = DEFAULT_HUMANOID_BODY.build_mesh(DEFAULT_HUMANOID_RIG)
        for triangle in mesh:
            self.assertEqual(len(triangle.normal), 3)
            self.assertTrue(all(math.isfinite(value) for value in triangle.normal))
            self.assertLessEqual(math.sqrt(sum(value * value for value in triangle.normal)), 1.0000001)

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
