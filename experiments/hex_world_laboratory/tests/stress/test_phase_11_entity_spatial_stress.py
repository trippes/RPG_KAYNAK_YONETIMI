"""Deterministic Phase 11 stress and lifecycle regression coverage.

The stress suite intentionally keeps NPCs/resources stationary. It exercises
entity indexing and registry mutation only; no autonomous actor movement or AI
is introduced.
"""
from __future__ import annotations

import random

import pytest

from hex_world_lab.entities import (
    EntityId,
    EntityKind,
    EntityLocation,
    EntityRecord,
    EntityRegistry,
    EntityTransform,
)
from hex_world_lab.entities.spatial_index import EntityAABB, EntitySpatialIndex
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.physics import BodyDefinition, CircleShape
from hex_world_lab.world import HexWorld, MapId, WorldId


def _make_index(cell_size: float = 128.0):
    world = HexWorld(WorldId("phase-11-stress-world"))
    map_id = MapId("stress-map")
    world.register_map(map_id, "Stress map")
    registry = EntityRegistry(world.world_id, world.map_registry)
    index = EntitySpatialIndex(registry, cell_size=cell_size)
    index.activate_map(map_id)
    return world, map_id, registry, index


def _entity(world, map_id, entity_number: int, x: float, y: float):
    return EntityRecord(
        EntityId(f"stress-{entity_number:05d}"),
        EntityKind.NPC if entity_number % 2 else EntityKind.RESOURCE,
        EntityTransform(EntityLocation(world.world_id, map_id, WorldPoint(x, y))),
        BodyDefinition(f"body-{entity_number:05d}", CircleShape(3.0)),
    )


def _assert_query_matches_brute_force(registry, index, map_id, bounds):
    indexed = {
        entity.entity_id
        for entity in index.query(map_id, bounds)
        if (entity_bounds := index.bounds_for(entity)) is not None
        and bounds.intersects(entity_bounds)
    }
    brute_force = {
        entity.entity_id
        for entity in registry.entities_for_map(registry.world_id, map_id)
        if entity.is_active
        and (entity_bounds := index.bounds_for(entity)) is not None
        and bounds.intersects(entity_bounds)
    }
    assert indexed == brute_force


@pytest.mark.parametrize("entity_count", [100, 1_000, 10_000])
@pytest.mark.parametrize("distribution", ["sparse", "clustered", "mixed"])
def test_seeded_entity_spatial_queries_have_no_false_negatives(
    entity_count: int, distribution: str
):
    """Exercise 100/1k/10k entities across repeatable spatial distributions."""
    seed = 110_000 + entity_count + len(distribution)
    rng = random.Random(seed)
    world, map_id, registry, index = _make_index()

    for number in range(entity_count):
        if distribution == "sparse":
            x, y = number * 180.0, (number % 17) * 180.0
        elif distribution == "clustered":
            x, y = rng.uniform(-250.0, 250.0), rng.uniform(-250.0, 250.0)
        else:
            if number % 4 == 0:
                x, y = rng.uniform(-250.0, 250.0), rng.uniform(-250.0, 250.0)
            else:
                x, y = rng.uniform(-25_000.0, 25_000.0), rng.uniform(-25_000.0, 25_000.0)
        entity = _entity(world, map_id, number, x, y)
        registry.register(entity)
        index.update_entity(entity)

    for _ in range(150):
        if distribution == "sparse":
            center_x = rng.randrange(entity_count) * 180.0
            center_y = rng.randrange(17) * 180.0
        elif distribution == "clustered":
            center_x, center_y = rng.uniform(-300.0, 300.0), rng.uniform(-300.0, 300.0)
        else:
            center_x, center_y = rng.uniform(-25_000.0, 25_000.0), rng.uniform(-25_000.0, 25_000.0)
        half_width = rng.uniform(1.0, 220.0)
        half_height = rng.uniform(1.0, 220.0)
        query = EntityAABB(
            center_x - half_width,
            center_y - half_height,
            center_x + half_width,
            center_y + half_height,
        )
        _assert_query_matches_brute_force(registry, index, map_id, query)


def test_randomized_entity_lifecycle_keeps_spatial_index_consistent():
    """Move, deactivate, reactivate and delete entities under a fixed seed."""
    rng = random.Random(110_911)
    world, map_id, registry, index = _make_index(cell_size=64.0)
    entities = {}

    for number in range(1_000):
        entity = _entity(
            world,
            map_id,
            number,
            rng.uniform(-5_000.0, 5_000.0),
            rng.uniform(-5_000.0, 5_000.0),
        )
        registry.register(entity)
        index.update_entity(entity)
        entities[entity.entity_id] = entity

    active_ids = list(entities)
    for operation in range(900):
        entity_id = rng.choice(active_ids)
        current = registry.require(entity_id)
        action = operation % 3
        if action == 0:
            moved = current.with_transform(
                EntityTransform(
                    EntityLocation(
                        world.world_id,
                        map_id,
                        WorldPoint(rng.uniform(-8_000.0, 8_000.0), rng.uniform(-8_000.0, 8_000.0)),
                    )
                )
            )
            registry.update_transform(entity_id, moved.transform)
            index.update_entity(moved)
        elif action == 1:
            inactive = registry.set_active(entity_id, False)
            index.update_entity(inactive)
            assert entity_id not in {item.entity_id for item in index.query(
                map_id,
                EntityAABB(-20_000.0, -20_000.0, 20_000.0, 20_000.0),
            )}
            active = registry.set_active(entity_id, True)
            index.update_entity(active)
        else:
            index.remove_entity(entity_id)
            registry.remove(entity_id)
            active_ids.remove(entity_id)

        center_x = rng.uniform(-8_000.0, 8_000.0)
        center_y = rng.uniform(-8_000.0, 8_000.0)
        query = EntityAABB(center_x - 300.0, center_y - 300.0, center_x + 300.0, center_y + 300.0)
        _assert_query_matches_brute_force(registry, index, map_id, query)


def test_unloaded_map_index_is_inactive_and_rebuild_restores_candidates():
    world, map_id, registry, index = _make_index()
    entity = _entity(world, map_id, 1, -10.0, -10.0)
    registry.register(entity)
    index.update_entity(entity)
    query = EntityAABB(-20.0, -20.0, 0.0, 0.0)
    assert [item.entity_id for item in index.query(map_id, query)] == [entity.entity_id]

    index.deactivate_map(map_id)
    assert index.query(map_id, query) == ()
    index.activate_map(map_id)
    assert [item.entity_id for item in index.query(map_id, query)] == [entity.entity_id]
