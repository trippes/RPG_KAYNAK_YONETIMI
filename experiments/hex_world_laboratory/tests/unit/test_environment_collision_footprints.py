"""Regression checks for tree-canopy and full-rock collision boundaries."""

from __future__ import annotations

from hex_world_lab.application.movement_demo import MovementDemo, PLAYER_COLLIDER_RADIUS
from hex_world_lab.movement import Vector2
from hex_world_lab.physics import CircleShape, ConvexPolygonShape, collide_shapes


def _environment_obstacle(demo: MovementDemo, object_id: str):
    return next(
        item for item in demo.collision_geometry.obstacles
        if item.obstacle_id == f"object:{object_id}"
    )


def _player_circle(x: float, y: float) -> CircleShape:
    return CircleShape(PLAYER_COLLIDER_RADIUS, Vector2(x, y))


def test_tree_blocks_trunk_and_roots_but_not_the_canopy() -> None:
    demo = MovementDemo()
    tree = _environment_obstacle(demo, "tree")
    assert isinstance(tree.shape, ConvexPolygonShape)

    # The lower trunk/root footprint blocks the player.
    assert collide_shapes(
        _player_circle(tree.position.x, tree.position.y + 5.0),
        tree.world_shape(),
        tree.obstacle_id,
    ) is not None

    # The upper canopy is deliberately outside the physical collider.
    assert collide_shapes(
        _player_circle(tree.position.x, tree.position.y + 75.0),
        tree.world_shape(),
        tree.obstacle_id,
    ) is None


def test_rock_collider_covers_its_full_footprint_including_edges() -> None:
    demo = MovementDemo()
    rock = _environment_obstacle(demo, "rock")
    assert isinstance(rock.shape, ConvexPolygonShape)

    # The center and the outer left/right portions of the visible footprint block.
    for offset_x, offset_y in ((0.0, 20.0), (-22.0, 15.0), (22.0, 15.0)):
        assert collide_shapes(
            _player_circle(rock.position.x + offset_x, rock.position.y + offset_y),
            rock.world_shape(),
            rock.obstacle_id,
        ) is not None

    # A point clearly beyond the rock's footprint remains traversable.
    assert collide_shapes(
        _player_circle(rock.position.x + 45.0, rock.position.y + 15.0),
        rock.world_shape(),
        rock.obstacle_id,
    ) is None
