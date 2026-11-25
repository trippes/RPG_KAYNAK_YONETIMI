"""GameplayService integration tests for world-scoped hex actor bindings."""

import pytest

from application import (
    GameApplication,
    GameplayService,
    GameplayServiceError,
    ProductionFacilityRegistry,
    SessionBundle,
    SessionHolder,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.application import GameSession
from core.domain.spatial import EntityPosition, HexDirection, LocalHexPosition
from core.foundation import WorldId
from resources import Inventory, ProductionJobManager, WorldResourceNodeManager


def make_service():
    session = GameSession()
    world = session.worlds.create("Actors", world_id="world_actors")
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
    service.configure_player_context("hero", "main", "hero")
    service.register_actor("hero", "player", inventory_id="main")
    return service, bundle


def make_map():
    return parse_hex_map({
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
        "valid_cells": [[0, 0], [1, 0], [2, 0]],
        "cell_overrides": [],
        "transitions": [],
    })


def test_gameplay_service_exposes_active_world_hex_binding():
    service, bundle = make_service()
    runtime = HexWorldRuntime(
        {"forest": make_map()},
        world_id=WorldId("world_actors"),
    )
    bundle.hex_world_runtime_owner.get_or_create(lambda: runtime)

    binding = service.hex_actor_binding
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("forest", LocalHexPosition(0, 0)),
    )
    result = service.hex_actor_binding.move("hero", HexDirection.EAST)

    assert result.success
    assert service.hex_world_runtime.entity("hero").position.cell == LocalHexPosition(1, 0)


def test_gameplay_service_rejects_hex_binding_before_runtime_initialization():
    service, _bundle = make_service()
    with pytest.raises(GameplayServiceError, match="no initialized hex world runtime"):
        _ = service.hex_actor_binding


def test_gameplay_service_rejects_runtime_bound_to_another_world():
    service, bundle = make_service()
    runtime = HexWorldRuntime(
        {"forest": make_map()},
        world_id=WorldId("different_world"),
    )
    bundle.hex_world_runtime_owner.get_or_create(lambda: runtime)

    with pytest.raises(GameplayServiceError, match="not bound to the active world"):
        _ = service.hex_actor_binding
