"""Generate deterministic Phase 9 multi-entity visual and state evidence."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
os.environ.setdefault("SDL_VIDEODRIVER","dummy")
os.environ.setdefault("SDL_AUDIODRIVER","dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT","1")
import pygame
from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.companions import CompanionCommand
from hex_world_lab.rendering import RenderDebugOptions

def main()->int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--output",default="artifacts/phase-09")
    args=parser.parse_args()
    output=Path(args.output); output.mkdir(parents=True,exist_ok=True)
    pygame.init()
    try:
        demo=EntityDemo()
        demo.recruit_guard()
        demo.issue_guard_command(CompanionCommand.WAIT)
        demo.issue_guard_command(CompanionCommand.RETURN)
        surface=pygame.Surface((960,640))
        demo.render(surface,60.0,RenderDebugOptions(show_hex_edges=True,show_collider_debug=True))
        pygame.image.save(surface,output/"entity-scene.png")
        entities=[]
        for entity in demo.coordinator.registry.all_entities():
            point=entity.transform.location.position
            entities.append({"id":entity.entity_id.value,"kind":entity.kind.value,
                "map":entity.map_id.value,"x":point.x,"y":point.y,"active":entity.is_active})
        relationships=[{"player_id":r.player_id.value,"companion_id":r.companion_id.value,
            "command":r.command.value,"command_revision":r.command_revision,
            "wait_position":None if r.wait_position is None else
                {"x":r.wait_position.x,"y":r.wait_position.y}}
            for r in demo.coordinator.companions.all_relationships()]
        (output/"entity-scene.json").write_text(json.dumps(
            {"entities":entities,"companions":relationships},indent=2),encoding="utf-8")
    finally:
        pygame.quit()
    return 0

if __name__=="__main__":
    raise SystemExit(main())
