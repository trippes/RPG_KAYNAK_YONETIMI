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
MAP_ID = MapId("village")
COORD = AxialCoord(0, 0)


def make_definition():
    return HexMapDefinition(
        world_id=WORLD_ID,
        map_id=MAP_ID,
        name="Village",
        layout=HexLayout(orientation=HexOrientation.FLAT_TOP, radius=2.0),
        cells={
            COORD: HexCellData(
                terrain_id="grass",
                is_walkable=True,
                has_obstacle=False,
                metadata={"region": {"name": "north"}},
            )
        },
    )


def make_world():
    world = HexWorld(WORLD_ID)
    world.register_map(MAP_ID, "Village")
    world.load_map(make_definition())
    return world


def address(map_id=MAP_ID, coord=COORD, world_id=WORLD_ID):
    return CellAddress(world_id, map_id, coord)


def test_view_returns_base_cell_without_override():
    world = make_world()
    base = world.get_map(MAP_ID).require_cell_data(COORD)
    assert world.view.get_cell(address()) is base


def test_view_combines_runtime_override_and_preserves_metadata():
    world = make_world()
    world.runtime.set_cell_state(address(), terrain_id="mud", is_walkable=False)
    current = world.view.require_cell(address())
    assert current.terrain_id == "mud"
    assert current.is_walkable is False
    assert current.has_obstacle is False
    assert current.metadata == {"region": {"name": "north"}}
    assert current is not world.get_map(MAP_ID).require_cell_data(COORD)


def test_view_result_remains_immutable():
    world = make_world()
    world.runtime.set_terrain(address(), "mud")
    current = world.view.require_cell(address())
    with pytest.raises((AttributeError, TypeError)):
        current.terrain_id = "stone"
    with pytest.raises(TypeError):
        current.metadata["region"]["name"] = "south"


def test_get_cell_returns_none_only_for_absent_cell():
    world = make_world()
    missing = address(coord=AxialCoord(5, 5))
    assert world.view.get_cell(missing) is None
    with pytest.raises(UnknownCellError):
        world.view.require_cell(missing)


def test_view_raises_unknown_map_instead_of_returning_none():
    world = make_world()
    with pytest.raises(UnknownMapError):
        world.view.get_cell(address(MapId("missing")))


def test_view_raises_map_not_loaded_instead_of_returning_none():
    world = make_world()
    world.unload_map(MAP_ID)
    with pytest.raises(MapNotLoadedError):
        world.view.get_cell(address())


def test_view_rejects_foreign_world_address():
    world = make_world()
    with pytest.raises(ValueError, match="belongs to world"):
        world.view.get_cell(address(world_id=WorldId("other")))


def test_view_keeps_same_coordinate_in_separate_maps_independent():
    world = make_world()
    other_id = MapId("other")
    world.register_map(other_id, "Other")
    world.load_map(
        HexMapDefinition(
            world_id=WORLD_ID,
            map_id=other_id,
            name="Other",
            layout=HexLayout(orientation=HexOrientation.FLAT_TOP, radius=2.0),
            cells={COORD: HexCellData("stone", False, True)},
        )
    )
    world.runtime.set_terrain(address(), "mud")
    assert world.view.require_cell(address()).terrain_id == "mud"
    assert world.view.require_cell(address(other_id)).terrain_id == "stone"


def test_world_owns_one_runtime_and_view():
    world = make_world()
    assert world.runtime.world_id == WORLD_ID
    assert world.view.world_id == WORLD_ID
    assert world.runtime is world.runtime
    assert world.view is world.view
