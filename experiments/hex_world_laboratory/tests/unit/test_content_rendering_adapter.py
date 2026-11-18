"""Pygame rendering and explicit environment adapter tests."""
import pygame
from hex_world_lab.content.adapters import definition_to_environment, to_environment_scene
from hex_world_lab.content.map_document import MapContentDocument
from hex_world_lab.rendering.procedural import (
    ProceduralSurfaceCache, build_profile_document, render_content_definition, render_visual_document,
)
from hex_world_lab.rendering.environment_assets import register_content_library_assets
from hex_world_lab.rendering.pygame_world_renderer import PygameWorldRenderer
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.world import HexMapDefinition, MapId, WorldId
from hex_world_lab.content import (
    CircleElement, ContentCategory, ContentDefinition, ContentLibrary,
    ContentPlacement, DrawingStyle, Layer, Point, PolygonElement, VisualDocument,
)
from hex_world_lab.content.collision import CircleCollider, ConvexPolygonCollider

def make_visual():
    return VisualDocument(
        (32, 40), (0.5, 0.95), (0.5, 0.8),
        {"green": (30, 120, 50, 255), "brown": (90, 55, 30, 255)},
        (Layer("base", 0, (
            PolygonElement("trunk", (Point(12, 35), Point(15, 12), Point(18, 35)), DrawingStyle(fill="brown")),
            CircleElement("crown", Point(15, 10), 8, DrawingStyle(fill="green")),
        )),),
    )

def make_definition(content_id="tree", collider=None):
    return ContentDefinition(content_id, "Tree", ContentCategory.ENVIRONMENTAL_OBJECT, make_visual(), collider, {"biome": "forest"})

def make_library():
    return ContentLibrary("default", (make_definition(collider=CircleCollider(0, 0, 4)),))


def test_all_five_vector_profiles_render_alpha_surfaces_deterministically():
    for key in ("tree", "rock", "bush", "grass", "flower"):
        first = render_visual_document(build_profile_document(key, seed=7))
        second = render_visual_document(build_profile_document(key, seed=7))
        assert first.get_flags() & pygame.SRCALPHA
        assert pygame.image.tostring(first, "RGBA") == pygame.image.tostring(second, "RGBA")
        assert pygame.mask.from_surface(first).count() > 0

def test_vector_renderer_does_not_derive_or_change_colliders():
    definition = make_definition()
    before = definition.collider
    render_visual_document(definition.visual_document)
    assert definition.collider is before
    adapted = definition_to_environment(definition)
    assert adapted.collider is None

def test_content_scene_adapter_resolves_map_placements_and_explicit_colliders():
    library = make_library()
    map_definition = HexMapDefinition(WorldId("eldoria"), MapId("valley"), "Valley",
        HexLayout(HexOrientation.POINTY_TOP, 1, WorldPoint(0,0)), {})
    document = MapContentDocument(map_definition, (ContentPlacement("tree-1", "tree", 12, 24),))
    scene = to_environment_scene(library, document)
    assert scene.world_id == map_definition.world_id
    assert scene.placements[0].ground_position == WorldPoint(12,24)
    assert scene.definitions[0].collider.radius == 4


def test_content_definition_surface_cache_and_renderer_registration():
    library = make_library()
    cache = ProceduralSurfaceCache(max_entries=4, max_bytes=1_000_000)
    first = render_content_definition(library.definitions[0], cache=cache)
    second = render_content_definition(library.definitions[0], cache=cache)
    assert first is second
    assert cache.stats().hits == 1
    renderer = PygameWorldRenderer()
    sizes = register_content_library_assets(renderer, library, cache=cache)
    assert sizes["tree"] == first.get_size()
