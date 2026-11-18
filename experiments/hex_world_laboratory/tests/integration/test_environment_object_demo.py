import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.rendering import RenderDebugOptions


def test_demo_environment_profiles_share_scene_and_existing_collision_pipeline():
    pygame.init()
    try:
        demo = MovementDemo()
        assert {item.instance_id for item in demo.environment_scene.placements} == {"tree", "rock", "bush"}
        obstacle_ids = {item.obstacle_id for item in demo.collision_geometry.obstacles}
        assert {"object:tree", "object:rock"}.issubset(obstacle_ids)
        assert "object:bush" not in obstacle_ids
        snapshot = demo.build_render_snapshot(debug_options=RenderDebugOptions(show_environment_debug=True))
        assert {item.visual_id for item in snapshot.sprites} >= {"tree", "rock", "bush"}
        assert {item.instance_id for item in snapshot.environment_debug} == {"tree", "rock", "bush"}
        assert "object:tree" in {item.owner_id for item in snapshot.colliders}
        assert "object:rock" in {item.owner_id for item in snapshot.colliders}
        # Environment collision geometry is hidden in normal rendering; F3 owns it.
        assert not snapshot.circles
    finally:
        pygame.quit()



def test_tree_trunk_and_rock_collide_but_canopy_and_bush_do_not():
    from hex_world_lab.movement import Vector2
    from hex_world_lab.physics import CircleShape, collide_shapes

    pygame.init()
    try:
        demo = MovementDemo()
        placements = {item.instance_id: item for item in demo.environment_scene.placements}
        obstacles = {item.obstacle_id: item for item in demo.collision_geometry.obstacles}
        player_radius = demo.body_definition.collider.radius

        tree_position = placements["tree"].ground_position
        tree = obstacles["object:tree"]
        at_trunk = CircleShape(player_radius, Vector2(tree_position.x, tree_position.y))
        above_trunk = CircleShape(player_radius, Vector2(tree_position.x, tree_position.y + 30.0))
        assert collide_shapes(at_trunk, tree.world_shape(), tree.obstacle_id) is not None
        assert collide_shapes(above_trunk, tree.world_shape(), tree.obstacle_id) is None

        rock_position = placements["rock"].ground_position
        rock = obstacles["object:rock"]
        at_rock = CircleShape(player_radius, Vector2(rock_position.x, rock_position.y))
        assert collide_shapes(at_rock, rock.world_shape(), rock.obstacle_id) is not None
        assert "object:bush" not in obstacles
    finally:
        pygame.quit()
