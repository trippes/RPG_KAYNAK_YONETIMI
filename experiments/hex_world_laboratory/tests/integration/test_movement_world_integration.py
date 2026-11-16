import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint, axial_to_world
from hex_world_lab.movement import MovementConfig, MovementIntent, MovementState, Vector2
from hex_world_lab.simulation import MovementCellTracker, MovementSystem
from hex_world_lab.world import (
    HexCellData,
    HexMapDefinition,
    HexWorld,
    MapId,
    MapNotLoadedError,
    MovementWorldContext,
    WorldId,
)


def make_world():
    world_id = WorldId("integration-world")
    map_id = MapId("integration-map")
    world = HexWorld(world_id)
    world.register_map(map_id, "Integration map")
    layout = HexLayout(HexOrientation.FLAT_TOP, radius=1.0)
    cells = {
        AxialCoord(q, r): HexCellData("grass", True, False)
        for q in range(-3, 5)
        for r in range(-3, 4)
    }
    world.load_map(HexMapDefinition(world_id, map_id, "Integration map", layout, cells))
    return world, map_id, layout


def test_movement_tick_updates_position_then_cell_resolution_without_snapping():
    world, map_id, layout = make_world()
    initial_position = WorldPoint(0.2, 0.1)
    movement = MovementSystem(
        MovementState(initial_position),
        MovementConfig(max_speed=60.0),
    )
    tracker = MovementCellTracker(MovementWorldContext(world, map_id))

    for tick in range(4):
        state = movement.step(tick, MovementIntent(Vector2(1.0, 0.0)))
        resolution = tracker.update(state.position)

    assert movement.next_tick_number == 4
    assert (movement.state.position.x, movement.state.position.y) == pytest.approx((4.2, 0.1))
    assert resolution.coord == AxialCoord(3, -1)
    assert movement.state.position != axial_to_world(resolution.coord, layout)


def test_same_axial_coordinate_on_different_maps_has_distinct_address():
    world, map_id, layout = make_world()
    other_id = MapId("other-map")
    world.register_map(other_id, "Other map")
    world.load_map(
        HexMapDefinition(
            world.world_id,
            other_id,
            "Other map",
            layout,
            {AxialCoord(0, 0): HexCellData("sand", True, False)},
        )
    )
    point = axial_to_world(AxialCoord(0, 0), layout)
    first = MovementWorldContext(world, map_id).resolve_position(point)
    second = MovementWorldContext(world, other_id).resolve_position(point)
    assert first.coord == second.coord
    assert first.address != second.address


def test_tracker_does_not_auto_load_unloaded_map():
    world, map_id, _ = make_world()
    tracker = MovementCellTracker(MovementWorldContext(world, map_id))
    world.unload_map(map_id)

    with pytest.raises(MapNotLoadedError):
        tracker.update(WorldPoint(0.0, 0.0))
    assert not world.is_loaded(map_id)
