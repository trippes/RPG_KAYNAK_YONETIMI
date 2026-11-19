"""Tests for native narrowphase and discrete kinematic collision resolution."""
import unittest

from core.domain.physics import (
    CircleShape, ConvexPolygonShape, StaticObstacle, Vector2,
)
from core.domain.physics.kinematic_solver import resolve_kinematic_motion
from core.domain.physics.narrowphase import collide_shapes
from core.domain.spatial import WorldPoint


def box(obstacle_id="wall", x=10.0, y=-10.0, width=2.0, height=20.0):
    return StaticObstacle(
        obstacle_id, "forest",
        ConvexPolygonShape((
            WorldPoint(0, 0), WorldPoint(width, 0),
            WorldPoint(width, height), WorldPoint(0, height),
        )),
        WorldPoint(x, y),
    )


class NativeNarrowphaseTests(unittest.TestCase):
    def test_circle_circle_overlap_and_separation(self):
        contact = collide_shapes(
            CircleShape(5, WorldPoint(0, 0)),
            CircleShape(5, WorldPoint(8, 0)), "other",
        )
        self.assertIsNotNone(contact)
        self.assertAlmostEqual(contact.penetration_depth, 2.0)
        self.assertAlmostEqual(contact.normal.x, -1.0)
        self.assertIsNone(collide_shapes(
            CircleShape(2, WorldPoint(0, 0)),
            CircleShape(2, WorldPoint(5, 0)), "other",
        ))

    def test_circle_polygon_contact_normal_points_out_of_obstacle(self):
        contact = collide_shapes(
            CircleShape(2, WorldPoint(9, 0)),
            box().world_shape(), "wall",
        )
        self.assertIsNotNone(contact)
        self.assertLess(contact.normal.x, 0.0)

    def test_polygon_polygon_overlap(self):
        first = ConvexPolygonShape((
            WorldPoint(0, 0), WorldPoint(4, 0),
            WorldPoint(4, 4), WorldPoint(0, 4),
        ))
        second = ConvexPolygonShape((
            WorldPoint(3, 0), WorldPoint(7, 0),
            WorldPoint(7, 4), WorldPoint(3, 4),
        ))
        contact = collide_shapes(first, second, "second")
        self.assertIsNotNone(contact)
        self.assertAlmostEqual(contact.penetration_depth, 1.0)


class NativeKinematicSolverTests(unittest.TestCase):
    def test_move_is_clamped_against_wall(self):
        wall = box()
        result = resolve_kinematic_motion(
            CircleShape(2, WorldPoint(0, 0)), Vector2(9, 0), (wall,),
            map_id="forest",
        )
        self.assertLess(result.final_shape.center.x, 8.01)
        self.assertGreater(result.final_shape.center.x, 7.9)
        self.assertTrue(result.contacts.contacts)

    def test_wall_slide_preserves_tangential_motion(self):
        wall = box()
        result = resolve_kinematic_motion(
            CircleShape(2, WorldPoint(0, 0)), Vector2(9, 6), (wall,),
            map_id="forest",
        )
        self.assertLess(result.final_shape.center.x, 8.01)
        self.assertAlmostEqual(result.final_shape.center.y, 6.0, places=4)

    def test_indexed_and_unindexed_candidates_match(self):
        from core.domain.physics import StaticObstacleIndex
        wall = box()
        index = StaticObstacleIndex((wall,))
        shape = CircleShape(2, WorldPoint(0, 0))
        displacement = Vector2(9, 0)
        direct = resolve_kinematic_motion(shape, displacement, (wall,), map_id="forest")
        indexed = resolve_kinematic_motion(
            shape, displacement, (wall,), map_id="forest", candidate_provider=index,
        )
        self.assertEqual(direct.final_shape, indexed.final_shape)
        self.assertEqual(direct.applied_displacement, indexed.applied_displacement)


if __name__ == "__main__":
    unittest.main()
