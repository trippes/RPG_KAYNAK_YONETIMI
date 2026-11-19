"""Tests for immutable hex-cell data and metadata isolation."""

from dataclasses import FrozenInstanceError

import pytest

from hex_world_lab.world import HexCellData


def make_cell(**overrides):
    values = {
        "terrain_id": "grass",
        "is_walkable": True,
        "has_obstacle": False,
    }
    values.update(overrides)
    return HexCellData(**values)


def test_cell_data_accepts_valid_values_and_defaults_metadata_to_none():
    cell = make_cell()

    assert cell.terrain_id == "grass"
    assert cell.is_walkable is True
    assert cell.has_obstacle is False
    assert cell.metadata is None


def test_cell_data_accepts_nested_json_compatible_metadata():
    cell = make_cell(
        metadata={
            "biome": "temperate",
            "fertility": 0.85,
            "active": True,
            "optional": None,
            "resources": ["herb", "wood"],
            "details": {"elevation": 12, "tags": ("green", "fertile")},
        }
    )

    assert cell.metadata["biome"] == "temperate"
    assert cell.metadata["fertility"] == 0.85
    assert cell.metadata["resources"] == ("herb", "wood")
    assert cell.metadata["details"]["tags"] == ("green", "fertile")


@pytest.mark.parametrize("terrain_id", ["", " ", "\t\n"])
def test_cell_data_rejects_empty_or_whitespace_terrain_id(terrain_id):
    with pytest.raises(ValueError):
        make_cell(terrain_id=terrain_id)


@pytest.mark.parametrize("terrain_id", [None, 1, True, b"grass"])
def test_cell_data_rejects_non_string_terrain_id(terrain_id):
    with pytest.raises(TypeError):
        make_cell(terrain_id=terrain_id)


@pytest.mark.parametrize("field", ["is_walkable", "has_obstacle"])
@pytest.mark.parametrize("value", [0, 1, "true", None, [], {}])
def test_boolean_fields_reject_non_boolean_values(field, value):
    with pytest.raises(TypeError):
        make_cell(**{field: value})


def test_cell_data_fields_are_immutable():
    cell = make_cell()

    with pytest.raises(FrozenInstanceError):
        cell.terrain_id = "stone"
    with pytest.raises(FrozenInstanceError):
        cell.is_walkable = False
    with pytest.raises(FrozenInstanceError):
        cell.metadata = {"changed": True}


def test_metadata_is_defensively_copied_at_construction():
    source = {"resources": ["wood", "herb"], "details": {"fertility": 0.8}}
    cell = make_cell(metadata=source)

    source["resources"].append("iron")
    source["details"]["fertility"] = 0.1
    source["new_key"] = "new value"

    assert cell.metadata["resources"] == ("wood", "herb")
    assert cell.metadata["details"]["fertility"] == 0.8
    assert "new_key" not in cell.metadata


def test_metadata_mappings_are_read_only_at_every_nesting_level():
    cell = make_cell(metadata={"details": {"fertility": 0.8}})

    with pytest.raises(TypeError):
        cell.metadata["new_key"] = "value"
    with pytest.raises(TypeError):
        cell.metadata["details"]["fertility"] = 0.2


def test_metadata_sequences_are_immutable_tuples():
    cell = make_cell(metadata={"resources": ["wood", ["herb"]]})

    assert cell.metadata["resources"] == ("wood", ("herb",))
    with pytest.raises(AttributeError):
        cell.metadata["resources"].append("iron")


@pytest.mark.parametrize("metadata", [[], "metadata", 1, True])
def test_metadata_root_must_be_a_mapping_or_none(metadata):
    with pytest.raises(TypeError):
        make_cell(metadata=metadata)


@pytest.mark.parametrize(
    "metadata",
    [
        {"bad": object()},
        {"bad": b"bytes"},
        {"bad": {1: "non-string key"}},
        {"bad": float("nan")},
        {"bad": float("inf")},
        {"bad": float("-inf")},
    ],
)
def test_metadata_rejects_non_json_values_and_invalid_numbers(metadata):
    with pytest.raises((TypeError, ValueError)):
        make_cell(metadata=metadata)


def test_metadata_rejects_circular_mapping_references():
    metadata = {}
    metadata["self"] = metadata

    with pytest.raises(ValueError, match="circular"):
        make_cell(metadata=metadata)


def test_metadata_rejects_circular_sequence_references():
    metadata = []
    metadata.append(metadata)

    with pytest.raises(ValueError, match="circular"):
        make_cell(metadata={"items": metadata})


def test_equal_cell_data_have_equal_hashes():
    first = make_cell(metadata={"biome": "temperate", "resources": ["wood", "herb"]})
    second = make_cell(metadata={"resources": ("wood", "herb"), "biome": "temperate"})

    assert first == second
    assert hash(first) == hash(second)
    assert len({first, second}) == 1


def test_metadata_scalar_equality_preserves_hash_contract():
    boolean_value = make_cell(metadata={"value": True})
    integer_value = make_cell(metadata={"value": 1})

    # Python mapping equality treats True and 1 as equal values.
    assert boolean_value == integer_value
    assert hash(boolean_value) == hash(integer_value)


def test_walkability_and_obstacle_flags_are_independent():
    cell = make_cell(is_walkable=True, has_obstacle=True)

    assert cell.is_walkable is True
    assert cell.has_obstacle is True
