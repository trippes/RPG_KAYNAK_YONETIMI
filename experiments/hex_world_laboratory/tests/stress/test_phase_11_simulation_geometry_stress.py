"""Phase 11 stress coverage for fixed ticks, geometry and collision ordering."""
from __future__ import annotations

import random

import pygame

from hex_world_lab.application.demo_tick_pump import DemoTickPump
from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.geometry import (
    AxialCoord,
    HexLayout,
    HexOrientation,
    WorldPoint,
    axial_to_world,
    world_to_axial,
)
from hex_world_lab.movement.vector import Vector2
from hex_world_lab.physics.continuous import resolve_continuous_motion
from hex_world_lab.physics.obstacle import ObstacleDefinition
from hex_world_lab.physics.shapes import CircleShape, ConvexPolygonShape
from hex_world_lab.world.identity import MapId


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


def test_irregular_frame_times_and_long_spikes_preserve_all_fixed_ticks():
    clock = FakeClock()
    completed_ticks: list[int] = []
    pump = DemoTickPump(completed_ticks.append, clock=clock)
    pump.start()

    for elapsed in (0.1, 0.25, 0.15, 0.3, 0.2):
        clock.advance(elapsed)
        diagnostics = pump.pump()
        assert diagnostics.last_frame_tick_count <= 8
        while diagnostics.pending_full_ticks:
            diagnostics = pump.pump()
            assert diagnostics.last_frame_tick_count <= 8

    assert completed_ticks == list(range(60))
    assert pump.diagnostics.total_ticks == 60
    assert pump.diagnostics.pending_full_ticks == 0
    assert abs(pump.diagnostics.time_debt_seconds) < 1e-9


def test_thirty_six_thousand_ticks_preserve_player_and_stationary_entity_state():
    pygame.init()
    try:
        demo = EntityDemo()
        stationary_ids = (*demo.npc_ids, *demo.resource_ids)
        initial_stationary = {
            entity_id: demo.coordinator.registry.require(entity_id).transform.location.position
            for entity_id in stationary_ids
        }
        tick_coordinator = demo.movement.tick_coordinator

        for tick_number in range(36_000):
            tick_coordinator.advance_tick(tick_number)

        position = demo.movement.state.position
        player = demo.coordinator.registry.require(demo.player_id)
        final_stationary = {
            entity_id: demo.coordinator.registry.require(entity_id).transform.location.position
            for entity_id in stationary_ids
        }

        assert tick_coordinator.last_completed_tick_number == 35_999
        assert tick_coordinator.next_tick_number == 36_000
        assert not tick_coordinator.has_pending_tick
        assert player.transform.location.position == position
        assert final_stationary == initial_stationary
    finally:
        pygame.quit()


def test_seeded_hex_center_round_trips_include_negative_and_large_coordinates():
    rng = random.Random(11_503)
    layout = HexLayout(HexOrientation.FLAT_TOP, radius=32.0)
    coordinates = {
        AxialCoord(rng.randint(-10_000, 10_000), rng.randint(-10_000, 10_000))
        for _ in range(5_000)
    }
    coordinates.update(
        AxialCoord(q, r)
        for q, r in (
            (-10_000, -10_000),
            (-10_000, 10_000),
            (10_000, -10_000),
            (10_000, 10_000),
            (-1, 0),
            (0, -1),
            (1, 1),
        )
    )

    for coordinate in coordinates:
        point = axial_to_world(coordinate, layout)
        assert world_to_axial(point, layout) == coordinate


def _wall(obstacle_id: str) -> ObstacleDefinition:
    shape = ConvexPolygonShape((
        Vector2(-0.025, -3.0),
        Vector2(0.025, -3.0),
        Vector2(0.025, 3.0),
        Vector2(-0.025, 3.0),
    ))
    return ObstacleDefinition(obstacle_id, MapId("phase-11-physics"), shape, WorldPoint(0.0, 0.0))


def test_collision_result_is_independent_of_far_obstacle_input_order():
    rng = random.Random(11_504)
    wall = _wall("central-wall")
    decoys = tuple(
        ObstacleDefinition(
            f"decoy-{number:03d}",
            MapId("phase-11-physics"),
            CircleShape(1.0),
            WorldPoint(rng.uniform(500.0, 5_000.0), rng.uniform(500.0, 5_000.0)),
        )
        for number in range(100)
    )
    obstacles = (wall, *decoys)
    start = CircleShape(0.2, Vector2(-10.0, 0.0))
    displacement = Vector2(20.0, 0.0)

    forward = resolve_continuous_motion(start, displacement, obstacles)
    reverse = resolve_continuous_motion(start, displacement, tuple(reversed(obstacles)))

    assert forward == reverse
    assert forward.final_shape.center.x <= -0.225 + 1e-6
    assert forward.impacts
    assert forward.unresolved_penetration <= 1e-7
