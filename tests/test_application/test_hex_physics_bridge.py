"""Physics projection and cell-step validation tests."""

import pytest

from application.actor_system import WorldActor, WorldActorRegistry
from application.hex_actor_binding import ActorHexBindingService
from application.hex_map_definition import parse_hex_map
from application.hex_physics_bridge import build_hex_physics_snapshot
from application.hex_world_geometry_bridge import local_position_to_world_point, make_lab_layout
from application.hex_world_runtime import HexWorldRuntime
from core.domain.spatial import (
    EntityPosition,
    HexDirection,
    LocalHexPosition,
    MovementFailureReason,
)
from core.foundation import WorldId
from hex_world_lab.geometry import WorldPoint
from hex_world_lab.physics import (
    BodyDefinition,
    BoundaryPolicy,
    CircleShape,
    ObstacleDefinition,
)
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.world.identity import MapId


def make_map(
    map_id="corridor",
    *,
    blocked_cells=(),
    landmarks=(),
    valid_cells=((0, 0), (1, 0), (2, 0), (0, 1)),
):
    return parse_hex_map({
        "schema_version": 2,
        "map_id": map_id,
        "name": "Test Map",
        "geometry": {
            "type": "hex_axial",
            "orientation": "pointy_top",
            "coordinate_system": "axial",
        },
        "terrain_ids": ["grass"],
        "default_terrain": "grass",
        "valid_cells": [list(cell) for cell in valid_cells],
        "cell_overrides": [
            {"q": q, "r": r, "blocked": True}
            for q, r in blocked_cells
        ],
        "landmarks": list(landmarks),
    })


def make_body(radius=4.0):
    return BodyDefinition(
        "player-body",
        CircleShape(radius, Vector2(0.0, 0.0)),
    )


def test_core_map_blocked_cells_and_nonwalkable_landmarks_become_lab_obstacles():
    map_definition = make_map(
        blocked_cells=((2, 0),),
        landmarks=(
            {
                "id": "old-tree",
                "name": "Old Tree",
                "position": [0, 1],
                "walkable": False,
            },
        ),
    )
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        make_lab_layout(32.0),
    )

    obstacles_by_id = {item.obstacle_id: item for item in snapshot.geometry.obstacles}
    assert "cell:2:0" in obstacles_by_id
    assert "cell:1:-1" in obstacles_by_id
    assert obstacles_by_id["cell:2:0"].source_cell.world_id.value == "eldoria"
    assert obstacles_by_id["cell:2:0"].source_cell.map_id.value == "corridor"
    assert snapshot.geometry.boundary_edges
    assert snapshot.map_id == "corridor"


def test_open_boundary_policy_does_not_create_perimeter_collision_walls():
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        make_map(valid_cells=((0, 0), (1, 0))),
        make_lab_layout(32.0),
        boundary_policy=BoundaryPolicy.OPEN,
    )
    assert snapshot.geometry.boundary_edges == ()
    assert snapshot.geometry.collision_obstacles == ()


def test_physics_snapshot_rejects_a_layout_with_different_map_identity():
    with pytest.raises(ValueError, match="different map"):
        from application.hex_physics_bridge import HexPhysicsSnapshot
        from hex_world_lab.physics import HexMapCollisionGeometry

        HexPhysicsSnapshot(
            WorldId("eldoria"),
            make_map("corridor"),
            make_lab_layout(32.0),
            HexMapCollisionGeometry(
                MapId("another-map"),
                (),
                (),
                BoundaryPolicy.OPEN,
            ),
        )


def test_clear_center_to_center_step_is_physically_reachable():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    layout = make_lab_layout(32.0)
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        layout,
    )
    result = snapshot.resolve_cell_step(
        LocalHexPosition(0, 0),
        LocalHexPosition(1, 0),
        make_body(),
    )

    start = local_position_to_world_point(LocalHexPosition(0, 0), layout)
    finish = local_position_to_world_point(LocalHexPosition(1, 0), layout)
    assert result.applied_displacement.x == pytest.approx(finish.x - start.x)
    assert result.applied_displacement.y == pytest.approx(finish.y - start.y)
    assert snapshot.can_reach_cell(
        LocalHexPosition(0, 0),
        LocalHexPosition(1, 0),
        make_body(),
    )


