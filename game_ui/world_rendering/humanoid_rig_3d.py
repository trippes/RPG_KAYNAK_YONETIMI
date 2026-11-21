"""Pygame-independent 3D humanoid anatomy and rest-pose rig.

Coordinate contract:
- Right-handed local coordinates.
- +X: character anatomical right.
- +Y: character forward.
- +Z: up.
- Angles: radians, intrinsic XYZ Euler inputs.
- The pelvis is the rig root; the ground anchor is measured from the pelvis.
- Runtime world position remains external and authoritative.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, TypeAlias

Vec3: TypeAlias = tuple[float, float, float]
Euler3: TypeAlias = tuple[float, float, float]
Quaternion: TypeAlias = tuple[float, float, float, float]


def _finite(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be a finite number.")
    return result


def _vec3(value: object, name: str) -> Vec3:
    if not isinstance(value, (tuple, list)) or len(value) != 3:
        raise ValueError(f"{name} must contain exactly three coordinates.")
    return (
        _finite(value[0], f"{name}.x"),
        _finite(value[1], f"{name}.y"),
        _finite(value[2], f"{name}.z"),
    )


def _euler3(value: object, name: str) -> Euler3:
    return _vec3(value, name)


def _quaternion(value: object, name: str) -> Quaternion:
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        raise ValueError(f"{name} must contain four quaternion components.")
    result = tuple(_finite(component, f"{name}[{index}]") for index, component in enumerate(value))
    magnitude = math.sqrt(sum(component * component for component in result))
    if magnitude <= 1e-12:
        raise ValueError(f"{name} must not be the zero quaternion.")
    return tuple(component / magnitude for component in result)  # type: ignore[return-value]


def _quat_multiply(first: Quaternion, second: Quaternion) -> Quaternion:
    aw, ax, ay, az = first
    bw, bx, by, bz = second
    return _quaternion(
        (
            aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
        ),
        "quaternion product",
    )


def _quat_from_euler_xyz(rotation: Euler3) -> Quaternion:
    x, y, z = (component * 0.5 for component in rotation)
    cx, sx = math.cos(x), math.sin(x)
    cy, sy = math.cos(y), math.sin(y)
    cz, sz = math.cos(z), math.sin(z)
    return _quaternion(
        (
            cx * cy * cz + sx * sy * sz,
            sx * cy * cz - cx * sy * sz,
            cx * sy * cz + sx * cy * sz,
            cx * cy * sz - sx * sy * cz,
        ),
        "Euler quaternion",
    )


def _quat_rotate(rotation: Quaternion, vector: Vec3) -> Vec3:
    w, x, y, z = rotation
    vx, vy, vz = vector
    tx = 2.0 * (y * vz - z * vy)
    ty = 2.0 * (z * vx - x * vz)
    tz = 2.0 * (x * vy - y * vx)
    return (
        vx + w * tx + y * tz - z * ty,
        vy + w * ty + z * tx - x * tz,
        vz + w * tz + x * ty - y * tx,
    )


@dataclass(frozen=True, slots=True)
class JointLimit:
    """Per-axis local Euler limits in radians."""

    minimum: Euler3
    maximum: Euler3

    def __post_init__(self) -> None:
        minimum = _euler3(self.minimum, "joint_limit.minimum")
        maximum = _euler3(self.maximum, "joint_limit.maximum")
        if any(low > high for low, high in zip(minimum, maximum, strict=True)):
            raise ValueError("Each joint limit minimum must be <= its maximum.")
        object.__setattr__(self, "minimum", minimum)
        object.__setattr__(self, "maximum", maximum)

    def clamp(self, rotation: Euler3) -> Euler3:
        return tuple(
            max(low, min(high, value))
            for value, low, high in zip(rotation, self.minimum, self.maximum, strict=True)
        )  # type: ignore[return-value]


@dataclass(frozen=True, slots=True)
class JointDefinition:
    """A joint whose offset and rest orientation are relative to its parent."""

    name: str
    parent: str | None
    offset: Vec3
    rest_rotation: Quaternion = (1.0, 0.0, 0.0, 0.0)
    limit: JointLimit | None = None
    is_control: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Joint name must be a non-empty string.")
        if self.parent is not None and (
            not isinstance(self.parent, str) or not self.parent.strip()
        ):
            raise ValueError("Joint parent must be a non-empty name or None.")
        if self.limit is not None and not isinstance(self.limit, JointLimit):
            raise ValueError("limit must be a JointLimit or None.")
        if not isinstance(self.is_control, bool):
            raise ValueError("is_control must be a boolean.")
        object.__setattr__(self, "offset", _vec3(self.offset, "joint.offset"))
        object.__setattr__(
            self, "rest_rotation", _quaternion(self.rest_rotation, "joint.rest_rotation")
        )


@dataclass(frozen=True, slots=True)
class BoneDefinition:
    """A semantic connection between two joints, with normalized display thickness."""

    name: str
    start_joint: str
    end_joint: str
    thickness: float = 0.04
    deform: bool = True

    def __post_init__(self) -> None:
        for field_name in ("name", "start_joint", "end_joint"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"Bone {field_name} must be a non-empty string.")
        thickness = _finite(self.thickness, "bone.thickness")
        if thickness <= 0:
            raise ValueError("Bone thickness must be greater than zero.")
        if not isinstance(self.deform, bool):
            raise ValueError("deform must be a boolean.")
        object.__setattr__(self, "thickness", thickness)


@dataclass(frozen=True, slots=True)
class JointTransform:
    """Resolved joint transform in rig-local space."""

    position: Vec3
    rotation: Quaternion


@dataclass(frozen=True, slots=True)
class HumanoidRig:
    """Immutable 3D humanoid hierarchy and its anatomical rest geometry."""

    joints: tuple[JointDefinition, ...]
    bones: tuple[BoneDefinition, ...]
    root_joint: str
    ground_anchor: Vec3
    forward_axis: Vec3 = (0.0, 1.0, 0.0)

    def __post_init__(self) -> None:
        joints = tuple(self.joints)
        bones = tuple(self.bones)
        if not joints:
            raise ValueError("A humanoid rig must define at least one joint.")
        if any(not isinstance(joint, JointDefinition) for joint in joints):
            raise ValueError("joints must contain JointDefinition values.")
        if any(not isinstance(bone, BoneDefinition) for bone in bones):
            raise ValueError("bones must contain BoneDefinition values.")

        names = [joint.name for joint in joints]
        if len(set(names)) != len(names):
            raise ValueError("Joint names must be unique.")
        if not isinstance(self.root_joint, str) or self.root_joint not in names:
            raise ValueError("root_joint must identify a joint in the rig.")

        by_name = {joint.name: joint for joint in joints}
        roots = [joint.name for joint in joints if joint.parent is None]
        if roots != [self.root_joint]:
            raise ValueError("The rig must have exactly one declared root joint.")
        for joint in joints:
            if joint.parent is not None and joint.parent not in by_name:
                raise ValueError(
                    f"Joint '{joint.name}' references missing parent '{joint.parent}'."
                )

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

        for name in names:
            visit(name, set())

        bone_names = [bone.name for bone in bones]
        if len(set(bone_names)) != len(bone_names):
            raise ValueError("Bone names must be unique.")
        for bone in bones:
            if bone.start_joint not in by_name or bone.end_joint not in by_name:
                raise ValueError(f"Bone '{bone.name}' references a missing joint.")
            if bone.start_joint == bone.end_joint:
                raise ValueError("A bone must connect two different joints.")

        forward = _vec3(self.forward_axis, "forward_axis")
        forward_length = math.sqrt(sum(component * component for component in forward))
        if forward_length <= 1e-12:
            raise ValueError("forward_axis must not be the zero vector.")

        object.__setattr__(self, "joints", joints)
        object.__setattr__(self, "bones", bones)
        object.__setattr__(self, "ground_anchor", _vec3(self.ground_anchor, "ground_anchor"))
        object.__setattr__(
            self, "forward_axis", tuple(component / forward_length for component in forward)
        )

    @property
    def joint_names(self) -> tuple[str, ...]:
        return tuple(joint.name for joint in self.joints)

    @property
    def control_joint_names(self) -> tuple[str, ...]:
        return tuple(joint.name for joint in self.joints if joint.is_control)

    def resolve_pose(
        self, local_rotations: Mapping[str, Euler3] | None = None
    ) -> dict[str, JointTransform]:
        """Resolve a pose from local XYZ Euler offsets, clamped by joint limits."""
        rotations = local_rotations or {}
        unknown = set(rotations) - set(self.joint_names)
        if unknown:
            raise ValueError(f"Rotations reference unknown joints: {', '.join(sorted(unknown))}.")

        by_name = {joint.name: joint for joint in self.joints}
        transforms: dict[str, JointTransform] = {}

        def resolve(name: str) -> None:
            if name in transforms:
                return
            joint = by_name[name]
            pose_rotation = _euler3(
                rotations.get(name, (0.0, 0.0, 0.0)), f"rotation[{name}]"
            )
            if joint.limit is not None:
                pose_rotation = joint.limit.clamp(pose_rotation)
            local_pose = _quat_from_euler_xyz(pose_rotation)
            local_rotation = _quat_multiply(joint.rest_rotation, local_pose)

            if joint.parent is None:
                transforms[name] = JointTransform(joint.offset, local_rotation)
                return

            resolve(joint.parent)
            parent = transforms[joint.parent]
            world_offset = _quat_rotate(parent.rotation, joint.offset)
            position = tuple(
                parent.position[index] + world_offset[index] for index in range(3)
            )
            transforms[name] = JointTransform(
                position, _quat_multiply(parent.rotation, local_rotation)
            )

        for joint in self.joints:
            resolve(joint.name)
        return transforms

    def joint_positions(
        self, local_rotations: Mapping[str, Euler3] | None = None
    ) -> dict[str, Vec3]:
        """Return resolved rig-local joint positions."""
        return {
            name: transform.position
            for name, transform in self.resolve_pose(local_rotations).items()
        }

    def bone_lengths(self) -> dict[str, float]:
        """Return rest-pose lengths for all semantic bones."""
        positions = self.joint_positions()
        return {
            bone.name: math.dist(
                positions[bone.start_joint], positions[bone.end_joint]
            )
            for bone in self.bones
        }


def _joint(
    name: str,
    parent: str | None,
    offset: Vec3,
    *,
    limit: JointLimit | None = None,
    control: bool = False,
) -> JointDefinition:
    return JointDefinition(
        name=name, parent=parent, offset=offset, limit=limit, is_control=control
    )


def _bone(name: str, start: str, end: str, thickness: float = 0.04) -> BoneDefinition:
    return BoneDefinition(name, start, end, thickness)


SHOULDER_LIMIT = JointLimit(
    minimum=(-1.2, -1.0, -1.6),
    maximum=(1.2, 1.0, 1.6),
)
ELBOW_LIMIT = JointLimit(
    minimum=(-0.05, -0.05, -2.53),
    maximum=(0.05, 0.05, 0.0),
)
WRIST_LIMIT = JointLimit(
    minimum=(-1.05, -0.7, -0.7),
    maximum=(1.05, 0.7, 0.7),
)
HIP_LIMIT = JointLimit(
    minimum=(-1.75, -0.8, -0.8),
    maximum=(1.75, 0.8, 0.8),
)
KNEE_LIMIT = JointLimit(
    minimum=(-2.36, -0.08, -0.08),
    maximum=(0.0, 0.08, 0.08),
)
ANKLE_LIMIT = JointLimit(
    minimum=(-0.35, -0.45, -0.45),
    maximum=(0.87, 0.45, 0.45),
)


def _build_default_rig() -> HumanoidRig:
    joints = (
        _joint("pelvis", None, (0.0, 0.0, 0.0)),
        _joint("spine_lower", "pelvis", (0.0, 0.0, 0.10)),
        _joint("spine_upper", "spine_lower", (0.0, 0.0, 0.12)),
        _joint("chest", "spine_upper", (0.0, 0.0, 0.08)),
        _joint("neck", "chest", (0.0, 0.0, 0.09)),
        _joint("head", "neck", (0.0, 0.0, 0.10)),
        _joint("clavicle_left", "chest", (-0.075, 0.0, 0.045)),
        _joint("shoulder_left", "clavicle_left", (-0.105, 0.0, 0.005), limit=SHOULDER_LIMIT),
        _joint(
            "scapula_left_control",
            "chest",
            (-0.11, -0.025, 0.035),
            control=True,
        ),
        _joint("elbow_left", "shoulder_left", (-0.19, 0.0, -0.11), limit=ELBOW_LIMIT),
        _joint("wrist_left", "elbow_left", (-0.17, 0.0, -0.10), limit=WRIST_LIMIT),
        _joint("hand_left", "wrist_left", (-0.055, 0.0, 0.0)),
        _joint("clavicle_right", "chest", (0.075, 0.0, 0.045)),
        _joint("shoulder_right", "clavicle_right", (0.105, 0.0, 0.005), limit=SHOULDER_LIMIT),
        _joint(
            "scapula_right_control",
            "chest",
            (0.11, -0.025, 0.035),
            control=True,
        ),
        _joint("elbow_right", "shoulder_right", (0.19, 0.0, -0.11), limit=ELBOW_LIMIT),
        _joint("wrist_right", "elbow_right", (0.17, 0.0, -0.10), limit=WRIST_LIMIT),
        _joint("hand_right", "wrist_right", (0.055, 0.0, 0.0)),
        _joint("hip_left", "pelvis", (-0.075, 0.0, -0.02), limit=HIP_LIMIT),
        _joint("knee_left", "hip_left", (0.0, 0.0, -0.22), limit=KNEE_LIMIT),
        _joint("ankle_left", "knee_left", (0.0, 0.0, -0.22), limit=ANKLE_LIMIT),
        _joint("heel_left", "ankle_left", (0.0, -0.035, -0.03)),
        _joint("foot_ball_left", "ankle_left", (0.0, 0.095, -0.03)),
        _joint("toe_left", "foot_ball_left", (0.0, 0.06, 0.0)),
        _joint("hip_right", "pelvis", (0.075, 0.0, -0.02), limit=HIP_LIMIT),
        _joint("knee_right", "hip_right", (0.0, 0.0, -0.22), limit=KNEE_LIMIT),
        _joint("ankle_right", "knee_right", (0.0, 0.0, -0.22), limit=ANKLE_LIMIT),
        _joint("heel_right", "ankle_right", (0.0, -0.035, -0.03)),
        _joint("foot_ball_right", "ankle_right", (0.0, 0.095, -0.03)),
        _joint("toe_right", "foot_ball_right", (0.0, 0.06, 0.0)),
    )
    bones = (
        _bone("pelvis_spine_lower", "pelvis", "spine_lower", 0.12),
        _bone("spine_lower_upper", "spine_lower", "spine_upper", 0.13),
        _bone("spine_upper_chest", "spine_upper", "chest", 0.17),
        _bone("chest_neck", "chest", "neck", 0.09),
        _bone("neck_head", "neck", "head", 0.11),
        _bone("clavicle_left", "chest", "shoulder_left", 0.045),
        _bone("clavicle_right", "chest", "shoulder_right", 0.045),
        _bone("left_upper_arm", "shoulder_left", "elbow_left", 0.075),
        _bone("left_forearm", "elbow_left", "wrist_left", 0.055),
        _bone("left_hand", "wrist_left", "hand_left", 0.045),
        _bone("right_upper_arm", "shoulder_right", "elbow_right", 0.075),
        _bone("right_forearm", "elbow_right", "wrist_right", 0.055),
        _bone("right_hand", "wrist_right", "hand_right", 0.045),
        _bone("left_thigh", "hip_left", "knee_left", 0.10),
        _bone("left_shin", "knee_left", "ankle_left", 0.07),
        _bone("left_heel", "ankle_left", "heel_left", 0.05),
        _bone("left_foot", "heel_left", "toe_left", 0.065),
        _bone("right_thigh", "hip_right", "knee_right", 0.10),
        _bone("right_shin", "knee_right", "ankle_right", 0.07),
        _bone("right_heel", "ankle_right", "heel_right", 0.05),
        _bone("right_foot", "heel_right", "toe_right", 0.065),
    )
    return HumanoidRig(
        joints=joints,
        bones=bones,
        root_joint="pelvis",
        ground_anchor=(0.0, 0.0, -0.47),
    )


DEFAULT_HUMANOID_RIG = _build_default_rig()
