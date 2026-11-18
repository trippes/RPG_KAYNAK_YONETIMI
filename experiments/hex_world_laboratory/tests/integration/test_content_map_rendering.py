"""Integration of content library, map placements, scene and sprite presentation."""
from hex_world_lab.content import ContentPlacement
from hex_world_lab.content.adapters import to_environment_scene
from hex_world_lab.content.map_document import MapContentDocument
from hex_world_lab.environment.presentation import environment_obstacles, environment_sprite_visuals
from hex_world_lab.geometry import HexLayout, HexOrientation, WorldPoint
from hex_world_lab.rendering.environment_assets import register_content_library_assets
from hex_world_lab.rendering.pygame_world_renderer import PygameWorldRenderer
from hex_world_lab.rendering.procedural import ProceduralSurfaceCache, build_builtin_content_library
from hex_world_lab.world import HexMapDefinition, MapId, WorldId

def test_builtin_library_map_placements_reach_existing_render_and_physics_adapters():
    library = build_builtin_content_library(seed=11)
    map_definition = HexMapDefinition(
        WorldId("eldoria"), MapId("content_preview"), "Content Preview",
        HexLayout(HexOrientation.POINTY_TOP, 32, WorldPoint(0, 0)), {},
    )
    placements = tuple(
        ContentPlacement(f"{key}-instance", f"environment.{key}", index * 50.0, 10.0)
        for index, key in enumerate(("tree", "rock", "bush", "grass", "flower"))
    )
    document = MapContentDocument(map_definition, placements)
    scene = to_environment_scene(library, document)
    renderer = PygameWorldRenderer()
    sizes = register_content_library_assets(
        renderer, library, ProceduralSurfaceCache(max_entries=8, max_bytes=2_000_000)
    )
    sprites = environment_sprite_visuals(scene, sizes)
    obstacles = environment_obstacles(scene)
    assert len(sprites) == 5
    assert {item.asset_key for item in sprites} == {item.content_id for item in library.definitions}
    assert obstacles == ()
