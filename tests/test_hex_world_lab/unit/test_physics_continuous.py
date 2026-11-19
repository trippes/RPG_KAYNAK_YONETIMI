"""Continuous collision and tunneling regression tests."""

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics.continuous import (
    resolve_continuous_motion,
    sweep_circle_polygon,
)
from hex_world_lab.physics.obstacle import ObstacleDefinition
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape
from hex_world_lab.world.identity import MapId


MAP = MapId("map")


def box(x, y, half_width, half_height, obstacle_id="wall", clockwise=False):
    points = (
        Vector2(-half_width, -half_height),
        Vector2(half_width, -half_height),
        Vector2(half_width, half_height),
        Vector2(-half_width, half_height),
    )
    if clockwise:
        points = tuple(reversed(points))
    return ObstacleDefinition(
        obstacle_id, MAP, ConvexPolygonShape(points), WorldPoint(x, y)
    )


def test_sweep_detects_thin_wall_crossed_in_one_tick():
    obstacle = box(0.0, 0.0, 0.025, 2.0)
    hit = sweep_circle_polygon(
        CircleShape(0.2, Vector2(-10.0, 0.0)),
        Vector2(20.0, 0.0),
        obstacle.shape,
        obstacle.obstacle_id,
    )
    assert hit is not None
    assert hit.time_of_impact == pytest.approx((10.0 - 0.225) / 20.0)
    assert hit.normal.x == pytest.approx(-1.0)


def test_continuous_solver_prevents_tunneling_at_high_speed():
    obstacle = box(0.0, 0.0, 0.025, 3.0)
    result = resolve_continuous_motion(
        CircleShape(0.2, Vector2(-10.0, 0.0)),
        Vector2(20.0, 0.0),
        (obstacle,),
    )
    assert result.final_shape.center.x <= -0.225 + 1e-6
    assert result.impacts
    assert result.unresolved_penetration <= 1e-7


def test_continuous_solver_slides_after_first_impact():
    obstacle = box(0.0, 0.0, 0.025, 5.0)
    result = resolve_continuous_motion(
        CircleShape(0.2, Vector2(-1.0, -2.0)),
        Vector2(3.0, 4.0),
        (obstacle,),
    )
    assert result.final_shape.center.x <= -0.225 + 1e-6
    assert result.final_shape.center.y == pytest.approx(2.0, abs=1e-5)


def test_sweep_handles_clockwise_polygon_vertices():
    obstacle = box(0.0, 0.0, 1.0, 1.0, clockwise=True)
    hit = sweep_circle_polygon(
        CircleShape(0.5, Vector2(-3.0, -3.0)),
        Vector2(4.0, 4.0),
        obstacle.shape,
        obstacle.obstacle_id,
    )
    assert hit is not None
    assert 0.0 < hit.time_of_impact < 1.0
    assert hit.normal.x < 0.0
    assert hit.normal.y < 0.0


def test_sweep_returns_none_when_path_misses_polygon():
    hit = sweep_circle_polygon(
        CircleShape(0.25, Vector2(-3.0, 3.0)),
        Vector2(6.0, 0.0),
        box(0.0, 0.0, 1.0, 1.0).shape,
        "wall",
    )
    assert hit is None


def test_continuous_solver_handles_circle_obstacle():
    obstacle = ObstacleDefinition(
        "boulder", MAP, CircleShape(0.5), WorldPoint(0.0, 0.0)
    )
    result = resolve_continuous_motion(
        CircleShape(0.25, Vector2(-5.0, 0.0)),
        Vector2(10.0, 0.0),
        (obstacle,),
    )
    assert result.final_shape.center.x <= -0.75 + 1e-6
    assert result.impacts
