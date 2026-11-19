"""End-to-end map persistence tests."""

import json

from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexCellData, HexMapDefinition, MapId, WorldId
from hex_world_lab.world.persistence import load_map_file, save_map_file


def test_map_definition_file_round_trip(tmp_path):
    original = HexMapDefinition(
        world_id=WorldId("eldoria"),
        map_id=MapId("starting_valley"),
        name="Başlangıç Vadisi",
        layout=HexLayout(HexOrientation.POINTY_TOP, 1.75, WorldPoint(3.0, -2.0)),
        cells={
            AxialCoord(-2, 1): HexCellData("grass", True, False, {"biome": "orman"}),
            AxialCoord(0, 0): HexCellData("water", False, False, None),
        },
    )
    path = tmp_path / "starting_valley.json"
    save_map_file(original, path)
    restored = load_map_file(path)
    assert restored == original


def test_load_does_not_change_any_world_registry(tmp_path):
    from hex_world_lab.world import HexWorld

    world = HexWorld(WorldId("eldoria"))
    before = world.map_registry.map_ids
    path = tmp_path / "broken.json"
    path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    try:
        load_map_file(path)
    except Exception:
        pass
    assert world.map_registry.map_ids == before


def test_successful_load_has_no_world_registry_side_effect(tmp_path):
    from hex_world_lab.world import HexWorld

    original = HexMapDefinition(
        world_id=WorldId("eldoria"),
        map_id=MapId("starting_valley"),
        name="Başlangıç Vadisi",
        layout=HexLayout(HexOrientation.POINTY_TOP),
        cells={},
    )
    path = tmp_path / "map.json"
    save_map_file(original, path)
    world = HexWorld(WorldId("eldoria"))
    loaded = load_map_file(path)
    assert loaded == original
    assert world.map_registry.map_ids == ()
    assert world.map_registry.loaded_map_ids == ()
