"""Render-purity and read-only snapshot guarantees for EntityDemo."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.companions import CompanionCommand
from hex_world_lab.entities.spatial_index import EntityAABB
from hex_world_lab.movement import MovementIntent, Vector2


def test_render_snapshot_and_render_do_not_mutate_authoritative_entity_state():
    pygame.init()
    try:
        demo = EntityDemo()
        demo.recruit_guard()
        demo.issue_guard_command(CompanionCommand.WAIT)
        records_before = demo.coordinator.registry.all_entities()
        relationships_before = demo.coordinator.companions.all_relationships()
        area = EntityAABB(-500, -500, 500, 500)
        spatial_before = demo.coordinator.spatial_index.query(demo.map_id, area)
        player_before = demo.coordinator.registry.require(demo.player_id)

        # Simulate a state change outside the tick pipeline. Rendering must not
        # perform the old render-time entity synchronization as a side effect.
        demo.movement.movement_system.step(0, MovementIntent(direction=Vector2(1, 0)))
        movement_position = demo.movement.state.position
        assert movement_position != player_before.transform.location.position

        first = demo.build_render_snapshot()
        second = demo.build_render_snapshot()
        demo.render(pygame.Surface((960, 640)), 60.0)

        assert first == second
        assert demo.coordinator.registry.all_entities() == records_before
        assert demo.coordinator.companions.all_relationships() == relationships_before
        assert demo.coordinator.spatial_index.query(demo.map_id, area) == spatial_before
        assert demo.coordinator.registry.require(demo.player_id) == player_before
        assert demo.coordinator.registry.require(demo.player_id).transform.location.position != movement_position
    finally:
        pygame.quit()


def test_rendering_repeatedly_does_not_advance_simulation_ticks():
    pygame.init()
    try:
        demo = EntityDemo()
        demo.movement.start()
        before = demo.movement.tick_pump.diagnostics
        for _ in range(5):
            demo.build_render_snapshot()
            demo.render(pygame.Surface((960, 640)), 60.0)
        assert demo.movement.tick_pump.diagnostics == before
        assert demo.movement.tick_coordinator.last_completed_tick_number is None
    finally:
        pygame.quit()
