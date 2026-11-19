"""Tests for Eldoria-native swept circle collision detection."""
import unittest

from core.domain.physics import (
    CircleShape,
    ConvexPolygonShape,
    StaticObstacle,
    Vector2,
)
from core.domain.physics.continuous_solver import (
    resolve_continuous_motion,
    sweep_circle_polygon,
)
from core.domain.spatial import WorldPoint


def wall():
    return StaticObstacle(
        "wall", "forest",
        ConvexPolygonShape((
            WorldPoint(0, 0), WorldPoint(1, 0),
            WorldPoint(1, 20), WorldPoint(0, 20),
        )),
        WorldPoint(5, -10),
    )


class NativeSweepTests(unittest.TestCase):
    def test_sweep_circle_polygon_finds_edge_time_of_impact(self):
        hit = sweep_circle_polygon(
            CircleShape(1, WorldPoint(0, 0)),
            Vector2(10, 0),
            wall().world_shape(),
            "wall",
        )
        self.assertIsNotNone(hit)
        self.assertAlmostEqual(hit.time_of_impact, 0.4)
        self.assertLess(hit.normal.x, 0.0)

    def test_continuous_solver_prevents_tunneling_through_thin_wall(self):
        result = resolve_continuous_motion(
            CircleShape(1, WorldPoint(0, 0)),
            Vector2(10, 0),
            (wall(),),
            map_id="forest",
        )
        self.assertLess(result.final_shape.center.x, 4.001)
        self.assertGreater(result.final_shape.center.x, 3.99)
        self.assertEqual(len(result.impacts), 1)
        self.assertEqual(result.impacts[0].obstacle_id, "wall")

    def test_continuous_solver_slides_along_wall(self):
        result = resolve_continuous_motion(
            CircleShape(1, WorldPoint(0, 0)),
            Vector2(10, 4),
            (wall(),),
            map_id="forest",
        )
        self.assertLess(result.final_shape.center.x, 4.001)
        self.assertGreater(result.final_shape.center.x, 3.99)
        self.assertAlmostEqual(result.final_shape.center.y, 4.0, places=5)
        self.assertTrue(result.impacts)

    def test_movement_away_from_wall_is_not_blocked(self):
        result = resolve_continuous_motion(
            CircleShape(1, WorldPoint(7, 0)),
            Vector2(3, 0),
            (wall(),),
            map_id="forest",
        )
        self.assertAlmostEqual(result.final_shape.center.x, 10.0)
        self.assertEqual(result.impacts, ())

    def test_circle_obstacle_is_swept(self):
        obstacle = StaticObstacle(
            "boulder", "forest", CircleShape(1), WorldPoint(5, 0),
        )
        result = resolve_continuous_motion(
            CircleShape(1, WorldPoint(0, 0)),
            Vector2(10, 0),
            (obstacle,),
            map_id="forest",
        )
        self.assertAlmostEqual(result.final_shape.center.x, 2.99999999, places=6)
        self.assertEqual(len(result.impacts), 1)

    def test_indexed_and_unindexed_sweep_results_match(self):
        from core.domain.physics import StaticObstacleIndex
        obstacle = wall()
        shape = CircleShape(1, WorldPoint(0, 0))
        displacement = Vector2(10, 2)
        direct = resolve_continuous_motion(
            shape, displacement, (obstacle,), map_id="forest",
        )
        indexed = resolve_continuous_motion(
            shape, displacement, (obstacle,), map_id="forest",
            candidate_provider=StaticObstacleIndex((obstacle,)),
        )
        self.assertEqual(direct.final_shape, indexed.final_shape)
        self.assertEqual(direct.impacts, indexed.impacts)


if __name__ == "__main__":
    unittest.main()
