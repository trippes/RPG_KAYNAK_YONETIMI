"""Register procedural environmental profiles with the world renderer."""

from __future__ import annotations

from hex_world_lab.content.library import ContentLibrary
from hex_world_lab.rendering.procedural import (
    render_content_definition,
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
        renderer.register_sprite_asset(key, SpriteAsset(surface, *PROFILE_DEFINITIONS[key].anchor))
        sizes[key] = surface.get_size()
    return sizes


def register_content_library_assets(
    renderer: PygameWorldRenderer,
    library: ContentLibrary,
    cache: ProceduralSurfaceCache | None = None,
    supersampling: int = 3,
) -> dict[str, tuple[int, int]]:
    """Render and register reusable vector content definitions by stable content ID."""
    if not isinstance(renderer, PygameWorldRenderer):
        raise TypeError("renderer must be a PygameWorldRenderer")
    if not isinstance(library, ContentLibrary):
        raise TypeError("library must be a ContentLibrary")
    sizes = {}
    for definition in library.definitions:
        surface = render_content_definition(definition, cache=cache, supersampling=supersampling)
        anchor = definition.visual_document.ground_anchor
        renderer.register_sprite_asset(definition.content_id, SpriteAsset(surface, *anchor))
        sizes[definition.content_id] = surface.get_size()
    return sizes
