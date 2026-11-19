"""Native hex-map collision geometry tests."""
import unittest

from application.hex_map_definition import parse_hex_map
from application.hex_map_physics import build_hex_map_collision_geometry
from core.domain.physics import BoundaryPolicy, StaticObstacleIndex
from core.domain.spatial import WorldPoint


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


class NativeHexMapGeometryTests(unittest.TestCase):
    def test_blocked_cell_becomes_native_hex_polygon_obstacle(self):
        geometry = build_hex_map_collision_geometry(make_map(blocked=((1, 0),)), 32.0)
        obstacle = next(item for item in geometry.obstacles if item.obstacle_id == "cell:1:0")
        self.assertEqual(obstacle.map_id, "forest")
        self.assertEqual(len(obstacle.shape.vertices), 6)
        self.assertAlmostEqual(obstacle.position.x, 32.0 * 3**0.5)
        self.assertEqual(obstacle.position.y, 0.0)

    def test_non_walkable_landmark_becomes_native_obstacle(self):
        geometry = build_hex_map_collision_geometry(
            make_map(landmarks=({
                "id": "old-oak", "name": "Old Oak", "position": [0, 0],
                "walkable": False,
            },)), 32.0,
        )
        self.assertEqual([item.obstacle_id for item in geometry.obstacles], ["landmark:old-oak"])

    def test_walkable_landmark_does_not_block_map_geometry(self):
        geometry = build_hex_map_collision_geometry(
            make_map(landmarks=({
                "id": "campfire", "name": "Campfire", "position": [0, 0],
                "walkable": True,
            },)), 32.0,
        )
        self.assertEqual(geometry.obstacles, ())

    def test_blocked_boundary_builds_only_exposed_hex_edges(self):
        geometry = build_hex_map_collision_geometry(make_map(), 32.0)
        self.assertEqual(len(geometry.boundary_edges), 10)
        self.assertEqual(len(geometry.collision_obstacles), 10)

    def test_open_boundary_has_no_perimeter_walls(self):
        geometry = build_hex_map_collision_geometry(
            make_map(), 32.0, boundary_policy=BoundaryPolicy.OPEN,
        )
        self.assertEqual(geometry.boundary_edges, ())
        self.assertEqual(geometry.collision_obstacles, ())

    def test_static_obstacle_index_queries_bounds_deterministically(self):
        geometry = build_hex_map_collision_geometry(make_map(blocked=((1, 0),)), 32.0)
        index = StaticObstacleIndex(geometry.collision_obstacles)
        result = index.query_circle("forest", WorldPoint(32.0 * 3**0.5, 0.0), 4.0)
        self.assertEqual([item.obstacle_id for item in result], ["cell:1:0"])

    def test_invalid_hex_size_is_rejected(self):
        with self.assertRaises(ValueError):
            build_hex_map_collision_geometry(make_map(), 0.0)


if __name__ == "__main__":
    unittest.main()
