"""Parametric 3D body volumes bound to the anatomical humanoid rig.

The model is presentation geometry only. It consumes rig-local joint positions
and never changes the skeleton, pose, or runtime world position.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
from typing import Mapping

from game_ui.world_rendering.humanoid_rig_3d import (
    HumanoidRig,
    Vec3,
)


@dataclass(frozen=True, slots=True)
class BodyPartDefinition:
    """A volume attached to one joint or spanning two joints."""

    name: str
    start_joint: str
    end_joint: str
    radii: Vec3
    material: str
    shape: str = "ellipsoid"
    profile: tuple[tuple[float, float], ...] | None = None

    def __post_init__(self) -> None:
        for field_name in ("name", "start_joint", "end_joint", "material"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} must be a non-empty string.")
        if self.shape not in {"ellipsoid", "segment"}:
            raise ValueError("shape must be 'ellipsoid' or 'segment'.")
        if (
            not isinstance(self.radii, (tuple, list))
            or len(self.radii) != 3
            or any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
                for value in self.radii
            )
        ):
            raise ValueError("radii must contain three finite positive values.")
        object.__setattr__(self, "radii", tuple(float(value) for value in self.radii))
        if self.profile is not None:
            profile = tuple(tuple(point) for point in self.profile)
            if len(profile) < 3 or any(
                len(point) != 2
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    for value in point
                )
                or point[1] <= 0
                for point in profile
            ):
                raise ValueError("profile must contain at least three finite positive-width samples.")
            if any(
                profile[index][0] >= profile[index + 1][0]
                for index in range(len(profile) - 1)
            ):
                raise ValueError("profile positions must be strictly increasing.")
            object.__setattr__(
                self, "profile",
                tuple((float(along), float(width)) for along, width in profile),
            )


@dataclass(frozen=True, slots=True)
class MeshTriangle:
    """One rig-local triangle and its material key."""

    vertices: tuple[Vec3, Vec3, Vec3]
    material: str


def _add(first: Vec3, second: Vec3) -> Vec3:
    return tuple(first[index] + second[index] for index in range(3))


def _subtract(first: Vec3, second: Vec3) -> Vec3:
    return tuple(first[index] - second[index] for index in range(3))


def _scale(vector: Vec3, amount: float) -> Vec3:
    return tuple(component * amount for component in vector)


def _dot(first: Vec3, second: Vec3) -> float:
    return sum(first[index] * second[index] for index in range(3))


def _cross(first: Vec3, second: Vec3) -> Vec3:
    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )


def _normalize(vector: Vec3) -> Vec3:
    length = math.sqrt(_dot(vector, vector))
    if length <= 1e-10:
        raise ValueError("A body segment cannot have zero length.")
    return _scale(vector, 1.0 / length)


@lru_cache(maxsize=8)
def _unit_circle(sides: int) -> tuple[tuple[float, float], ...]:
    """Cache unit-circle samples shared by every body part."""
    return tuple(
        (math.cos(math.tau * side / sides), math.sin(math.tau * side / sides))
        for side in range(sides)
    )


@lru_cache(maxsize=8)
def _latitude_samples(rings: int) -> tuple[tuple[float, float], ...]:
    """Cache latitude sine/cosine pairs for low-poly ellipsoids."""
    return tuple(
        (math.cos(-math.pi / 2 + math.pi * ring / rings),
         math.sin(-math.pi / 2 + math.pi * ring / rings))
        for ring in range(rings + 1)
    )


def _ellipsoid_triangles(
    center: Vec3, radii: Vec3, material: str, sides: int = 12, rings: int = 8
) -> list[MeshTriangle]:
    vertices: list[list[Vec3]] = []
    circle = _unit_circle(sides)
    latitudes = _latitude_samples(rings)
    for ring in range(rings + 1):
        cosine_latitude, sine_latitude = latitudes[ring]
        row = []
        for cosine_longitude, sine_longitude in circle:
            row.append(
                (
                    center[0] + radii[0] * cosine_latitude * cosine_longitude,
                    center[1] + radii[1] * cosine_latitude * sine_longitude,
                    center[2] + radii[2] * sine_latitude,
                )
            )
        vertices.append(row)

    triangles: list[MeshTriangle] = []
    for ring in range(rings):
        for side in range(sides):
            next_side = (side + 1) % sides
            a = vertices[ring][side]
            b = vertices[ring][next_side]
            c = vertices[ring + 1][next_side]
            d = vertices[ring + 1][side]
            triangles.append(MeshTriangle((a, b, c), material))
            triangles.append(MeshTriangle((a, c, d), material))
    return triangles


def _segment_triangles(
    start: Vec3,
    end: Vec3,
    radii: Vec3,
    material: str,
    sides: int = 10,
    profile: tuple[tuple[float, float], ...] | None = None,
) -> list[MeshTriangle]:
    axis = _normalize(_subtract(end, start))
    reference = (0.0, 1.0, 0.0)
    if abs(_dot(axis, reference)) > 0.92:
        reference = (1.0, 0.0, 0.0)
    basis_u = _normalize(_cross(axis, reference))
    basis_v = _normalize(_cross(axis, basis_u))
    length = math.dist(start, end)

    # The end rings extend slightly into neighboring volumes. This overlap
    # avoids visible gaps at elbows, knees, shoulders, and ankles.
    segment_profile = profile or (
        (-0.10, 0.28),
        (0.00, 0.70),
        (0.10, 0.90),
        (0.28, 1.00),
        (0.52, 0.94),
        (0.76, 0.82),
        (0.92, 0.68),
        (1.00, 0.56),
        (1.10, 0.24),
    )
    circle = _unit_circle(sides)
    rows: list[list[Vec3]] = []
    for along, factor in segment_profile:
        center = _add(start, _scale(axis, along * length))
        row = []
        for cosine_angle, sine_angle in circle:
            offset = _add(
                _scale(basis_u, cosine_angle * radii[0] * factor),
                _scale(basis_v, sine_angle * radii[1] * factor),
            )
            row.append(_add(center, offset))
        rows.append(row)

    triangles: list[MeshTriangle] = []
    for row in range(len(rows) - 1):
        for side in range(sides):
            next_side = (side + 1) % sides
            a = rows[row][side]
            b = rows[row][next_side]
            c = rows[row + 1][next_side]
            d = rows[row + 1][side]
            triangles.append(MeshTriangle((a, b, c), material))
            triangles.append(MeshTriangle((a, c, d), material))
    return triangles


@dataclass(frozen=True, slots=True)
class HumanoidBodyModel:
    """Low-poly anatomical volumes attached to a HumanoidRig."""

    parts: tuple[BodyPartDefinition, ...]
    mesh_sides: int = 12
    mesh_rings: int = 8

    def __post_init__(self) -> None:
        parts = tuple(self.parts)
        if not parts or any(not isinstance(part, BodyPartDefinition) for part in parts):
            raise ValueError("parts must contain BodyPartDefinition values.")
        names = [part.name for part in parts]
        if len(names) != len(set(names)):
            raise ValueError("Body part names must be unique.")
        if isinstance(self.mesh_sides, bool) or self.mesh_sides < 6:
            raise ValueError("mesh_sides must be an integer of at least 6.")
        if isinstance(self.mesh_rings, bool) or self.mesh_rings < 4:
            raise ValueError("mesh_rings must be an integer of at least 4.")
        object.__setattr__(self, "parts", parts)

    def build_mesh(
        self,
        rig: HumanoidRig,
        local_rotations: Mapping[str, tuple[float, float, float]] | None = None,
    ) -> tuple[MeshTriangle, ...]:
        """Build rig-local low-poly triangles for the supplied pose."""
        positions = rig.joint_positions(local_rotations)
        mesh: list[MeshTriangle] = []
        for part in self.parts:
            if part.start_joint not in positions or part.end_joint not in positions:
                raise ValueError(f"Body part '{part.name}' references an unknown rig joint.")
            if part.shape == "ellipsoid":
                if part.start_joint != part.end_joint:
                    raise ValueError("Ellipsoid body parts must attach to one joint.")
                mesh.extend(
                    _ellipsoid_triangles(
                        positions[part.start_joint],
                        part.radii,
                        part.material,
                        self.mesh_sides,
                        self.mesh_rings,
                    )
                )
            else:
                mesh.extend(
                    _segment_triangles(
                        positions[part.start_joint],
                        positions[part.end_joint],
                        part.radii,
                        part.material,
                        self.mesh_sides,
                        part.profile,
                    )
                )
        return tuple(mesh)


def _ellipsoid(name: str, joint: str, radii: Vec3, material: str) -> BodyPartDefinition:
    return BodyPartDefinition(name, joint, joint, radii, material)


def _segment(
    name: str,
    start: str,
    end: str,
    radii: Vec3,
    material: str,
    profile: tuple[tuple[float, float], ...] | None = None,
) -> BodyPartDefinition:
    return BodyPartDefinition(name, start, end, radii, material, "segment", profile)


def _build_default_body() -> HumanoidBodyModel:
    parts = [
        # Core torso volumes overlap deliberately to form a continuous silhouette.
        _ellipsoid("pelvis_volume", "pelvis", (0.105, 0.078, 0.105), "trousers"),
        _ellipsoid("abdomen_volume", "spine_lower", (0.092, 0.073, 0.115), "tunic"),
        _ellipsoid("waist_volume", "spine_upper", (0.103, 0.078, 0.078), "tunic"),
        _ellipsoid("chest_volume", "chest", (0.158, 0.103, 0.132), "tunic"),
        _ellipsoid("upper_back_volume", "chest", (0.145, 0.075, 0.112), "tunic"),
        _segment("neck_volume", "chest", "neck", (0.043, 0.043, 0.043), "skin"),
        _ellipsoid("head_volume", "head", (0.078, 0.074, 0.105), "skin"),
        # Shoulder caps bridge clavicles, chest, and upper arms.
        _ellipsoid("shoulder_left_volume", "shoulder_left", (0.064, 0.060, 0.064), "skin"),
        _ellipsoid("shoulder_right_volume", "shoulder_right", (0.064, 0.060, 0.064), "skin"),
        _segment(
            "left_clavicle_volume", "chest", "clavicle_left",
            (0.035, 0.035, 0.035), "skin",
            ((-0.08, 0.25), (0.0, 0.85), (0.65, 1.0), (1.0, 0.55), (1.08, 0.2)),
        ),
        _segment(
            "right_clavicle_volume", "chest", "clavicle_right",
            (0.035, 0.035, 0.035), "skin",
            ((-0.08, 0.25), (0.0, 0.85), (0.65, 1.0), (1.0, 0.55), (1.08, 0.2)),
        ),
    ]
    for side in ("left", "right"):
        parts.extend(
            (
                _segment(
                    f"{side}_upper_arm_volume", f"shoulder_{side}", f"elbow_{side}",
                    (0.052, 0.044, 0.044), "skin",
                    ((-0.10, 0.25), (0.0, 0.72), (0.20, 0.92), (0.43, 1.0),
                     (0.68, 0.88), (0.88, 0.70), (1.0, 0.55), (1.10, 0.22)),
                ),
                _ellipsoid(
                    f"{side}_elbow_volume", f"elbow_{side}",
                    (0.043, 0.043, 0.043), "skin",
                ),
                _segment(
                    f"{side}_forearm_volume", f"elbow_{side}", f"wrist_{side}",
                    (0.043, 0.036, 0.036), "skin",
                    ((-0.10, 0.22), (0.0, 0.58), (0.18, 0.82), (0.42, 0.92),
                     (0.68, 0.78), (0.88, 0.62), (1.0, 0.48), (1.10, 0.20)),
                ),
                _ellipsoid(
                    f"{side}_hand_volume", f"hand_{side}",
                    (0.035, 0.025, 0.050), "skin",
                ),
                _segment(
                    f"{side}_thigh_volume", f"hip_{side}", f"knee_{side}",
                    (0.074, 0.064, 0.064), "trousers",
                    ((-0.10, 0.28), (0.0, 0.72), (0.18, 0.92), (0.38, 1.0),
                     (0.62, 0.92), (0.82, 0.78), (1.0, 0.62), (1.10, 0.24)),
                ),
                _ellipsoid(
                    f"{side}_knee_volume", f"knee_{side}",
                    (0.050, 0.052, 0.050), "trousers",
                ),
                _segment(
                    f"{side}_shin_volume", f"knee_{side}", f"ankle_{side}",
                    (0.050, 0.044, 0.044), "trousers",
                    ((-0.10, 0.24), (0.0, 0.68), (0.20, 0.82), (0.44, 0.76),
                     (0.68, 0.66), (0.88, 0.54), (1.0, 0.46), (1.10, 0.20)),
                ),
                _ellipsoid(
                    f"{side}_foot_volume", f"foot_ball_{side}",
                    (0.050, 0.115, 0.035), "boots",
                ),
            )
        )
    return HumanoidBodyModel(tuple(parts))


DEFAULT_HUMANOID_BODY = _build_default_body()
