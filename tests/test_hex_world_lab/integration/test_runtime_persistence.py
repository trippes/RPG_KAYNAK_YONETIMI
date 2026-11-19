from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import CellAddress, HexCellData, HexMapDefinition, HexWorld, MapId, WorldId
from hex_world_lab.world.persistence import (
    RuntimeBaseMapMismatchError,
    restore_runtime_file,
    save_runtime_file,
)


def make_definition(terrain="grass"):
    return HexMapDefinition(
        WorldId("eldoria"), MapId("starting_valley"), "Starting Valley",
        HexLayout(HexOrientation.POINTY_TOP, 1.0),
        {
            AxialCoord(0, 0): HexCellData(terrain, True, False),
            AxialCoord(1, 0): HexCellData("stone", True, False),
        },
    )


def make_world(definition):
    world = HexWorld(definition.world_id)
    world.register_map(definition.map_id, definition.name)
    world.load_map(definition)
    return world


def test_runtime_snapshot_restores_into_a_fresh_world(tmp_path):
    original_definition = make_definition()
    original = make_world(original_definition)
    address = CellAddress(
        original_definition.world_id,
        original_definition.map_id,
        AxialCoord(0, 0),
    )
    original.runtime.set_cell_state(address, terrain_id="burned_grass", is_walkable=False)
    path = tmp_path / "starting_valley.runtime.json"
    save_runtime_file(original.runtime, original_definition, path)

    fresh_definition = make_definition()
    fresh_world = make_world(fresh_definition)
    restore_runtime_file(fresh_world.runtime, fresh_definition, path)
    current = fresh_world.view.require_cell(address)
    assert current.terrain_id == "burned_grass"
    assert current.is_walkable is False
    assert current.has_obstacle is False


def test_restore_rejects_changed_base_map_without_partial_mutation(tmp_path):
    definition = make_definition()
    source = make_world(definition)
    path = tmp_path / "snapshot.json"
    source.runtime.set_terrain(
        CellAddress(definition.world_id, definition.map_id, AxialCoord(0, 0)),
        "mud",
    )
    save_runtime_file(source.runtime, definition, path)

    changed_definition = make_definition(terrain="dirt")
    target = make_world(changed_definition)
    target_address = CellAddress(
        changed_definition.world_id, changed_definition.map_id, AxialCoord(1, 0)
    )
    target.runtime.set_obstacle(target_address, True)
    before = dict(target.runtime.export_map_overrides(changed_definition.map_id))
    try:
        restore_runtime_file(target.runtime, changed_definition, path)
    except RuntimeBaseMapMismatchError:
        pass
    else:
        raise AssertionError("base map mismatch should reject restore")
    assert dict(target.runtime.export_map_overrides(changed_definition.map_id)) == before


def test_runtime_snapshots_are_isolated_between_maps(tmp_path):
    first_definition = make_definition()
    second_definition = HexMapDefinition(
        first_definition.world_id, MapId("cave"), "Cave",
        first_definition.layout, first_definition.cells,
    )
    world = make_world(first_definition)
    world.register_map(second_definition.map_id, second_definition.name)
    world.load_map(second_definition)
    first_address = CellAddress(
        first_definition.world_id, first_definition.map_id, AxialCoord(0, 0)
    )
    second_address = CellAddress(
        second_definition.world_id, second_definition.map_id, AxialCoord(0, 0)
    )
    world.runtime.set_terrain(first_address, "mud")
    world.runtime.set_terrain(second_address, "lava")
    path = tmp_path / "first.runtime.json"
    save_runtime_file(world.runtime, first_definition, path)

    fresh = make_world(first_definition)
    fresh.register_map(second_definition.map_id, second_definition.name)
    fresh.load_map(second_definition)
    restore_runtime_file(fresh.runtime, first_definition, path)
    assert fresh.view.require_cell(first_address).terrain_id == "mud"
    assert fresh.view.require_cell(second_address).terrain_id == "grass"


def test_checked_in_starting_valley_runtime_sample_matches_base_map():
    from pathlib import Path

    from hex_world_lab.world.persistence import load_map_file, load_runtime_file

    lab_root = Path(__file__).resolve().parents[2]
    base_map = load_map_file(lab_root / "scenarios" / "maps" / "starting_valley.json")
    snapshot = load_runtime_file(
        lab_root / "scenarios" / "runtime" / "starting_valley.runtime.json",
        base_map,
    )
    assert snapshot.world_id == base_map.world_id
    assert snapshot.map_id == base_map.map_id
    assert snapshot.overrides[AxialCoord(0, 0)].terrain_id == "burned_grass"
