"""Construction-space coordinates and deterministic snapping primitives.

Construction coordinates are map-scoped canonical world points. They are not
hex cells, renderer pixels, camera coordinates, or actor-position authority.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
from numbers import Real

from .hex_coord import HexCoord
from .hex_geometry import axial_to_world_point, world_point_to_hex
from .world_point import WorldPoint


def _finite_real(value: object, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field} must be a finite real number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{field} must be finite.")
    return result


def _non_empty_text(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a non-empty string.")
    return value


@dataclass(frozen=True, slots=True)
class ConstructionPosition:
    """Map-local construction pose in canonical world units.

    Rotation is expressed in degrees, clockwise in the y-down world plane.
    Elevation is a logical vertical coordinate and does not alter x/y.
    """

    map_id: str
    point: WorldPoint
    elevation: float = 0.0
    rotation_degrees: float = 0.0

    def __post_init__(self) -> None:
        _non_empty_text(self.map_id, "map_id")
        if not isinstance(self.point, WorldPoint):
            raise TypeError("point must be a WorldPoint.")
        elevation = _finite_real(self.elevation, "elevation")
        rotation = _finite_real(self.rotation_degrees, "rotation_degrees") % 360.0
        object.__setattr__(self, "elevation", elevation)
        object.__setattr__(self, "rotation_degrees", rotation)

    def translated(
        self, dx: float = 0.0, dy: float = 0.0, *, dz: float = 0.0
    ) -> "ConstructionPosition":
        return ConstructionPosition(
            self.map_id,
            self.point.translated(dx, dy),
            self.elevation + _finite_real(dz, "dz"),
            self.rotation_degrees,
        )

    def rotated(self, delta_degrees: float) -> "ConstructionPosition":
        return ConstructionPosition(
            self.map_id,
            self.point,
            self.elevation,
            self.rotation_degrees + _finite_real(delta_degrees, "delta_degrees"),
        )


@dataclass(frozen=True, slots=True)
class ConstructionSnapPolicy:
    """Explicit position and angular quantization; zero disables that axis."""

    step_x: float = 0.0
    step_y: float = 0.0
    rotation_step_degrees: float = 0.0

    def __post_init__(self) -> None:
        for name in ("step_x", "step_y", "rotation_step_degrees"):
            value = _finite_real(getattr(self, name), name)
            if value < 0:
                raise ValueError(f"{name} must be non-negative.")
            object.__setattr__(self, name, value)

    @staticmethod
    def _snap(value: float, step: float) -> float:
        if step == 0.0:
            return value
        magnitude = math.floor(abs(value) / step + 0.5) * step
        return math.copysign(magnitude, value)

    def apply(self, position: ConstructionPosition) -> ConstructionPosition:
        if not isinstance(position, ConstructionPosition):
            raise TypeError("position must be a ConstructionPosition.")
        return ConstructionPosition(
            position.map_id,
            WorldPoint(
                self._snap(position.point.x, self.step_x),
                self._snap(position.point.y, self.step_y),
            ),
            position.elevation,
            self._snap(position.rotation_degrees, self.rotation_step_degrees)
            % 360.0
            if self.rotation_step_degrees
            else position.rotation_degrees,
        )


@dataclass(frozen=True, slots=True)
class ConstructionSpaceTransform:
    """Convert between one map's construction plane and its canonical hex cells.

    The transform is map-local. World-map placement, camera projection, zoom,
    and viewport offsets are intentionally outside this domain contract.
    """

    map_id: str
    hex_size: float
    origin: WorldPoint = WorldPoint(0.0, 0.0)

    def __post_init__(self) -> None:
        _non_empty_text(self.map_id, "map_id")
        size = _finite_real(self.hex_size, "hex_size")
        if size <= 0:
            raise ValueError("hex_size must be greater than zero.")
        if not isinstance(self.origin, WorldPoint):
            raise TypeError("origin must be a WorldPoint.")
        object.__setattr__(self, "hex_size", size)

    def hex_to_position(self, coord: HexCoord) -> ConstructionPosition:
        if not isinstance(coord, HexCoord):
            raise TypeError("coord must be a HexCoord.")
        return ConstructionPosition(
            self.map_id,
            axial_to_world_point(coord, self.hex_size, self.origin),
        )

    def position_to_hex(
        self,
        position: ConstructionPosition,
        *,
        previous_cell: HexCoord | None = None,
    ) -> HexCoord:
        if not isinstance(position, ConstructionPosition):
            raise TypeError("position must be a ConstructionPosition.")
        if position.map_id != self.map_id:
            raise ValueError("construction position belongs to a different map.")
        return world_point_to_hex(
            position.point,
            self.hex_size,
            origin=self.origin,
            previous_cell=previous_cell,
        )


__all__ = [
    "ConstructionPosition",
    "ConstructionSnapPolicy",
    "ConstructionSpaceTransform",
]
