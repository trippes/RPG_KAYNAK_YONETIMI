"""Integration tests for fixed-tick movement with continuous collision."""

import pytest

from hex_world_lab.geometry import WorldPoint
from hex_world_lab.movement import (
    MovementConfig,
    MovementIntent,
    MovementMode,
    MovementState,
    Vector2,
)
from hex_world_lab.physics import (BodyDefinition, CircleShape, ConvexPolygonShape, ObstacleDefinition)
from hex_world_lab.simulation import CollisionAwareMovementSystem
from hex_world_lab.simulation.movement_system import TICK_DELTA_SECONDS
from hex_world_lab.world.identity import MapId


MAP = MapId("map")


def wall(*, x=2.0, half_width=0.25, half_height=3.0, obstacle_id="wall"):
    return ObstacleDefinition(
        obstacle_id,
        MAP,
        ConvexPolygonShape((
            Vector2(-half_width, -half_height),
            Vector2(half_width, -half_height),
            Vector2(half_width, half_height),
            Vector2(-half_width, half_height),
        )),
        WorldPoint(x, 0.0),
    )


def make_system(*, obstacles=(), body_offset=Vector2(0, 0)):
    return CollisionAwareMovementSystem(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementConfig(max_speed=60.0),
        BodyDefinition("player", CircleShape(0.25), local_offset=body_offset),
        obstacles,
    )


