"""Application-level NPC target lookup tests."""

import pytest

from application.hex_interaction import HexInteractionService
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    EntityPosition,
    LocalHexPosition,
    WorldPoint,
    axial_to_world_point,
)


def make_runtime():
    definition = parse_hex_map({
        "schema_version": 2,
        "map_id": "forest",
        "name": "Forest",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0]],
        "cell_overrides": [],
        "transitions": [],
    })
    return HexWorldRuntime({"forest": definition})


def test_npc_target_lookup_uses_world_point_and_spatial_candidates():
    runtime = make_runtime()
    runtime.register_entity(
        "guard",
        "npc",
        EntityPosition("forest", LocalHexPosition(0, 0)),
    )
    runtime.set_continuous_position("guard", WorldPoint(4.0, 5.0))

    service = HexInteractionService(runtime)
    assert service.npc_at_world_point("forest", WorldPoint(8.0, 9.0)) == "guard"


def test_npc_target_lookup_does_not_select_an_adjacent_hex_actor():
    runtime = make_runtime()
    runtime.register_entity(
        "guard",
        "npc",
        EntityPosition("forest", LocalHexPosition(1, 0)),
    )
    service = HexInteractionService(runtime)

    clicked = axial_to_world_point(
        LocalHexPosition(0, 0).to_hex_coord(), runtime.HEX_SIZE
    )
    assert service.npc_at_world_point("forest", clicked) is None


def test_npc_target_lookup_uses_stable_actor_id_for_same_cell_ties():
    runtime = make_runtime()
    position = EntityPosition("forest", LocalHexPosition(0, 0))
    runtime.register_entity("z_guard", "npc", position, blocks_movement=False, blocks_occupancy=False)
    runtime.register_entity("a_guard", "npc", position, blocks_movement=False, blocks_occupancy=False)

    service = HexInteractionService(runtime)
    center = axial_to_world_point(position.cell.to_hex_coord(), runtime.HEX_SIZE)
    assert service.npc_at_world_point("forest", center) == "a_guard"


def test_npc_target_lookup_validates_map_and_world_point():
    service = HexInteractionService(make_runtime())
    with pytest.raises(KeyError, match="Unknown hex map"):
        service.npc_at_world_point("missing", WorldPoint(0, 0))
    with pytest.raises(TypeError, match="WorldPoint"):
        service.npc_at_world_point("forest", (0, 0))


def test_object_target_lookup_resolves_non_blocking_world_objects():
    runtime = make_runtime()
    position = EntityPosition("forest", LocalHexPosition(0, 0))
    runtime.register_entity(
        "herb_patch", "object", position,
        blocks_movement=False, blocks_occupancy=False,
    )
    center = axial_to_world_point(position.cell.to_hex_coord(), runtime.HEX_SIZE)

    service = HexInteractionService(runtime)

    assert service.object_at_world_point("forest", center) == "herb_patch"
    assert service.npc_at_world_point("forest", center) is None


def test_object_target_lookup_does_not_select_an_adjacent_hex_object():
    runtime = make_runtime()
    runtime.register_entity(
        "herb_patch", "object",
        EntityPosition("forest", LocalHexPosition(1, 0)),
        blocks_movement=False, blocks_occupancy=False,
    )
    center = axial_to_world_point(
        LocalHexPosition(0, 0).to_hex_coord(), runtime.HEX_SIZE,
    )

    assert HexInteractionService(runtime).object_at_world_point(
        "forest", center,
    ) is None
