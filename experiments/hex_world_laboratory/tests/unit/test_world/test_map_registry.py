import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from hex_world_lab.world.map_registry import (
    DuplicateMapError,
    MapAlreadyLoadedError,
    MapNameMismatchError,
    MapNotLoadedError,
    MapRegistration,
    MapWorldMismatchError,
    MapRegistry,
    UnknownMapError,
)


WORLD_ID = WorldId("eldoria")
MAP_ID = MapId("valley")
NAME = "Starting Valley"
LAYOUT = HexLayout(orientation=HexOrientation.POINTY_TOP, radius=1.0)


def make_definition(*, world_id=WORLD_ID, map_id=MAP_ID, name=NAME):
    return HexMapDefinition(
        world_id=world_id,
        map_id=map_id,
        name=name,
        layout=LAYOUT,
        cells={AxialCoord(0, 0): HexCellData(terrain_id="grass", is_walkable=True, has_obstacle=False)},
    )


def make_registry():
    registry = MapRegistry(WORLD_ID)
    registry.register_map(MAP_ID, NAME)
    return registry


def test_registration_is_lightweight_and_not_loaded():
    registry = make_registry()
    registration = registry.get_registration(MAP_ID)
    assert registration == MapRegistration(MAP_ID, NAME)
    assert registry.is_registered(MAP_ID)
    assert not registry.is_loaded(MAP_ID)
    assert registry.get_map(MAP_ID) is None
    assert registry.loaded_map_ids == ()


def test_multiple_map_registrations_are_supported():
    registry = make_registry()
    forest_id = MapId("forest")
    registry.register_map(forest_id, "Northern Forest")
    assert registry.map_ids == (MAP_ID, forest_id)


def test_duplicate_registration_is_rejected():
    registry = make_registry()
    with pytest.raises(DuplicateMapError):
        registry.register_map(MAP_ID, NAME)


def test_load_registered_map_and_retrieve_definition():
    registry = make_registry()
    definition = make_definition()
    registry.load_map(definition)
    assert registry.is_loaded(MAP_ID)
    assert registry.get_map(MAP_ID) is definition
    assert registry.loaded_map_ids == (MAP_ID,)


def test_loading_unknown_map_is_rejected():
    registry = MapRegistry(WORLD_ID)
    with pytest.raises(UnknownMapError):
        registry.load_map(make_definition())


def test_loading_map_from_another_world_is_rejected():
    registry = make_registry()
    definition = make_definition(world_id=WorldId("other-world"))
    with pytest.raises(MapWorldMismatchError):
        registry.load_map(definition)


def test_loading_definition_with_different_name_is_rejected():
    registry = make_registry()
    with pytest.raises(MapNameMismatchError):
        registry.load_map(make_definition(name="Different name"))


def test_loading_same_map_twice_is_rejected():
    registry = make_registry()
    definition = make_definition()
    registry.load_map(definition)
    with pytest.raises(MapAlreadyLoadedError):
        registry.load_map(definition)


def test_unload_releases_loaded_definition_but_keeps_registration():
    registry = make_registry()
    definition = make_definition()
    registry.load_map(definition)
    registry.unload_map(MAP_ID)
    assert registry.is_registered(MAP_ID)
    assert not registry.is_loaded(MAP_ID)
    assert registry.get_registration(MAP_ID) == MapRegistration(MAP_ID, NAME)
    assert registry.get_map(MAP_ID) is None
    assert registry.loaded_map_ids == ()


def test_unloading_registered_but_unloaded_map_is_rejected():
    registry = make_registry()
    with pytest.raises(MapNotLoadedError):
        registry.unload_map(MAP_ID)


def test_removing_map_also_removes_loaded_definition():
    registry = make_registry()
    registry.load_map(make_definition())
    registry.remove_map(MAP_ID)
    assert not registry.is_registered(MAP_ID)
    assert not registry.is_loaded(MAP_ID)
    assert registry.get_registration(MAP_ID) is None
    assert registry.get_map(MAP_ID) is None


def test_removing_unknown_map_is_rejected():
    with pytest.raises(UnknownMapError):
        MapRegistry(WORLD_ID).remove_map(MAP_ID)


def test_unknown_map_queries_are_safe():
    registry = MapRegistry(WORLD_ID)
    assert registry.get_registration(MAP_ID) is None
    assert registry.get_map(MAP_ID) is None
    assert not registry.is_registered(MAP_ID)
    assert not registry.is_loaded(MAP_ID)


def test_registry_exposes_immutable_snapshots():
    registry = make_registry()
    ids = registry.map_ids
    registrations = registry.registrations
    assert isinstance(ids, tuple)
    assert isinstance(registrations, tuple)
    with pytest.raises(AttributeError):
        ids.append(MapId("other"))
    with pytest.raises(AttributeError):
        registrations.append(MapRegistration(MapId("other"), "Other"))


@pytest.mark.parametrize("bad_id", ["valley", None, 3])
def test_map_id_arguments_are_validated(bad_id):
    registry = MapRegistry(WORLD_ID)
    with pytest.raises(TypeError):
        registry.is_registered(bad_id)


@pytest.mark.parametrize("bad_name", ["", "   ", None, 5])
def test_registration_name_is_validated(bad_name):
    registry = MapRegistry(WORLD_ID)
    expected = TypeError if not isinstance(bad_name, str) else ValueError
    with pytest.raises(expected):
        registry.register_map(MAP_ID, bad_name)


def test_registry_requires_world_id():
    with pytest.raises(TypeError):
        MapRegistry("eldoria")
