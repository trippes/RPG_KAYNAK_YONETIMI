"""Launch the interactive Phase 9 player/NPC/resource acceptance scene."""
from __future__ import annotations
import os
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
import pygame
from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.rendering import RenderDebugOptions

def main()->int:
    pygame.init()
    screen=pygame.display.set_mode((960,640),pygame.RESIZABLE)
    pygame.display.set_caption("Eldoria — Phase 9 Entity Laboratory")
    clock=pygame.time.Clock()
    demo=EntityDemo()
    demo.movement.start()
    running=True
    show_colliders=True
    while running:
        delta=min(clock.tick(120)/1000.0,0.1)
        for event in pygame.event.get():
            if event.type==pygame.QUIT:
                running=False
                continue
            demo.handle_event(event)
            if event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:
                    running=False
                elif event.key==pygame.K_F3:
                    show_colliders=not show_colliders
        demo.movement.pump()
        demo.movement.update_camera(delta)
        demo.render(screen,clock.get_fps(),
            RenderDebugOptions(show_hex_edges=True,show_collider_debug=show_colliders))
        pygame.display.flip()
    pygame.quit()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
