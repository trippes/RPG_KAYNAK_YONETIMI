"""Parametric 3D body volumes bound to the anatomical humanoid rig.

The model is presentation geometry only. It consumes rig-local joint positions
and never changes the skeleton, pose, or runtime world position.
"""

from __future__ import annotations

from dataclasses import dataclass
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


def _ellipsoid_triangles(
    center: Vec3, radii: Vec3, material: str, sides: int = 12, rings: int = 8
) -> list[MeshTriangle]:
    vertices: list[list[Vec3]] = []
    for ring in range(rings + 1):
        latitude = -math.pi / 2 + math.pi * ring / rings
        row = []
        for side in range(sides):
            longitude = math.tau * side / sides
            row.append(
                (
                    center[0] + radii[0] * math.cos(latitude) * math.cos(longitude),
                    center[1] + radii[1] * math.cos(latitude) * math.sin(longitude),
                    center[2] + radii[2] * math.sin(latitude),
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
    start: Vec3, end: Vec3, radii: Vec3, material: str, sides: int = 10
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
    profile = (
        (-0.10, 0.34),
        (0.00, 0.78),
        (0.14, 1.00),
        (0.50, 0.94),
        (0.86, 1.00),
        (1.00, 0.78),
        (1.10, 0.34),
    )
    rows: list[list[Vec3]] = []
    for along, factor in profile:
        center = _add(start, _scale(axis, along * length))
        row = []
        for side in range(sides):
            angle = math.tau * side / sides
            offset = _add(
                _scale(basis_u, math.cos(angle) * radii[0] * factor),
                _scale(basis_v, math.sin(angle) * radii[1] * factor),
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
                    )
                )
        return tuple(mesh)


def _ellipsoid(name: str, joint: str, radii: Vec3, material: str) -> BodyPartDefinition:
    return BodyPartDefinition(name, joint, joint, radii, material)


def _segment(
    name: str, start: str, end: str, radii: Vec3, material: str
) -> BodyPartDefinition:
    return BodyPartDefinition(name, start, end, radii, material, "segment")


def _build_default_body() -> HumanoidBodyModel:
    parts = [
        # Core torso volumes overlap deliberately to form a continuous silhouette.
        _ellipsoid("pelvis_volume", "pelvis", (0.105, 0.078, 0.105), "trousers"),
        _ellipsoid("abdomen_volume", "spine_lower", (0.090, 0.070, 0.125), "tunic"),
        _ellipsoid("chest_volume", "chest", (0.145, 0.092, 0.135), "tunic"),
        _segment("neck_volume", "chest", "neck", (0.043, 0.043, 0.043), "skin"),
        _ellipsoid("head_volume", "head", (0.078, 0.074, 0.105), "skin"),
        # Shoulder caps bridge clavicles, chest, and upper arms.
        _ellipsoid("shoulder_left_volume", "shoulder_left", (0.064, 0.060, 0.064), "skin"),
        _ellipsoid("shoulder_right_volume", "shoulder_right", (0.064, 0.060, 0.064), "skin"),
    ]
    for side in ("left", "right"):
        parts.extend(
            (
                _segment(
                    f"{side}_upper_arm_volume", f"shoulder_{side}", f"elbow_{side}",
                    (0.047, 0.047, 0.047), "skin",
                ),
                _ellipsoid(
                    f"{side}_elbow_volume", f"elbow_{side}",
                    (0.043, 0.043, 0.043), "skin",
                ),
                _segment(
                    f"{side}_forearm_volume", f"elbow_{side}", f"wrist_{side}",
                    (0.038, 0.038, 0.038), "skin",
                ),
                _ellipsoid(
                    f"{side}_hand_volume", f"hand_{side}",
                    (0.035, 0.025, 0.050), "skin",
                ),
                _segment(
                    f"{side}_thigh_volume", f"hip_{side}", f"knee_{side}",
                    (0.067, 0.067, 0.067), "trousers",
                ),
                _ellipsoid(
                    f"{side}_knee_volume", f"knee_{side}",
                    (0.050, 0.052, 0.050), "trousers",
                ),
                _segment(
                    f"{side}_shin_volume", f"knee_{side}", f"ankle_{side}",
                    (0.046, 0.046, 0.046), "trousers",
                ),
                _ellipsoid(
                    f"{side}_foot_volume", f"foot_ball_{side}",
                    (0.050, 0.115, 0.035), "boots",
                ),
            )
        )
    return HumanoidBodyModel(tuple(parts))


DEFAULT_HUMANOID_BODY = _build_default_body()
