"""Generate visual evidence for the five Phase 13 procedural profiles."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import argparse
from dataclasses import replace
from pathlib import Path

import pygame

from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.rendering.procedural import build_environment_profiles
from hex_world_lab.rendering import RenderDebugOptions


def render_scenes(output_dir: str | Path) -> tuple[Path, ...]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    pygame.init()
    try:
        profiles = build_environment_profiles(seed=17)
        for key, surface in profiles.items():
            path = output / f"profile-{key}.png"
            pygame.image.save(surface, path)
            paths.append(path)

        demo = MovementDemo()
        surface = pygame.Surface((960, 640))
        snapshot = demo.build_render_snapshot()
        renderer = demo.renderer
        layout = demo._layout
        transform = demo.camera.transform
        for name, options in (
            ("integrated-scene.png", RenderDebugOptions()),
            ("collider-overlay-f3.png", RenderDebugOptions(show_collider_debug=True)),
            ("anchor-bounds-overlay-f4.png", RenderDebugOptions(show_environment_debug=True)),
        ):
            renderer.render(
                surface,
                replace(snapshot, debug_options=options),
                layout,
                transform,
            )
            path = output / name
            pygame.image.save(surface, path)
            paths.append(path)

        return tuple(paths)
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/phase-13")
    args = parser.parse_args()
    paths = render_scenes(args.output)
    print(f"Generated {len(paths)} Phase 13 visual evidence files:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
