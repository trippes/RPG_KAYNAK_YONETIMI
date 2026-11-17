"""Physics adapter and indexed collision path equivalence."""
import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics import (
    CircleShape, ObstacleDefinition, ObstacleSpatialIndex, AABB,
    resolve_continuous_motion, resolve_kinematic_motion,
)
from hex_world_lab.world.identity import MapId


def make_obstacle(name, x):
    return ObstacleDefinition(name, MapId("map"), CircleShape(1.0, Vector2(0, 0)), WorldPoint(x, 0))


def test_obstacle_index_is_map_scoped_and_tracks_lifecycle():
    first = make_obstacle("a", 0)
    index = ObstacleSpatialIndex((first,), cell_size=4)
    assert index.query(AABB(-2, -2, 2, 2)) == (first,)
    moved = make_obstacle("a", 20)
    index.update(moved)
    assert index.query(AABB(-2, -2, 2, 2)) == ()
    assert index.query(AABB(18, -2, 22, 2)) == (moved,)
    index.remove("a")
    assert len(index) == 0
    with pytest.raises(KeyError):
        index.remove("a")


def test_indexed_and_linear_solver_results_match():
    obstacles = (make_obstacle("wall-a", 4), make_obstacle("wall-b", 8))
    provider = ObstacleSpatialIndex(obstacles, cell_size=3)
    start = CircleShape(0.5, Vector2(0, 0))
    delta = Vector2(10, 0)
    baseline = resolve_kinematic_motion(start, delta, obstacles)
    indexed = resolve_kinematic_motion(start, delta, obstacles, candidate_provider=provider)
    assert indexed == baseline


def test_indexed_and_linear_continuous_results_match():
    obstacles = (make_obstacle("wall-a", 4), make_obstacle("wall-b", 8))
    provider = ObstacleSpatialIndex(obstacles, cell_size=3)
    start = CircleShape(0.5, Vector2(0, 0))
    delta = Vector2(10, 0)
    baseline = resolve_continuous_motion(start, delta, obstacles)
    indexed = resolve_continuous_motion(start, delta, obstacles, candidate_provider=provider)
    assert indexed == baseline


def test_index_rejects_duplicate_and_cross_map_obstacles():
    item = make_obstacle("same", 0)
    with pytest.raises(ValueError):
        ObstacleSpatialIndex((item, item))
    index = ObstacleSpatialIndex((item,))
    other = ObstacleDefinition("other", MapId("other-map"), item.shape, WorldPoint(0, 0))
    with pytest.raises(ValueError):
        index.insert(other)
