"""Strict schema-v1 validation tests."""

import copy

import pytest

from hex_world_lab.world.persistence import (
    MapValidationError,
    UnsupportedMapSchemaVersionError,
    validate_map_payload,
)


def valid_payload():
    return {
        "schema_version": 1,
        "world_id": "eldoria",
        "map_id": "starting_valley",
        "name": "Başlangıç Vadisi",
        "layout": {
            "orientation": "pointy_top",
            "radius": 1.0,
            "origin": {"x": 0.0, "y": 0.0},
        },
        "cells": [
            {
                "q": -1,
                "r": 2,
                "terrain_id": "grass",
                "is_walkable": True,
                "has_obstacle": False,
                "metadata": {"tags": ["green", {"kind": "meadow"}]},
            }
        ],
    }


def test_accepts_valid_payload_and_empty_cell_list():
    payload = valid_payload()
    assert validate_map_payload(payload) is payload
    payload["cells"] = []
    assert validate_map_payload(payload)["cells"] == []


@pytest.mark.parametrize("field", [
    "schema_version", "world_id", "map_id", "name", "layout", "cells"
])
def test_rejects_missing_top_level_fields(field):
    payload = valid_payload()
    del payload[field]
    with pytest.raises(MapValidationError):
        validate_map_payload(payload)


def test_rejects_non_object_top_level():
    with pytest.raises(MapValidationError, match="object"):
        validate_map_payload([])


def test_rejects_unknown_fields_at_each_level():
    payload = valid_payload()
    payload["surprise"] = 1
    with pytest.raises(MapValidationError, match="unknown field"):
        validate_map_payload(payload)
    payload = valid_payload()
    payload["layout"]["extra"] = 1
    with pytest.raises(MapValidationError, match="unknown field"):
        validate_map_payload(payload)
    payload = valid_payload()
    payload["cells"][0]["extra"] = 1
    with pytest.raises(MapValidationError, match="unknown field"):
        validate_map_payload(payload)


@pytest.mark.parametrize("version", [2, 0, True, "1"])
def test_rejects_unsupported_or_invalid_schema_version(version):
    payload = valid_payload()
    payload["schema_version"] = version
    error = UnsupportedMapSchemaVersionError if version == 2 or version == 0 else MapValidationError
    with pytest.raises(error):
        validate_map_payload(payload)


@pytest.mark.parametrize("orientation", ["flat", "POINTY_TOP", None])
def test_rejects_invalid_orientation(orientation):
    payload = valid_payload()
    payload["layout"]["orientation"] = orientation
    with pytest.raises(MapValidationError):
        validate_map_payload(payload)


@pytest.mark.parametrize("radius", [0, -1, True, float("nan"), float("inf")])
def test_rejects_invalid_radius(radius):
    payload = valid_payload()
    payload["layout"]["radius"] = radius
    with pytest.raises(MapValidationError):
        validate_map_payload(payload)


@pytest.mark.parametrize("axis_value", [True, 1.5, "1"])
def test_rejects_non_integer_or_boolean_axial_coordinates(axis_value):
    payload = valid_payload()
    payload["cells"][0]["q"] = axis_value
    with pytest.raises(MapValidationError):
        validate_map_payload(payload)


def test_rejects_duplicate_axial_coordinates():
    payload = valid_payload()
    payload["cells"].append(copy.deepcopy(payload["cells"][0]))
    with pytest.raises(MapValidationError, match="duplicate axial coordinate"):
        validate_map_payload(payload)


@pytest.mark.parametrize("field", ["is_walkable", "has_obstacle"])
def test_rejects_non_boolean_cell_flags(field):
    payload = valid_payload()
    payload["cells"][0][field] = 1
    with pytest.raises(MapValidationError):
        validate_map_payload(payload)


@pytest.mark.parametrize("metadata", [[], "text", 3, float("nan"), {"x": float("inf")}])
def test_rejects_invalid_metadata(metadata):
    payload = valid_payload()
    payload["cells"][0]["metadata"] = metadata
    with pytest.raises(MapValidationError):
        validate_map_payload(payload)


def test_reports_precise_cell_field_path():
    payload = valid_payload()
    payload["cells"][0]["terrain_id"] = " "
    with pytest.raises(MapValidationError) as error:
        validate_map_payload(payload)
    assert error.value.path == "$.cells[0].terrain_id"
