"""Correctness and differential tests for generic spatial indexes."""
import random
import pytest

from hex_world_lab.physics.broadphase import AABB
from hex_world_lab.spatial import Quadtree, UniformGrid


def test_grid_insert_update_remove_and_negative_coordinates():
    grid = UniformGrid(10)
    grid.insert("a", AABB(-11, -1, -1, 1))
    grid.insert("b", AABB(10, 0, 12, 2))
    assert grid.query(AABB(-10, -2, 0, 2)) == ("a",)
    grid.update("a", AABB(30, 30, 31, 31))
    assert grid.query(AABB(-20, -20, 20, 20)) == ("b",)
    grid.remove("b")
    assert grid.query(AABB(0, 0, 50, 50)) == ("a",)
    assert len(grid) == 1


def test_grid_rejects_invalid_cell_size_and_duplicate_ids():
    with pytest.raises(ValueError):
        UniformGrid(0)
    grid = UniformGrid(4)
    grid.insert("a", AABB(0, 0, 1, 1))
    with pytest.raises(ValueError):
        grid.insert("a", AABB(2, 2, 3, 3))


def test_quadtree_splits_and_keeps_spanning_entries_at_parent():
    tree = Quadtree(AABB(0, 0, 100, 100), capacity=1, max_depth=4)
    tree.insert("wide", AABB(40, 40, 60, 60))
    tree.insert("left", AABB(1, 1, 2, 2))
    tree.insert("right", AABB(90, 90, 95, 95))
    assert tree.query(AABB(45, 45, 46, 46)) == ("wide",)
    assert tree.query(AABB(0, 0, 10, 10)) == ("left",)
    assert tree.node_count > 1


def test_quadtree_rejects_outside_root_and_updates():
    tree = Quadtree(AABB(0, 0, 10, 10))
    with pytest.raises(ValueError):
        tree.insert("outside", AABB(9, 9, 11, 11))
    tree.insert("a", AABB(1, 1, 2, 2))
    tree.update("a", AABB(7, 7, 8, 8))
    assert tree.query(AABB(1, 1, 2, 2)) == ()
    assert tree.query(AABB(7, 7, 8, 8)) == ("a",)


@pytest.mark.parametrize("kind", ["grid", "quadtree"])
def test_randomized_queries_match_linear_reference(kind):
    rng = random.Random(8108)
    values = {}
    for index in range(250):
        x, y = rng.uniform(-900, 900), rng.uniform(-900, 900)
        w, h = rng.uniform(0, 120), rng.uniform(0, 120)
        values[str(index)] = AABB(x, y, x + w, y + h)
    if kind == "grid":
        index = UniformGrid(64)
    else:
        index = Quadtree(AABB(-1100, -1100, 1100, 1100), capacity=8, max_depth=8)
    for item_id, bounds in values.items():
        index.insert(item_id, bounds)
    for _ in range(300):
        x, y = rng.uniform(-1000, 1000), rng.uniform(-1000, 1000)
        query = AABB(x, y, x + rng.uniform(0, 180), y + rng.uniform(0, 180))
        expected = tuple(sorted(k for k, b in values.items() if query.intersects(b)))
        assert index.query(query) == expected


def test_grid_inclusive_bucket_edges_and_deduplication():
    grid = UniformGrid(10)
    grid.insert("cross", AABB(0, 0, 20, 20))
    assert grid.query(AABB(10, 10, 10, 10)) == ("cross",)
    assert grid.bucket_count == 9


def test_quadtree_retains_root_edge_and_removes_records():
    tree = Quadtree(AABB(0, 0, 100, 100), capacity=1)
    tree.insert("edge", AABB(100, 50, 100, 50))
    assert tree.query(AABB(100, 50, 100, 50)) == ("edge",)
    tree.remove("edge")
    assert tree.query(AABB(100, 50, 100, 50)) == ()


def test_quadtree_invalid_update_is_atomic():
    tree = Quadtree(AABB(0, 0, 10, 10))
    original = AABB(1, 1, 2, 2)
    tree.insert("a", original)
    with pytest.raises(ValueError):
        tree.update("a", AABB(9, 9, 11, 11))
    assert tree.query(original) == ("a",)


def test_uniform_grid_default_cell_size_uses_measured_balanced_value():
    assert UniformGrid().cell_size == 128.0
