"""Subpixel camera motion and final raster quantization tests."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
import pytest
from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering import PygameWorldRenderer, SpriteVisual, WorldRenderSnapshot
from hex_world_lab.rendering.pygame_world_renderer import SpriteAsset


def _snapshot(anchor):
    return WorldRenderSnapshot(cells=(),circles=(),polygons=(),boundaries=(),house_lines=(),
        actor_position=WorldPoint(10000,10000),actor_radius=1,
        sprites=(SpriteVisual("pixel","pixel",anchor,anchor.y),))


def test_subpixel_camera_pan_quantizes_only_at_final_blit_position():
    pygame.init()
    try:
        pixel=pygame.Surface((1,1),pygame.SRCALPHA); pixel.fill((250,220,40))
        renderer=PygameWorldRenderer({"pixel":SpriteAsset(pixel,0.0,0.0)})
        anchor=WorldPoint(0.0,0.0)
        layout=HexLayout(HexOrientation.FLAT_TOP,10)
        viewport=Viewport(40,40)
        observed=[]
        for center_x in (0.0,0.1,0.2,0.3,0.4,0.5,0.6,0.0):
            transform=WorldScreenTransform(viewport,WorldPoint(center_x,0.0),1.0)
            screen=transform.world_to_screen(anchor)
            surface=pygame.Surface((40,40))
            renderer.render(surface,_snapshot(anchor),layout,transform)
            expected=(round(screen.x),round(screen.y))
            assert surface.get_at(expected)[:3] == (250,220,40)
            observed.append(expected)
        assert observed[0] == observed[-1]
        assert anchor == WorldPoint(0.0,0.0)
    finally:
        pygame.quit()


def test_world_to_screen_retains_fractional_precision_before_rasterization():
    transform=WorldScreenTransform(Viewport(100,80),WorldPoint(0.25,-0.25),1.0)
    point=transform.world_to_screen(WorldPoint(0.0,0.0))
    assert point.x == pytest.approx(49.75)
    assert point.y == pytest.approx(40.25)
