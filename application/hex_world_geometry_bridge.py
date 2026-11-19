"""Explicit boundary adapters between Eldoria axial contracts and Hex World geometry.

Eldoria's screen-world uses y-down pixels. Hex World uses mathematical y-up
world points. The axial basis is reflected at this boundary so the same
logical cell keeps the same on-screen location and named direction.
"""

from __future__ import annotations

from core.domain.spatial import (
    EntityPosition,
    HexCoord,
    HexDirection,
    LocalHexPosition,
    WorldHexPosition,
)
from core.foundation import WorldId as EldoriaWorldId
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
    axial_to_world,
    world_to_axial,
)
from hex_world_lab.world.identity import (
    CellAddress,
    MapId as LabMapId,
    WorldId as LabWorldId,
)


def hex_coord_to_lab_axial(coord: HexCoord) -> AxialCoord:
    """Convert Eldoria's pointy-top axial basis to the laboratory basis."""
    if not isinstance(coord, HexCoord):
        raise TypeError("coord must be a HexCoord")
    return AxialCoord(coord.q + coord.r, -coord.r)


def local_position_to_lab_axial(position: LocalHexPosition) -> AxialCoord:
    """Convert a map-local Eldoria cell without changing its map scope."""
    if not isinstance(position, LocalHexPosition):
        raise TypeError("position must be a LocalHexPosition")
    return AxialCoord(position.q + position.r, -position.r)


def world_position_to_lab_axial(position: WorldHexPosition) -> AxialCoord:
    """Convert a world-map placement; this is not a map-local cell."""
    if not isinstance(position, WorldHexPosition):
        raise TypeError("position must be a WorldHexPosition")
    return AxialCoord(position.q + position.r, -position.r)


def lab_axial_to_hex_coord(coord: AxialCoord) -> HexCoord:
    """Convert laboratory geometry coordinates to Eldoria geometry coordinates."""
    if not isinstance(coord, AxialCoord):
        raise TypeError("coord must be an AxialCoord")
    return HexCoord(coord.q + coord.r, -coord.r)


def lab_axial_to_local_position(coord: AxialCoord) -> LocalHexPosition:
    """Convert laboratory coordinates to an Eldoria map-local cell."""
    if not isinstance(coord, AxialCoord):
        raise TypeError("coord must be an AxialCoord")
    return LocalHexPosition(coord.q + coord.r, -coord.r)


def lab_axial_to_world_position(coord: AxialCoord) -> WorldHexPosition:
    """Convert laboratory coordinates to an Eldoria world-map placement."""
    if not isinstance(coord, AxialCoord):
        raise TypeError("coord must be an AxialCoord")
    return WorldHexPosition(coord.q + coord.r, -coord.r)


def hex_direction_to_lab_delta(direction: HexDirection) -> AxialCoord:
    """Convert a named Eldoria direction to the laboratory axial basis."""
    if not isinstance(direction, HexDirection):
        raise TypeError("direction must be a HexDirection")
    return AxialCoord(direction.dq + direction.dr, -direction.dr)


def make_lab_layout(
    hex_size: float,
    *,
    origin_x: float = 0.0,
    origin_y: float = 0.0,
) -> HexLayout:
    """Build a pointy-top lab layout from Eldoria's y-down world-pixel origin."""
    return HexLayout(
        orientation=HexOrientation.POINTY_TOP,
        radius=hex_size,
        origin=WorldPoint(origin_x, -origin_y),
    )


def make_lab_camera_center(camera_x: float, camera_y: float) -> WorldPoint:
    """Convert Eldoria's y-down camera center to the lab's y-up coordinates."""
    return WorldPoint(camera_x, -camera_y)


def local_position_to_world_point(
    position: LocalHexPosition,
    layout: HexLayout,
) -> WorldPoint:
    """Project one Eldoria local cell into the lab's reflected world basis."""
    if not isinstance(position, LocalHexPosition):
        raise TypeError("position must be a LocalHexPosition")
    _require_pointy_top(layout)
    return axial_to_world(local_position_to_lab_axial(position), layout)


def world_point_to_local_position(
    point: WorldPoint,
    layout: HexLayout,
) -> LocalHexPosition:
    """Resolve a lab world point to the nearest Eldoria local cell."""
    if not isinstance(point, WorldPoint):
        raise TypeError("point must be a WorldPoint")
    _require_pointy_top(layout)
    return lab_axial_to_local_position(world_to_axial(point, layout))


def lab_world_point_to_eldoria_xy(point: WorldPoint) -> tuple[float, float]:
    """Return the same world point in Eldoria's y-down presentation frame."""
    if not isinstance(point, WorldPoint):
        raise TypeError("point must be a WorldPoint")
    return point.x, -point.y


def to_lab_world_id(world_id: EldoriaWorldId) -> LabWorldId:
    """Wrap the canonical Eldoria world ID for a lab API boundary."""
    if not isinstance(world_id, EldoriaWorldId):
        raise TypeError("world_id must be an Eldoria WorldId")
    return LabWorldId(world_id.value)


def to_eldoria_world_id(world_id: LabWorldId) -> EldoriaWorldId:
    """Recover the canonical Eldoria world ID from a lab wrapper."""
    if not isinstance(world_id, LabWorldId):
        raise TypeError("world_id must be a lab WorldId")
    return EldoriaWorldId(world_id.value)


def to_lab_map_id(map_id: str) -> LabMapId:
    """Wrap an Eldoria map identifier for a lab API boundary."""
    return LabMapId(map_id)


def to_lab_cell_address(
    world_id: EldoriaWorldId,
    position: EntityPosition,
) -> CellAddress:
    """Build a lab cell address from Eldoria's authoritative logical position."""
    if not isinstance(world_id, EldoriaWorldId):
        raise TypeError("world_id must be an Eldoria WorldId")
    if not isinstance(position, EntityPosition):
        raise TypeError("position must be an EntityPosition")
    return CellAddress(
        to_lab_world_id(world_id),
        to_lab_map_id(position.map_id),
        local_position_to_lab_axial(position.cell),
    )


def from_lab_cell_address(
    address: CellAddress,
    *,
    expected_world_id: EldoriaWorldId,
) -> EntityPosition:
    """Convert a lab address back, rejecting cross-world identity leakage."""
    if not isinstance(address, CellAddress):
        raise TypeError("address must be a lab CellAddress")
    if not isinstance(expected_world_id, EldoriaWorldId):
        raise TypeError("expected_world_id must be an Eldoria WorldId")
    if address.world_id.value != expected_world_id.value:
        raise ValueError("cell address belongs to a different Eldoria world")
    return EntityPosition(
        address.map_id.value,
        lab_axial_to_local_position(address.coord),
    )


def _require_pointy_top(layout: HexLayout) -> None:
    if not isinstance(layout, HexLayout):
        raise TypeError("layout must be a HexLayout")
    if layout.orientation is not HexOrientation.POINTY_TOP:
        raise ValueError("Eldoria's current axial contract supports pointy-top geometry only")


__all__ = [
    "from_lab_cell_address",
    "hex_coord_to_lab_axial",
    "hex_direction_to_lab_delta",
    "lab_axial_to_hex_coord",
    "lab_axial_to_local_position",
    "lab_axial_to_world_position",
    "lab_world_point_to_eldoria_xy",
    "local_position_to_lab_axial",
    "local_position_to_world_point",
    "make_lab_camera_center",
    "make_lab_layout",
    "to_eldoria_world_id",
    "to_lab_cell_address",
    "to_lab_map_id",
    "to_lab_world_id",
    "world_point_to_local_position",
    "world_position_to_lab_axial",
]
