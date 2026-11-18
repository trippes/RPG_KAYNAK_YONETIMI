from hex_world_lab.environment import (
    EnvironmentalObjectDefinition, EnvironmentalObjectPlacement, EnvironmentalObjectScene,
    environment_debug_visuals, environment_obstacles, environment_sprite_visuals,
)
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.physics import CircleShape
from hex_world_lab.world import MapId, WorldId


def test_adapters_keep_visual_metadata_and_collider_separate():
    world, map_id = WorldId("world"), MapId("map")
    definitions = (
        EnvironmentalObjectDefinition("tree", "tree", (0.5, 0.95), (0.5, 0.8), (0.1, 0.0, 0.8, 0.7), CircleShape(8)),
        EnvironmentalObjectDefinition("bush", "bush", (0.5, 1), (0.5, 0.9), None, None),
    )
    placements = (
        EnvironmentalObjectPlacement("tree-1", "tree", world, map_id, WorldPoint(10, 20)),
        EnvironmentalObjectPlacement("bush-1", "bush", world, map_id, WorldPoint(30, 40)),
    )
    scene = EnvironmentalObjectScene(world, map_id, definitions, placements)
    obstacles = environment_obstacles(scene)
    assert len(obstacles) == 1
    assert obstacles[0].obstacle_id == "object:tree-1"
    assert obstacles[0].shape == CircleShape(8)
    sprites = environment_sprite_visuals(scene, {"tree": (100, 120), "bush": (40, 30)})
    tree = next(item for item in sprites if item.visual_id == "tree-1")
    assert abs(tree.depth_anchor_y - 38.0) < 1e-9
    assert tree.normalized_anchor == (0.5, 0.95)
    debug = environment_debug_visuals(scene, {"tree": (100, 120), "bush": (40, 30)})
    tree_debug = next(item for item in debug if item.instance_id == "tree-1")
    assert tree_debug.visual_bounds == (WorldPoint(-40, 14), WorldPoint(60, 134))
    assert tree_debug.canopy_bounds is not None
