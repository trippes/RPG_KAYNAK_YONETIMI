import math
import unittest
from types import SimpleNamespace

from game_ui.world_rendering.character_rig_renderer import CharacterRigRenderer
from game_ui.world_rendering.character_skeleton import DEFAULT_CHARACTER_SKELETON


class FakeDraw:
    def __init__(self):
        self.calls = []

    def polygon(self, *args, **kwargs):
        self.calls.append(("polygon", args, kwargs))

    def circle(self, *args, **kwargs):
        self.calls.append(("circle", args, kwargs))

    def line(self, *args, **kwargs):
        self.calls.append(("line", args, kwargs))


class TestCharacterRigRenderer(unittest.TestCase):
    def setUp(self):
        self.draw = FakeDraw()
        self.renderer = SimpleNamespace(
            pg=SimpleNamespace(draw=self.draw),
            surface=object(),
        )
        self.rig_renderer = CharacterRigRenderer()

    def test_draws_shaped_body_parts_and_returns_projected_joints(self):
        positions = self.rig_renderer.draw(
            self.renderer, DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0
        )

        self.assertEqual(set(positions), set(DEFAULT_CHARACTER_SKELETON.joint_names))
        self.assertGreaterEqual(
            sum(call[0] == "polygon" for call in self.draw.calls), 22
        )
        # Joint markers are deliberately smaller/fewer than the first preview.
        self.assertGreaterEqual(
            sum(call[0] == "circle" for call in self.draw.calls), 16
        )
        self.assertTrue(any(call[0] == "line" for call in self.draw.calls))

    def test_rest_pose_places_both_feet_on_the_supplied_ground_line(self):
        positions = self.rig_renderer.project_joint_positions(
            DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0
        )

        self.assertAlmostEqual(positions["left_foot"][1], 240.0)
        self.assertAlmostEqual(positions["right_foot"][1], 240.0)

    def test_all_eight_existing_facing_directions_are_supported(self):
        for direction in CharacterRigRenderer.DIRECTIONS:
            with self.subTest(direction=direction):
                positions = self.rig_renderer.project_joint_positions(
                    DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0, facing=direction
                )
                self.assertEqual(set(positions), set(DEFAULT_CHARACTER_SKELETON.joint_names))

    def test_eight_directions_have_distinct_projected_body_orientations(self):
        shoulder_vectors = set()
        for direction in CharacterRigRenderer.DIRECTIONS:
            positions = self.rig_renderer.project_joint_positions(
                DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0, facing=direction
            )
            vector = (
                round(positions["right_shoulder"][0] - positions["left_shoulder"][0], 5),
                round(positions["right_shoulder"][1] - positions["left_shoulder"][1], 5),
            )
            shoulder_vectors.add(vector)

        self.assertEqual(len(shoulder_vectors), 8)

    def test_east_and_west_side_views_project_lateral_axis_in_opposite_depth_directions(self):
        east = self.rig_renderer.project_joint_positions(
            DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0, facing="east"
        )
        west = self.rig_renderer.project_joint_positions(
            DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0, facing="west"
        )

        self.assertLess(east["left_shoulder"][1], east["right_shoulder"][1])
        self.assertGreater(west["left_shoulder"][1], west["right_shoulder"][1])

    def test_joint_pose_changes_articulated_limb_without_mutating_skeleton(self):
        rest = self.rig_renderer.draw(
            self.renderer, DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0
        )
        posed = self.rig_renderer.project_joint_positions(
            DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0,
            {"left_shoulder": math.pi / 2},
        )

        self.assertNotEqual(rest["left_elbow"], posed["left_elbow"])
        rest_elbow = DEFAULT_CHARACTER_SKELETON.joint_positions()["left_elbow"]
        self.assertAlmostEqual(rest_elbow[0], -0.15)
        self.assertAlmostEqual(rest_elbow[1], 0.25)

    def test_palette_overrides_are_applied_and_unknown_keys_rejected(self):
        custom_tunic = (10, 20, 30)
        self.rig_renderer.draw(
            self.renderer, DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0,
            palette={"tunic": custom_tunic},
        )
        self.assertTrue(
            any(
                call[0] == "polygon" and call[1][1] == custom_tunic
                for call in self.draw.calls
            )
        )

        with self.assertRaisesRegex(ValueError, "Unknown character palette"):
            self.rig_renderer.draw(
                self.renderer, DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0,
                palette={"unknown": (0, 0, 0)},
            )

    def test_invalid_direction_scale_and_foot_position_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "direction"):
            self.rig_renderer.project_joint_positions(
                DEFAULT_CHARACTER_SKELETON, (120, 240), 64.0, facing="up"
            )
        with self.assertRaisesRegex(ValueError, "positive"):
            self.rig_renderer.project_joint_positions(
                DEFAULT_CHARACTER_SKELETON, (120, 240), 0
            )
        with self.assertRaisesRegex(ValueError, "finite coordinates"):
            self.rig_renderer.project_joint_positions(
                DEFAULT_CHARACTER_SKELETON, (120, float("nan")), 64.0
            )


if __name__ == "__main__":
    unittest.main()
