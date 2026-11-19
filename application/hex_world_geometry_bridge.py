"""Native Eldoria adapters for axial cells and continuous world geometry.

This module intentionally has no dependency on the former Hex World laboratory.
All points use Eldoria's canonical y-down world frame.
"""
from __future__ import annotations

from core.domain.spatial import (
    HexCoord,
    HexDirection,
    LocalHexPosition,
    WorldHexPosition,
    WorldPoint,
    axial_to_world_point,
    world_point_to_hex,
)


def hex_coord_to_local_position(coord: HexCoord) -> LocalHexPosition:
    if not isinstance(coord, HexCoord):
        raise TypeError("coord must be a HexCoord")
    return LocalHexPosition(coord.q, coord.r)


def local_position_to_hex_coord(position: LocalHexPosition) -> HexCoord:
    if not isinstance(position, LocalHexPosition):
        raise TypeError("position must be a LocalHexPosition")
    return HexCoord(position.q, position.r)


def world_position_to_hex_coord(position: WorldHexPosition) -> HexCoord:
    if not isinstance(position, WorldHexPosition):
        raise TypeError("position must be a WorldHexPosition")
    return HexCoord(position.q, position.r)


def hex_coord_to_world_position(coord: HexCoord) -> WorldHexPosition:
    if not isinstance(coord, HexCoord):
        raise TypeError("coord must be a HexCoord")
    return WorldHexPosition(coord.q, coord.r)


def hex_direction_to_delta(direction: HexDirection) -> HexCoord:
    if not isinstance(direction, HexDirection):
        raise TypeError("direction must be a HexDirection")
    return HexCoord(direction.dq, direction.dr)


def local_position_to_world_point(
    position: LocalHexPosition,
    hex_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
) -> WorldPoint:
    if not isinstance(position, LocalHexPosition):
        raise TypeError("position must be a LocalHexPosition")
    return axial_to_world_point(
        HexCoord(position.q, position.r),
        hex_size,
        origin,
    )


def world_point_to_local_position(
    point: WorldPoint,
    hex_size: int | float,
    *,
    origin: WorldPoint = WorldPoint(0.0, 0.0),
    previous_position: LocalHexPosition | None = None,
) -> LocalHexPosition:
    if not isinstance(point, WorldPoint):
        raise TypeError("point must be a WorldPoint")
    if previous_position is not None and not isinstance(
        previous_position, LocalHexPosition
    ):
        raise TypeError("previous_position must be a LocalHexPosition or None")
    previous = (
        None if previous_position is None
        else HexCoord(previous_position.q, previous_position.r)
    )
    coord = world_point_to_hex(
        point,
        hex_size,
        origin=origin,
        previous_cell=previous,
    )
    return LocalHexPosition(coord.q, coord.r)


__all__ = [
    "hex_coord_to_local_position",
    "local_position_to_hex_coord",
    "world_position_to_hex_coord",
    "hex_coord_to_world_position",
    "hex_direction_to_delta",
    "local_position_to_world_point",
    "world_point_to_local_position",
]
