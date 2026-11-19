"""Versioned hex-world snapshot and atomic restore tests."""

import pytest

from application import (
    HexWorldEntityRecord,
    HexWorldPersistenceError,
    HexWorldSnapshot,
)
from application.hex_map_definition import parse_hex_map
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import EntityPosition, LocalHexPosition, MovementProfile
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
