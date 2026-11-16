import copy

import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from hex_world_lab.world.persistence import (
    RuntimeBaseMapMismatchError,
    RuntimeMapMismatchError,
    RuntimeSchemaVersionError,
    RuntimeValidationError,
    RuntimeWorldMismatchError,
    base_map_sha256,
    runtime_to_payload,
    validate_runtime_payload,
)
from hex_world_lab.world import HexWorld


def make_map(world_id="eldoria", map_id="forest", terrain="grass"):
    return HexMapDefinition(
        WorldId(world_id), MapId(map_id), map_id,
        HexLayout(HexOrientation.POINTY_TOP, 1.0),
        {
            AxialCoord(0, 0): HexCellData(terrain, True, False),
            AxialCoord(1, -1): HexCellData("stone", False, True),
        },
    )


def payload_for(definition):
    return {
        "schema_version": 1,
        "kind": "hex_world_runtime_snapshot",
        "world_id": definition.world_id.value,
        "map_id": definition.map_id.value,
        "base_map_sha256": base_map_sha256(definition),
        "overrides": [{"q": 0, "r": 0, "terrain_id": "mud"}],
    }


def test_valid_empty_and_nonempty_payloads():
    definition = make_map()
    empty = payload_for(definition)
    empty["overrides"] = []
    assert validate_runtime_payload(empty, definition)["overrides"] == []
    assert validate_runtime_payload(payload_for(definition), definition)["overrides"][0]["terrain_id"] == "mud"


@pytest.mark.parametrize("mutate", [
    lambda p: p.update(extra=True),
    lambda p: p.update(schema_version=True),
    lambda p: p.update(schema_version=2),
    lambda p: p.update(kind="wrong"),
    lambda p: p.update(world_id="other"),
    lambda p: p.update(map_id="other"),
    lambda p: p.update(base_map_sha256="bad"),
    lambda p: p.update(overrides="not-an-array"),
    lambda p: p.update(overrides=[{"q": True, "r": 0, "terrain_id": "mud"}]),
    lambda p: p.update(overrides=[{"q": 0, "r": 0}]),
    lambda p: p.update(overrides=[{"q": 0, "r": 0, "terrain_id": None}]),
    lambda p: p.update(overrides=[{"q": 0, "r": 0, "is_walkable": 1}]),
    lambda p: p.update(overrides=[{"q": 0, "r": 0, "terrain_id": "grass"}]),
    lambda p: p.update(overrides=[{"q": 0, "r": 0, "terrain_id": "mud"}, {"q": 0, "r": 0, "has_obstacle": True}]),
    lambda p: p.update(overrides=[{"q": 99, "r": 99, "has_obstacle": True}]),
    lambda p: p.update(overrides=[{"q": 0, "r": 0, "metadata": {"x": 1}}]),
])
def test_invalid_payloads_are_rejected(mutate):
    definition = make_map()
    payload = payload_for(definition)
    mutate(payload)
    with pytest.raises(RuntimeValidationError):
        validate_runtime_payload(payload, definition)


def test_base_map_fingerprint_mismatch_is_rejected():
    with pytest.raises(RuntimeBaseMapMismatchError):
        validate_runtime_payload(payload_for(make_map(terrain="dirt")), make_map(terrain="grass"))


def test_world_and_map_mismatch_have_specific_errors():
    definition = make_map()
    with pytest.raises(RuntimeWorldMismatchError):
        validate_runtime_payload(payload_for(definition), make_map(world_id="another"))
    with pytest.raises(RuntimeMapMismatchError):
        validate_runtime_payload(payload_for(definition), make_map(map_id="another"))


def test_unsupported_schema_has_specific_error():
    definition = make_map()
    payload = payload_for(definition)
    payload["schema_version"] = 7
    with pytest.raises(RuntimeSchemaVersionError):
        validate_runtime_payload(payload, definition)


def test_runtime_to_payload_contains_only_sparse_changed_fields():
    definition = make_map()
    world = HexWorld(definition.world_id)
    world.register_map(definition.map_id, definition.name)
    world.load_map(definition)
    world.runtime.set_terrain(
        __import__("hex_world_lab.world", fromlist=["CellAddress"]).CellAddress(
            definition.world_id, definition.map_id, AxialCoord(0, 0)
        ),
        "mud",
    )
    payload = runtime_to_payload(world.runtime, definition)
    assert payload["overrides"] == [{"q": 0, "r": 0, "terrain_id": "mud"}]
