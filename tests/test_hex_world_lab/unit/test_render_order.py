"""Stable Y-sort tests for world sprites."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering import PygameWorldRenderer, SpriteVisual, WorldRenderSnapshot
from hex_world_lab.rendering.pygame_world_renderer import SpriteAsset


def _snapshot(sprites):
    return WorldRenderSnapshot(cells=(), circles=(), polygons=(), boundaries=(), house_lines=(),
        actor_position=WorldPoint(1000, 1000), actor_radius=1, sprites=tuple(sprites))


def test_y_sort_draws_higher_world_y_first_and_lower_world_y_last():
    pygame.init()
    try:
        red=pygame.Surface((8,8),pygame.SRCALPHA); red.fill((220,20,20))
        blue=pygame.Surface((8,8),pygame.SRCALPHA); blue.fill((20,20,220))
        renderer=PygameWorldRenderer({"red":SpriteAsset(red,.5,.5),"blue":SpriteAsset(blue,.5,.5)})
        sprites=(SpriteVisual("lower-red","red",WorldPoint(0,0),0),
                 SpriteVisual("upper-blue","blue",WorldPoint(0,0),10))
        surface=pygame.Surface((100,100))
        renderer.render(surface,_snapshot(sprites),HexLayout(HexOrientation.FLAT_TOP,10),
            WorldScreenTransform(Viewport(100,100),WorldPoint(0,0),1))
        assert surface.get_at((50,50))[:3] == (220,20,20)
    finally: pygame.quit()


def test_y_sort_is_independent_of_input_collection_order():
    pygame.init()
    try:
        assets={}
        for key,color in (("a",(200,10,10)),("b",(10,10,200))):
            image=pygame.Surface((6,6),pygame.SRCALPHA); image.fill(color)
            assets[key]=SpriteAsset(image,.5,.5)
        renderer=PygameWorldRenderer(assets)
        a=SpriteVisual("a","a",WorldPoint(0,0),2)
        b=SpriteVisual("b","b",WorldPoint(0,0),8)
        transform=WorldScreenTransform(Viewport(80,80),WorldPoint(0,0),1)
        layout=HexLayout(HexOrientation.POINTY_TOP,10)
        outputs=[]
        for items in ((a,b),(b,a)):
            surface=pygame.Surface((80,80)); renderer.render(surface,_snapshot(items),layout,transform)
            outputs.append(surface.get_at((40,40))[:3])
        assert outputs[0] == outputs[1] == (200,10,10)
    finally: pygame.quit()
