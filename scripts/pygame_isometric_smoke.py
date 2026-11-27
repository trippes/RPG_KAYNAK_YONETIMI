"""Headless visual smoke test for Eldoria's isometric world composition."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

from application.content_loader import load_content_package
from core.domain.spatial import HexCoord
from game_ui.world_transform import WorldTransform
from game_ui.world_rendering.depth_sorter import DepthSorter
from game_ui.world_rendering.character_renderer import HexCharacterRenderer
from game_ui.world_rendering.character_sprite_factory import ProceduralCharacterSpriteFactory
from game_ui.world_rendering.scene_object_pipeline import SceneObjectPipeline
from game_ui.world_rendering.terrain_renderer import HexTerrainRenderer


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "content" / "demo_eldoria"
OUTPUT = ROOT / "artifacts" / "eldoria-isometric-smoke.png"
WIDTH, HEIGHT = 960, 600


class RenderContext:
    def __init__(self, pygame_module, surface):
        self.pg = pygame_module
        self.surface = surface
        self.width, self.height = surface.get_size()

    def blit(self, image, position):
        self.surface.blit(image, position)


def main():
    pygame.init()
    pygame.display.set_mode((1, 1))
    surface = pygame.Surface((WIDTH, HEIGHT)).convert()
    renderer = RenderContext(pygame, surface)
    transform = WorldTransform(
        hex_size=32.0,
        viewport_center=(WIDTH / 2, HEIGHT / 2 + 8),
        zoom=0.92,
        projection="isometric",
    )

    package = load_content_package(PACKAGE)
    map_data = json.loads(
        (PACKAGE / "hex_maps" / "starting_valley.json").read_text(encoding="utf-8")
    )
    overrides = {
        (item["q"], item["r"]): item
        for item in map_data.get("cell_overrides", ())
    }
    terrain_ids = [
        overrides.get((q, r), {}).get(
            "terrain_id", map_data.get("default_terrain", "grass")
        )
        for q, r in map_data["valid_cells"]
    ]
    render_started = time.perf_counter()
    terrain = HexTerrainRenderer()
    terrain.begin_frame(renderer, terrain_ids)
    for q, r in map_data["valid_cells"]:
        override = overrides.get((q, r), {})
        cell = SimpleNamespace(q=q, r=r)
        data = SimpleNamespace(
            terrain_id=override.get(
                "terrain_id", map_data.get("default_terrain", "grass")
            ),
            blocked=bool(override.get("blocked", False)),
        )
        terrain.draw_cell(
            renderer, cell, data,
            transform.axial_to_screen(HexCoord(q, r)),
            32.0 * transform.zoom,
        )

    pipeline = SceneObjectPipeline(PACKAGE, pygame, 32.0)
    characters = HexCharacterRenderer()
    factory = ProceduralCharacterSpriteFactory()
    player = factory.create_animator(pygame, palette="player")
    npc = factory.create_animator(pygame, palette="npc")
    player.select(direction="south_east", state="idle")
    npc.select(direction="north_west", state="idle")

    draw_items = []
    viewport = pygame.Rect(0, 0, WIDTH, HEIGHT)
    for obj in pipeline.objects_for_map("starting_valley"):
        foot = transform.world_to_screen(obj.world_x, obj.world_y)
        if pipeline.is_visible(obj, foot, viewport, transform.zoom):
            group = 0 if obj.layer == "underlay" else 2 if obj.layer == "overlay" else 1
            draw_items.append((
                group, foot[1] + obj.depth_offset * transform.zoom,
                f"scene:{obj.object_id}", "scene", obj, foot,
            ))

    starter = package.files["starter"]
    start = starter["world"]["hex_start"]
    player_foot = transform.axial_to_screen(
        HexCoord(start["q"], start["r"]),
    )
    draw_items.append((
        1, player_foot[1], "actor:player", "actor", player, player_foot,
    ))

    for placement in package.gameplay_placements.placements:
        coord = placement.position.cell.to_hex_coord()
        foot = transform.axial_to_screen(coord)
        if placement.kind == "npc":
            draw_items.append((
                1, foot[1], f"actor:{placement.domain_id}",
                "actor", npc, foot,
            ))
        elif placement.kind == "resource_node":
            draw_items.append((
                1, foot[1], f"resource:{placement.domain_id}",
                "resource", placement, foot,
            ))
        elif placement.kind == "container":
            draw_items.append((
                1, foot[1], f"container:{placement.domain_id}",
                "container", placement, foot,
            ))

    ordered_items = DepthSorter.sort_by_depth(
        draw_items,
        lambda item: (item[0], item[1]),
        lambda item: item[2],
    )
    for _, _, _, kind, item, foot in ordered_items:
        if kind == "scene":
            if not pipeline.draw(renderer, item, foot, transform.zoom):
                pipeline.draw_fallback(renderer, item, foot, transform.zoom)
        elif kind == "actor":
            characters.draw_sprite(
                renderer, item.current_frame, foot,
                64.0 * transform.zoom, (0.5, 1.0), {},
            )
        elif kind == "resource":
            center = (round(foot[0]), round(foot[1] - 8 * transform.zoom))
            pygame.draw.circle(
                surface, (68, 133, 88), center, max(5, round(8 * transform.zoom)),
            )
            pygame.draw.circle(
                surface, (190, 220, 156), center, max(2, round(3 * transform.zoom)),
            )
        elif kind == "container":
            chest = pygame.Rect(
                round(foot[0] - 12 * transform.zoom),
                round(foot[1] - 20 * transform.zoom),
                max(12, round(24 * transform.zoom)),
                max(8, round(16 * transform.zoom)),
            )
            pygame.draw.rect(surface, (105, 66, 39), chest)
            pygame.draw.rect(surface, (207, 166, 91), chest, 2)
            pygame.draw.line(
                surface, (207, 166, 91),
                (chest.centerx, chest.top + 2),
                (chest.centerx, chest.bottom - 2), 2,
            )

    render_elapsed_ms = (time.perf_counter() - render_started) * 1000.0
    pygame.draw.rect(
        surface, (20, 28, 38), pygame.Rect(12, 10, 352, 42),
        border_radius=6,
    )
    pygame.draw.rect(
        surface, (90, 112, 139), pygame.Rect(12, 10, 352, 42),
        1, border_radius=6,
    )
    font = pygame.font.Font(None, 28)
    label = font.render("ELDORIA  |  ISOMETRIC WORLD SMOKE", True, (235, 230, 211))
    surface.blit(label, (20, 18))
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(surface, OUTPUT)

    sampled = {
        surface.get_at((x, y))[:3]
        for x in range(0, WIDTH, 24)
        for y in range(0, HEIGHT, 24)
    }
    assert len(pipeline.objects_for_map("starting_valley")) == 15
    assert len(package.gameplay_placements.placements) == 4
    assert len(sampled) > 12, "The composed isometric scene appears blank."
    assert OUTPUT.is_file() and OUTPUT.stat().st_size > 10_000
    print(
        f"Isometric render smoke passed: {len(pipeline.objects_for_map('starting_valley'))} "
        f"scene objects, {len(package.gameplay_placements.placements)} gameplay placements, "
        f"{pipeline.loaded_asset_count} assets, {len(sampled)} sampled colors, "
        f"{render_elapsed_ms:.2f} ms composition time."
    )
    pygame.quit()


if __name__ == "__main__":
    main()
