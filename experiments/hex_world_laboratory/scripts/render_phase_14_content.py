"""Render Phase 14 vector content profiles and a combined evidence sheet."""

from __future__ import annotations
import argparse
import json
from pathlib import Path
import pygame
from hex_world_lab.rendering.procedural import build_profile_document, render_visual_document


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("artifacts/phase-14"))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    profiles = ("tree", "rock", "bush", "grass", "flower")
    rendered = {}
    manifest = {"phase": 14, "profiles": {}}
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
