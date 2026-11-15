"""Tests for immutable map definitions and explicit cell boundaries."""

from dataclasses import FrozenInstanceError

import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import (
    HexCellData,
    HexMapDefinition,
    MapId,
    UnknownCellError,
    WorldId,
)


def make_cell(terrain_id="grass"):
    return HexCellData(
        terrain_id=terrain_id,
        is_walkable=True,
        has_obstacle=False,
    )


def make_map(cells=None, **overrides):
    values = {
        "world_id": WorldId("eldoria"),
        "map_id": MapId("starting_valley"),
        "name": "Başlangıç Vadisi",
        "layout": HexLayout(
            orientation=HexOrientation.POINTY_TOP,
            radius=1.0,
            origin=WorldPoint(0.0, 0.0),
        ),
        "cells": {} if cells is None else cells,
    }
    values.update(overrides)
    return HexMapDefinition(**values)


def test_map_definition_accepts_valid_identity_layout_and_cells():
    coord = AxialCoord(2, -1)
    cell = make_cell()

    map_definition = make_map({coord: cell})

    assert map_definition.world_id == WorldId("eldoria")
    assert map_definition.map_id == MapId("starting_valley")
    assert map_definition.name == "Başlangıç Vadisi"
    assert map_definition.layout.orientation is HexOrientation.POINTY_TOP
    assert map_definition.get_cell_data(coord) is cell


def test_map_definition_allows_an_empty_explicit_cell_set():
    map_definition = make_map()

    assert len(map_definition.cells) == 0
    assert map_definition.get_cell_data(AxialCoord(0, 0)) is None


def test_normal_query_returns_none_for_a_cell_outside_the_map():
    map_definition = make_map({AxialCoord(0, 0): make_cell()})

    assert map_definition.get_cell_data(AxialCoord(1, 0)) is None


def test_strict_query_returns_existing_cell_data():
    cell = make_cell()
    map_definition = make_map({AxialCoord(0, 0): cell})

    assert map_definition.require_cell_data(AxialCoord(0, 0)) is cell


def test_strict_query_raises_unknown_cell_error_with_address_context():
    map_definition = make_map()
    missing_coord = AxialCoord(-3, 2)

    with pytest.raises(UnknownCellError) as error:
        map_definition.require_cell_data(missing_coord)

    assert error.value.world_id == WorldId("eldoria")
    assert error.value.map_id == MapId("starting_valley")
    assert error.value.coord == missing_coord
    assert "(-3, 2)" in str(error.value)


def test_map_definition_copies_the_input_cell_mapping():
    coord = AxialCoord(0, 0)
    original_cell = make_cell()
    source = {coord: original_cell}

    map_definition = make_map(source)
    source[AxialCoord(1, 0)] = make_cell("stone")
    source[coord] = make_cell("sand")

    assert len(map_definition.cells) == 1
    assert map_definition.get_cell_data(coord) is original_cell
    assert map_definition.get_cell_data(AxialCoord(1, 0)) is None


def test_map_definition_cell_mapping_is_read_only():
    map_definition = make_map({AxialCoord(0, 0): make_cell()})

    with pytest.raises(TypeError):
        map_definition.cells[AxialCoord(1, 0)] = make_cell()


def test_map_definition_fields_are_immutable():
    map_definition = make_map()

    with pytest.raises(FrozenInstanceError):
        map_definition.name = "Changed"
    with pytest.raises(FrozenInstanceError):
        map_definition.map_id = MapId("changed")


@pytest.mark.parametrize(
    ("field", "value", "error"),
    [
        ("world_id", "eldoria", TypeError),
        ("map_id", "valley", TypeError),
        ("name", None, TypeError),
        ("name", "", ValueError),
        ("name", "  ", ValueError),
        ("layout", None, TypeError),
        ("cells", [], TypeError),
        ("cells", None, TypeError),
    ],
)
def test_map_definition_rejects_invalid_field_values(field, value, error):
    with pytest.raises(error):
        make_map(**{field: value})


@pytest.mark.parametrize(
    ("coord", "cell_data", "error"),
    [
        ((0, 0), make_cell(), TypeError),
        (AxialCoord(0, 0), "grass", TypeError),
        (AxialCoord(0, 0), None, TypeError),
    ],
)
def test_map_definition_rejects_invalid_cell_entries(coord, cell_data, error):
    with pytest.raises(error):
        make_map({coord: cell_data})


@pytest.mark.parametrize("coord", [(0, 0), None, "0,0"])
def test_cell_queries_reject_non_axial_coordinates(coord):
    map_definition = make_map()

    with pytest.raises(TypeError):
        map_definition.get_cell_data(coord)
    with pytest.raises(TypeError):
        map_definition.require_cell_data(coord)


def test_same_axial_coordinate_can_exist_independently_on_different_maps():
    coord = AxialCoord(0, 0)
    first_cell = make_cell("grass")
    second_cell = make_cell("stone")
    first_map = make_map(
        {coord: first_cell},
        map_id=MapId("village"),
        name="Village",
    )
    second_map = make_map(
        {coord: second_cell},
        map_id=MapId("mountain"),
        name="Mountain",
    )

    assert first_map.get_cell_data(coord) is first_cell
    assert second_map.get_cell_data(coord) is second_cell
    assert first_map.map_id != second_map.map_id


def test_map_definition_rejects_wrong_identifier_and_layout_types():
    with pytest.raises(TypeError):
        make_map(world_id=MapId("not-a-world"))
    with pytest.raises(TypeError):
        make_map(map_id=WorldId("not-a-map"))
    with pytest.raises(TypeError):
        make_map(layout=object())
