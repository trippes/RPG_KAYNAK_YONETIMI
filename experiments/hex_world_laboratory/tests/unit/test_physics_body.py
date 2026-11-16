"""Tests for immutable physical body contracts."""

from dataclasses import FrozenInstanceError

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics import (
    ActorBodyTransform,
    BodyDefinition,
    CircleShape,
    ConvexPolygonShape,
)


def square():
    return ConvexPolygonShape((
        Vector2(-1, -1), Vector2(1, -1),
        Vector2(1, 1), Vector2(-1, 1),
    ))


def test_circle_shape_requires_positive_finite_radius():
    assert CircleShape(2).radius == 2
    for value in (0, -1, float("nan"), float("inf"), True):
        with pytest.raises((TypeError, ValueError)):
            CircleShape(value)


def test_polygon_shape_requires_three_or_more_unique_convex_vertices():
    assert len(square().vertices) == 4
    with pytest.raises(ValueError):
        ConvexPolygonShape((Vector2(0, 0), Vector2(1, 0)))
    with pytest.raises(ValueError):
        ConvexPolygonShape((Vector2(0, 0), Vector2(1, 0), Vector2(0, 0)))
    with pytest.raises(ValueError):
        ConvexPolygonShape((
            Vector2(0, 0), Vector2(2, 2),
            Vector2(0, 2), Vector2(2, 0),
        ))


def test_polygon_vertices_are_copied_to_an_immutable_tuple():
    vertices = [Vector2(0, 0), Vector2(2, 0), Vector2(1, 2)]
    shape = ConvexPolygonShape(vertices)
    vertices.clear()
    assert len(shape.vertices) == 3
    with pytest.raises(FrozenInstanceError):
        shape.vertices = ()


def test_body_definition_validates_identity_shape_offset_and_height():
    body = BodyDefinition("player", CircleShape(0.5), Vector2(0.1, -0.2), 1.8)
    assert body.body_id == "player"
    assert body.enabled is True
    for height in (0, -1, float("nan"), float("inf"), True):
        with pytest.raises((TypeError, ValueError)):
            BodyDefinition("player", CircleShape(0.5), body_height=height)
    with pytest.raises(ValueError):
        BodyDefinition(" ", CircleShape(0.5))
    with pytest.raises(TypeError):
        BodyDefinition("player", object())


def test_ground_anchor_and_local_offset_define_circle_center_contract():
    body = BodyDefinition("player", CircleShape(0.4), Vector2(0.5, 0.0))
    transform = ActorBodyTransform(WorldPoint(10.0, 20.0))
    world_shape = transform.transform_shape(body)
    assert world_shape == CircleShape(0.4)
    assert transform.ground_anchor == WorldPoint(10.0, 20.0)


def test_polygon_shape_is_transformed_by_anchor_offset_and_rotation():
    body = BodyDefinition("box", square(), Vector2(1.0, 0.0))
    transform = ActorBodyTransform(WorldPoint(10.0, 20.0), 0.0)
    world_shape = transform.transform_shape(body)
    assert isinstance(world_shape, ConvexPolygonShape)
    assert world_shape.vertices[0] == Vector2(10.0, 19.0)
    assert world_shape.vertices[1] == Vector2(12.0, 19.0)


def test_body_and_transform_reject_non_finite_or_wrong_types():
    with pytest.raises(TypeError):
        ActorBodyTransform((0, 0))
    with pytest.raises(ValueError):
        ActorBodyTransform(WorldPoint(0, 0), float("inf"))
    with pytest.raises(TypeError):
        ActorBodyTransform(WorldPoint(0, 0)).transform_shape(object())
