"""Tests for conservative AABB broadphase candidate gathering."""

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics.broadphase import AABB, gather_candidates
from hex_world_lab.physics.narrowphase import collide_shapes
from hex_world_lab.physics.obstacle import ObstacleDefinition
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape
from hex_world_lab.world.identity import MapId


def obstacle(obstacle_id, shape, position=WorldPoint(0, 0)):
    return ObstacleDefinition(obstacle_id, MapId("map"), shape, position)


def test_aabb_from_circle_and_polygon():
    assert AABB.from_shape(CircleShape(2, Vector2(3, 4))) == AABB(1, 2, 5, 6)
    polygon = ConvexPolygonShape((Vector2(-2, 1), Vector2(3, 1), Vector2(0, 4)))
    assert AABB.from_shape(polygon) == AABB(-2, 1, 3, 4)


def test_aabb_intersection_includes_touching_edges_and_corners():
    first = AABB(0, 0, 1, 1)
    assert first.intersects(AABB(1, 0.2, 2, 0.8))
    assert first.intersects(AABB(1, 1, 2, 2))
    assert not first.intersects(AABB(1.0001, 0, 2, 1))


def test_expanded_aabb_is_conservative_and_validated():
    assert AABB(0, 0, 1, 1).expanded(0.5) == AABB(-0.5, -0.5, 1.5, 1.5)
    with pytest.raises(ValueError):
        AABB(0, 0, 1, 1).expanded(-0.1)


def test_gather_candidates_returns_only_overlapping_bounds_in_stable_order():
    values = (
        obstacle("tree-b", CircleShape(0.5), WorldPoint(2, 0)),
        obstacle("tree-a", CircleShape(0.5), WorldPoint(0, 0)),
        obstacle("far", CircleShape(0.5), WorldPoint(10, 10)),
    )
    found = gather_candidates(AABB(-1, -1, 1, 1), values)
    assert tuple(item.obstacle_id for item in found) == ("tree-a",)


def test_aabb_false_positive_is_rejected_by_exact_narrowphase():
    candidate = obstacle("rock", CircleShape(0.5), WorldPoint(1.4, 1.4))
    query = AABB(-1, -1, 1, 1)
    found = gather_candidates(query, (candidate,))
    assert found == (candidate,)

    square = ConvexPolygonShape((
        Vector2(-1, -1), Vector2(1, -1),
        Vector2(1, 1), Vector2(-1, 1),
    ))
    assert collide_shapes(square, candidate.world_shape(), "rock") is None


def test_duplicate_obstacle_ids_are_rejected():
    item = obstacle("same", CircleShape(0.5))
    with pytest.raises(ValueError, match="unique"):
        gather_candidates(AABB(-1, -1, 1, 1), (item, item))
