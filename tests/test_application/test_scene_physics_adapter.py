"""Scene placement collision metadata is projected into native map physics."""
from pathlib import Path

from application.content_loader import load_content_package
from application.scene_physics_adapter import build_scene_object_obstacles
from core.domain.physics import ConvexPolygonShape
from core.domain.spatial import HexCoord, WorldPoint, axial_to_world_point


ROOT = Path(__file__).resolve().parents[2]
PACKAGE_ROOT = ROOT / "content" / "demo_eldoria"


def test_authored_tree_placements_produce_independent_static_colliders():
    package = load_content_package(PACKAGE_ROOT)
    map_definition = package.hex_map_definitions["starting_valley"]

    obstacles = build_scene_object_obstacles(
        PACKAGE_ROOT, map_definition, 32.0,
    )

    assert len(obstacles) == 8
    assert len({item.obstacle_id for item in obstacles}) == len(obstacles)
    assert all(item.map_id == "starting_valley" for item in obstacles)
    assert all(isinstance(item.shape, ConvexPolygonShape) for item in obstacles)


def test_scene_collision_is_separate_from_visual_sprite_bounds():
    package = load_content_package(PACKAGE_ROOT)
    map_definition = package.hex_map_definitions["starting_valley"]
    obstacles = build_scene_object_obstacles(
        PACKAGE_ROOT, map_definition, 32.0,
    )
    first = obstacles[0]
    expected = axial_to_world_point(HexCoord(-3, 0), 32.0)
    assert first.position == expected
    xs = [point.x for point in first.shape.vertices]
    ys = [point.y for point in first.shape.vertices]
    assert max(xs) - min(xs) == 16
    assert max(ys) - min(ys) == 14


def test_absent_package_has_no_implicit_presentation_colliders():
    package = load_content_package(PACKAGE_ROOT)
    map_definition = package.hex_map_definitions["starting_valley"]
    assert build_scene_object_obstacles(None, map_definition) == ()
