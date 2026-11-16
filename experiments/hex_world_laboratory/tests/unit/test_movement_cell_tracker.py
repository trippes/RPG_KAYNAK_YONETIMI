import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint, axial_to_world
from hex_world_lab.simulation import MovementCellTracker
from hex_world_lab.world import HexCellData, HexMapDefinition, HexWorld, MapId, MovementWorldContext, WorldId


def make_tracker():
    world_id = WorldId("tracker-world")
    map_id = MapId("tracker-map")
    world = HexWorld(world_id)
    world.register_map(map_id, "Tracker map")
    layout = HexLayout(HexOrientation.FLAT_TOP, radius=1.0)
    cells = {
        AxialCoord(q, r): HexCellData("grass", True, False)
        for q, r in ((0, 0), (1, 0), (2, 0), (-1, 0))
    }
    world.load_map(HexMapDefinition(world_id, map_id, "Tracker map", layout, cells))
    return world, map_id, layout, MovementCellTracker(MovementWorldContext(world, map_id))


def test_tracker_starts_without_a_previous_cell_or_resolution():
    _, _, _, tracker = make_tracker()
    assert tracker.previous_cell is None
    assert tracker.current_resolution is None


def test_tracker_commits_successful_resolution():
    _, _, layout, tracker = make_tracker()
    position = axial_to_world(AxialCoord(1, 0), layout)
    result = tracker.update(position)
    assert result.coord == AxialCoord(1, 0)
    assert tracker.previous_cell == AxialCoord(1, 0)
    assert tracker.current_resolution is result


def test_tracker_preserves_previous_cell_on_exact_shared_boundary():
    _, _, layout, tracker = make_tracker()
    first = AxialCoord(0, 0)
    second = AxialCoord(1, 0)
    first_center = axial_to_world(first, layout)
    second_center = axial_to_world(second, layout)
    boundary = WorldPoint(
        (first_center.x + second_center.x) / 2.0,
        (first_center.y + second_center.y) / 2.0,
    )
    tracker.update(first_center)
    result = tracker.update(boundary)
    assert result.coord == first


def test_tracker_updates_after_crossing_boundary():
    _, _, layout, tracker = make_tracker()
    tracker.update(axial_to_world(AxialCoord(0, 0), layout))
    result = tracker.update(axial_to_world(AxialCoord(1, 0), layout))
    assert result.coord == AxialCoord(1, 0)
    assert tracker.previous_cell == AxialCoord(1, 0)


def test_tracker_keeps_geometric_cell_even_when_cell_data_is_missing():
    _, _, layout, tracker = make_tracker()
    result = tracker.update(axial_to_world(AxialCoord(12, -5), layout))
    assert result.coord == AxialCoord(12, -5)
    assert result.cell_data is None
    assert tracker.previous_cell == AxialCoord(12, -5)


def test_tracker_state_is_atomic_when_map_is_unloaded():
    world, map_id, layout, tracker = make_tracker()
    previous = tracker.update(axial_to_world(AxialCoord(0, 0), layout))
    world.unload_map(map_id)
    with pytest.raises(Exception):
        tracker.update(WorldPoint(10.0, 10.0))
    assert tracker.current_resolution is previous
    assert tracker.previous_cell == AxialCoord(0, 0)


def test_tracker_rejects_invalid_position_without_mutating_state():
    _, _, layout, tracker = make_tracker()
    previous = tracker.update(axial_to_world(AxialCoord(0, 0), layout))
    with pytest.raises(TypeError):
        tracker.update(object())
    assert tracker.current_resolution is previous
    assert tracker.previous_cell == AxialCoord(0, 0)
