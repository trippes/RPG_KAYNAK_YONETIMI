import json

import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import CellAddress, HexCellData, HexMapDefinition, HexWorld, MapId, WorldId
from hex_world_lab.world.persistence import (
    MapFileAlreadyExistsError,
    MapFileNotFoundError,
    RuntimeJSONDecodeError,
    load_runtime_file,
    restore_runtime_file,
    save_runtime_file,
)


def setup_world():
    definition = HexMapDefinition(
        WorldId("eldoria"), MapId("forest"), "forest",
        HexLayout(HexOrientation.POINTY_TOP, 1.0),
        {AxialCoord(0, 0): HexCellData("grass", True, False)},
    )
    world = HexWorld(definition.world_id)
    world.register_map(definition.map_id, definition.name)
    world.load_map(definition)
    return world, definition


def test_save_load_and_restore_round_trip(tmp_path):
    world, definition = setup_world()
    address = CellAddress(definition.world_id, definition.map_id, AxialCoord(0, 0))
    world.runtime.set_terrain(address, "mud")
    path = tmp_path / "forest.runtime.json"
    save_runtime_file(world.runtime, definition, path)
    snapshot = load_runtime_file(path, definition)
    assert snapshot.overrides[AxialCoord(0, 0)].terrain_id == "mud"

    restored, restored_definition = setup_world()
    restore_runtime_file(restored.runtime, restored_definition, path)
    assert restored.view.require_cell(address).terrain_id == "mud"


def test_create_mode_does_not_overwrite(tmp_path):
    world, definition = setup_world()
    path = tmp_path / "runtime.json"
    path.write_text("keep", encoding="utf-8")
    with pytest.raises(MapFileAlreadyExistsError):
        save_runtime_file(world.runtime, definition, path)
    assert path.read_text(encoding="utf-8") == "keep"


def test_replace_mode_replaces_atomically(tmp_path):
    world, definition = setup_world()
    path = tmp_path / "runtime.json"
    path.write_text("old", encoding="utf-8")
    save_runtime_file(world.runtime, definition, path, mode="replace")
    assert load_runtime_file(path, definition).overrides == {}


def test_invalid_json_and_duplicate_keys_are_rejected(tmp_path):
    world, definition = setup_world()
    path = tmp_path / "bad.json"
    path.write_text('{"schema_version":1,"schema_version":1}', encoding="utf-8")
    with pytest.raises(RuntimeJSONDecodeError):
        load_runtime_file(path, definition)


def test_missing_file_has_controlled_error(tmp_path):
    _, definition = setup_world()
    with pytest.raises(MapFileNotFoundError):
        load_runtime_file(tmp_path / "missing.json", definition)


def test_failed_restore_leaves_existing_runtime_unchanged(tmp_path):
    world, definition = setup_world()
    address = CellAddress(definition.world_id, definition.map_id, AxialCoord(0, 0))
    world.runtime.set_terrain(address, "mud")
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    before = dict(world.runtime.export_map_overrides(definition.map_id))
    with pytest.raises(Exception):
        restore_runtime_file(world.runtime, definition, path)
    assert dict(world.runtime.export_map_overrides(definition.map_id)) == before


def test_save_fails_for_missing_parent_directory(tmp_path):
    world, definition = setup_world()
    with pytest.raises(Exception):
        save_runtime_file(world.runtime, definition, tmp_path / "missing" / "runtime.json")
