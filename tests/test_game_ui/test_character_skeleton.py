import math

import pytest

from game_ui.world_rendering.character_skeleton import (
    BoneDefinition,
    CharacterSkeleton,
    DEFAULT_CHARACTER_SKELETON,
    JointDefinition,
)


def test_default_skeleton_has_unique_hierarchical_joints_and_bones():
    skeleton = DEFAULT_CHARACTER_SKELETON

    assert skeleton.root_joint == "pelvis"
    assert len(skeleton.joints) == 19
    assert len(skeleton.bones) == 14
    assert len(skeleton.joint_names) == len(set(skeleton.joint_names))
    assert "left_knee" in skeleton.joint_names
    assert "right_elbow" in skeleton.joint_names


def test_default_rest_pose_resolves_joint_positions_and_ground_anchor():
    positions = DEFAULT_CHARACTER_SKELETON.joint_positions()

    assert positions["pelvis"] == (0.0, 0.0)
    assert positions["head"] == (0.0, 0.59)
    assert positions["left_foot"][1] == pytest.approx(-0.53)
    assert positions["right_foot"][1] == pytest.approx(-0.53)
    assert DEFAULT_CHARACTER_SKELETON.ground_anchor == (0.0, -0.53)


def test_parent_rotation_is_inherited_by_descendant_joint_offsets():
    positions = DEFAULT_CHARACTER_SKELETON.joint_positions(
        {"pelvis": math.pi / 2}
    )

    assert positions["spine"] == pytest.approx((-0.16, 0.0))
    assert positions["chest"] == pytest.approx((-0.34, 0.0))


def test_local_rotation_changes_descendant_positions_without_moving_parent():
    rest = DEFAULT_CHARACTER_SKELETON.joint_positions()
    posed = DEFAULT_CHARACTER_SKELETON.joint_positions(
        {"left_shoulder": math.pi / 2}
    )

    assert posed["left_shoulder"] == rest["left_shoulder"]
    assert posed["left_elbow"] != rest["left_elbow"]
    assert posed["left_hand"] != rest["left_hand"]
    assert posed["right_elbow"] == rest["right_elbow"]


def test_joint_rotation_overrides_are_independent_per_call():
    first = DEFAULT_CHARACTER_SKELETON.joint_positions(
        {"left_hip": math.pi / 4}
    )
    second = DEFAULT_CHARACTER_SKELETON.joint_positions()

    assert first["left_knee"] != second["left_knee"]
    assert second["left_knee"] == pytest.approx((0.075 * -1, -0.26))


def test_duplicate_joint_names_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        CharacterSkeleton(
            joints=(
                JointDefinition("root", None, (0.0, 0.0)),
                JointDefinition("root", "root", (0.0, 1.0)),
            ),
            bones=(),
            root_joint="root",
            ground_anchor=(0.0, 0.0),
        )


def test_missing_parent_is_rejected():
    with pytest.raises(ValueError, match="missing parent"):
        CharacterSkeleton(
            joints=(JointDefinition("root", None, (0.0, 0.0)),
                    JointDefinition("child", "missing", (0.0, 1.0))),
            bones=(),
            root_joint="root",
            ground_anchor=(0.0, 0.0),
        )


def test_cyclic_hierarchy_is_rejected():
    with pytest.raises(ValueError, match="cycles"):
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


def test_bones_must_reference_existing_distinct_joints():
    with pytest.raises(ValueError, match="missing joint"):
        CharacterSkeleton(
            joints=(JointDefinition("root", None, (0.0, 0.0)),),
            bones=(BoneDefinition("invalid", "root", "missing"),),
            root_joint="root",
            ground_anchor=(0.0, 0.0),
        )


def test_invalid_vectors_angles_and_bone_thickness_are_rejected():
    with pytest.raises(ValueError, match="finite"):
        JointDefinition("root", None, (0.0, float("nan")))

    with pytest.raises(ValueError, match="finite"):
        JointDefinition("root", None, (0.0, 0.0), rest_angle=float("inf"))

    with pytest.raises(ValueError, match="greater than zero"):
        BoneDefinition("invalid", "a", "b", thickness=0)


def test_unknown_or_non_finite_pose_rotations_are_rejected():
    with pytest.raises(ValueError, match="unknown joints"):
        DEFAULT_CHARACTER_SKELETON.joint_positions({"tail": 0.2})

    with pytest.raises(ValueError, match="finite"):
        DEFAULT_CHARACTER_SKELETON.joint_positions({"head": float("nan")})
