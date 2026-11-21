"""Pygame-independent articulated character skeleton geometry.

Coordinates use character-local space: +X points right and +Y points up.
Joint offsets are relative to their parent. Angles are radians, counter-clockwise.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping


def _finite_number(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number.")
    return float(value)


def _vector(value: object, name: str) -> tuple[float, float]:
    if not isinstance(value, (tuple, list)) or len(value) != 2:
        raise ValueError(f"{name} must contain exactly two coordinates.")
    return (_finite_number(value[0], f"{name}.x"), _finite_number(value[1], f"{name}.y"))


@dataclass(frozen=True, slots=True)
class JointDefinition:
    """One joint and its rest-pose offset from its parent."""

    name: str
    parent: str | None
    offset: tuple[float, float]
    rest_angle: float = 0.0

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Joint name must be a non-empty string.")
        if self.parent is not None and (
            not isinstance(self.parent, str) or not self.parent.strip()
        ):
            raise ValueError("Joint parent must be a non-empty name or None.")
        object.__setattr__(self, "offset", _vector(self.offset, "joint.offset"))
        object.__setattr__(self, "rest_angle", _finite_number(self.rest_angle, "joint.rest_angle"))


@dataclass(frozen=True, slots=True)
class BoneDefinition:
    """A drawable connection between two named joints."""

    name: str
    start_joint: str
    end_joint: str
    thickness: float = 0.06

    def __post_init__(self) -> None:
        for field_name in ("name", "start_joint", "end_joint"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Bone {field_name} must be a non-empty string.")
        thickness = _finite_number(self.thickness, "bone.thickness")
        if thickness <= 0:
            raise ValueError("Bone thickness must be greater than zero.")
        object.__setattr__(self, "thickness", thickness)


@dataclass(frozen=True, slots=True)
class CharacterSkeleton:
    """Immutable joint hierarchy and rest geometry for one character type."""

    joints: tuple[JointDefinition, ...]
    bones: tuple[BoneDefinition, ...]
    root_joint: str
    ground_anchor: tuple[float, float]

    def __post_init__(self) -> None:
        joints = tuple(self.joints)
        bones = tuple(self.bones)
        if not joints:
            raise ValueError("A character skeleton must define at least one joint.")
        if any(not isinstance(joint, JointDefinition) for joint in joints):
            raise ValueError("joints must contain JointDefinition values.")
        if any(not isinstance(bone, BoneDefinition) for bone in bones):
            raise ValueError("bones must contain BoneDefinition values.")

        joint_names = [joint.name for joint in joints]
        if len(set(joint_names)) != len(joint_names):
            raise ValueError("Joint names must be unique.")
        if not isinstance(self.root_joint, str) or self.root_joint not in joint_names:
            raise ValueError("root_joint must identify a joint in the skeleton.")

        by_name = {joint.name: joint for joint in joints}
        roots = [joint.name for joint in joints if joint.parent is None]
        if roots != [self.root_joint]:
            raise ValueError("The skeleton must have exactly one declared root joint.")

        for joint in joints:
            if joint.parent is not None and joint.parent not in by_name:
                raise ValueError(f"Joint '{joint.name}' references missing parent '{joint.parent}'.")

        resolved: set[str] = set()

        def visit(name: str, visiting: set[str]) -> None:
            if name in visiting:
                raise ValueError("Joint hierarchy must not contain cycles.")
            if name in resolved:
                return
            visiting.add(name)
            parent = by_name[name].parent
            if parent is not None:
                visit(parent, visiting)
            visiting.remove(name)
            resolved.add(name)

        for name in joint_names:
            visit(name, set())

        bone_names = [bone.name for bone in bones]
        if len(set(bone_names)) != len(bone_names):
            raise ValueError("Bone names must be unique.")
        for bone in bones:
            if bone.start_joint not in by_name or bone.end_joint not in by_name:
                raise ValueError(f"Bone '{bone.name}' references a missing joint.")
            if bone.start_joint == bone.end_joint:
                raise ValueError("A bone must connect two different joints.")

        object.__setattr__(self, "joints", joints)
        object.__setattr__(self, "bones", bones)
        object.__setattr__(self, "ground_anchor", _vector(self.ground_anchor, "ground_anchor"))

    @property
    def joint_names(self) -> tuple[str, ...]:
        """Return joint names in their declared order."""
        return tuple(joint.name for joint in self.joints)

    def joint_positions(
        self, local_rotations: Mapping[str, float] | None = None
    ) -> dict[str, tuple[float, float]]:
        """Resolve joint positions; child offsets inherit parent world rotation."""
        rotations = local_rotations or {}
        unknown = set(rotations) - set(self.joint_names)
        if unknown:
            raise ValueError(f"Rotations reference unknown joints: {', '.join(sorted(unknown))}.")

        by_name = {joint.name: joint for joint in self.joints}
        positions: dict[str, tuple[float, float]] = {}
        world_angles: dict[str, float] = {}

        def resolve(name: str) -> None:
            if name in positions:
                return
            joint = by_name[name]
            angle = _finite_number(rotations.get(name, joint.rest_angle), f"rotation[{name}]")
            if joint.parent is None:
                positions[name] = joint.offset
                world_angles[name] = angle
                return

            resolve(joint.parent)
            parent_x, parent_y = positions[joint.parent]
            parent_angle = world_angles[joint.parent]
            offset_x, offset_y = joint.offset
            cosine = math.cos(parent_angle)
            sine = math.sin(parent_angle)
            positions[name] = (
                parent_x + offset_x * cosine - offset_y * sine,
                parent_y + offset_x * sine + offset_y * cosine,
            )
            world_angles[name] = parent_angle + angle

        for joint in self.joints:
            resolve(joint.name)
        return positions


def _joint(name: str, parent: str | None, offset: tuple[float, float]) -> JointDefinition:
    return JointDefinition(name=name, parent=parent, offset=offset)


DEFAULT_CHARACTER_SKELETON = CharacterSkeleton(
    root_joint="pelvis",
    ground_anchor=(0.0, -0.53),
    joints=(
        _joint("pelvis", None, (0.0, 0.0)),
        _joint("spine", "pelvis", (0.0, 0.16)),
        _joint("chest", "spine", (0.0, 0.18)),
        _joint("neck", "chest", (0.0, 0.12)),
        _joint("head", "neck", (0.0, 0.13)),
        _joint("left_shoulder", "chest", (-0.13, 0.07)),
        _joint("left_elbow", "left_shoulder", (-0.02, -0.16)),
        _joint("left_hand", "left_elbow", (0.0, -0.15)),
        _joint("right_shoulder", "chest", (0.13, 0.07)),
        _joint("right_elbow", "right_shoulder", (0.02, -0.16)),
        _joint("right_hand", "right_elbow", (0.0, -0.15)),
        _joint("left_hip", "pelvis", (-0.075, -0.03)),
        _joint("left_knee", "left_hip", (0.0, -0.23)),
        _joint("left_ankle", "left_knee", (0.0, -0.23)),
        _joint("left_foot", "left_ankle", (0.035, -0.04)),
        _joint("right_hip", "pelvis", (0.075, -0.03)),
        _joint("right_knee", "right_hip", (0.0, -0.23)),
        _joint("right_ankle", "right_knee", (0.0, -0.23)),
        _joint("right_foot", "right_ankle", (0.035, -0.04)),
    ),
    bones=(
        BoneDefinition("pelvis_spine", "pelvis", "spine", 0.13),
        BoneDefinition("spine_chest", "spine", "chest", 0.19),
        BoneDefinition("chest_neck", "chest", "neck", 0.10),
        BoneDefinition("neck_head", "neck", "head", 0.13),
        BoneDefinition("left_upper_arm", "left_shoulder", "left_elbow", 0.075),
        BoneDefinition("left_forearm", "left_elbow", "left_hand", 0.06),
        BoneDefinition("right_upper_arm", "right_shoulder", "right_elbow", 0.075),
        BoneDefinition("right_forearm", "right_elbow", "right_hand", 0.06),
        BoneDefinition("left_thigh", "left_hip", "left_knee", 0.11),
        BoneDefinition("left_shin", "left_knee", "left_ankle", 0.075),
        BoneDefinition("left_foot", "left_ankle", "left_foot", 0.07),
        BoneDefinition("right_thigh", "right_hip", "right_knee", 0.11),
        BoneDefinition("right_shin", "right_knee", "right_ankle", 0.075),
        BoneDefinition("right_foot", "right_ankle", "right_foot", 0.07),
    ),
)
