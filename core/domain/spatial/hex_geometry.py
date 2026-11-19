"""Pure pointy-top axial/pixel conversion helpers."""

from __future__ import annotations

import math
from numbers import Real

from .hex_coord import HexCoord
from .world_point import WorldPoint


def _validate_finite_real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a finite real number.")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite.")
    return result


def _validate_hex_size(hex_size: object) -> float:
    size = _validate_finite_real(hex_size, "hex_size")
    if size <= 0:
        raise ValueError("hex_size must be greater than zero.")
    return size


def axial_to_pixel(coord: HexCoord, hex_size: int | float) -> tuple[float, float]:
    """Convert an axial coordinate to a pointy-top hex center.

    hex_size is the center-to-corner radius. The returned tuple is a
    presentation-layer pixel point, not a domain Position.
    """
    if not isinstance(coord, HexCoord):
        raise TypeError("coord must be a HexCoord.")
    size = _validate_hex_size(hex_size)
    pixel_x = size * math.sqrt(3.0) * (coord.q + coord.r / 2.0)
    pixel_y = size * 1.5 * coord.r
    return pixel_x, pixel_y


def fractional_axial_to_hex(q: int | float, r: int | float) -> HexCoord:
    """Round fractional axial coordinates using deterministic cube rounding.

    Exact ties are resolved in a stable order: q, then r, then the implicit
    cube s component. This makes shared edges/vertices deterministic.
    """
    q_value = _validate_finite_real(q, "q")
    r_value = _validate_finite_real(r, "r")
    s_value = -q_value - r_value

    rounded_q = round(q_value)
    rounded_r = round(r_value)
    rounded_s = round(s_value)

    q_error = abs(rounded_q - q_value)
    r_error = abs(rounded_r - r_value)
    s_error = abs(rounded_s - s_value)

    if q_error >= r_error and q_error >= s_error:
        rounded_q = -rounded_r - rounded_s
    elif r_error >= s_error:
        rounded_r = -rounded_q - rounded_s

    return HexCoord(rounded_q, rounded_r)


def pixel_to_axial(
    pixel_x: int | float,
    pixel_y: int | float,
    hex_size: int | float,
) -> HexCoord:
    """Convert a pointy-top pixel point to its nearest axial cell.

    The caller is responsible for undoing camera/viewport transforms first
    and for checking the resulting coordinate against a map's valid-cell mask.
    """
    x_value = _validate_finite_real(pixel_x, "pixel_x")
    y_value = _validate_finite_real(pixel_y, "pixel_y")
    size = _validate_hex_size(hex_size)

    q_fraction = (math.sqrt(3.0) / 3.0 * x_value - y_value / 3.0) / size
    r_fraction = (2.0 / 3.0 * y_value) / size
    return fractional_axial_to_hex(q_fraction, r_fraction)


# Continuous y-down world geometry is the canonical Eldoria coordinate boundary.

_GEOMETRY_ABS_TOLERANCE = 1e-9
_GEOMETRY_REL_TOLERANCE = 1e-9


def axial_to_world_point(
    coord: HexCoord,
    hex_size: int | float,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> WorldPoint:
    """Return an axial cell center as an Eldoria y-down world point."""
    if not isinstance(origin, WorldPoint):
        raise TypeError("origin must be a WorldPoint.")
    x, y = axial_to_pixel(coord, hex_size)
    return WorldPoint(origin.x + x, origin.y + y)


def world_point_to_fractional_axial(
    point: WorldPoint,
    hex_size: int | float,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> tuple[float, float]:
    """Convert an Eldoria y-down world point to unrounded axial coordinates."""
    if not isinstance(point, WorldPoint):
        raise TypeError("point must be a WorldPoint.")
    if not isinstance(origin, WorldPoint):
        raise TypeError("origin must be a WorldPoint.")
    size = _validate_hex_size(hex_size)
    x = point.x - origin.x
    y = point.y - origin.y
    q = (math.sqrt(3.0) / 3.0 * x - y / 3.0) / size
    r = (2.0 / 3.0 * y) / size
    return q, r


def _round_half_up(value: float) -> int:
    """Round to nearest integer with deterministic half-up behavior."""
    return math.floor(value + 0.5)


def _cube_round_fractional(q: float, r: float) -> HexCoord:
    """Round fractional axial coordinates using deterministic cube correction."""
    s = -q - r
    rounded_q = _round_half_up(q)
    rounded_r = _round_half_up(r)
    rounded_s = _round_half_up(s)
    q_error = abs(rounded_q - q)
    r_error = abs(rounded_r - r)
    s_error = abs(rounded_s - s)

    if q_error >= r_error and q_error >= s_error:
        rounded_q = -rounded_r - rounded_s
    elif r_error >= s_error:
        rounded_r = -rounded_q - rounded_s

    return HexCoord(rounded_q, rounded_r)


def world_point_to_hex(
    point: WorldPoint,
    hex_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
    previous_cell: HexCoord | None = None,
) -> HexCoord:
    """Resolve a world point to its nearest cell, retaining a previous cell only on a tie.

    The previous cell is a boundary tie-break hint, never a second position
    authority. Without an equal-distance tie, cube rounding decides the cell.
    """
    if previous_cell is not None and not isinstance(previous_cell, HexCoord):
        raise TypeError("previous_cell must be a HexCoord or None.")
    q, r = world_point_to_fractional_axial(point, hex_size, origin)
    selected = _cube_round_fractional(q, r)
    if previous_cell is None:
        return selected

    selected_center = axial_to_world_point(selected, hex_size, origin)
    previous_center = axial_to_world_point(previous_cell, hex_size, origin)
    selected_distance = point.distance_to(selected_center)
    previous_distance = point.distance_to(previous_center)
    if math.isclose(
        previous_distance,
        selected_distance,
        abs_tol=_GEOMETRY_ABS_TOLERANCE,
        rel_tol=_GEOMETRY_REL_TOLERANCE,
    ):
        return previous_cell
    return selected
