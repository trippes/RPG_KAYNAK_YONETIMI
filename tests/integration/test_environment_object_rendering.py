import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering import (
    EnvironmentDebugVisual, PygameWorldRenderer, RenderDebugOptions,
    SpriteAsset, SpriteVisual, WorldRenderSnapshot,
)


def _snapshot(sprite, debug=()):
    return WorldRenderSnapshot(
        cells=(), circles=(), polygons=(), boundaries=(), house_lines=(),
        actor_position=WorldPoint(10_000, 10_000), actor_radius=1,
        sprites=(sprite,), environment_debug=debug,
        debug_options=RenderDebugOptions(show_environment_debug=bool(debug)),
    )


def test_normalized_anchor_override_is_used_for_environment_sprite():
    pygame.init()
    try:
        image = pygame.Surface((20, 20), pygame.SRCALPHA)
        image.fill((30, 180, 90))
        renderer = PygameWorldRenderer({"tree": SpriteAsset(image, 0.5, 1.0)})
        sprite = SpriteVisual("tree-1", "tree", WorldPoint(0, 0), 0, normalized_anchor=(0.5, 0.5))
        surface = pygame.Surface((100, 100))
        renderer.render(surface, _snapshot(sprite), HexLayout(HexOrientation.FLAT_TOP, 10),
                        WorldScreenTransform(Viewport(100, 100), WorldPoint(0, 0), 1))
        assert surface.get_at((50, 50))[:3] == (30, 180, 90)
        assert surface.get_at((50, 60))[:3] != (30, 180, 90)
    finally:
        pygame.quit()


def test_full_sprite_bounds_keep_visible_canopy_when_ground_anchor_is_offscreen():
    pygame.init()
    try:
        image = pygame.Surface((20, 100), pygame.SRCALPHA)
        image.fill((30, 180, 90))
        renderer = PygameWorldRenderer({"tree": SpriteAsset(image, 0.5, 1.0)})
        sprite = SpriteVisual("tree-1", "tree", WorldPoint(0, -70), -70)
        surface = pygame.Surface((100, 100))
        renderer.render(surface, _snapshot(sprite), HexLayout(HexOrientation.FLAT_TOP, 10),
                        WorldScreenTransform(Viewport(100, 100), WorldPoint(0, 0), 1))
        assert surface.get_at((50, 20))[:3] == (30, 180, 90)
    finally:
        pygame.quit()


def test_fully_offscreen_sprite_is_culled_by_its_visual_bounds():
    pygame.init()
    try:
        image = pygame.Surface((20, 100), pygame.SRCALPHA)
        image.fill((30, 180, 90))
        renderer = PygameWorldRenderer({"tree": SpriteAsset(image, 0.5, 1.0)})
        sprite = SpriteVisual("tree-1", "tree", WorldPoint(0, -170), -170)
        surface = pygame.Surface((100, 100))
        renderer.render(surface, _snapshot(sprite), HexLayout(HexOrientation.FLAT_TOP, 10),
                        WorldScreenTransform(Viewport(100, 100), WorldPoint(0, 0), 1))
        assert surface.get_at((50, 20))[:3] != (30, 180, 90)
    finally:
        pygame.quit()


def test_environment_debug_draws_bounds_and_independent_depth_anchor():
    pygame.init()
    try:
        image = pygame.Surface((30, 40), pygame.SRCALPHA)
        image.fill((30, 180, 90))
        renderer = PygameWorldRenderer({"tree": SpriteAsset(image)})
        sprite = SpriteVisual("tree-1", "tree", WorldPoint(0, 0), 0)
        debug = EnvironmentDebugVisual(
            "tree-1", WorldPoint(0, 0), WorldPoint(0, 8),
            (WorldPoint(-15, -2), WorldPoint(15, 38)),
            (WorldPoint(-12, 8), WorldPoint(12, 32)),
        )
        surface = pygame.Surface((100, 100))
        renderer.render(surface, _snapshot(sprite, (debug,)), HexLayout(HexOrientation.FLAT_TOP, 10),
                        WorldScreenTransform(Viewport(100, 100), WorldPoint(0, 0), 1))
        assert surface.get_at((35, 30))[:3] != (21, 25, 34)
    finally:
        pygame.quit()
