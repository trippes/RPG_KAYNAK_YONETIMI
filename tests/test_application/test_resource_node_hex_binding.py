"""Resource-node spatial registration tests for the active hex world."""

import pytest

from application import (
    GameApplication,
    GameplayService,
    GameplayServiceError,
    ProductionFacilityRegistry,
    ResourceNodeHexBindingError,
    SessionBundle,
    SessionHolder,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.application import GameSession
from core.domain.spatial import EntityPosition, LocalHexPosition
from core.foundation import WorldId
from resources import (
    Inventory,
    ProductionJobManager,
    Quantity,
    ResourceType,
    ResourceUnit,
    WorldResourceNode,
    WorldResourceNodeManager,
)


def make_service():
    session = GameSession()
    world = session.worlds.create("Resource World", world_id="resource_world")
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
    runtime = HexWorldRuntime(
        {"field": make_map()},
        world_id=WorldId("resource_world"),
    )
    bundle.hex_world_runtime_owner.get_or_create(lambda: runtime)
    return service, bundle, runtime


def make_map():
    return parse_hex_map({
        "schema_version": 2,
        "map_id": "field",
        "name": "Field",
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


def make_node(node_id="iron-vein", world_id="resource_world"):
    return WorldResourceNode(
        node_id,
        world_id,
        ResourceType("iron"),
        Quantity(8, ResourceUnit.ITEM),
        Quantity(10, ResourceUnit.ITEM),
        Quantity(1, ResourceUnit.ITEM),
    )


def test_resource_node_registers_as_non_movable_non_blocking_spatial_object():
    service, bundle, runtime = make_service()
    node = make_node()
    bundle.resource_nodes.add(node)

    spatial = service.resource_node_hex_binding.register_spatial(
        node.node_id,
        EntityPosition("field", LocalHexPosition(0, 0)),
    )

    assert spatial.entity_id == node.node_id
    assert spatial.kind == "object"
    assert spatial.profile.can_move is False
    assert runtime.occupancy.get(node.node_id).blocks_movement is False
    assert runtime.occupancy.get(node.node_id).blocks_occupancy is False
    assert bundle.resource_nodes.get(node.node_id) is node


def test_resource_node_does_not_block_actor_occupancy():
    service, _bundle, runtime = make_service()
    service._current_bundle().resource_nodes.add(make_node())
    service.resource_node_hex_binding.register_spatial(
        "iron-vein",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )

    actor = runtime.register_entity(
        "hero",
        "player",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )

    assert actor.position.cell == LocalHexPosition(0, 0)
    assert runtime.occupancy.get("iron-vein") is not None
    assert runtime.occupancy.get("hero") is not None


def test_resource_node_binding_rejects_unknown_node():
    service, _bundle, _runtime = make_service()

    with pytest.raises(KeyError, match="Resource node not found"):
        service.resource_node_hex_binding.register_spatial(
            "missing-node",
            EntityPosition("field", LocalHexPosition(0, 0)),
        )


def test_resource_node_binding_rejects_node_from_another_world():
    service, bundle, _runtime = make_service()
    other_world = bundle.session.worlds.create("Other", world_id="other_resource_world")
    bundle.resource_nodes.add(make_node(world_id=other_world.world_id))

    with pytest.raises(ResourceNodeHexBindingError, match="belongs to world"):
        service.resource_node_hex_binding.register_spatial(
            "iron-vein",
            EntityPosition("field", LocalHexPosition(0, 0)),
        )


def test_resource_node_outside_map_mask_is_rejected_without_spatial_registration():
    service, bundle, runtime = make_service()
    bundle.resource_nodes.add(make_node())

    with pytest.raises(ValueError, match="outside the map valid_cells"):
        service.resource_node_hex_binding.register_spatial(
            "iron-vein",
            EntityPosition("field", LocalHexPosition(9, 9)),
        )

    assert runtime.occupancy.get("iron-vein") is None
    assert bundle.resource_nodes.get("iron-vein") is not None


def test_unregistering_resource_node_spatial_binding_preserves_resource_state():
    service, bundle, runtime = make_service()
    node = make_node()
    bundle.resource_nodes.add(node)
    service.resource_node_hex_binding.register_spatial(
        node.node_id,
        EntityPosition("field", LocalHexPosition(1, 0)),
    )
    quantity_before = node.quantity
    tick_before = node.last_simulation_tick

    removed = service.resource_node_hex_binding.unregister_spatial(node.node_id)

    assert removed.entity_id == node.node_id
    assert runtime.occupancy.get(node.node_id) is None
    assert bundle.resource_nodes.get(node.node_id) is node
    assert node.quantity == quantity_before
    assert node.last_simulation_tick == tick_before


def test_resource_node_binding_rejects_a_runtime_from_another_active_world():
    service, bundle, _runtime = make_service()
    other_world = bundle.session.worlds.create("Other", world_id="other_world")
    bundle.session.worlds.set_active(other_world.world_id)

    with pytest.raises(GameplayServiceError, match="not bound to the active world"):
        _ = service.resource_node_hex_binding


def test_resource_node_binding_requires_an_initialized_hex_runtime():
    session = GameSession()
    world = session.worlds.create("Resource World", world_id="resource_world")
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

    with pytest.raises(GameplayServiceError, match="no initialized hex world runtime"):
        _ = service.resource_node_hex_binding
