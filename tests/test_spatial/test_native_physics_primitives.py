"""Contract tests for Eldoria-native physics primitives."""
import math
import unittest

from core.domain.physics import (
    ActorBodyTransform,
    CircleShape,
    ConvexPolygonShape,
    PhysicsBodyDefinition,
    StaticObstacle,
    Vector2,
)
from core.domain.spatial import WorldPoint


class NativeVectorTests(unittest.TestCase):
    def test_vector_math_and_y_down_basis(self):
        vector = Vector2(3, 4)
        self.assertEqual(vector.length, 5)
        self.assertEqual(vector.normalized(), Vector2(0.6, 0.8))
        self.assertEqual(Vector2(1, 0).perpendicular(), Vector2(0, 1))
        self.assertEqual(Vector2(2, 3).dot(Vector2(4, 5)), 23)

    def test_vector_rejects_non_finite_components(self):
        with self.assertRaises(ValueError):
            Vector2(math.nan, 0)
        with self.assertRaises(TypeError):
            Vector2(True, 0)


class NativeShapeTests(unittest.TestCase):
    def test_circle_requires_positive_finite_radius(self):
        with self.assertRaises(ValueError):
            CircleShape(0)
        with self.assertRaises(ValueError):
            CircleShape(math.inf)

    def test_polygon_requires_strictly_convex_ordered_vertices(self):
        polygon = ConvexPolygonShape((
            WorldPoint(0, 0), WorldPoint(2, 0),
            WorldPoint(2, 2), WorldPoint(0, 2),
        ))
        self.assertEqual(len(polygon.vertices), 4)
        with self.assertRaises(ValueError):
            ConvexPolygonShape((
                WorldPoint(0, 0), WorldPoint(2, 0),
                WorldPoint(1, 1), WorldPoint(2, 2), WorldPoint(0, 2),
            ))


class NativeBodyTests(unittest.TestCase):
    def test_ground_anchor_transform_places_circle_in_world(self):
        body = PhysicsBodyDefinition(
            "player", CircleShape(8, WorldPoint(1, 2)),
            local_offset=Vector2(3, 4),
        )
        transformed = ActorBodyTransform(WorldPoint(100, 200)).transform_shape(body)
        self.assertEqual(transformed, CircleShape(8, WorldPoint(104, 206)))

    def test_rotated_polygon_is_transformed_around_ground_anchor(self):
        body = PhysicsBodyDefinition(
            "prop",
            ConvexPolygonShape((
                WorldPoint(0, 0), WorldPoint(2, 0),
                WorldPoint(2, 1), WorldPoint(0, 1),
            )),
        )
        transformed = ActorBodyTransform(
            WorldPoint(10, 20), math.pi / 2
        ).transform_shape(body)
        self.assertAlmostEqual(transformed.vertices[1].x, 10)
        self.assertAlmostEqual(transformed.vertices[1].y, 22)

    def test_static_obstacle_translates_local_shape(self):
        obstacle = StaticObstacle(
            "tree", "forest", CircleShape(5), WorldPoint(12, 18)
        )
        self.assertEqual(obstacle.world_shape(), CircleShape(5, WorldPoint(12, 18)))


if __name__ == "__main__":
    unittest.main()
