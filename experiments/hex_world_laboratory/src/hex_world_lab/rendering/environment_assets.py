"""Register code-generated environmental art with the world renderer."""
from __future__ import annotations

from .procedural_environment import build_environment_surfaces
from .pygame_world_renderer import PygameWorldRenderer, SpriteAsset


def register_environment_assets(renderer: PygameWorldRenderer) -> dict[str, tuple[int, int]]:
    """Generate tree, rock and bush surfaces without loading raster assets."""
    if not isinstance(renderer, PygameWorldRenderer):
        raise TypeError("renderer must be a PygameWorldRenderer")
    surfaces = build_environment_surfaces()
    sizes = {}
    anchors = {"tree": (0.5, 0.94), "rock": (0.5, 0.92), "bush": (0.5, 0.92)}
    for key, surface in surfaces.items():
        renderer.register_sprite_asset(key, SpriteAsset(surface, *anchors[key]))
        sizes[key] = surface.get_size()
    return sizes
