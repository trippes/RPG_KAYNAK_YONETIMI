"""Container custody and canonical Hex placement boundary tests."""

import pytest

from application.container_hex_binding import (
    ContainerHexBindingError,
    ContainerHexBindingService,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from containers import ContainerDefinition, ContainerInstance, ContainerManager
from core.application import GameSession
from core.domain.spatial import EntityPosition, LocalHexPosition
from core.entity import Entity, EntityType
from core.foundation import WorldId


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


def make_binding(*, runtime_world="container_world"):
    session = GameSession()
    world = session.worlds.create("Container World", world_id="container_world")
    session.worlds.set_active(world.world_id)
    manager = ContainerManager()
    manager.register_definition(ContainerDefinition(
        "wooden_chest",
        "Wooden Chest",
        nesting_enabled=True,
        max_nesting_depth=2,
    ))
    for container_id, entity_id in (
        ("chest", "chest_entity"),
        ("bag", "bag_entity"),
    ):
        session.add_entity(
            Entity(EntityType.ESYA, container_id, entity_id=entity_id),
            world.world_id,
        )
        manager.register(ContainerInstance(
            container_id, entity_id, "wooden_chest",
        ))
    runtime = HexWorldRuntime(
        {"village": make_map()},
        world_id=WorldId(runtime_world),
    )
    binding = ContainerHexBindingService(
        manager, session.membership, runtime, WorldId("container_world"),
    )
    return session, manager, runtime, binding


def test_world_placed_container_uses_core_identity_and_hex_runtime_position():
    session, manager, runtime, binding = make_binding()

    spatial = binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=True,
        blocks_occupancy=False,
    )

    assert spatial.entity_id == "chest_entity"
    assert binding.position("chest") == EntityPosition(
        "village", LocalHexPosition(1, 0),
    )
    assert runtime.occupancy.get("chest_entity").blocks_movement is True
    assert runtime.occupancy.get("chest_entity").blocks_occupancy is False
    assert session.membership.world_id_for("chest_entity") == "container_world"
    assert manager.get("chest").entity_id == "chest_entity"


def test_carried_container_cannot_receive_a_world_placement():
    _session, manager, runtime, binding = make_binding()
    manager.set_inventory_custody("chest", "player_inventory")

    with pytest.raises(ContainerHexBindingError, match="Carried container"):
        binding.register_spatial(
            "chest",
            EntityPosition("village", LocalHexPosition(0, 0)),
            blocks_movement=True,
            blocks_occupancy=True,
        )

    assert runtime.entities() == ()


def test_nested_container_cannot_receive_a_separate_world_placement():
    _session, manager, runtime, binding = make_binding()
    manager.contain("bag", "chest")

    with pytest.raises(ContainerHexBindingError, match="Nested container"):
        binding.register_spatial(
            "chest",
            EntityPosition("village", LocalHexPosition(0, 0)),
            blocks_movement=True,
            blocks_occupancy=True,
        )

    assert runtime.entities() == ()


def test_container_without_canonical_world_membership_is_rejected():
    session, manager, runtime, _binding = make_binding()
    session.membership.remove("chest_entity")

    with pytest.raises(ContainerHexBindingError, match="not a member of world"):
        ContainerHexBindingService(
            manager, session.membership, runtime, WorldId("container_world"),
        ).register_spatial(
            "chest",
            EntityPosition("village", LocalHexPosition(0, 0)),
            blocks_movement=True,
            blocks_occupancy=True,
        )

    assert runtime.entities() == ()


def test_runtime_from_another_world_is_rejected():
    with pytest.raises(ContainerHexBindingError, match="Runtime belongs to world"):
        make_binding(runtime_world="other_world")


def test_placement_outside_valid_hex_mask_does_not_mutate_runtime():
    _session, _manager, runtime, binding = make_binding()

    with pytest.raises(ValueError, match="outside the map valid_cells"):
        binding.register_spatial(
            "chest",
            EntityPosition("village", LocalHexPosition(9, 9)),
            blocks_movement=True,
            blocks_occupancy=True,
        )

    assert runtime.entities() == ()
    assert runtime.occupancy.get("chest_entity") is None


def test_unregistering_spatial_binding_preserves_container_capability_and_membership():
    session, manager, runtime, binding = make_binding()
    binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(0, 0)),
        blocks_movement=True,
        blocks_occupancy=True,
    )

    removed = binding.unregister_spatial("chest")

    assert removed.entity_id == "chest_entity"
    assert runtime.occupancy.get("chest_entity") is None
    assert manager.get("chest").entity_id == "chest_entity"
    assert session.membership.world_id_for("chest_entity") == "container_world"

def test_carry_removes_world_occupancy_before_assigning_inventory_custody():
    _session, manager, runtime, binding = make_binding()
    binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=True,
        blocks_occupancy=False,
    )

    binding.carry("chest", "player_inventory")

    assert manager.inventory_custody("chest") == "player_inventory"
    assert runtime.occupancy.get("chest_entity") is None
    assert runtime.entities() == ()


def test_contain_removes_child_world_occupancy_before_nesting():
    _session, manager, runtime, binding = make_binding()
    binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=True,
        blocks_occupancy=True,
    )

    binding.contain("bag", "chest")

    assert manager.parent_of("chest").container_id == "bag"
    assert runtime.occupancy.get("chest_entity") is None
    assert runtime.entities() == ()


def test_failed_carry_validation_restores_world_placement_and_custody():
    _session, manager, runtime, binding = make_binding()
    original = binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=True,
        blocks_occupancy=False,
    )

    def reject():
        raise RuntimeError("session validation failed")

    with pytest.raises(RuntimeError, match="session validation failed"):
        binding.carry("chest", "player_inventory", validate=reject)

    restored = runtime.entity("chest_entity")
    occupant = runtime.occupancy.get("chest_entity")
    assert restored.position == original.position
    assert restored.profile == original.profile
    assert occupant.blocks_movement is True
    assert occupant.blocks_occupancy is False
    assert manager.inventory_custody("chest") is None


def test_failed_nesting_validation_restores_world_placement_and_parentage():
    _session, manager, runtime, binding = make_binding()
    original = binding.register_spatial(
        "chest",
        EntityPosition("village", LocalHexPosition(1, 0)),
        blocks_movement=False,
        blocks_occupancy=True,
    )

    def reject():
        raise RuntimeError("session validation failed")

    with pytest.raises(RuntimeError, match="session validation failed"):
        binding.contain("bag", "chest", validate=reject)

    restored = runtime.entity("chest_entity")
    occupant = runtime.occupancy.get("chest_entity")
    assert restored.position == original.position
    assert occupant.blocks_movement is False
    assert occupant.blocks_occupancy is True
    assert manager.parent_of("chest") is None

