"""Contract tests for the Eldoria ↔ Hex World geometry/identity bridge."""

import pytest

from application.hex_world_geometry_bridge import (
    from_lab_cell_address,
    hex_coord_to_lab_axial,
    hex_direction_to_lab_delta,
    lab_axial_to_hex_coord,
    lab_axial_to_local_position,
    lab_axial_to_world_position,
    lab_world_point_to_eldoria_xy,
    local_position_to_lab_axial,
    local_position_to_world_point,
    make_lab_camera_center,
    make_lab_layout,
    to_eldoria_world_id,
    to_lab_cell_address,
    to_lab_world_id,
    world_point_to_local_position,
    world_position_to_lab_axial,
)
from core.domain.spatial import (
    EntityPosition,
    HexCoord,
    HexDirection,
    LocalHexPosition,
    WorldHexPosition,
)
from core.foundation import WorldId
from game_ui.world_transform import WorldTransform
from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world.identity import CellAddress, MapId, WorldId as LabWorldId


@pytest.mark.parametrize(
    ("position", "expected"),
    [
        (LocalHexPosition(0, 0), AxialCoord(0, 0)),
        (LocalHexPosition(1, 0), AxialCoord(1, 0)),
        (LocalHexPosition(0, 1), AxialCoord(1, -1)),
        (LocalHexPosition(-3, 5), AxialCoord(2, -5)),
    ],
)
def test_local_axial_conversion_uses_the_reflected_basis(position, expected):
    assert local_position_to_lab_axial(position) == expected
    assert lab_axial_to_local_position(expected) == position


@pytest.mark.parametrize("coord", [HexCoord(0, 0), HexCoord(2, -4), HexCoord(-7, 3)])
def test_geometry_coordinate_conversion_round_trips(coord):
    assert lab_axial_to_hex_coord(hex_coord_to_lab_axial(coord)) == coord


@pytest.mark.parametrize(
    "position",
    [WorldHexPosition(0, 0), WorldHexPosition(3, -2), WorldHexPosition(-4, 6)],
)
def test_world_map_placement_conversion_preserves_its_separate_type(position):
    converted = world_position_to_lab_axial(position)
    assert lab_axial_to_world_position(converted) == position
    assert not isinstance(position, LocalHexPosition)


@pytest.mark.parametrize("direction", list(HexDirection))
def test_direction_conversion_preserves_neighbor_screen_orientation(direction):
    core_origin = LocalHexPosition(0, 0)
    core_neighbor = LocalHexPosition(direction.dq, direction.dr)
    lab_delta = hex_direction_to_lab_delta(direction)
    assert local_position_to_lab_axial(core_neighbor) == lab_delta
    assert lab_axial_to_local_position(lab_delta) == core_neighbor


def test_lab_and_eldoria_screen_projection_match_for_cells_camera_zoom_and_origin():
    size = 32.0
    origin = (17.0, -23.0)
    camera = (11.0, 9.0)
    zoom = 1.75
    viewport = Viewport(800, 600)
    layout = make_lab_layout(size, origin_x=origin[0], origin_y=origin[1])
    lab_transform = WorldScreenTransform(
        viewport,
        make_lab_camera_center(*camera),
        zoom,
    )
    eldoria_transform = WorldTransform(
        hex_size=size,
        camera_x=camera[0] - origin[0],
        camera_y=camera[1] - origin[1],
        viewport_center=(viewport.width / 2, viewport.height / 2),
        zoom=zoom,
    )

    for q, r in ((0, 0), (1, 0), (0, 1), (2, -3), (-5, 4), (8, -2)):
        local = LocalHexPosition(q, r)
        lab_point = local_position_to_world_point(local, layout)
        lab_screen = lab_transform.world_to_screen(lab_point)
        eldoria_screen = eldoria_transform.axial_to_screen(HexCoord(q, r))
        assert lab_screen.x == pytest.approx(eldoria_screen[0])
        assert lab_screen.y == pytest.approx(eldoria_screen[1])
        assert lab_world_point_to_eldoria_xy(lab_point) == pytest.approx(
            (origin[0] + eldoria_transform.axial_to_world(HexCoord(q, r))[0],
             origin[1] + eldoria_transform.axial_to_world(HexCoord(q, r))[1])
        )


def test_world_point_cell_resolution_round_trips_cell_centers():
    layout = make_lab_layout(24.0, origin_x=120.0, origin_y=75.0)
    for position in (
        LocalHexPosition(0, 0),
        LocalHexPosition(1, -2),
        LocalHexPosition(-4, 3),
    ):
        point = local_position_to_world_point(position, layout)
        assert world_point_to_local_position(point, layout) == position


def test_flat_top_layout_is_rejected_by_eldoria_bridge():
    flat_layout = HexLayout(HexOrientation.FLAT_TOP, 24.0)
    with pytest.raises(ValueError, match="pointy-top"):
        local_position_to_world_point(LocalHexPosition(0, 0), flat_layout)
    with pytest.raises(ValueError, match="pointy-top"):
        world_point_to_local_position(WorldPoint(0.0, 0.0), flat_layout)


def test_world_and_map_identity_are_wrapped_without_changing_values():
    world_id = WorldId("eldoria-main")
    position = EntityPosition("starting_valley", LocalHexPosition(2, -1))
    address = to_lab_cell_address(world_id, position)

    assert address == CellAddress(
        LabWorldId("eldoria-main"),
        MapId("starting_valley"),
        AxialCoord(1, 1),
    )
    assert from_lab_cell_address(address, expected_world_id=world_id) == position
    assert to_eldoria_world_id(to_lab_world_id(world_id)) == world_id


def test_cell_address_from_another_world_is_rejected():
    address = CellAddress(
        LabWorldId("other-world"),
        MapId("starting_valley"),
        AxialCoord(0, 0),
    )
    with pytest.raises(ValueError, match="different Eldoria world"):
        from_lab_cell_address(address, expected_world_id=WorldId("eldoria-main"))


def test_lab_map_identity_does_not_accept_empty_ids():
    with pytest.raises(ValueError):
        to_lab_cell_address(
            WorldId("eldoria-main"),
            EntityPosition(" ", LocalHexPosition(0, 0)),
        )
