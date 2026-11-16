"""Unit tests for the deterministic movement-demo world factory."""

from hex_world_lab.application.movement_demo import (
    MAP_ID,
    MAP_NAME,
    WORLD_ID,
    build_demo_world,
)
from hex_world_lab.geometry import AxialCoord, HexOrientation


def test_demo_world_contains_one_registered_loaded_map_and_61_cells() -> None:
    world, map_id = build_demo_world()

    assert world.world_id == WORLD_ID
    assert map_id == MAP_ID
    assert world.map_registry.map_ids == (MAP_ID,)
    assert world.map_registry.loaded_map_ids == (MAP_ID,)

    definition = world.get_map(map_id)
    assert definition is not None
    assert definition.name == MAP_NAME
    assert definition.layout.orientation is HexOrientation.FLAT_TOP
    assert definition.layout.radius == 32.0
    assert len(definition.cells) == 61
    assert definition.get_cell_data(AxialCoord(0, 0)).terrain_id == "grass"


def test_demo_world_factory_is_deterministic() -> None:
    first_world, first_id = build_demo_world()
    second_world, second_id = build_demo_world()

    first = first_world.get_map(first_id)
    second = second_world.get_map(second_id)
    assert first is not None and second is not None
    assert first.cells == second.cells
    assert first.layout == second.layout