def test_collision_aware_system_preserves_fixed_60_tps_movement():
    system = make_system()
    for tick in range(60):
        system.step(tick, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state.position == WorldPoint(60.0, 0.0)
    assert system.next_tick_number == 60
    assert TICK_DELTA_SECONDS == 1.0 / 60.0
    assert system.last_resolution is not None


def test_collision_aware_system_stops_at_wall_and_removes_inward_velocity():
    system = make_system(obstacles=(wall(),))
    for tick in range(5):
        system.step(tick, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state.position.x <= 1.500001
    assert system.state.position.x == pytest.approx(1.5, abs=1e-5)
    assert system.state.velocity.x == pytest.approx(0.0, abs=1e-5)
    assert system.last_resolution is not None
    assert system.last_resolution.impacts


def test_collision_aware_system_slides_along_wall():
    system = make_system(obstacles=(wall(half_height=100.0),))
    for tick in range(60):
        system.step(tick, MovementIntent(Vector2(1.0, 1.0)))
    assert system.state.position.x <= 1.500001
    assert system.state.position.y > 40.0
    assert abs(system.state.velocity.x) <= 1e-5
    assert system.state.velocity.y > 0.0


@pytest.mark.parametrize(
    ("mode", "expected_distance"),
    [
        (MovementMode.NORMAL, 60.0),
        (MovementMode.RUNNING, 90.0),
        (MovementMode.STEALTH, 30.0),
    ],
)
def test_collision_aware_system_preserves_movement_mode_speed_profiles(
    mode, expected_distance
):
    system = make_system()
    for tick in range(60):
        system.step(tick, MovementIntent(Vector2(1.0, 0.0), mode))
    assert system.state.position.x == pytest.approx(expected_distance)
    assert system.state.mode is mode



@pytest.mark.parametrize("mode", [MovementMode.NORMAL, MovementMode.RUNNING, MovementMode.STEALTH])
def test_collision_blocks_normal_running_and_stealth_modes(mode):
    system = make_system(obstacles=(wall(),))
    for tick in range(8):
        system.step(tick, MovementIntent(Vector2(1.0, 0.0), mode))
    assert system.state.position.x == pytest.approx(1.5, abs=1e-5)
    assert system.state.velocity.x == pytest.approx(0.0, abs=1e-5)
    assert system.state.mode is mode


def test_collision_aware_system_resolves_two_wall_corner_contacts():
    vertical = wall(obstacle_id="vertical")
    horizontal = ObstacleDefinition(
        "horizontal",
        MAP,
        ConvexPolygonShape((
            Vector2(-3.0, -0.25),
            Vector2(3.0, -0.25),
            Vector2(3.0, 0.25),
            Vector2(-3.0, 0.25),
        )),
        WorldPoint(0.0, 2.0),
    )
    system = make_system(obstacles=(horizontal, vertical))
    for tick in range(8):
        system.step(tick, MovementIntent(Vector2(1.0, 1.0)))
    assert system.state.position.x <= 1.50001
    assert system.state.position.y <= 1.50001
    assert system.last_resolution is not None
    assert len(system.last_resolution.contacts) >= 1

def test_body_local_offset_is_respected_without_changing_ground_anchor():
    system = make_system(
        obstacles=(wall(x=2.0),),
        body_offset=Vector2(0.5, 0.0),
    )
    for tick in range(5):
        system.step(tick, MovementIntent(Vector2(1.0, 0.0)))
    # The collider center is offset by +0.5, so the ground anchor stops at x=1.0.
    assert system.state.position.x == pytest.approx(1.0, abs=1e-5)


def test_tick_rejection_does_not_mutate_state_or_diagnostics():
    system = make_system()
    original = system.state
    with pytest.raises(ValueError, match="expected tick 0"):
        system.step(1, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state is original
    assert system.next_tick_number == 0
    assert system.last_resolution is None


def test_disabled_body_skips_collision_but_keeps_movement_contract():
    system = CollisionAwareMovementSystem(
        MovementState(WorldPoint(0.0, 0.0)),
        MovementConfig(max_speed=60.0),
        BodyDefinition("player", CircleShape(0.25), enabled=False),
        (wall(),),
    )
    system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state.position == WorldPoint(1.0, 0.0)
    assert system.last_resolution is None


def test_non_circle_body_is_rejected_until_polygon_ccd_is_supported():
    from hex_world_lab.physics import ConvexPolygonShape

    body = BodyDefinition(
        "player",
        ConvexPolygonShape((
            Vector2(-0.5, -0.5), Vector2(0.5, -0.5),
            Vector2(0.5, 0.5), Vector2(-0.5, 0.5),
        )),
    )
    with pytest.raises(TypeError, match="circle body"):
        CollisionAwareMovementSystem(
            MovementState(WorldPoint(0.0, 0.0)),
            MovementConfig(max_speed=60.0),
            body,
        )


def test_failed_collision_resolution_rolls_back_state_tick_and_diagnostics(monkeypatch):
    import hex_world_lab.simulation.collision_aware_movement_system as module

    system = make_system(obstacles=(wall(),))
    original = system.state

    def fail(*args, **kwargs):
        raise RuntimeError("synthetic collision failure")

    monkeypatch.setattr(module, "resolve_continuous_motion", fail)
    with pytest.raises(RuntimeError, match="synthetic collision failure"):
        system.step(0, MovementIntent(Vector2(1.0, 0.0)))
    assert system.state is original
    assert system.next_tick_number == 0
    assert system.last_resolution is None


def test_hex_map_geometry_blocks_movement_at_map_perimeter():
    from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
    from hex_world_lab.physics.hex_geometry import (
        BoundaryPolicy, build_hex_map_collision_geometry,
    )
    from hex_world_lab.world import HexCellData, HexMapDefinition, HexWorld, WorldId

    world_id = WorldId("boundary_world")
    map_id = MapId("boundary_map")
    world = HexWorld(world_id)
    world.register_map(map_id, "Boundary test")
    world.load_map(HexMapDefinition(
        world_id,
        map_id,
        "Boundary test",
        HexLayout(HexOrientation.FLAT_TOP, radius=2.0, origin=WorldPoint(10.0, -4.0)),
        {AxialCoord(0, 0): HexCellData("grass", True, False)},
    ))
    geometry = build_hex_map_collision_geometry(
        world.view, world.runtime, map_id, boundary_policy=BoundaryPolicy.BLOCKED
    )
    system = CollisionAwareMovementSystem(
        MovementState(WorldPoint(10.0, -4.0)),
        MovementConfig(max_speed=600.0),
        BodyDefinition("player", CircleShape(0.25)),
        geometry,
    )

    system.step(0, MovementIntent(Vector2(1.0, 0.0)))

    assert system.map_id == map_id
    assert system.state.position.x < 12.0
    assert 10.5 < system.state.position.x < 12.0


def test_open_hex_map_boundary_allows_movement_outside_map():
    from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
    from hex_world_lab.physics.hex_geometry import (
        BoundaryPolicy, build_hex_map_collision_geometry,
    )
    from hex_world_lab.world import HexCellData, HexMapDefinition, HexWorld, WorldId

    world_id = WorldId("open_boundary_world")
    map_id = MapId("open_boundary_map")
    world = HexWorld(world_id)
    world.register_map(map_id, "Open boundary test")
    world.load_map(HexMapDefinition(
        world_id,
        map_id,
        "Open boundary test",
        HexLayout(HexOrientation.FLAT_TOP, radius=2.0, origin=WorldPoint(10.0, -4.0)),
        {AxialCoord(0, 0): HexCellData("grass", True, False)},
    ))
    geometry = build_hex_map_collision_geometry(
        world.view, world.runtime, map_id, boundary_policy=BoundaryPolicy.OPEN
    )
    system = CollisionAwareMovementSystem(
        MovementState(WorldPoint(10.0, -4.0)),
        MovementConfig(max_speed=600.0),
        BodyDefinition("player", CircleShape(0.25)),
        geometry,
    )

    system.step(0, MovementIntent(Vector2(1.0, 0.0)))

    assert system.state.position.x == pytest.approx(20.0)


def test_movement_system_rejects_wrong_or_mixed_map_obstacles():
    wrong_map = wall()
    with pytest.raises(ValueError, match="movement system map"):
        CollisionAwareMovementSystem(
            MovementState(WorldPoint(0.0, 0.0)),
            MovementConfig(max_speed=60.0),
            BodyDefinition("player", CircleShape(0.25)),
            (wrong_map,),
            map_id=MapId("different_map"),
        )

    other_map_wall = ObstacleDefinition(
        "other_wall",
        MapId("another_map"),
        ConvexPolygonShape((
            Vector2(-0.25, -3.0), Vector2(0.25, -3.0),
            Vector2(0.25, 3.0), Vector2(-0.25, 3.0),
        )),
        WorldPoint(4.0, 0.0),
    )
    with pytest.raises(ValueError, match="different maps"):
        CollisionAwareMovementSystem(
            MovementState(WorldPoint(0.0, 0.0)),
            MovementConfig(max_speed=60.0),
            BodyDefinition("player", CircleShape(0.25)),
            (wrong_map, other_map_wall),
        )


def test_geometry_map_id_cannot_be_overridden_by_constructor():
    from hex_world_lab.physics.hex_geometry import (
        BoundaryPolicy, build_hex_map_collision_geometry,
    )
    from hex_world_lab.geometry import AxialCoord, HexLayout, HexOrientation
    from hex_world_lab.world import HexCellData, HexMapDefinition, HexWorld, WorldId

    world_id = WorldId("geometry_map_world")
    map_id = MapId("geometry_map")
    world = HexWorld(world_id)
    world.register_map(map_id, "Geometry map")
    world.load_map(HexMapDefinition(
        world_id, map_id, "Geometry map",
        HexLayout(HexOrientation.FLAT_TOP, radius=2.0, origin=WorldPoint(0.0, 0.0)),
        {AxialCoord(0, 0): HexCellData("grass", True, False)},
    ))
    geometry = build_hex_map_collision_geometry(
        world.view, world.runtime, map_id, boundary_policy=BoundaryPolicy.OPEN
    )
    with pytest.raises(ValueError, match="does not match"):
        CollisionAwareMovementSystem(
            MovementState(WorldPoint(0.0, 0.0)),
            MovementConfig(max_speed=60.0),
            BodyDefinition("player", CircleShape(0.25)),
            geometry,
            map_id=MapId("wrong_map"),
        )
