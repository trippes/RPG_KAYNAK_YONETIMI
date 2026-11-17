"""Sprite foot-anchor placement tests."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering import PygameWorldRenderer, SpriteVisual, WorldRenderSnapshot
from hex_world_lab.rendering.pygame_world_renderer import SpriteAsset


def test_normalized_foot_anchor_is_blitted_at_transformed_world_point():
    pygame.init()
    try:
        image=pygame.Surface((10,10),pygame.SRCALPHA); image.fill((30,180,90))
        renderer=PygameWorldRenderer({"test":SpriteAsset(image,.5,1.0)})
        snapshot=WorldRenderSnapshot(cells=(),circles=(),polygons=(),boundaries=(),house_lines=(),
            actor_position=WorldPoint(1000,1000),actor_radius=1,
            sprites=(SpriteVisual("test-sprite","test",WorldPoint(0,0),0),))
        surface=pygame.Surface((100,100))
        renderer.render(surface,snapshot,HexLayout(HexOrientation.FLAT_TOP,10),
            WorldScreenTransform(Viewport(100,100),WorldPoint(0,0),1))
        assert surface.get_at((50,49))[:3] == (30,180,90)
        assert surface.get_at((50,50))[:3] != (30,180,90)
    finally: pygame.quit()


def test_sprite_asset_rejects_invalid_normalized_anchor():
    pygame.init()
    try:
        image=pygame.Surface((4,4))
        try: SpriteAsset(image,1.2,1.0)
        except ValueError: pass
        else: raise AssertionError("out-of-range anchor should be rejected")
    finally: pygame.quit()
