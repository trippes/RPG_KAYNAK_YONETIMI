"""Versioned hex-world snapshot and atomic restore tests."""

import pytest
from types import SimpleNamespace

from application import (
    HexWorldEntityRecord,
    HexWorldPersistenceError,
    HexWorldSnapshot,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    ContinuousEntityPosition, EntityPosition, LocalHexPosition, MovementProfile,
    WorldPoint, axial_to_world_point,
)
from core.foundation import WorldId


def make_map(*, blocked_cell=False):
    overrides = [{"q": 2, "r": 0, "blocked": True}] if blocked_cell else []
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
        "cell_overrides": overrides,
        "transitions": [],
    })


def make_runtime(*, world_id="world", blocked_cell=False):
    return HexWorldRuntime(
        {"field": make_map(blocked_cell=blocked_cell)},
        world_id=WorldId(world_id),
    )


def record(entity_id, cell, *, kind="npc", blocks_movement=True,
           blocks_occupancy=True, active=True, profile=None):
    return HexWorldEntityRecord(
        entity_id,
        kind,
        EntityPosition("field", cell),
        profile or MovementProfile(),
        active,
        blocks_movement,
        blocks_occupancy,
    )


def test_snapshot_round_trip_preserves_positions_profiles_occupancy_and_patrol():
    source = make_runtime()
    source.register_entity(
        "hero",
        "player",
        EntityPosition("field", LocalHexPosition(0, 0)),
        MovementProfile(allowed_terrain_ids={"grass"}, ignores_occupancy=True),
    )
    source.register_entity(
        "guard",
        "npc",
        EntityPosition("field", LocalHexPosition(1, 0)),
        MovementProfile(can_move=True, can_traverse_blocked_cells=False),
        active=False,
        blocks_movement=True,
        blocks_occupancy=False,
    )
    source.register_entity(
        "ore",
        "object",
        EntityPosition("field", LocalHexPosition(0, 0)),
        MovementProfile(can_move=False),
        blocks_movement=False,
        blocks_occupancy=False,
    )
    source.restore_patrol_indices({"guard": 3})

    snapshot = HexWorldSnapshot.from_runtime(source)
    decoded = HexWorldSnapshot.from_dict(snapshot.to_dict())
    target = make_runtime()

    assert decoded == snapshot
    decoded.restore_into(target)

    assert target.entities() == source.entities()
    assert target.occupancy.snapshot() == source.occupancy.snapshot()
    assert dict(target.patrol_indices) == {"guard": 3}


def test_snapshot_round_trip_preserves_continuous_subcell_position():
    source = make_runtime()
    source.register_entity(
        "hero",
        "player",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )
    source.set_continuous_position("hero", WorldPoint(4.0, 5.0))

    snapshot = HexWorldSnapshot.from_runtime(source)
    decoded = HexWorldSnapshot.from_dict(snapshot.to_dict())
    target = make_runtime()
    decoded.restore_into(target)

    assert decoded == snapshot
    assert target.continuous_position("hero") == ContinuousEntityPosition(
        "field", WorldPoint(4.0, 5.0)
    )


def test_schema_v1_cell_only_snapshot_migrates_to_cell_center():
    source = make_runtime()
    source.register_entity(
        "hero",
        "player",
        EntityPosition("field", LocalHexPosition(1, 0)),
    )
    legacy = HexWorldSnapshot.from_runtime(source).to_dict()
    legacy["schema_version"] = 1
    for entity in legacy["entities"]:
        entity.pop("continuous_position")

    migrated = HexWorldSnapshot.from_dict(legacy)
    expected_center = axial_to_world_point(
        LocalHexPosition(1, 0).to_hex_coord(), HexWorldRuntime.HEX_SIZE
    )

    assert migrated.schema_version == 2
    assert migrated.entities[0].continuous_position == ContinuousEntityPosition(
        "field", expected_center
    )


def test_unscoped_runtime_cannot_be_snapshotted():
    runtime = HexWorldRuntime({"field": make_map()})

    with pytest.raises(HexWorldPersistenceError, match="unscoped"):
        HexWorldSnapshot.from_runtime(runtime)


def test_restore_rejects_wrong_world_before_mutating_target():
    snapshot = HexWorldSnapshot(
        WorldId("source-world"),
        (record("hero", LocalHexPosition(0, 0), kind="player"),),
    )
    target = make_runtime(world_id="target-world")

    with pytest.raises(HexWorldPersistenceError, match="different worlds"):
        snapshot.restore_into(target)

    assert target.entities() == ()
    assert target.occupancy.snapshot() == ()


