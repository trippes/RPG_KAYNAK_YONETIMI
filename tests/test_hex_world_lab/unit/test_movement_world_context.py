import pytest

from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
    axial_to_world,
)
from hex_world_lab.world import (
    CellAddress,
    HexCellData,
    HexMapDefinition,
    HexWorld,
    MapId,
    MapNotLoadedError,
    MovementCellResolution,
    MovementWorldContext,
    UnknownMapError,
    WorldId,
)


def make_world(*, orientation=HexOrientation.FLAT_TOP, radius=1.0, origin=None):
    world_id = WorldId("world-a")
    map_id = MapId("map-a")
    world = HexWorld(world_id)
    world.register_map(map_id, "Test map")
    layout = HexLayout(
        orientation=orientation,
        radius=radius,
        origin=origin or WorldPoint(0.0, 0.0),
    )
    cells = {
        AxialCoord(q, r): HexCellData("grass", True, False)
        for q, r in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (1, -1))
    }
    world.load_map(HexMapDefinition(world_id, map_id, "Test map", layout, cells))
    return world, map_id, layout


def test_context_requires_world_and_map_id_types():
    world, map_id, _ = make_world()
    with pytest.raises(TypeError):
        MovementWorldContext(object(), map_id)
    with pytest.raises(TypeError):
        MovementWorldContext(world, "map-a")


def test_context_rejects_unregistered_map():
    world, _, _ = make_world()
    with pytest.raises(UnknownMapError):
        MovementWorldContext(world, MapId("missing"))


def test_context_rejects_registered_but_unloaded_map_without_loading_it():
    world, map_id, _ = make_world()
    world.unload_map(map_id)
    with pytest.raises(MapNotLoadedError):
        MovementWorldContext(world, map_id)
    assert not world.is_loaded(map_id)


@pytest.mark.parametrize(
    "orientation",
    [HexOrientation.FLAT_TOP, HexOrientation.POINTY_TOP],
)
@pytest.mark.parametrize(
    "radius,origin",
    [
        (1.0, WorldPoint(0.0, 0.0)),
        (2.5, WorldPoint(13.0, -7.0)),
    ],
)
def test_context_uses_map_layout_for_both_orientations(orientation, radius, origin):
    world, map_id, layout = make_world(
        orientation=orientation, radius=radius, origin=origin
    )
    expected = AxialCoord(1, 0)
    result = MovementWorldContext(world, map_id).resolve_position(
        axial_to_world(expected, layout)
    )
    assert result.coord == expected
    assert result.cell_data.terrain_id == "grass"


def test_resolution_contains_world_scoped_cell_address():
    world, map_id, layout = make_world()
    result = MovementWorldContext(world, map_id).resolve_position(
        axial_to_world(AxialCoord(1, 0), layout)
    )
    assert result.world_id == world.world_id
    assert result.map_id == map_id
    assert result.address == CellAddress(world.world_id, map_id, result.coord)


def test_missing_explicit_cell_returns_none_without_rejecting_position():
    world, map_id, layout = make_world()
    position = axial_to_world(AxialCoord(8, -4), layout)
    result = MovementWorldContext(world, map_id).resolve_position(position)
    assert result.coord == AxialCoord(8, -4)
    assert result.cell_data is None


def test_runtime_cell_override_is_visible_in_resolution():
    world, map_id, layout = make_world()
    address = CellAddress(world.world_id, map_id, AxialCoord(0, 0))
    world.runtime.set_terrain(address, "mud")
    world.runtime.set_walkable(address, False)
    result = MovementWorldContext(world, map_id).resolve_position(
        axial_to_world(AxialCoord(0, 0), layout)
    )
    assert result.cell_data.terrain_id == "mud"
    assert result.cell_data.is_walkable is False


def test_resolution_rejects_inconsistent_address():
    world, map_id, _ = make_world()
    with pytest.raises(ValueError, match="coord"):
        MovementCellResolution(
            world.world_id,
            map_id,
            AxialCoord(0, 0),
            CellAddress(world.world_id, map_id, AxialCoord(1, 0)),
            None,
        )


def test_context_rejects_invalid_position_and_previous_cell():
    world, map_id, _ = make_world()
    context = MovementWorldContext(world, map_id)
    with pytest.raises(TypeError):
        context.resolve_position((0.0, 0.0))
    with pytest.raises(TypeError):
        context.resolve_position(WorldPoint(0.0, 0.0), previous_cell=(0, 0))
