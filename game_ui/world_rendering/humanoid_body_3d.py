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
class BodySurfaceDefinition:
    """A connected anatomical surface lofted through ordered rig landmarks.

    Each station is (joint_name, half_width, half_depth, material).
    The surface shares rings between stations instead of stacking closed volumes.
    """

    name: str
    stations: tuple[tuple[str, float, float, str], ...]
    sides: int = 12
    subdivisions: int = 3

    def __post_init__(self) -> None:
        stations = tuple(tuple(station) for station in self.stations)
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("surface name must be a non-empty string.")
        if len(stations) < 2:
            raise ValueError("A connected surface requires at least two stations.")
        for station in stations:
            if (
                len(station) != 4
                or not isinstance(station[0], str)
                or not station[0].strip()
                or not isinstance(station[3], str)
                or not station[3].strip()
                or any(
                    isinstance(value, bool)
                    or not isinstance(value, (int, float))
                    or not math.isfinite(value)
                    or value <= 0
                    for value in station[1:3]
                )
            ):
                raise ValueError("Each surface station needs a joint, positive width/depth, and material.")
        if isinstance(self.sides, bool) or not isinstance(self.sides, int) or self.sides < 6:
            raise ValueError("surface sides must be an integer of at least 6.")
        if (
            isinstance(self.subdivisions, bool)
            or not isinstance(self.subdivisions, int)
            or self.subdivisions < 1
        ):
            raise ValueError("surface subdivisions must be a positive integer.")
        object.__setattr__(
            self,
            "stations",
            tuple((s[0], float(s[1]), float(s[2]), s[3]) for s in stations),
        )


@dataclass(frozen=True, slots=True)
class MeshTriangle:
    """One triangle with optional per-vertex linear-blend skin weights."""

    vertices: tuple[Vec3, Vec3, Vec3]
    material: str
    vertex_weights: tuple[
        tuple[tuple[str, float], ...],
        tuple[tuple[str, float], ...],
        tuple[tuple[str, float], ...],
    ] = ()


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


def _quat_multiply(first, second):
    aw, ax, ay, az = first
    bw, bx, by, bz = second
    return (
        aw * bw - ax * bx - ay * by - az * bz,
        aw * bx + ax * bw + ay * bz - az * by,
        aw * by - ax * bz + ay * bw + az * bx,
        aw * bz + ax * by - ay * bx + az * bw,
    )


def _quat_rotate(rotation, vector: Vec3) -> Vec3:
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


def _skin_vertex(vertex, weights, rest_transforms, posed_transforms) -> Vec3:
    if not weights:
        return vertex
    result = (0.0, 0.0, 0.0)
    for joint_name, weight in weights:
        rest = rest_transforms[joint_name]
        posed = posed_transforms[joint_name]
        rw, rx, ry, rz = rest.rotation
        delta = _quat_multiply(posed.rotation, (rw, -rx, -ry, -rz))
        relative = _subtract(vertex, rest.position)
        transformed = _add(posed.position, _quat_rotate(delta, relative))
        result = _add(result, _scale(transformed, weight))
    return result


def _skin_mesh(mesh, rig, local_rotations):
    if not local_rotations:
        return mesh
    rest_transforms = rig.resolve_pose()
    posed_transforms = rig.resolve_pose(local_rotations)
    return tuple(
        MeshTriangle(
            tuple(
                _skin_vertex(
                    vertex,
                    triangle.vertex_weights[index] if triangle.vertex_weights else (),
                    rest_transforms,
                    posed_transforms,
                )
                for index, vertex in enumerate(triangle.vertices)
            ),
            triangle.material,
            triangle.vertex_weights,
        )
        for triangle in mesh
    )


def _rotate_axis_angle(vector: Vec3, axis: Vec3, angle: float) -> Vec3:
    cosine = math.cos(angle)
    sine = math.sin(angle)
    return _add(
        _add(_scale(vector, cosine), _scale(_cross(axis, vector), sine)),
        _scale(axis, _dot(axis, vector) * (1.0 - cosine)),
    )


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
    center: Vec3, radii: Vec3, material: str, joint_name: str,
    sides: int = 12, rings: int = 8
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
            weight = ((joint_name, 1.0),)
            triangles.append(MeshTriangle((a, b, c), material, (weight, weight, weight)))
            triangles.append(MeshTriangle((a, c, d), material, (weight, weight, weight)))
    return triangles


