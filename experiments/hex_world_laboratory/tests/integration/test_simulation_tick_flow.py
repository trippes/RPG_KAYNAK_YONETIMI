"""Integration tests for deterministic simulation tick orchestration."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from hex_world_lab.application.entity_demo import EntityDemo
from hex_world_lab.application.movement_demo import MovementDemo
from hex_world_lab.companions import CompanionCommand
from hex_world_lab.entities.spatial_index import EntityAABB


class FakeClock:
    def __init__(self) -> None:
        self.value = 0.0

    def __call__(self) -> float:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += seconds


class PressedKeys:
    def __init__(self, active: set[int] | None = None) -> None:
        self.active = active or set()

    def __getitem__(self, key: int) -> bool:
        return key in self.active


def make_demo(active_keys: set[int] | None = None):
    clock = FakeClock()
    movement = MovementDemo(
        key_state_provider=lambda: PressedKeys(active_keys),
        clock=clock,
    )
    demo = EntityDemo(movement)
    movement.start()
    return demo, clock


def drain_pending_ticks(demo: EntityDemo) -> None:
    while demo.movement.diagnostics.pending_full_ticks:
        demo.movement.pump()


def test_completed_tick_synchronizes_player_entity_and_spatial_index():
    pygame.init()
    try:
        demo, clock = make_demo()
        clock.advance(1.0 / 60.0)
        diagnostics = demo.movement.pump()
        player = demo.coordinator.registry.require(demo.player_id)
        position = demo.movement.state.position
        bounds = EntityAABB(position.x - 1, position.y - 1, position.x + 1, position.y + 1)
        indexed = demo.coordinator.spatial_index.query(demo.map_id, bounds)
        assert diagnostics.total_ticks == 1
        assert demo.movement.tick_coordinator.last_completed_tick_number == 0
        assert player.transform.location.position == position
        assert demo.player_id in {entity.entity_id for entity in indexed}
    finally:
        pygame.quit()


def test_npcs_resources_and_companion_commands_remain_stationary_for_sixty_ticks():
    pygame.init()
    try:
        demo, clock = make_demo()
        initial_positions = {
            entity_id: demo.coordinator.registry.require(entity_id).transform.location.position
            for entity_id in (*demo.npc_ids, *demo.resource_ids)
        }
        relationship = demo.recruit_guard()
        assert relationship.command is CompanionCommand.FOLLOW
        wait = demo.issue_guard_command(CompanionCommand.WAIT)
        assert wait.wait_position == initial_positions[demo.npc_ids[0]]
        follow = demo.issue_guard_command(CompanionCommand.FOLLOW)
        returned = demo.issue_guard_command(CompanionCommand.RETURN)
        assert wait.command_revision < follow.command_revision < returned.command_revision

        clock.advance(1.0)
        demo.movement.pump()
        drain_pending_ticks(demo)
        final_positions = {
            entity_id: demo.coordinator.registry.require(entity_id).transform.location.position
            for entity_id in (*demo.npc_ids, *demo.resource_ids)
        }
        assert demo.movement.diagnostics.total_ticks == 60
        assert final_positions == initial_positions
        assert demo.coordinator.companions.get_relationship(demo.npc_ids[0]).command is CompanionCommand.RETURN
    finally:
        pygame.quit()


def test_completed_tick_state_is_consistent_across_movement_registry_and_spatial_query():
    pygame.init()
    try:
        demo, clock = make_demo()
        clock.advance(0.25)
        demo.movement.pump()
        drain_pending_ticks(demo)
        position = demo.movement.state.position
        player = demo.coordinator.registry.require(demo.player_id)
        assert player.transform.location.position == position
        area = EntityAABB(position.x - 2, position.y - 2, position.x + 2, position.y + 2)
        candidates = demo.coordinator.spatial_index.query(demo.map_id, area)
        assert demo.player_id in {item.entity_id for item in candidates}
        assert demo.movement.tick_coordinator.last_completed_tick_number == 14
    finally:
        pygame.quit()

def test_three_thousand_six_hundred_ticks_preserve_world_entity_and_spatial_consistency():
    pygame.init()
    try:
        demo, _ = make_demo()
        stationary_ids = (*demo.npc_ids, *demo.resource_ids)
        stationary_before = {
            entity_id: demo.coordinator.registry.require(entity_id).transform.location.position
            for entity_id in stationary_ids
        }
        coordinator = demo.movement.tick_coordinator
        for tick_number in range(3600):
            coordinator.advance_tick(tick_number)

        position = demo.movement.state.position
        player = demo.coordinator.registry.require(demo.player_id)
        area = EntityAABB(position.x - 1, position.y - 1, position.x + 1, position.y + 1)
        indexed = demo.coordinator.spatial_index.query(demo.map_id, area)
        stationary_after = {
            entity_id: demo.coordinator.registry.require(entity_id).transform.location.position
            for entity_id in stationary_ids
        }

        assert coordinator.last_completed_tick_number == 3599
        assert player.transform.location.position == position
        assert demo.player_id in {entity.entity_id for entity in indexed}
        assert stationary_after == stationary_before
    finally:
        pygame.quit()

