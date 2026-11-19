"""Conversions between axial hex coordinates and continuous world points."""
import math

from .coordinates import AxialCoord, CubeCoord, WorldPoint
from .layout import HexLayout
from .orientation import HexOrientation


def axial_to_cube(coord: AxialCoord) -> CubeCoord:
    return CubeCoord(coord.q, coord.r, -coord.q - coord.r)


def cube_to_axial(coord: CubeCoord) -> AxialCoord:
    return AxialCoord(coord.q, coord.r)


def axial_to_world(coord: AxialCoord, layout: HexLayout) -> WorldPoint:
    """Return the center of an axial cell in world coordinates."""
    q, r, radius = coord.q, coord.r, layout.radius
    if layout.orientation is HexOrientation.FLAT_TOP:
        x = radius * 1.5 * q
        y = radius * math.sqrt(3.0) * (r + q / 2.0)
    else:
        x = radius * math.sqrt(3.0) * (q + r / 2.0)
        y = radius * 1.5 * r
    return WorldPoint(layout.origin.x + x, layout.origin.y + y)


def world_to_fractional_axial(point: WorldPoint, layout: HexLayout) -> tuple[float, float]:
    """Convert a world point to unrounded fractional axial coordinates."""
    x = (point.x - layout.origin.x) / layout.radius
    y = (point.y - layout.origin.y) / layout.radius
    if layout.orientation is HexOrientation.FLAT_TOP:
        return (2.0 / 3.0) * x, (-1.0 / 3.0) * x + (math.sqrt(3.0) / 3.0) * y
    return (math.sqrt(3.0) / 3.0) * x - (1.0 / 3.0) * y, (2.0 / 3.0) * y


def _round_half_up(value: float) -> int:
    """Round to nearest integer; exact halves consistently choose +infinity."""
    return math.floor(value + 0.5)


def cube_round(q: float, r: float, s: float) -> CubeCoord:
    """Round fractional cube coordinates with deterministic q/r/s fallback priority."""
    from .tolerance import GEOMETRY_ABS_TOLERANCE, GEOMETRY_REL_TOLERANCE

    if not all(math.isfinite(value) for value in (q, r, s)):
        raise ValueError("fractional cube coordinates must be finite")
    if not math.isclose(
        q + r + s,
        0.0,
        abs_tol=GEOMETRY_ABS_TOLERANCE,
        rel_tol=GEOMETRY_REL_TOLERANCE,
    ):
        raise ValueError("fractional cube coordinates must sum to zero")

    rq, rr, rs = _round_half_up(q), _round_half_up(r), _round_half_up(s)
    qdiff, rdiff, sdiff = abs(rq - q), abs(rr - r), abs(rs - s)
    if qdiff >= rdiff and qdiff >= sdiff:
        rq = -rr - rs
    elif rdiff >= sdiff:
        rr = -rq - rs
    else:
        rs = -rq - rr
    return CubeCoord(rq, rr, rs)


def world_to_axial(
    point: WorldPoint,
    layout: HexLayout,
    previous_cell: AxialCoord | None = None,
) -> AxialCoord:
    """Select the nearest cell, retaining previous_cell only on an equal-distance boundary.

    When no previous cell is supplied, or it is not equally near, deterministic
    cube rounding provides the fallback selection.
    """
    from .tolerance import GEOMETRY_ABS_TOLERANCE, GEOMETRY_REL_TOLERANCE

    q, r = world_to_fractional_axial(point, layout)
    selected_cell = cube_to_axial(cube_round(q, r, -q - r))

    if previous_cell is None:
        return selected_cell

    selected_center = axial_to_world(selected_cell, layout)
    previous_center = axial_to_world(previous_cell, layout)
    selected_distance = math.hypot(
        point.x - selected_center.x,
        point.y - selected_center.y,
    )
    previous_distance = math.hypot(
        point.x - previous_center.x,
        point.y - previous_center.y,
    )

    if math.isclose(
        previous_distance,
        selected_distance,
        abs_tol=GEOMETRY_ABS_TOLERANCE,
        rel_tol=GEOMETRY_REL_TOLERANCE,
    ):
        return previous_cell

    return selected_cell