def test_restore_requires_an_empty_runtime():
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("guard", LocalHexPosition(1, 0)),),
    )
    target = make_runtime()
    target.register_entity(
        "existing",
        "npc",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )

    with pytest.raises(HexWorldPersistenceError, match="must be empty"):
        snapshot.restore_into(target)

    assert tuple(item.entity_id for item in target.entities()) == ("existing",)


def test_restore_rejects_map_mask_and_blocked_cell_violations():
    outside = HexWorldSnapshot(
        WorldId("world"),
        (record("guard", LocalHexPosition(9, 9)),),
    )
    blocked = HexWorldSnapshot(
        WorldId("world"),
        (record("guard", LocalHexPosition(2, 0)),),
    )

    target = make_runtime()
    with pytest.raises(HexWorldPersistenceError, match="outside map valid_cells"):
        outside.restore_into(target)
    assert target.entities() == ()

    blocked_target = make_runtime(blocked_cell=True)
    with pytest.raises(HexWorldPersistenceError, match="blocked cell"):
        blocked.restore_into(blocked_target)
    assert blocked_target.entities() == ()


def test_restore_rolls_back_all_registrations_after_occupancy_conflict():
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (
            record("first", LocalHexPosition(0, 0)),
            record("second", LocalHexPosition(0, 0)),
        ),
    )
    target = make_runtime()

    with pytest.raises(HexWorldPersistenceError, match="atomically"):
        snapshot.restore_into(target)

    assert target.entities() == ()
    assert target.occupancy.snapshot() == ()


def test_snapshot_rejects_patrol_progress_for_non_npc_or_unknown_entity():
    with pytest.raises(HexWorldPersistenceError, match="same snapshot"):
        HexWorldSnapshot(
            WorldId("world"),
            (record("hero", LocalHexPosition(0, 0), kind="player"),),
            (("hero", 1),),
        )
    with pytest.raises(HexWorldPersistenceError, match="same snapshot"):
        HexWorldSnapshot(
            WorldId("world"),
            (record("guard", LocalHexPosition(0, 0)),),
            (("missing", 1),),
        )


def test_from_dict_rejects_non_integer_axial_coordinates_and_unknown_fields():
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("hero", LocalHexPosition(0, 0), kind="player"),),
    ).to_dict()
    snapshot["entities"][0]["position"]["q"] = True

    with pytest.raises(HexWorldPersistenceError, match="integers"):
        HexWorldSnapshot.from_dict(snapshot)

    valid = HexWorldSnapshot(
        WorldId("world"),
        (record("hero", LocalHexPosition(0, 0), kind="player"),),
    ).to_dict()
    valid["legacy_square_position"] = {"x": 1, "y": 2}
    with pytest.raises(HexWorldPersistenceError, match="unknown fields"):
        HexWorldSnapshot.from_dict(valid)


def test_snapshot_detects_orphaned_occupancy_records():
    runtime = make_runtime()
    runtime.register_entity(
        "hero",
        "player",
        EntityPosition("field", LocalHexPosition(0, 0)),
    )
    runtime.occupancy.remove("hero")

    with pytest.raises(HexWorldPersistenceError, match="inconsistent"):
        HexWorldSnapshot.from_runtime(runtime)



def owner_context(*, actor_world="world", include_npc=True, resource_world="world",
                  container_parent=None, container_custody=None):
    container = SimpleNamespace(
        container_id="chest_01",
        entity_id="container_entity",
    )
    actors = SimpleNamespace(
        get=lambda entity_id: (
            SimpleNamespace(world_id=actor_world)
            if entity_id in {"hero", "guard"} else None
        )
    )
    npcs = SimpleNamespace(
        get=lambda entity_id: (
            object() if include_npc and entity_id == "guard" else None
        )
    )
    resource_nodes = SimpleNamespace(
        get=lambda entity_id: (
            SimpleNamespace(world_id=resource_world)
            if entity_id == "ore" else None
        )
    )
    containers = SimpleNamespace(
        for_entity=lambda entity_id: container if entity_id == "container_entity" else None,
        parent_of=lambda container_id: container_parent,
        inventory_custody=lambda container_id: container_custody,
    )
    membership = SimpleNamespace(
        world_id_for=lambda entity_id: "world" if entity_id == "container_entity" else None
    )
    return actors, npcs, resource_nodes, containers, membership


