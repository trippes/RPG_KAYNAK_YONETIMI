"""Generate repeatable Phase 12 environmental-object visual acceptance scenes."""
from __future__ import annotations

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from dataclasses import replace
from pathlib import Path
import argparse
import pygame

from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.rendering import RenderDebugOptions


def render_scenes(output_dir: str | Path) -> tuple[Path, ...]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pygame.init()
    try:
        demo = EntityDemo()
        surface = pygame.Surface((960, 640))
        base = demo.build_render_snapshot()
        renderer = demo.movement.renderer
        layout = demo.movement._layout
        transform = demo.movement.camera.transform
        paths = []

        def save(name: str, snapshot, options: RenderDebugOptions) -> None:
            render_snapshot = replace(snapshot, debug_options=options)
            renderer.render(surface, render_snapshot, layout, transform)
            path = output / name
            pygame.image.save(surface, path)
            paths.append(path)

        save("01-environment-scene.png", base, RenderDebugOptions())
        save("02-collider-overlay-f3.png", base, RenderDebugOptions(show_collider_debug=True))
        save("03-anchor-bounds-overlay-f4.png", base, RenderDebugOptions(show_environment_debug=True))

        tree = next(item for item in base.sprites if item.visual_id == "tree")
        player = next(item for item in base.sprites if item.visual_id == "demo-player")
        behind_position = WorldPoint(tree.ground_anchor.x, tree.depth_anchor_y + 20.0)
        behind_sprites = tuple(
            replace(item, ground_anchor=behind_position, depth_anchor_y=behind_position.y)
            if item.visual_id == player.visual_id else item
            for item in base.sprites
        )
        save("04-player-behind-tree.png", replace(base, actor_position=behind_position, sprites=behind_sprites),
             RenderDebugOptions())

        front_position = WorldPoint(tree.ground_anchor.x, tree.depth_anchor_y - 20.0)
        front_sprites = tuple(
            replace(item, ground_anchor=front_position, depth_anchor_y=front_position.y)
            if item.visual_id == player.visual_id else item
            for item in base.sprites
            for _ in (0,)
        )
        save("05-player-in-front-of-tree.png", replace(base, actor_position=front_position, sprites=front_sprites),
             RenderDebugOptions())
        return tuple(paths)
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/phase-12")
    args = parser.parse_args()
    paths = render_scenes(args.output)
    print(f"Generated {len(paths)} Phase 12 visual scenes:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