def test_static_obstacle_on_step_path_prevents_full_cell_transition():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    layout = make_lab_layout(32.0)
    start = local_position_to_world_point(LocalHexPosition(0, 0), layout)
    finish = local_position_to_world_point(LocalHexPosition(1, 0), layout)
    rock = ObstacleDefinition(
        "rock-on-path",
        MapId("corridor"),
        CircleShape(8.0, Vector2(0.0, 0.0)),
        WorldPoint((start.x + finish.x) / 2, (start.y + finish.y) / 2),
    )
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        layout,
        object_obstacles=(rock,),
    )

    assert not snapshot.can_reach_cell(
        LocalHexPosition(0, 0),
        LocalHexPosition(1, 0),
        make_body(),
    )
    assert snapshot.resolve_cell_step(
        LocalHexPosition(0, 0),
        LocalHexPosition(1, 0),
        make_body(),
    ).impacts


def test_actor_binding_checks_physics_before_committing_hex_occupancy():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    layout = make_lab_layout(32.0)
    start = local_position_to_world_point(LocalHexPosition(0, 0), layout)
    finish = local_position_to_world_point(LocalHexPosition(1, 0), layout)
    rock = ObstacleDefinition(
        "rock-on-path",
        MapId("corridor"),
        CircleShape(8.0, Vector2(0.0, 0.0)),
        WorldPoint((start.x + finish.x) / 2, (start.y + finish.y) / 2),
    )
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        layout,
        object_obstacles=(rock,),
    )

    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime(
        {"corridor": map_definition},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("corridor", LocalHexPosition(0, 0)),
    )

    result = binding.move_to_with_physics(
        "hero",
        LocalHexPosition(1, 0),
        snapshot,
        make_body(),
    )
    assert not result.success
    assert result.reason is MovementFailureReason.PHYSICAL_COLLISION
    assert runtime.entity("hero").position.cell == LocalHexPosition(0, 0)
    assert runtime.occupancy.get("hero").position.cell == LocalHexPosition(0, 0)
    assert actors.get("hero").actor_id == "hero"


def test_clear_physics_step_commits_through_the_existing_hex_runtime():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        make_lab_layout(32.0),
    )
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime(
        {"corridor": map_definition},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("corridor", LocalHexPosition(0, 0)),
    )

    result = binding.move_to_with_physics(
        "hero",
        LocalHexPosition(1, 0),
        snapshot,
        make_body(),
    )
    assert result.success
    assert runtime.entity("hero").position.cell == LocalHexPosition(1, 0)


def test_physics_snapshot_from_another_map_is_rejected_before_move():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    other_snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        make_map("other-map", valid_cells=((0, 0), (1, 0))),
        make_lab_layout(32.0),
    )
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime(
        {"corridor": map_definition},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("corridor", LocalHexPosition(0, 0)),
    )

    with pytest.raises(ValueError, match="different map"):
        binding.move_to_with_physics(
            "hero",
            LocalHexPosition(1, 0),
            other_snapshot,
            make_body(),
        )
    assert runtime.entity("hero").position.cell == LocalHexPosition(0, 0)



def test_physics_snapshot_world_scope_is_checked_before_move():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    foreign_snapshot = build_hex_physics_snapshot(
        WorldId("another-world"),
        map_definition,
        make_lab_layout(32.0),
    )
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime(
        {"corridor": map_definition},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("corridor", LocalHexPosition(0, 0)),
    )

    with pytest.raises(ValueError, match="different world"):
        binding.move_to_with_physics(
            "hero",
            LocalHexPosition(1, 0),
            foreign_snapshot,
            make_body(),
        )
    assert runtime.entity("hero").position.cell == LocalHexPosition(0, 0)


def test_directional_physics_move_uses_the_same_preflight_and_commit_path():
    map_definition = make_map(valid_cells=((0, 0), (1, 0)))
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        map_definition,
        make_lab_layout(32.0),
    )
    actors = WorldActorRegistry()
    actors.add(WorldActor("hero", "eldoria", "player"))
    runtime = HexWorldRuntime(
        {"corridor": map_definition},
        world_id=WorldId("eldoria"),
    )
    binding = ActorHexBindingService(actors, runtime, WorldId("eldoria"))
    binding.register_spatial(
        "hero",
        "player",
        EntityPosition("corridor", LocalHexPosition(0, 0)),
    )

    result = binding.move_with_physics(
        "hero",
        HexDirection.EAST,
        snapshot,
        make_body(),
    )

    assert result.success
    assert runtime.entity("hero").position.cell == LocalHexPosition(1, 0)



def test_physics_snapshot_is_immutable_after_construction():
    snapshot = build_hex_physics_snapshot(
        WorldId("eldoria"),
        make_map(),
        make_lab_layout(32.0),
    )

    with pytest.raises(AttributeError, match="immutable"):
        snapshot._world_id = WorldId("other-world")
