"""Native hex-map collision geometry tests."""
import pytest

from application.hex_map_definition import parse_hex_map
from core.domain.physics import (
    BoundaryPolicy,
    StaticObstacleIndex,
    build_hex_map_collision_geometry,
)
from core.domain.spatial import LocalHexPosition, WorldPoint


def make_map(*, valid=((0, 0), (1, 0)), blocked=(), landmarks=()):
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
        "valid_cells": [list(cell) for cell in valid],
        "cell_overrides": [
            {"q": q, "r": r, "blocked": True} for q, r in blocked
        ],
        "landmarks": list(landmarks),
    })


def test_blocked_cell_becomes_native_hex_polygon_obstacle():
    geometry = build_hex_map_collision_geometry(
        make_map(blocked=((1, 0),)), 32.0,
    )
    obstacle = next(item for item in geometry.obstacles if item.obstacle_id == "cell:1:0")
    assert obstacle.map_id == "forest"
    assert len(obstacle.shape.vertices) == 6
    assert obstacle.position == WorldPoint(32.0 * 3**0.5, 0.0)


def test_non_walkable_landmark_becomes_native_obstacle():
    geometry = build_hex_map_collision_geometry(
        make_map(landmarks=({
            "id": "old-oak", "name": "Old Oak", "position": [0, 0],
            "walkable": False,
        },)), 32.0,
    )
    assert [item.obstacle_id for item in geometry.obstacles] == ["landmark:old-oak"]


def test_walkable_landmark_does_not_block_map_geometry():
    geometry = build_hex_map_collision_geometry(
        make_map(landmarks=({
            "id": "campfire", "name": "Campfire", "position": [0, 0],
            "walkable": True,
        },)), 32.0,
    )
    assert geometry.obstacles == ()


def test_blocked_boundary_builds_only_exposed_hex_edges():
    geometry = build_hex_map_collision_geometry(make_map(), 32.0)
    assert len(geometry.boundary_edges) == 10
    assert len(geometry.collision_obstacles) == 10


def test_open_boundary_has_no_perimeter_walls():
    geometry = build_hex_map_collision_geometry(
        make_map(), 32.0, boundary_policy=BoundaryPolicy.OPEN,
    )
    assert geometry.boundary_edges == ()
    assert geometry.collision_obstacles == ()


def test_static_obstacle_index_queries_bounds_deterministically():
    geometry = build_hex_map_collision_geometry(
        make_map(blocked=((1, 0),)), 32.0,
    )
    index = StaticObstacleIndex(geometry.collision_obstacles)
    result = index.query_circle("forest", WorldPoint(32.0 * 3**0.5, 0.0), 4.0)
    assert [item.obstacle_id for item in result] == ["cell:1:0"]


def test_invalid_hex_size_is_rejected():
    with pytest.raises(ValueError):
        build_hex_map_collision_geometry(make_map(), 0.0)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
