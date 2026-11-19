"""Ground-anchor placement and visual/physical separation tests."""

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics import ActorBodyTransform, BodyDefinition, CircleShape


@pytest.mark.parametrize("height", [0.25, 1.0, 1.8, 4.0])
def test_body_height_is_positive_metadata_not_a_2d_collider_axis(height):
    body = BodyDefinition("actor", CircleShape(0.5), body_height=height)
    transform = ActorBodyTransform(WorldPoint(12.0, -3.0))

    assert body.body_height == height
    assert transform.transform_shape(body) == CircleShape(
        0.5, Vector2(12.0, -3.0)
    )


def test_ground_anchor_remains_authoritative_when_body_offset_changes():
    anchor = WorldPoint(7.0, 11.0)
    transform = ActorBodyTransform(anchor)
    centered = BodyDefinition("centered", CircleShape(0.4))
    offset = BodyDefinition("offset", CircleShape(0.4), Vector2(0.0, 0.75))

    assert transform.ground_anchor == anchor
    assert transform.transform_shape(centered).center == Vector2(7.0, 11.0)
    assert transform.transform_shape(offset).center == Vector2(7.0, 11.75)


def test_local_collider_offset_rotates_around_ground_anchor():
    body = BodyDefinition("actor", CircleShape(0.25), Vector2(1.0, 0.0))
    transform = ActorBodyTransform(WorldPoint(3.0, 4.0), 1.5707963267948966)

    world_shape = transform.transform_shape(body)

    assert world_shape.center.x == pytest.approx(3.0)
    assert world_shape.center.y == pytest.approx(5.0)
    assert transform.ground_anchor == WorldPoint(3.0, 4.0)


def test_visual_pivot_is_not_part_of_physics_body_contract():
    body = BodyDefinition("actor", CircleShape(0.3), Vector2(0.0, 0.2))
    transform = ActorBodyTransform(WorldPoint(2.0, 5.0))

    # Different render pivots are deliberately not inputs to physics.
    render_pivots = (Vector2(0.0, 0.0), Vector2(0.5, 1.25))
    collider_results = tuple(transform.transform_shape(body) for _ in render_pivots)

    assert collider_results[0] == collider_results[1]
    assert collider_results[0].center == Vector2(2.0, 5.2)
