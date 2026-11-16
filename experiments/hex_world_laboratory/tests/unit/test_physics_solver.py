"""Tests for deterministic kinematic collision resolution and sliding."""

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics.obstacle import ObstacleDefinition
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape
from hex_world_lab.physics.solver import resolve_kinematic_motion
from hex_world_lab.world.identity import MapId


MAP = MapId("world", "map")


def wall(x=2.0, y=0.0, half_width=0.25, half_height=3.0, obstacle_id="wall"):
    shape = ConvexPolygonShape((
        Vector2(-half_width, -half_height),
        Vector2(half_width, -half_height),
        Vector2(half_width, half_height),
        Vector2(-half_width, half_height),
    ))
    return ObstacleDefinition(
        obstacle_id, MAP, shape, WorldPoint(x, y)
    )


def test_circle_stops_before_wall_without_entering_it():
    result = resolve_kinematic_motion(
        CircleShape(0.5, Vector2(0.8, 0.0)), Vector2(0.5, 0.0), (wall(),)
    )
    assert result.final_shape.center.x == pytest.approx(1.25, abs=1e-6)
    assert result.final_shape.center.y == pytest.approx(0.0)
    assert result.applied_displacement.x == pytest.approx(1.25, abs=1e-6)
    assert result.unresolved_penetration <= 1e-7
    assert result.contacts.contacts


def test_circle_slides_along_wall_and_preserves_tangent_motion():
    result = resolve_kinematic_motion(
        CircleShape(0.5, Vector2(0.8, 0.0)), Vector2(0.5, 1.5), (wall(),)
    )
    assert result.final_shape.center.x == pytest.approx(1.25, abs=1e-6)
    assert result.final_shape.center.y == pytest.approx(1.5, abs=1e-6)
    assert result.applied_displacement.y == pytest.approx(1.5, abs=1e-6)


def test_circle_moving_away_from_wall_is_not_blocked():
    start = CircleShape(0.5, Vector2(1.25, 0.0))
    result = resolve_kinematic_motion(start, Vector2(-1.0, 0.5), (wall(),))
    assert result.final_shape.center.x == pytest.approx(0.25)
    assert result.final_shape.center.y == pytest.approx(0.5)


def test_initial_penetration_is_corrected_before_motion():
    start = CircleShape(0.5, Vector2(1.8, 0.0))
    result = resolve_kinematic_motion(start, Vector2(0.0, 1.0), (wall(),))
    assert result.final_shape.center.x <= 1.250001
    assert result.final_shape.center.y == pytest.approx(1.0)
    assert result.unresolved_penetration <= 1e-7


def test_two_walls_resolve_corner_without_inward_motion():
    vertical = wall(x=2.0, obstacle_id="vertical")
    horizontal = wall(
        x=0.0, y=2.0, half_width=3.0, half_height=0.25,
        obstacle_id="horizontal",
    )
    result = resolve_kinematic_motion(
        CircleShape(0.5), Vector2(1.5, 1.5), (horizontal, vertical)
    )
    assert result.final_shape.center.x <= 1.250001
    assert result.final_shape.center.y <= 1.250001
    assert result.unresolved_penetration <= 1e-7


def test_solver_result_is_independent_of_obstacle_input_order():
    obstacles = (wall(obstacle_id="b"), wall(x=4.0, obstacle_id="a"))
    first = resolve_kinematic_motion(
        CircleShape(0.5), Vector2(3.0, 0.25), obstacles
    )
    second = resolve_kinematic_motion(
        CircleShape(0.5), Vector2(3.0, 0.25), tuple(reversed(obstacles))
    )
    assert first == second


def test_polygon_actor_can_be_resolved_against_polygon_obstacle():
    actor = ConvexPolygonShape((
        Vector2(-0.5, -0.5), Vector2(0.5, -0.5),
        Vector2(0.5, 0.5), Vector2(-0.5, 0.5),
    ))
    result = resolve_kinematic_motion(
        actor, Vector2(1.5, 0.0), (wall(),)
    )
    xs = tuple(point.x for point in result.final_shape.vertices)
    assert max(xs) <= 1.750001


def test_empty_world_applies_full_displacement():
    displacement = Vector2(2.0, -3.0)
    result = resolve_kinematic_motion(
        CircleShape(0.5), displacement, ()
    )
    assert result.final_shape.center == displacement
    assert result.applied_displacement == displacement
    assert result.contacts.contacts == ()


def test_invalid_solver_inputs_are_rejected():
    with pytest.raises(ValueError, match="at least one"):
        resolve_kinematic_motion(CircleShape(1), Vector2(1, 0), (), max_iterations=0)
    with pytest.raises(ValueError, match="non-negative"):
        resolve_kinematic_motion(
            CircleShape(1), Vector2(1, 0), (), penetration_slop=-1
        )
    with pytest.raises(ValueError, match="unique"):
        resolve_kinematic_motion(
            CircleShape(1), Vector2(1, 0), (wall(), wall())
        )
