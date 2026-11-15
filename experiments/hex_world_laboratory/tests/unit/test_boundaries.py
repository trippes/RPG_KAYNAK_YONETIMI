import pytest

from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
    axial_to_world,
    world_to_axial,
)


@pytest.mark.parametrize("orientation", list(HexOrientation))
def test_world_origin_maps_to_axial_origin(orientation):
    layout = HexLayout(
        orientation=orientation,
        radius=1.0,
        origin=WorldPoint(4.0, -3.0),
    )
    assert world_to_axial(layout.origin, layout) == AxialCoord(0, 0)


@pytest.mark.parametrize("orientation", list(HexOrientation))
def test_cell_center_with_small_offsets_stays_in_cell(orientation):
    layout = HexLayout(orientation=orientation, radius=2.0)
    for q in range(-8, 9):
        for r in range(-8, 9):
            center = axial_to_world(AxialCoord(q, r), layout)
            assert world_to_axial(
                WorldPoint(center.x + 0.01, center.y - 0.01),
                layout,
            ) == AxialCoord(q, r)


@pytest.mark.parametrize("orientation", list(HexOrientation))
def test_shared_edge_tie_break_is_repeatable(orientation):
    layout = HexLayout(orientation=orientation, radius=1.0)
    first = axial_to_world(AxialCoord(0, 0), layout)
    second = axial_to_world(AxialCoord(1, 0), layout)
    midpoint = WorldPoint((first.x + second.x) / 2, (first.y + second.y) / 2)

    assert world_to_axial(midpoint, layout) == AxialCoord(0, 0)
    assert world_to_axial(midpoint, layout) == world_to_axial(midpoint, layout)


@pytest.mark.parametrize("orientation", list(HexOrientation))
def test_shared_edge_keeps_previous_cell_when_distances_are_equal(orientation):
    layout = HexLayout(orientation=orientation, radius=1.0)
    previous_cell = AxialCoord(1, 0)
    first = axial_to_world(AxialCoord(0, 0), layout)
    second = axial_to_world(previous_cell, layout)
    midpoint = WorldPoint((first.x + second.x) / 2, (first.y + second.y) / 2)

    assert world_to_axial(midpoint, layout, previous_cell=previous_cell) == previous_cell


@pytest.mark.parametrize("orientation", list(HexOrientation))
def test_nearest_cell_wins_after_crossing_shared_edge(orientation):
    layout = HexLayout(orientation=orientation, radius=1.0)
    previous_cell = AxialCoord(0, 0)
    first = axial_to_world(previous_cell, layout)
    second = axial_to_world(AxialCoord(1, 0), layout)
    midpoint = WorldPoint((first.x + second.x) / 2, (first.y + second.y) / 2)
    crossed_point = WorldPoint(
        midpoint.x + (second.x - first.x) * 1e-6,
        midpoint.y + (second.y - first.y) * 1e-6,
    )

    assert world_to_axial(crossed_point, layout, previous_cell=previous_cell) == AxialCoord(1, 0)
