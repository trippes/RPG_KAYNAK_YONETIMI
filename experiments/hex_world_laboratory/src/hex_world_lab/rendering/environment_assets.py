"""Register procedural environmental profiles with the world renderer."""
from __future__ import annotations

from hex_world_lab.rendering.procedural import (
    PROFILE_DEFINITIONS,
    ProceduralSurfaceCache,
    build_environment_profiles,
)
from .pygame_world_renderer import PygameWorldRenderer, SpriteAsset


def register_environment_assets(
    renderer: PygameWorldRenderer,
    cache: ProceduralSurfaceCache | None = None,
    seed: int = 0,
) -> dict[str, tuple[int, int]]:
    """Generate and register all five environment profiles."""
    if not isinstance(renderer, PygameWorldRenderer):
        raise TypeError("renderer must be a PygameWorldRenderer")
    surfaces = build_environment_profiles(seed=seed, cache=cache)
    sizes = {}
    for key, surface in surfaces.items():
        renderer.register_sprite_asset(
            key, SpriteAsset(surface, *PROFILE_DEFINITIONS[key].anchor)
        )
        sizes[key] = surface.get_size()
    return sizes
