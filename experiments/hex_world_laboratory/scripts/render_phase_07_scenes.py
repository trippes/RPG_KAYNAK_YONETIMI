"""Generate repeatable Phase 7 visual acceptance scenes as PNG evidence."""

from __future__ import annotations

import argparse
from dataclasses import replace
from pathlib import Path

import pygame

from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.camera import WorldScreenTransform
from hex_world_lab.geometry import AxialCoord, WorldPoint, axial_to_world
from hex_world_lab.rendering import (
    CellVisual,
    PygameWorldRenderer,
    RenderDebugOptions,
    SpriteVisual,
    WorldRenderSnapshot,
)
from hex_world_lab.rendering.pygame_world_renderer import SpriteAsset
from hex_world_lab.rendering.visibility import VisibleAreaCuller


def render_scenes(output_dir: str | Path) -> tuple[Path, ...]:
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    pygame.init()
    try:
        demo = MovementDemo()
        surface = pygame.Surface((960, 640))
        results: list[Path] = []
        initial_transform = demo.camera.transform
        culler = VisibleAreaCuller()

        def save_demo_scene(name: str, options: RenderDebugOptions,
                            transform: WorldScreenTransform | None = None) -> None:
            snapshot = demo.build_render_snapshot(debug_options=options)
            demo.renderer.render(surface, snapshot, demo._layout, transform or demo.camera.transform)
            path = output / name
            pygame.image.save(surface, path)
            results.append(path)


        def save_culling_scene(name: str, transform: WorldScreenTransform,
                               options: RenderDebugOptions) -> None:
            # A synthetic 41x41 map makes the viewport filter visible even
            # though the interactive demo map is intentionally only 61 cells.
            all_cells = {
                AxialCoord(q, r): None
                for q in range(-20, 21)
                for r in range(-20, 21)
            }
            visible = culler.visible_cells(all_cells, demo._layout, transform)
            base = demo.build_render_snapshot(debug_options=options)
            snapshot = replace(
                base,
                cells=tuple(CellVisual(coord) for coord in visible),
                visible_region=culler.visible_region(transform, demo._layout),
            )
            demo.renderer.render(surface, snapshot, demo._layout, transform)
            path = output / name
            pygame.image.save(surface, path)
            results.append(path)

        save_demo_scene(
            "01-hex-geometry-debug.png",
            RenderDebugOptions(show_cell_centers=True, show_coordinate_labels=True),
        )
        save_culling_scene(
            "02-visible-region-culling.png",
            initial_transform,
            RenderDebugOptions(show_culling_debug=True, show_cell_centers=True),
        )
        save_demo_scene(
            "03-sprite-foot-anchor.png",
            RenderDebugOptions(show_cell_centers=True),
        )
        save_demo_scene(
            "04-collider-physics-overlay.png",
            RenderDebugOptions(show_collider_debug=True, show_cell_centers=True),
        )

        demo.camera.set_zoom(3.0)
        demo.camera.set_center(axial_to_world(AxialCoord(4, 0), demo._layout))
        save_culling_scene(
            "05-viewport-edge-culling.png",
            demo.camera.transform,
            RenderDebugOptions(show_culling_debug=True, show_coordinate_labels=True),
        )

        subpixel_transform = WorldScreenTransform(
            initial_transform.viewport,
            WorldPoint(initial_transform.center.x + 0.35,
                       initial_transform.center.y - 0.35),
            initial_transform.zoom,
        )
        save_demo_scene(
            "06-subpixel-camera-sample.png",
            RenderDebugOptions(show_cell_centers=True),
            subpixel_transform,
        )

        back = pygame.Surface((100, 110), pygame.SRCALPHA)
        pygame.draw.ellipse(back, (46, 112, 67), (8, 0, 84, 82))
        pygame.draw.rect(back, (112, 76, 48), (40, 68, 20, 42))
        front = pygame.Surface((62, 82), pygame.SRCALPHA)
        pygame.draw.circle(front, (220, 183, 145), (31, 15), 12)
        pygame.draw.rect(front, (155, 65, 59), (14, 28, 34, 42), border_radius=7)
        pygame.draw.ellipse(front, (35, 42, 55), (12, 63, 18, 18))
        pygame.draw.ellipse(front, (35, 42, 55), (33, 63, 18, 18))
        depth_renderer = PygameWorldRenderer({
            "back-tree": SpriteAsset(back, 0.5, 1.0),
            "front-actor": SpriteAsset(front, 0.5, 1.0),
        })
        depth_snapshot = WorldRenderSnapshot(
            cells=(), circles=(), polygons=(), boundaries=(), house_lines=(),
            actor_position=WorldPoint(100_000, 100_000), actor_radius=1,
            sprites=(
                SpriteVisual("tree-back", "back-tree", WorldPoint(0, 25), 25, 0),
                SpriteVisual("actor-front", "front-actor", WorldPoint(0, -10), -10, 1),
            ),
        )
        depth_renderer.render(
            surface, depth_snapshot, demo._layout,
            WorldScreenTransform(demo.camera.transform.viewport, WorldPoint(0, 0), 1.0),
        )
        depth_path = output / "07-y-sort-depth-order.png"
        pygame.image.save(surface, depth_path)
        results.append(depth_path)
        return tuple(results)
    finally:
        pygame.quit()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="artifacts/phase-07")
    args = parser.parse_args()
    paths = render_scenes(args.output)
    print(f"Generated {len(paths)} Phase 7 visual scenes:")
    for path in paths:
        print(path)


if __name__ == "__main__":
    main()
