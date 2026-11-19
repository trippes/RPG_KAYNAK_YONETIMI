"""GameplayService integration for canonical container Hex placement."""

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
from containers import ContainerDefinition, ContainerInstance
from core.application import GameSession
from core.domain.spatial import EntityPosition, LocalHexPosition
from core.entity import Entity, EntityType
from core.foundation import WorldId
from resources import Inventory, ProductionJobManager, WorldResourceNodeManager


def make_service(*, runtime_world="container_world", initialize_runtime=True):
    session = GameSession()
    world = session.worlds.create("Container World", world_id="container_world")
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
    session.add_entity(
        Entity(EntityType.ESYA, "Chest", entity_id="chest_entity"),
        world.world_id,
    )
    service.register_container_definition(ContainerDefinition(
        "wooden_chest", "Wooden Chest",
    ))
    service.register_container(ContainerInstance(
        "chest", "chest_entity", "wooden_chest",
    ))
    if initialize_runtime:
        map_definition = parse_hex_map({
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
            "valid_cells": [[0, 0], [1, 0]],
            "cell_overrides": [],
            "transitions": [],
        })
        runtime = HexWorldRuntime(
            {"village": map_definition},
            world_id=WorldId(runtime_world),
        )
        bundle.hex_world_runtime_owner.get_or_create(lambda: runtime)
    return service, bundle


def test_gameplay_service_exposes_active_world_container_hex_binding():
    service, bundle = make_service()

    spatial = service.container_hex_binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(0, 0)),
        blocks_movement=True,
        blocks_occupancy=True,
    )

    assert spatial.entity_id == "chest_entity"
    assert service.container_hex_binding.position("chest") == EntityPosition(
        "village", LocalHexPosition(0, 0),
    )
    assert bundle.session.membership.world_id_for("chest_entity") == "container_world"


def test_gameplay_service_rejects_container_binding_before_runtime_initialization():
    service, _bundle = make_service(initialize_runtime=False)

    with pytest.raises(GameplayServiceError, match="no initialized hex world runtime"):
        _ = service.container_hex_binding


def test_gameplay_service_rejects_container_binding_for_another_world_runtime():
    service, _bundle = make_service(runtime_world="other_world")

    with pytest.raises(GameplayServiceError, match="not bound to the active world"):
        _ = service.container_hex_binding

def test_gameplay_service_carries_and_drops_container_through_hex_binding():
    service, bundle = make_service()
    service.container_hex_binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(0, 0)),
        blocks_movement=True,
        blocks_occupancy=True,
    )

    service.carry_container("chest", "main")
    assert bundle.containers.inventory_custody("chest") == "main"

    placed = service.place_container_from_inventory(
        "chest",
        "main",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=False,
        blocks_occupancy=True,
    )

    assert placed.entity_id == "chest_entity"
    assert bundle.containers.inventory_custody("chest") is None
    assert service.container_hex_binding.position("chest") == EntityPosition(
        "village", LocalHexPosition(1, 0),
    )


def test_gameplay_service_releases_nested_container_to_hex_world():
    service, bundle = make_service()
    session = bundle.session
    world_id = "container_world"
    session.add_entity(
        Entity(EntityType.ESYA, "Bag", entity_id="bag_entity"),
        world_id,
    )
    service.register_container_definition(ContainerDefinition(
        "bag", "Bag", nesting_enabled=True, max_nesting_depth=2,
    ))
    service.register_container(ContainerInstance(
        "bag", "bag_entity", "bag",
    ))
    service.contain_container("bag", "chest")

    placed = service.release_nested_container(
        "chest",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=False,
        blocks_occupancy=True,
    )

    assert placed.entity_id == "chest_entity"
    assert bundle.containers.parent_of("chest") is None
    assert service.container_hex_binding.position("chest") == EntityPosition(
        "village", LocalHexPosition(1, 0),
    )

