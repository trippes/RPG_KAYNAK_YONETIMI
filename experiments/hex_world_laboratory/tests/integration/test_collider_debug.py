"""Collider debug overlay integration tests."""
import os
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
import pygame
from hex_world_lab.camera import Viewport, WorldScreenTransform
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering import CircleVisual, ColliderVisual, PygameWorldRenderer, RenderDebugOptions, WorldRenderSnapshot


def test_collider_overlay_is_separate_and_toggleable():
    pygame.init()
    try:
        collider=ColliderVisual("test-circle",CircleVisual(WorldPoint(0,0),10),"obstacle")
        base=dict(cells=(),circles=(),polygons=(),boundaries=(),house_lines=(),
                  actor_position=WorldPoint(1000,1000),actor_radius=1,colliders=(collider,))
        transform=WorldScreenTransform(Viewport(100,100),WorldPoint(0,0),1)
        layout=HexLayout(HexOrientation.FLAT_TOP,10)
        renderer=PygameWorldRenderer()
        normal=pygame.Surface((100,100))
        debug=pygame.Surface((100,100))
        renderer.render(normal,WorldRenderSnapshot(**base),layout,transform)
        renderer.render(debug,WorldRenderSnapshot(**base,debug_options=RenderDebugOptions(show_collider_debug=True)),layout,transform)
        assert normal.get_at((50,50))[:3] == (21,25,34)
        assert any(
            debug.get_at((x, y))[:3] == (235,91,204)
            for x in range(38, 63) for y in range(38, 63)
        )
    finally:
        pygame.quit()
