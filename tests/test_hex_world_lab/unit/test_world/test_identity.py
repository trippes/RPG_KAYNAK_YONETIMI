"""Tests for world identifiers and cell addresses."""

from dataclasses import FrozenInstanceError

import pytest

from hex_world_lab.geometry import AxialCoord
from hex_world_lab.world import CellAddress, MapId, WorldId


@pytest.mark.parametrize("value", ["", " ", "\t\n"])
@pytest.mark.parametrize("identifier_type", [WorldId, MapId])
def test_identifiers_reject_empty_or_whitespace_values(identifier_type, value):
    with pytest.raises(ValueError):
        identifier_type(value)


@pytest.mark.parametrize("value", [None, 1, True, b"world"])
@pytest.mark.parametrize("identifier_type", [WorldId, MapId])
def test_identifiers_reject_non_string_values(identifier_type, value):
    with pytest.raises(TypeError):
        identifier_type(value)


def test_world_and_map_ids_are_immutable_and_type_distinct():
    world_id = WorldId("shared")
    map_id = MapId("shared")

    assert world_id != map_id
    assert len({world_id, map_id}) == 2
    assert WorldId("shared") == world_id
    assert MapId("shared") == map_id
    assert len({WorldId("shared"), WorldId("shared")}) == 1

    with pytest.raises(FrozenInstanceError):
        world_id.value = "changed"


def test_cell_address_preserves_world_map_and_axial_coordinate():
    coord = AxialCoord(2, -1)
    address = CellAddress(WorldId("eldoria"), MapId("valley"), coord)

    assert address.world_id == WorldId("eldoria")
    assert address.map_id == MapId("valley")
    assert address.coord is coord


def test_same_axial_coordinate_in_different_maps_has_distinct_address():
    coord = AxialCoord(0, 0)
    first = CellAddress(WorldId("eldoria"), MapId("village"), coord)
    second = CellAddress(WorldId("eldoria"), MapId("forest"), coord)
    third = CellAddress(WorldId("other_world"), MapId("village"), coord)

    assert len({first, second, third}) == 3
    assert first != second
    assert first != third


@pytest.mark.parametrize(
    ("world_id", "map_id", "coord"),
    [
        ("eldoria", MapId("valley"), AxialCoord(0, 0)),
        (WorldId("eldoria"), "valley", AxialCoord(0, 0)),
        (WorldId("eldoria"), MapId("valley"), (0, 0)),
    ],
)
def test_cell_address_rejects_invalid_component_types(world_id, map_id, coord):
    with pytest.raises(TypeError):
        CellAddress(world_id, map_id, coord)


def test_equal_cell_addresses_have_equal_hashes():
    first = CellAddress(WorldId("eldoria"), MapId("valley"), AxialCoord(3, -2))
    second = CellAddress(WorldId("eldoria"), MapId("valley"), AxialCoord(3, -2))

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1
