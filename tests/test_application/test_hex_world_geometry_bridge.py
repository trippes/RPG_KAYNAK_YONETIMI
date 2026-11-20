"""Native Eldoria axial/world geometry adapter contract tests."""
import pytest

from application.hex_world_geometry_bridge import (
    hex_coord_to_local_position,
    local_position_to_hex_coord,
    world_position_to_hex_coord,
    hex_coord_to_world_position,
    hex_direction_to_delta,
    local_position_to_world_point,
    world_point_to_local_position,
)
from core.domain.spatial import (
    HexCoord,
    HexDirection,
    LocalHexPosition,
    WorldHexPosition,
    WorldPoint,
    axial_to_world_point,
)
from game_ui.world_transform import WorldTransform


@pytest.mark.parametrize(
    ("coord", "position"),
    [
        (HexCoord(0, 0), LocalHexPosition(0, 0)),
        (HexCoord(2, -4), LocalHexPosition(2, -4)),
        (HexCoord(-7, 3), LocalHexPosition(-7, 3)),
    ],
)
def test_axial_and_map_local_values_round_trip_without_basis_reflection(
    coord, position
):
    assert hex_coord_to_local_position(coord) == position
    assert local_position_to_hex_coord(position) == coord


@pytest.mark.parametrize(
    "position",
    [
        WorldHexPosition(0, 0),
        WorldHexPosition(3, -2),
        WorldHexPosition(-4, 6),
    ],
)
def test_world_map_placement_keeps_its_distinct_domain_type(position):
    coord = world_position_to_hex_coord(position)
    assert hex_coord_to_world_position(coord) == position
    assert not isinstance(position, LocalHexPosition)


@pytest.mark.parametrize("direction", list(HexDirection))
def test_named_direction_preserves_axial_neighbor_delta(direction):
    assert hex_direction_to_delta(direction) == HexCoord(
        direction.dq, direction.dr
    )


def test_native_world_projection_matches_presentation_transform():
    size = 32.0
    origin = WorldPoint(17.0, -23.0)
    camera = WorldPoint(11.0, 9.0)
    zoom = 1.75
    transform = WorldTransform(
        hex_size=size,
        camera_x=camera.x,
        camera_y=camera.y,
        viewport_center=(400.0, 300.0),
        zoom=zoom,
    )

    for q, r in ((0, 0), (1, 0), (0, 1), (2, -3), (-5, 4), (8, -2)):
        position = LocalHexPosition(q, r)
        world = local_position_to_world_point(position, size, origin=origin)
        expected = axial_to_world_point(HexCoord(q, r), size, origin)
        assert world == expected
        screen = transform.world_point_to_screen(world)
        dx = world.x - camera.x
        dy = world.y - camera.y
        expected_screen = (
            400.0 + (dx - dy) * zoom,
            300.0 + (dx + dy) * 0.5 * zoom,
        )
        assert screen == pytest.approx(expected_screen)


def test_world_point_cell_resolution_round_trips_cell_centers():
    origin = WorldPoint(120.0, 75.0)
    for position in (
        LocalHexPosition(0, 0),
        LocalHexPosition(1, -2),
        LocalHexPosition(-4, 3),
    ):
        point = local_position_to_world_point(position, 24.0, origin=origin)
        assert world_point_to_local_position(
            point, 24.0, origin=origin
        ) == position


def test_world_point_resolution_uses_previous_cell_only_as_tie_break_hint():
    previous = LocalHexPosition(0, 0)
    center = local_position_to_world_point(previous, 24.0)
    assert world_point_to_local_position(
        center, 24.0, previous_position=previous
    ) == previous


def test_native_adapter_rejects_invalid_domain_values():
    with pytest.raises(TypeError, match="HexCoord"):
        hex_coord_to_local_position((1, 2))
    with pytest.raises(TypeError, match="LocalHexPosition"):
        local_position_to_world_point((1, 2), 24.0)
    with pytest.raises(TypeError, match="WorldPoint"):
        world_point_to_local_position((0.0, 0.0), 24.0)
