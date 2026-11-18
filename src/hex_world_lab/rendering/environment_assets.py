"""Deterministic visual assets for the isolated environment-object prototype."""
from __future__ import annotations

from pathlib import Path

import pygame

from .pygame_world_renderer import PygameWorldRenderer, SpriteAsset


def register_environment_assets(renderer: PygameWorldRenderer) -> dict[str, tuple[int, int]]:
    """Load the repository's tree data asset and register deterministic rock/bush art.

    The tree PNG is copied into the laboratory assets directory as data. A missing
    or corrupt tree file is an explicit error; it is never silently substituted.
    """
    asset_root = Path(__file__).resolve().parents[3] / "assets"
    tree_path = asset_root / "tree_test.png"
    if not tree_path.is_file():
        raise FileNotFoundError(f"required environmental tree asset is missing: {tree_path}")
    try:
        tree = pygame.image.load(str(tree_path))
    except (pygame.error, OSError) as exc:
        raise RuntimeError(f"required environmental tree asset is invalid: {tree_path}") from exc
    renderer.register_sprite_asset("tree", SpriteAsset(tree, 0.5, 0.94))

    rock = pygame.Surface((48, 36), pygame.SRCALPHA)
    pygame.draw.polygon(rock, (100, 108, 119), ((4, 22), (12, 7), (29, 2), (44, 14), (39, 31), (15, 34)))
    pygame.draw.polygon(rock, (170, 179, 190), ((12, 7), (29, 2), (23, 17), (4, 22)))
    pygame.draw.polygon(rock, (58, 66, 78), ((4, 22), (15, 34), (39, 31), (44, 14)), 2)
    renderer.register_sprite_asset("rock", SpriteAsset(rock, 0.5, 0.92))

    bush = pygame.Surface((62, 44), pygame.SRCALPHA)
    pygame.draw.ellipse(bush, (44, 104, 61), (3, 13, 36, 28))
    pygame.draw.ellipse(bush, (57, 132, 72), (19, 4, 39, 34))
    pygame.draw.ellipse(bush, (83, 158, 83), (9, 7, 29, 27))
    pygame.draw.ellipse(bush, (30, 77, 49), (4, 23, 54, 17), 2)
    renderer.register_sprite_asset("bush", SpriteAsset(bush, 0.5, 0.92))

    return {
        "tree": tree.get_size(),
        "rock": rock.get_size(),
        "bush": bush.get_size(),
    }
