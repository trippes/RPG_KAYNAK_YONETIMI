"""Tests for map-scoped hex and object collision geometry."""

import pytest

from hex_world_lab.geometry import (
    AxialCoord, HexLayout, HexOrientation, WorldPoint, axial_to_world,
)
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics import CircleShape, ConvexPolygonShape
from hex_world_lab.physics.hex_geometry import (
    BoundaryPolicy, build_hex_map_collision_geometry,
)
from hex_world_lab.physics.obstacle import ObstacleDefinition
from hex_world_lab.world import (
    CellAddress, HexCellData, HexMapDefinition, HexWorld, MapId,
    MapNotLoadedError, UnknownMapError, WorldId,
)


def make_world(orientation=HexOrientation.FLAT_TOP, cells=None):
    world_id = WorldId("world")
    map_id = MapId("map")
    world = HexWorld(world_id)
    world.register_map(map_id, "Test map")
    definition = HexMapDefinition(
        world_id, map_id, "Test map",
        HexLayout(orientation, radius=2.0, origin=WorldPoint(10.0, -4.0)),
        cells if cells is not None else {
            AxialCoord(0, 0): HexCellData("grass", True, True),
            AxialCoord(1, 0): HexCellData("grass", True, False),
        },
    )
    world.load_map(definition)
    return world, map_id, definition


@pytest.mark.parametrize("orientation", [HexOrientation.FLAT_TOP, HexOrientation.POINTY_TOP])
def test_cell_obstacle_uses_exact_six_hex_vertices(orientation):
    world, map_id, definition = make_world(orientation)
    geometry = build_hex_map_collision_geometry(world.view, world.runtime, map_id)

    assert len(geometry.obstacles) == 1
    obstacle = geometry.obstacles[0]
    assert obstacle.obstacle_id == "cell:0:0"
    assert isinstance(obstacle.shape, ConvexPolygonShape)
    assert len(obstacle.shape.vertices) == 6
    world_shape = obstacle.world_shape()
    expected_center = axial_to_world(AxialCoord(0, 0), definition.layout)
    assert world_shape.vertices[0] == Vector2(
        expected_center.x + obstacle.shape.vertices[0].x,
        expected_center.y + obstacle.shape.vertices[0].y,
    )


@pytest.mark.parametrize("orientation", [HexOrientation.FLAT_TOP, HexOrientation.POINTY_TOP])
def test_boundary_edges_follow_real_hex_edges_for_both_layouts(orientation):
    world, map_id, _ = make_world(orientation)
    geometry = build_hex_map_collision_geometry(world.view, world.runtime, map_id)

    # Two adjacent hexes have ten exposed outer edges.
    assert len(geometry.boundary_edges) == 10
    assert len({edge.edge_id for edge in geometry.boundary_edges}) == 10


def test_open_boundary_policy_emits_no_blocking_edges():
    world, map_id, _ = make_world()
    geometry = build_hex_map_collision_geometry(
        world.view, world.runtime, map_id, boundary_policy=BoundaryPolicy.OPEN
    )
    assert geometry.boundary_policy is BoundaryPolicy.OPEN
    assert geometry.boundary_edges == ()


def test_runtime_obstacle_override_is_reflected_and_can_be_removed():
    world, map_id, _ = make_world(cells={
        AxialCoord(0, 0): HexCellData("grass", True, False),
    })
    cell_address = CellAddress(world.world_id, map_id, AxialCoord(0, 0))

    assert build_hex_map_collision_geometry(world.view, world.runtime, map_id).obstacles == ()
    world.runtime.set_obstacle(cell_address, True)
    assert len(build_hex_map_collision_geometry(world.view, world.runtime, map_id).obstacles) == 1
    world.runtime.set_obstacle(cell_address, False)
    assert build_hex_map_collision_geometry(world.view, world.runtime, map_id).obstacles == ()


def test_duplicate_object_obstacle_ids_are_rejected():
    world, map_id, _ = make_world(cells={AxialCoord(0, 0): HexCellData("grass", True, False)})
    item = ObstacleDefinition("tree-1", map_id, CircleShape(0.5), WorldPoint(1.0, 2.0))
    with pytest.raises(ValueError, match="unique"):
        build_hex_map_collision_geometry(
            world.view, world.runtime, map_id, object_obstacles=(item, item)
        )


def test_duplicate_cell_and_object_ids_are_rejected():
    world, map_id, _ = make_world()
    duplicate = ObstacleDefinition(
        "cell:0:0", map_id, CircleShape(0.5), WorldPoint(1.0, 2.0)
    )
    with pytest.raises(ValueError, match="unique"):
        build_hex_map_collision_geometry(
            world.view, world.runtime, map_id, object_obstacles=(duplicate,)
        )


def test_object_circle_and_polygon_obstacles_are_supported():
    world, map_id, _ = make_world(cells={AxialCoord(0, 0): HexCellData("grass", True, False)})
    circle = ObstacleDefinition("tree", map_id, CircleShape(0.4), WorldPoint(2.0, 3.0))
    polygon = ObstacleDefinition(
        "rock", map_id,
        ConvexPolygonShape((Vector2(-1, -1), Vector2(1, -1), Vector2(0, 1))),
        WorldPoint(4.0, 5.0),
    )
    geometry = build_hex_map_collision_geometry(
        world.view, world.runtime, map_id, object_obstacles=(polygon, circle)
    )
    assert [item.obstacle_id for item in geometry.obstacles] == ["rock", "tree"]
    assert geometry.obstacles[1].world_shape() == CircleShape(0.4, Vector2(2.0, 3.0))


def test_unloaded_map_is_rejected_without_automatic_loading():
    world, map_id, _ = make_world()
    world.unload_map(map_id)
    with pytest.raises(MapNotLoadedError):
        build_hex_map_collision_geometry(world.view, world.runtime, map_id)
    assert world.is_loaded(map_id) is False


def test_unknown_map_is_rejected():
    world, _, _ = make_world()
    with pytest.raises(UnknownMapError):
        build_hex_map_collision_geometry(world.view, world.runtime, MapId("missing"))


def test_object_obstacle_cannot_claim_a_different_map():
    world, map_id, _ = make_world(cells={AxialCoord(0, 0): HexCellData("grass", True, False)})
    other = ObstacleDefinition("tree", MapId("other"), CircleShape(0.5), WorldPoint(0, 0))
    with pytest.raises(ValueError, match="belong to the collision map"):
        build_hex_map_collision_geometry(
            world.view, world.runtime, map_id, object_obstacles=(other,)
        )


def test_blocked_boundary_edges_are_exposed_as_real_collision_obstacles():
    world, map_id, _ = make_world()
    geometry = build_hex_map_collision_geometry(world.view, world.runtime, map_id)

    collision_obstacles = geometry.collision_obstacles
    boundary_obstacles = tuple(
        item for item in collision_obstacles if item.obstacle_id.startswith("boundary:")
    )
    assert len(boundary_obstacles) == 10
    assert len(collision_obstacles) == len(geometry.obstacles) + 10
    assert all(item.map_id == map_id for item in boundary_obstacles)
    assert all(len(item.world_shape().vertices) == 4 for item in boundary_obstacles)


def test_open_boundary_policy_has_no_boundary_collision_obstacles():
    world, map_id, _ = make_world()
    geometry = build_hex_map_collision_geometry(
        world.view, world.runtime, map_id, boundary_policy=BoundaryPolicy.OPEN
    )
    assert geometry.collision_obstacles == geometry.obstacles
