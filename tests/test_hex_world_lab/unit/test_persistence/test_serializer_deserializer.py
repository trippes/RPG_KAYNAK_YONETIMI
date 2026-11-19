"""Deterministic serialization and immutable deserialization tests."""

import json

import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from hex_world_lab.world.persistence import (
    MapValidationError,
    deserialize_map_payload,
    map_to_payload,
    serialize_map,
)


def make_map():
    return HexMapDefinition(
        world_id=WorldId("eldoria"),
        map_id=MapId("starting_valley"),
        name="Başlangıç Vadisi",
        layout=HexLayout(
            orientation=HexOrientation.FLAT_TOP,
            radius=2.5,
            origin=WorldPoint(-10.25, 4.5),
        ),
        cells={
            AxialCoord(2, -1): HexCellData(
                "stone", True, False,
                {"empty": {}, "nested": ["taş", {"hardness": 2}]},
            ),
            AxialCoord(-3, 4): HexCellData("grass", True, False, None),
        },
    )


def test_serializer_is_deterministic_and_sorts_cells():
    map_definition = make_map()
    first = serialize_map(map_definition)
    assert first == serialize_map(map_definition)
    payload = json.loads(first)
    assert [(item["q"], item["r"]) for item in payload["cells"]] == [(-3, 4), (2, -1)]
    assert first.endswith("\n")
    assert "Başlangıç Vadisi" in first


def test_serializer_preserves_null_empty_metadata_and_nested_sequences():
    payload = map_to_payload(make_map())
    assert payload["cells"][0]["metadata"] is None
    assert payload["cells"][1]["metadata"]["empty"] == {}
    assert payload["cells"][1]["metadata"]["nested"] == ["taş", {"hardness": 2}]


def test_round_trip_preserves_map_and_deep_metadata():
    original = make_map()
    restored = deserialize_map_payload(json.loads(serialize_map(original)))
    assert restored == original
    assert restored.cells[AxialCoord(2, -1)].metadata["nested"][1]["hardness"] == 2
    with pytest.raises(TypeError):
        restored.cells[AxialCoord(2, -1)].metadata["nested"][1]["hardness"] = 9


def test_deserializer_rejects_invalid_late_cell_without_partial_map():
    payload = map_to_payload(make_map())
    payload["cells"][-1]["terrain_id"] = ""
    with pytest.raises(MapValidationError):
        deserialize_map_payload(payload)


def test_serializer_rejects_wrong_model_type():
    with pytest.raises(TypeError):
        serialize_map({})
