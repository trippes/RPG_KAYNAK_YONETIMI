"""NPC-to-hex spatial binding tests without duplicate identity or position owners."""

import pytest

from application import (
    GameApplication,
    GameplayService,
    GameplayServiceError,
    NPCSpatialBindingError,
    ProductionFacilityRegistry,
    SessionBundle,
    SessionHolder,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.application import GameSession
from core.domain.spatial import (
    AABB,
    EntityPosition,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
    WorldPoint,
)
from core.foundation import WorldId
from npc import NPC
from resources import Inventory, ProductionJobManager, WorldResourceNodeManager


def make_service():
    session = GameSession()
    world = session.worlds.create("NPC World", world_id="npc_world")
    session.worlds.set_active(world.world_id)
    bundle = SessionBundle(
        session=session,
        simulation=session.simulation,
        production_jobs=ProductionJobManager(session.simulation),
        resource_nodes=WorldResourceNodeManager(session.worlds),
        inventories={"main": Inventory()},
        recipes={},
        facilities=ProductionFacilityRegistry(),
    )
    service = GameplayService(GameApplication(SessionHolder(bundle)))
    return service, bundle


def make_map():
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "village",
        "name": "Village",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [[0, 0], [1, 0], [2, 0]],
        "cell_overrides": [],
        "transitions": [],
    })


def prepare_npc(*, active=True, register_actor=True):
    service, bundle = make_service()
    npc = NPC("village_guard", "Village Guard", active=active)
    service.register_npc(npc)
    if register_actor:
        service.register_actor("village_guard", "npc")
    runtime = HexWorldRuntime(
        {"village": make_map()},
        world_id=WorldId("npc_world"),
    )
    bundle.hex_world_runtime_owner.get_or_create(lambda: runtime)
    return service, bundle, npc, runtime


def test_npc_spatial_binding_reuses_the_existing_npc_and_actor_identity():
    service, bundle, npc, runtime = prepare_npc()

    spatial = service.npc_hex_binding.register_spatial(
        "village_guard",
        EntityPosition("village", LocalHexPosition(0, 0)),
    )

    assert spatial.entity_id == "village_guard"
    assert service.npc_hex_binding.npc("village_guard") is npc
    assert bundle.social.npcs.get("village_guard") is npc
    assert bundle.actors.get("village_guard").actor_id == "village_guard"
    assert runtime.entity("village_guard").position.cell == LocalHexPosition(0, 0)


def test_npc_spatial_binding_indexes_the_npc_collider_bounds():
    service, _bundle, _npc, runtime = prepare_npc()
    service.npc_hex_binding.register_spatial(
        "village_guard", EntityPosition("village", LocalHexPosition(0, 0)),
    )
    anchor = runtime.continuous_position("village_guard").point
    inside = AABB.around_point(WorldPoint(anchor.x + 3.5, anchor.y), 0.1)
    outside = AABB.around_point(WorldPoint(anchor.x + 4.5, anchor.y), 0.1)
    assert "village_guard" in runtime.query_spatial_candidates("village", inside)
    assert "village_guard" not in runtime.query_spatial_candidates("village", outside)


def test_npc_spatial_binding_requires_an_existing_world_actor():
    service, bundle, _npc, _runtime = prepare_npc(register_actor=False)

    with pytest.raises(KeyError, match="Actor not found"):
        service.npc_hex_binding.register_spatial(
            "village_guard",
            EntityPosition("village", LocalHexPosition(0, 0)),
        )

    assert bundle.actors.count() == 0
    assert bundle.social.npcs.get("village_guard") is not None


def test_npc_spatial_binding_rejects_unknown_npc():
    service, _bundle, _npc, _runtime = prepare_npc()

    with pytest.raises(KeyError, match="NPC not found"):
        service.npc_hex_binding.register_spatial(
            "missing_npc",
            EntityPosition("village", LocalHexPosition(0, 0)),
        )


def test_inactive_npc_cannot_register_or_move_spatially():
    service, _bundle, npc, runtime = prepare_npc(active=False)

    with pytest.raises(NPCSpatialBindingError, match="Inactive NPC"):
        service.npc_hex_binding.register_spatial(
            "village_guard",
            EntityPosition("village", LocalHexPosition(0, 0)),
        )

    npc.active = True
    service.npc_hex_binding.register_spatial(
        "village_guard",
        EntityPosition("village", LocalHexPosition(0, 0)),
    )
    npc.active = False

    result = service.npc_hex_binding.move("village_guard", HexDirection.EAST)

    assert not result.success
    assert result.reason is MovementFailureReason.MOVEMENT_NOT_ALLOWED
    assert runtime.entity("village_guard").position.cell == LocalHexPosition(0, 0)


def test_npc_movement_uses_the_shared_hex_runtime_and_occupancy_owner():
    service, _bundle, _npc, runtime = prepare_npc()
    service.npc_hex_binding.register_spatial(
        "village_guard",
        EntityPosition("village", LocalHexPosition(0, 0)),
    )

    result = service.npc_hex_binding.move("village_guard", HexDirection.EAST)

    assert result.success
    assert runtime.entity("village_guard").position.cell == LocalHexPosition(1, 0)
    assert runtime.occupancy.get("village_guard").position.cell == LocalHexPosition(1, 0)


def test_unregistering_npc_spatial_binding_preserves_npc_and_actor_records():
    service, bundle, npc, runtime = prepare_npc()
    service.npc_hex_binding.register_spatial(
        "village_guard",
        EntityPosition("village", LocalHexPosition(0, 0)),
    )

    removed = service.npc_hex_binding.unregister_spatial("village_guard")

    assert removed.entity_id == "village_guard"
    assert runtime.occupancy.get("village_guard") is None
    assert bundle.social.npcs.get("village_guard") is npc
    assert bundle.actors.get("village_guard").actor_id == "village_guard"


def test_npc_spatial_binding_is_scoped_to_the_active_world():
    service, bundle, _npc, _runtime = prepare_npc()
    other_world = bundle.session.worlds.create("Other", world_id="other_world")
    bundle.session.worlds.set_active(other_world.world_id)

    with pytest.raises(GameplayServiceError, match="not bound to the active world"):
        _ = service.npc_hex_binding


def test_npc_collider_aabb_moves_with_authoritative_continuous_position():
    service, _bundle, _npc, runtime = prepare_npc()
    service.npc_hex_binding.register_spatial(
        "village_guard", EntityPosition("village", LocalHexPosition(0, 0)),
    )
    anchor = runtime.continuous_position("village_guard").point
    old_edge = AABB.around_point(WorldPoint(anchor.x - 4.5, anchor.y), 0.1)

    result = runtime.set_continuous_position(
        "village_guard", WorldPoint(anchor.x + 8.0, anchor.y),
    )

    assert result.success
    assert "village_guard" not in runtime.query_spatial_candidates("village", old_edge)
    new_edge = AABB.around_point(WorldPoint(anchor.x + 11.5, anchor.y), 0.1)
    assert "village_guard" in runtime.query_spatial_candidates("village", new_edge)


def test_unregistering_npc_removes_its_collider_from_broadphase_queries():
    service, _bundle, _npc, runtime = prepare_npc()
    service.npc_hex_binding.register_spatial(
        "village_guard", EntityPosition("village", LocalHexPosition(0, 0)),
    )
    anchor = runtime.continuous_position("village_guard").point
    query = AABB.around_point(anchor, 0.1)
    assert "village_guard" in runtime.query_spatial_candidates("village", query)

    service.npc_hex_binding.unregister_spatial("village_guard")

    assert "village_guard" not in runtime.query_spatial_candidates("village", query)
