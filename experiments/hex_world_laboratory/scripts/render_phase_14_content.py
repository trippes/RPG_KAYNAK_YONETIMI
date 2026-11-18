"""Render Phase 14 vector content profiles and a combined evidence sheet."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pygame

from hex_world_lab.content.adapters import to_environment_scene
from hex_world_lab.content.map_document import MapContentDocument
from hex_world_lab.content.placement import ContentPlacement
from hex_world_lab.environment.presentation import environment_sprite_visuals
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering.environment_assets import register_content_library_assets
from hex_world_lab.rendering.procedural import (
    build_builtin_content_library,
    build_profile_document,
    render_visual_document,
)
from hex_world_lab.rendering.pygame_world_renderer import PygameWorldRenderer
from hex_world_lab.world import HexMapDefinition, MapId, WorldId


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/phase-14"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    profiles = ("tree", "rock", "bush", "grass", "flower")
    library = build_builtin_content_library(seed=17)
    map_definition = HexMapDefinition(
        WorldId("eldoria"),
        MapId("phase14_preview"),
        "Phase 14 Preview",
        HexLayout(HexOrientation.POINTY_TOP, 32, WorldPoint(0, 0)),
        {},
    )
    placements = tuple(
        ContentPlacement(f"{key}-preview", f"environment.{key}", index * 140 + 80, 80)
        for index, key in enumerate(profiles)
    )
    map_document = MapContentDocument(map_definition, placements)
    scene = to_environment_scene(library, map_document)
    renderer = PygameWorldRenderer()
    asset_sizes = register_content_library_assets(renderer, library)
    sprite_visuals = environment_sprite_visuals(scene, asset_sizes)
    rendered = {}
    manifest = {
        "phase": 14,
        "profiles": {},
        "integrated_scene": {
            "library_id": library.library_id,
            "map_id": map_definition.map_id.value,
            "placement_count": len(scene.placements),
            "sprite_visuals": [
                {
                    "visual_id": item.visual_id,
                    "asset_key": item.asset_key,
                    "depth_anchor_y": item.depth_anchor_y,
                }
                for item in sprite_visuals
            ],
        },
    }
    for key in profiles:
        document = build_profile_document(key, seed=17)
        surface = render_visual_document(document)
        path = args.output / f"{key}.png"
        pygame.image.save(surface, path)
        rendered[key] = surface
        manifest["profiles"][key] = {
            "size": list(surface.get_size()),
            "ground_anchor": list(document.ground_anchor),
            "depth_anchor": list(document.depth_anchor),
            "layers": len(document.layers),
            "elements": sum(len(layer.elements) for layer in document.layers),
            "generator": dict(document.generator),
        }
    width, height = 640, 440
    sheet = pygame.Surface((width, height), pygame.SRCALPHA, 32)
    positions = {
        "tree": (20, 20),
        "rock": (210, 20),
        "bush": (340, 20),
        "grass": (470, 20),
        "flower": (470, 190),
    }
    for key, surface in rendered.items():
        scaled = pygame.transform.smoothscale(
            surface, (surface.get_width() * 2, surface.get_height() * 2)
        )
        sheet.blit(scaled, positions[key])
    pygame.image.save(sheet, args.output / "profile-sheet.png")
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
