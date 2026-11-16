import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import (
    CellAddress,
    HexCellData,
    HexMapDefinition,
    HexWorld,
    MapId,
    MapNotLoadedError,
    UnknownCellError,
    UnknownMapError,
    WorldId,
)


WORLD_ID = WorldId("eldoria")
MAP_ID = MapId("forest")
COORD = AxialCoord(1, -1)
BASE = HexCellData(
    terrain_id="grass",
    is_walkable=True,
    has_obstacle=False,
    metadata={"biome": "woodland", "tags": ["north"]},
)


def make_definition(map_id=MAP_ID, terrain_id="grass"):
    return HexMapDefinition(
        world_id=WORLD_ID,
        map_id=map_id,
        name=map_id.value,
        layout=HexLayout(orientation=HexOrientation.POINTY_TOP, radius=1.0),
        cells={
            COORD: HexCellData(
                terrain_id=terrain_id,
                is_walkable=True,
                has_obstacle=False,
                metadata={"biome": "woodland", "tags": ["north"]},
            )
        },
    )


def make_world(*map_ids):
    world = HexWorld(WORLD_ID)
    for map_id in map_ids or (MAP_ID,):
        world.register_map(map_id, map_id.value)
        world.load_map(make_definition(map_id))
    return world


def address(map_id=MAP_ID, coord=COORD):
    return CellAddress(WORLD_ID, map_id, coord)


def test_runtime_stores_only_fields_different_from_base():
    world = make_world()
    world.runtime.set_cell_state(
        address(), terrain_id="mud", is_walkable=False, has_obstacle=True
    )
    override = world.runtime.get_override(address())
    assert override.terrain_id == "mud"
    assert override.is_walkable is False
    assert override.has_obstacle is True
    assert world.runtime.override_count == 1
    assert world.runtime.field_override_count == 3


def test_runtime_does_not_change_immutable_base_definition():
    world = make_world()
    base = world.get_map(MAP_ID).require_cell_data(COORD)
    world.runtime.set_terrain(address(), "mud")
    assert world.get_map(MAP_ID).require_cell_data(COORD) is base
    assert base.terrain_id == "grass"
    assert world.view.require_cell(address()).terrain_id == "mud"


def test_setting_value_equal_to_base_does_not_create_override():
    world = make_world()
    world.runtime.set_terrain(address(), "grass")
    world.runtime.set_walkable(address(), True)
    world.runtime.set_obstacle(address(), False)
    assert world.runtime.override_count == 0
    assert world.runtime.field_override_count == 0


def test_resetting_last_field_removes_cell_override():
    world = make_world()
    world.runtime.set_terrain(address(), "mud")
    world.runtime.reset_terrain(address())
    assert not world.runtime.has_override(address())
    assert world.runtime.override_count == 0


def test_reset_one_field_preserves_other_overrides():
    world = make_world()
    world.runtime.set_cell_state(address(), terrain_id="mud", has_obstacle=True)
    world.runtime.reset_terrain(address())
    override = world.runtime.get_override(address())
    assert override.terrain_id is None
    assert override.has_obstacle is True
    assert world.runtime.field_override_count == 1


@pytest.mark.parametrize(
    "kwargs, error",
    [
        ({"terrain_id": ""}, ValueError),
        ({"terrain_id": 7}, TypeError),
        ({"is_walkable": 1}, TypeError),
        ({"has_obstacle": "yes"}, TypeError),
        ({}, ValueError),
    ],
)
def test_runtime_rejects_invalid_state_values(kwargs, error):
    world = make_world()
    with pytest.raises(error):
        world.runtime.set_cell_state(address(), **kwargs)


def test_runtime_rejects_unknown_world_address():
    world = make_world()
    foreign = CellAddress(WorldId("other"), MAP_ID, COORD)
    with pytest.raises(ValueError, match="belongs to world"):
        world.runtime.set_terrain(foreign, "mud")


def test_runtime_rejects_unknown_map():
    world = make_world()
    with pytest.raises(UnknownMapError):
        world.runtime.set_terrain(address(MapId("missing")), "mud")


def test_runtime_rejects_registered_but_unloaded_map():
    world = make_world()
    other = MapId("unloaded")
    world.register_map(other, other.value)
    with pytest.raises(MapNotLoadedError):
        world.runtime.set_terrain(address(other), "mud")


def test_runtime_rejects_absent_cell():
    world = make_world()
    with pytest.raises(UnknownCellError):
        world.runtime.set_terrain(address(coord=AxialCoord(9, 9)), "mud")


def test_runtime_isolates_same_coordinate_between_maps():
    first, second = MapId("first"), MapId("second")
    world = make_world(first, second)
    world.runtime.set_terrain(address(first), "mud")
    assert world.runtime.get_override(address(second)) is None


def test_runtime_overrides_survive_unload_and_apply_after_reload():
    world = make_world()
    world.runtime.set_terrain(address(), "mud")
    world.unload_map(MAP_ID)
    assert world.runtime.get_override(address()).terrain_id == "mud"
    with pytest.raises(MapNotLoadedError):
        world.view.get_cell(address())
    world.load_map(make_definition())
    assert world.view.require_cell(address()).terrain_id == "mud"


def test_runtime_overrides_are_cleared_when_map_is_removed():
    world = make_world()
    world.runtime.set_terrain(address(), "mud")
    world.remove_map(MAP_ID)
    assert world.runtime.get_override(address()) is None
    assert world.runtime.override_count == 0


def test_clear_cell_restores_base_data():
    world = make_world()
    world.runtime.set_cell_state(address(), terrain_id="mud", is_walkable=False)
    world.runtime.clear_cell(address())
    assert world.runtime.get_override(address()) is None
    assert world.view.require_cell(address()).terrain_id == "grass"
    assert world.view.require_cell(address()).is_walkable is True


def test_runtime_requires_map_registry_from_same_world():
    from hex_world_lab.world import HexWorldRuntime, MapRegistry

    with pytest.raises(ValueError):
        HexWorldRuntime(WORLD_ID, MapRegistry(WorldId("other")))
