from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
from hex_world_lab.world import CellAddress, HexCellData, HexMapDefinition, HexWorld, MapId, WorldId
from hex_world_lab.world.persistence import (
    deserialize_runtime_payload,
    runtime_to_payload,
    serialize_runtime,
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


def test_serialization_is_deterministic_and_round_trips():
    world, definition = setup_world()
    world.runtime.set_cell_state(
        CellAddress(definition.world_id, definition.map_id, AxialCoord(0, 0)),
        terrain_id="mud", is_walkable=False, has_obstacle=True,
    )
    first = serialize_runtime(world.runtime, definition)
    second = serialize_runtime(world.runtime, definition)
    assert first == second
    snapshot = deserialize_runtime_payload(runtime_to_payload(world.runtime, definition), definition)
    assert snapshot.overrides[AxialCoord(0, 0)].terrain_id == "mud"
    assert snapshot.overrides[AxialCoord(0, 0)].is_walkable is False


def test_empty_runtime_serializes_empty_override_list():
    world, definition = setup_world()
    assert runtime_to_payload(world.runtime, definition)["overrides"] == []
