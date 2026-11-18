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
    finally:
        pygame.quit()
