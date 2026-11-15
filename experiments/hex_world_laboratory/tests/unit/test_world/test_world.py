import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, Orientation
from hex_world_lab.world import HexCellData, HexMapDefinition, HexWorld, MapId, WorldId
from hex_world_lab.world.map_registry import MapWorldMismatchError


def make_definition(world_id, map_id, name):
    return HexMapDefinition(
        world_id=world_id,
        map_id=map_id,
        name=name,
        layout=HexLayout(orientation=Orientation.POINTY, radius=1.0),
        cells={AxialCoord(0, 0): HexCellData(terrain_id="grass")},
    )


def test_world_manages_multiple_maps():
    world_id = WorldId("eldoria")
    world = HexWorld(world_id)
    valley_id = MapId("valley")
    forest_id = MapId("forest")
    world.register_map(valley_id, "Starting Valley")
    world.register_map(forest_id, "Northern Forest")
    world.load_map(make_definition(world_id, valley_id, "Starting Valley"))
    world.load_map(make_definition(world_id, forest_id, "Northern Forest"))
    assert world.world_id == world_id
    assert world.map_registry.map_ids == (valley_id, forest_id)
    assert world.map_registry.loaded_map_ids == (valley_id, forest_id)


def test_same_axial_coordinate_is_independent_between_maps():
    world_id = WorldId("eldoria")
    world = HexWorld(world_id)
    first_id, second_id = MapId("first"), MapId("second")
    world.register_map(first_id, "First")
    world.register_map(second_id, "Second")
    first = make_definition(world_id, first_id, "First")
    second = make_definition(world_id, second_id, "Second")
    world.load_map(first)
    world.load_map(second)
    coord = AxialCoord(0, 0)
    assert world.get_map(first_id).get_cell_data(coord).terrain_id == "grass"
    assert world.get_map(second_id).get_cell_data(coord).terrain_id == "grass"
    assert first is not second
    assert first.map_id != second.map_id


def test_world_rejects_definition_from_another_world():
    world = HexWorld(WorldId("eldoria"))
    map_id = MapId("foreign")
    world.register_map(map_id, "Foreign")
    foreign = make_definition(WorldId("another-world"), map_id, "Foreign")
    with pytest.raises(MapWorldMismatchError):
        world.load_map(foreign)


def test_world_exposes_no_mutable_registry_storage():
    world = HexWorld(WorldId("eldoria"))
    world.register_map(MapId("valley"), "Valley")
    assert isinstance(world.map_registry.map_ids, tuple)
    assert isinstance(world.map_registry.registrations, tuple)


def test_world_requires_world_id():
    with pytest.raises(TypeError):
        HexWorld("eldoria")