def _segment_triangles(
    start: Vec3,
    end: Vec3,
    radii: Vec3,
    material: str,
    start_joint: str,
    end_joint: str,
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
            first_t = max(0.0, min(1.0, segment_profile[row][0]))
            second_t = max(0.0, min(1.0, segment_profile[row + 1][0]))
            first_weights = ((start_joint, 1.0 - first_t), (end_joint, first_t))
            second_weights = ((start_joint, 1.0 - second_t), (end_joint, second_t))
            triangles.append(
                MeshTriangle((a, b, c), material, (first_weights, first_weights, second_weights))
            )
            triangles.append(
                MeshTriangle((a, c, d), material, (first_weights, second_weights, second_weights))
            )
    return triangles


def _connected_surface_triangles(
    surface: BodySurfaceDefinition,
    positions: Mapping[str, Vec3],
) -> tuple[MeshTriangle, ...]:
    """Create a connected loft and retain two-joint weights per vertex."""
    for joint_name, _, _, _ in surface.stations:
        if joint_name not in positions:
            raise ValueError(f"Body surface '{surface.name}' references unknown rig joint '{joint_name}'.")

    circle = _unit_circle(surface.sides)
    samples = []
    stations = surface.stations
    for index in range(len(stations) - 1):
        first = stations[index]
        second = stations[index + 1]
        start = positions[first[0]]
        end = positions[second[0]]
        for step in range(surface.subdivisions):
            t = step / surface.subdivisions
            smooth_t = t * t * (3.0 - 2.0 * t)
            center = tuple(
                start[axis] + (end[axis] - start[axis]) * smooth_t
                for axis in range(3)
            )
            width = first[1] + (second[1] - first[1]) * smooth_t
            depth = first[2] + (second[2] - first[2]) * smooth_t
            weights = ((first[0], 1.0 - t), (second[0], t))
            samples.append((center, width, depth, first[3], weights))

    last = stations[-1]
    samples.append((positions[last[0]], last[1], last[2], last[3], ((last[0], 1.0),)))

    rings = []
    previous_tangent = None
    previous_u = None
    for index, (center, width, depth, material, weights) in enumerate(samples):
        previous = samples[max(0, index - 1)][0]
        following = samples[min(len(samples) - 1, index + 1)][0]
        tangent = _normalize(_subtract(following, previous))
        if previous_tangent is None:
            reference = (0.0, 1.0, 0.0)
            if abs(_dot(tangent, reference)) > 0.92:
                reference = (1.0, 0.0, 0.0)
            basis_u = _normalize(_cross(tangent, reference))
        else:
            cross_axis = _cross(previous_tangent, tangent)
            cross_length = math.sqrt(_dot(cross_axis, cross_axis))
            alignment = max(-1.0, min(1.0, _dot(previous_tangent, tangent)))
            if cross_length > 1e-8:
                axis = _scale(cross_axis, 1.0 / cross_length)
                angle = math.atan2(cross_length, alignment)
                basis_u = _rotate_axis_angle(previous_u, axis, angle)
            elif alignment < 0.0:
                axis = _normalize(_cross(previous_tangent, previous_u))
                basis_u = _rotate_axis_angle(previous_u, axis, math.pi)
            else:
                basis_u = previous_u
            basis_u = _subtract(basis_u, _scale(tangent, _dot(basis_u, tangent)))
            basis_u = _normalize(basis_u)
        basis_v = _normalize(_cross(tangent, basis_u))
        ring = [
            _add(
                center,
                _add(
                    _scale(basis_u, cosine * width),
                    _scale(basis_v, sine * depth),
                ),
            )
            for cosine, sine in circle
        ]
        rings.append((ring, material, weights))
        previous_tangent = tangent
        previous_u = basis_u

    triangles = []
    for ring_index in range(len(rings) - 1):
        first_ring, material, first_weights = rings[ring_index]
        second_ring, _, second_weights = rings[ring_index + 1]
        for side in range(surface.sides):
            next_side = (side + 1) % surface.sides
            a = first_ring[side]
            b = first_ring[next_side]
            c = second_ring[next_side]
            d = second_ring[side]
            triangles.append(
                MeshTriangle((a, b, c), material, (first_weights, first_weights, second_weights))
            )
            triangles.append(
                MeshTriangle((a, c, d), material, (first_weights, second_weights, second_weights))
            )
    return tuple(triangles)


@dataclass(frozen=True, slots=True)
class HumanoidBodyModel:
    """Low-poly anatomical volumes attached to a HumanoidRig."""

    parts: tuple[BodyPartDefinition, ...]
    surfaces: tuple[BodySurfaceDefinition, ...] = ()
    mesh_sides: int = 8
    mesh_rings: int = 5

    def __post_init__(self) -> None:
        parts = tuple(self.parts)
        if not parts or any(not isinstance(part, BodyPartDefinition) for part in parts):
            raise ValueError("parts must contain BodyPartDefinition values.")
        surfaces = tuple(self.surfaces)
        if any(not isinstance(surface, BodySurfaceDefinition) for surface in surfaces):
            raise ValueError("surfaces must contain BodySurfaceDefinition values.")
        names = [part.name for part in parts]
        surface_names = [surface.name for surface in surfaces]
        if len(names) != len(set(names)) or len(surface_names) != len(set(surface_names)):
            raise ValueError("Body part and surface names must be unique within their groups.")
        if isinstance(self.mesh_sides, bool) or self.mesh_sides < 6:
            raise ValueError("mesh_sides must be an integer of at least 6.")
        if isinstance(self.mesh_rings, bool) or self.mesh_rings < 4:
            raise ValueError("mesh_rings must be an integer of at least 4.")
        object.__setattr__(self, "parts", parts)
        object.__setattr__(self, "surfaces", surfaces)

    def build_mesh(
        self,
        rig: HumanoidRig,
        local_rotations: Mapping[str, tuple[float, float, float]] | None = None,
    ) -> tuple[MeshTriangle, ...]:
        """Build or reuse rig-local low-poly triangles for the supplied pose."""
        pose_key = tuple(
            sorted(
                (name, tuple(rotation))
                for name, rotation in (local_rotations or {}).items()
            )
        )
        return _build_mesh_cached(
            self.parts, self.surfaces, self.mesh_sides, self.mesh_rings, rig, pose_key
        )


@lru_cache(maxsize=16)
def _build_mesh_cached(
    parts: tuple[BodyPartDefinition, ...],
    surfaces: tuple[BodySurfaceDefinition, ...],
    mesh_sides: int,
    mesh_rings: int,
    rig: HumanoidRig,
    pose_key: tuple[tuple[str, tuple[float, float, float]], ...],
) -> tuple[MeshTriangle, ...]:
    """Reuse immutable local meshes for repeated rigs and animation poses."""
    positions = rig.joint_positions()
    mesh: list[MeshTriangle] = []
    for surface in surfaces:
        mesh.extend(_connected_surface_triangles(surface, positions))
    for part in parts:
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
                    part.start_joint,
                    mesh_sides,
                    mesh_rings,
                )
            )
        else:
            mesh.extend(
                _segment_triangles(
                    positions[part.start_joint],
                    positions[part.end_joint],
                    part.radii,
                    part.material,
                    part.start_joint,
                    part.end_joint,
                    mesh_sides,
                    part.profile,
                )
            )
    return _skin_mesh(tuple(mesh), rig, dict(pose_key))


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
        # Limbs remain independently articulated; the torso is a single connected loft.
        _ellipsoid("head_volume", "head", (0.078, 0.074, 0.105), "skin"),
        # Shoulder caps bridge the connected torso surface and upper arms.
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
                _ellipsoid(
                    f"{side}_hand_volume", f"hand_{side}",
                    (0.035, 0.025, 0.050), "skin",
                ),
                _ellipsoid(
                    f"{side}_foot_volume", f"foot_ball_{side}",
                    (0.050, 0.115, 0.035), "boots",
                ),
            )
        )
    surfaces = [
        BodySurfaceDefinition(
            "connected_torso",
            (
                ("pelvis", 0.105, 0.078, "trousers"),
                ("spine_lower", 0.092, 0.073, "tunic"),
                ("spine_upper", 0.103, 0.078, "tunic"),
                ("chest", 0.158, 0.103, "tunic"),
                ("neck", 0.043, 0.043, "skin"),
            ),
            sides=8,
            subdivisions=3,
        ),
    ]
    for side in ("left", "right"):
        surfaces.extend(
            (
                BodySurfaceDefinition(
                    f"connected_arm_{side}",
                    (
                        (f"shoulder_{side}", 0.052, 0.044, "skin"),
                        (f"elbow_{side}", 0.043, 0.038, "skin"),
                        (f"wrist_{side}", 0.026, 0.024, "skin"),
                    ),
                    sides=8,
                    subdivisions=3,
                ),
                BodySurfaceDefinition(
                    f"connected_leg_{side}",
                    (
                        (f"hip_{side}", 0.074, 0.064, "trousers"),
                        (f"knee_{side}", 0.050, 0.052, "trousers"),
                        (f"ankle_{side}", 0.032, 0.032, "trousers"),
                    ),
                    sides=10,
                    subdivisions=4,
                ),
            )
        )
    return HumanoidBodyModel(tuple(parts), tuple(surfaces))


DEFAULT_HUMANOID_BODY = _build_default_body()