def test_domain_owner_validation_accepts_actor_npc_resource_and_world_placed_container():
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (
            record("hero", LocalHexPosition(0, 0), kind="player"),
            record("guard", LocalHexPosition(1, 0), kind="npc"),
            record("ore", LocalHexPosition(2, 0), kind="object"),
            record("container_entity", LocalHexPosition(0, 0), kind="object",
                   blocks_movement=False, blocks_occupancy=False),
        ),
    )
    owners = owner_context()

    snapshot.validate_domain_owners(
        actors=owners[0],
        npcs=owners[1],
        resource_nodes=owners[2],
        containers=owners[3],
        membership=owners[4],
    )


def test_domain_owner_validation_rejects_missing_actor_or_npc_record():
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("guard", LocalHexPosition(0, 0), kind="npc"),),
    )
    owners = owner_context(include_npc=False)

    with pytest.raises(HexWorldPersistenceError, match="NPC domain record is missing"):
        snapshot.validate_domain_owners(
            actors=owners[0],
            npcs=owners[1],
            resource_nodes=owners[2],
            containers=owners[3],
            membership=owners[4],
        )

    missing_actor = HexWorldSnapshot(
        WorldId("world"),
        (record("missing", LocalHexPosition(0, 0), kind="player"),),
    )
    with pytest.raises(HexWorldPersistenceError, match="actor owner is missing"):
        missing_actor.validate_domain_owners(
            actors=owners[0],
            npcs=owners[1],
            resource_nodes=owners[2],
            containers=owners[3],
            membership=owners[4],
        )


def test_domain_owner_validation_rejects_actor_or_resource_from_another_world():
    actor_snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("hero", LocalHexPosition(0, 0), kind="player"),),
    )
    actor_owners = owner_context(actor_world="other")
    with pytest.raises(HexWorldPersistenceError, match="actor belongs to another world"):
        actor_snapshot.validate_domain_owners(
            actors=actor_owners[0],
            npcs=actor_owners[1],
            resource_nodes=actor_owners[2],
            containers=actor_owners[3],
            membership=actor_owners[4],
        )

    resource_snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("ore", LocalHexPosition(0, 0), kind="object"),),
    )
    resource_owners = owner_context(resource_world="other")
    with pytest.raises(HexWorldPersistenceError, match="Resource node belongs to another world"):
        resource_snapshot.validate_domain_owners(
            actors=resource_owners[0],
            npcs=resource_owners[1],
            resource_nodes=resource_owners[2],
            containers=resource_owners[3],
            membership=resource_owners[4],
        )


def test_domain_owner_validation_rejects_unowned_objects_and_wrong_container_membership():
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("unknown-object", LocalHexPosition(0, 0), kind="object"),),
    )
    owners = owner_context()
    with pytest.raises(HexWorldPersistenceError, match="no resource/container owner"):
        snapshot.validate_domain_owners(
            actors=owners[0],
            npcs=owners[1],
            resource_nodes=owners[2],
            containers=owners[3],
            membership=owners[4],
        )

    owners = list(owner_context())
    owners[4] = SimpleNamespace(world_id_for=lambda entity_id: "other")
    container_snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("container_entity", LocalHexPosition(0, 0), kind="object"),),
    )
    with pytest.raises(HexWorldPersistenceError, match="not a member of this world"):
        container_snapshot.validate_domain_owners(
            actors=owners[0],
            npcs=owners[1],
            resource_nodes=owners[2],
            containers=owners[3],
            membership=owners[4],
        )


@pytest.mark.parametrize("custody", ["nested", "inventory"])
def test_domain_owner_validation_rejects_nested_or_carried_containers(custody):
    owners = list(owner_context(
        container_parent=object() if custody == "nested" else None,
        container_custody="player" if custody == "inventory" else None,
    ))
    snapshot = HexWorldSnapshot(
        WorldId("world"),
        (record("container_entity", LocalHexPosition(0, 0), kind="object"),),
    )

    with pytest.raises(HexWorldPersistenceError, match="Nested or carried container"):
        snapshot.validate_domain_owners(
            actors=owners[0],
            npcs=owners[1],
            resource_nodes=owners[2],
            containers=owners[3],
            membership=owners[4],
        )
