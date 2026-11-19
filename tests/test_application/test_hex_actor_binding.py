"""Actor identity and movement-ownership bridge tests."""

import pytest

from application.actor_system import WorldActor, WorldActorRegistry
from application.hex_actor_binding import (
    ActorHexBindingError,
    ActorHexBindingService,
    actor_id_to_lab_entity_id,
    lab_entity_id_to_actor_id,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    EntityPosition,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
    MovementProfile,
)
from core.foundation import WorldId


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
        "valid_cells": [[0, 0], [1, 0], [2, 0], [0, 1]],
        "cell_overrides": [],
        "transitions": [],
    })


def make_binding(*, actor_active=True, world_id="eldoria"):
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", world_id, "player", active=actor_active))
    runtime = HexWorldRuntime(
        {"forest": make_map()},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    return actors, runtime, binding


def test_actor_id_maps_one_to_one_to_lab_entity_id_without_new_identity():
    lab_id = actor_id_to_lab_entity_id("hero")
    assert lab_entity_id_to_actor_id(lab_id) == "hero"
    assert lab_id.value == "hero"


def test_spatial_registration_reuses_actor_id_and_keeps_actor_registry_authoritative():
    actors, runtime, binding = make_binding()
    actor_before = actors.get("hero")
    spatial = binding.register_spatial(
        "hero",
        "player",
        EntityPosition("forest", LocalHexPosition(0, 0)),
    )

    assert spatial.entity_id == actor_before.actor_id
    assert actors.get("hero") == actor_before
    assert runtime.entity("hero").position == EntityPosition(
        "forest", LocalHexPosition(0, 0)
    )
    with pytest.raises(ValueError, match="Duplicate hex entity"):
        binding.register_spatial(
            "hero",
            "player",
            EntityPosition("forest", LocalHexPosition(1, 0)),
        )


def test_actor_from_another_world_cannot_be_bound_to_this_runtime():
    actors = WorldActorRegistry()
    actors.add(WorldActor("remote-hero", "other-world", "player"))
    runtime = HexWorldRuntime(
        {"forest": make_map()},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))

    with pytest.raises(ActorHexBindingError, match="belongs to world"):
        binding.register_spatial(
            "remote-hero",
            "player",
            EntityPosition("forest", LocalHexPosition(0, 0)),
        )


def test_inactive_actor_cannot_move_even_when_spatial_movement_is_enabled():
    _actors, runtime, binding = make_binding(actor_active=False)
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("forest", LocalHexPosition(0, 0)),
    )

    result = binding.move("hero", HexDirection.EAST)
    assert not result.success
    assert result.reason is MovementFailureReason.MOVEMENT_NOT_ALLOWED
    assert runtime.entity("hero").position.cell == LocalHexPosition(0, 0)


def test_movement_enabled_is_distinct_from_actor_active_state():
    actors, runtime, binding = make_binding()
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("forest", LocalHexPosition(0, 0)),
    )

    binding.set_movement_enabled("hero", False)
    assert actors.get("hero").active is True
    assert runtime.entity("hero").active is False
    blocked = binding.move("hero", HexDirection.EAST)
    assert not blocked.success
    assert blocked.reason is MovementFailureReason.MOVEMENT_NOT_ALLOWED

    binding.set_movement_enabled("hero", True)
    moved = binding.move("hero", HexDirection.EAST)
    assert moved.success
    assert actors.get("hero").active is True


def test_occupancy_failure_does_not_change_actor_or_spatial_position():
    actors, runtime, binding = make_binding()
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("forest", LocalHexPosition(0, 0)),
    )
    runtime.register_entity(
        "guard",
        "npc",
        EntityPosition("forest", LocalHexPosition(1, 0)),
    )

    result = binding.move("hero", HexDirection.EAST)
    assert not result.success
    assert result.reason is MovementFailureReason.OCCUPIED_CELL
    assert runtime.entity("hero").position.cell == LocalHexPosition(0, 0)
    assert actors.get("hero").active is True


def test_unregistering_spatial_binding_keeps_actor_identity_and_gameplay_state():
    actors, runtime, binding = make_binding()
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("forest", LocalHexPosition(0, 0)),
        MovementProfile(),
    )

    removed = binding.unregister_spatial("hero")
    assert removed.entity_id == "hero"
    assert runtime.occupancy.get("hero") is None
    with pytest.raises(KeyError, match="Unknown hex entity"):
        runtime.entity("hero")
    assert actors.get("hero").actor_id == "hero"
    assert actors.get("hero").world_id == "eldoria"



def test_runtime_from_another_world_cannot_be_bound():
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime(
        {"forest": make_map()},
        world_id=WorldId("other-world"),
    )

    with pytest.raises(ActorHexBindingError, match="Runtime belongs to world"):
        ActorHexBindingService(actors, runtime, WorldId("eldoria"))


def test_unscoped_runtime_cannot_be_bound_to_an_actor_registry():
    actors = WorldActorRegistry()
    runtime = HexWorldRuntime({"forest": make_map()})

    with pytest.raises(ValueError, match="bound to a WorldId"):
        ActorHexBindingService(actors, runtime, WorldId("eldoria"))

def test_unknown_actor_cannot_be_registered_or_moved():
    actors = WorldActorRegistry()
    binding = ActorHexBindingService(
        actors,
        HexWorldRuntime(
            {"forest": make_map()},
            world_id=WorldId("eldoria"),
        ),
        WorldId("eldoria"),
    )
    with pytest.raises(KeyError, match="Actor not found"):
        binding.register_spatial(
            "missing",
            "player",
            EntityPosition("forest", LocalHexPosition(0, 0)),
        )
    with pytest.raises(KeyError, match="Actor not found"):
        binding.move("missing", HexDirection.EAST)
