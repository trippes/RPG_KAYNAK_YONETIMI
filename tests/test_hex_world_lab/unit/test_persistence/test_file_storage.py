"""Filesystem persistence behavior and failure-safety tests."""

import json

import pytest

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from hex_world_lab.world.persistence import (
    MapFileAlreadyExistsError,
    MapFileNotFoundError,
    MapFileWriteError,
    MapJSONDecodeError,
    load_map_file,
    save_map_file,
)


def make_map(terrain="grass"):
    return HexMapDefinition(
        world_id=WorldId("eldoria"),
        map_id=MapId("starting_valley"),
        name="Başlangıç Vadisi",
        layout=HexLayout(HexOrientation.POINTY_TOP, 1.0, WorldPoint(0.0, 0.0)),
        cells={AxialCoord(0, 0): HexCellData(terrain, True, False, {"not": ["değişmez"]})},
    )


def test_create_mode_writes_and_reads_utf8(tmp_path):
    path = tmp_path / "map.json"
    save_map_file(make_map(), path)
    assert "Başlangıç Vadisi" in path.read_text(encoding="utf-8")
    assert load_map_file(path) == make_map()


def test_create_mode_never_overwrites_existing_file(tmp_path):
    path = tmp_path / "map.json"
    path.write_text("keep me", encoding="utf-8")
    with pytest.raises(MapFileAlreadyExistsError):
        save_map_file(make_map(), path)
    assert path.read_text(encoding="utf-8") == "keep me"


def test_replace_mode_replaces_existing_file(tmp_path):
    path = tmp_path / "map.json"
    save_map_file(make_map("grass"), path)
    save_map_file(make_map("stone"), path, mode="replace")
    assert load_map_file(path).cells[AxialCoord(0, 0)].terrain_id == "stone"


def test_invalid_mode_is_rejected(tmp_path):
    with pytest.raises(ValueError, match="mode"):
        save_map_file(make_map(), tmp_path / "map.json", mode="silent")


def test_missing_file_has_controlled_error(tmp_path):
    with pytest.raises(MapFileNotFoundError):
        load_map_file(tmp_path / "missing.json")


@pytest.mark.parametrize("contents", [
    "{not json",
    '{"schema_version":1,"schema_version":1}',
    '{"value": NaN}',
])
def test_invalid_json_and_duplicate_keys_are_rejected(tmp_path, contents):
    path = tmp_path / "bad.json"
    path.write_text(contents, encoding="utf-8")
    with pytest.raises(MapJSONDecodeError):
        load_map_file(path)


def test_missing_target_directory_has_controlled_write_error(tmp_path):
    with pytest.raises(MapFileWriteError):
        save_map_file(make_map(), tmp_path / "missing" / "map.json")


def test_replace_failure_preserves_previous_target(tmp_path, monkeypatch):
    path = tmp_path / "map.json"
    path.write_text("original", encoding="utf-8")

    def fail_replace(source, target):
        raise OSError("simulated replace failure")

    monkeypatch.setattr("hex_world_lab.world.persistence.file_storage.os.replace", fail_replace)
    with pytest.raises(MapFileWriteError):
        save_map_file(make_map(), path, mode="replace")
    assert path.read_text(encoding="utf-8") == "original"
    assert list(tmp_path.glob(".map.json.*.tmp")) == []
