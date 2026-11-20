"""Follow/wait command execution for NPC companions."""
from __future__ import annotations

import math

from core.domain.spatial import EntityPosition, HexDirection, LocalHexPosition
from npc import (
    BehaviorState, CompanionCommand, CompanionRegistry, NPCRegistry,
)


class CompanionCommandService:
    FOLLOW_INTERVAL = 0.25
    FOLLOW_DISTANCE = 64.0

    def __init__(
        self,
        runtime,
        npcs: NPCRegistry,
        registry: CompanionRegistry,
        player_id: str,
        *,
        physics_snapshot=None,
    ):
        if runtime is None:
            raise TypeError("runtime is required.")
        if not isinstance(npcs, NPCRegistry):
            raise TypeError("npcs must be an NPCRegistry.")
        if not isinstance(registry, CompanionRegistry):
            raise TypeError("registry must be a CompanionRegistry.")
        if not isinstance(player_id, str) or not player_id.strip():
            raise ValueError("player_id must be a non-empty string.")
        self.runtime = runtime
        self.npcs = npcs
        self.registry = registry
        self.player_id = player_id
        self.physics_snapshot = physics_snapshot
        self._elapsed = {}

    def enlist(self, npc_id: str):
        npc = self.npcs.get(npc_id)
        if npc is None:
            raise KeyError(f"NPC not found: {npc_id}")
        entity = self.runtime.entity(npc_id)
        if entity.kind != "npc":
            raise ValueError("Only NPC entities can join the companion roster.")
        return self.registry.add(npc_id)

    def dismiss(self, npc_id: str):
        self._elapsed.pop(npc_id, None)
        return self.registry.remove(npc_id)

    def command(self, npc_id: str, command: CompanionCommand | str):
        state = self.registry.get(npc_id)
        if state is None:
            raise KeyError(f"Companion not found: {npc_id}")
        command = CompanionCommand(command)
        wait_position = (
            self.runtime.continuous_position(npc_id)
            if command is CompanionCommand.WAIT else None
        )
        return self.registry.set_command(npc_id, command, wait_position)

    def tick(self, delta_seconds: float) -> tuple[str, ...]:
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, (int, float)):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds) or delta_seconds < 0:
            raise ValueError("delta_seconds must be finite and non-negative.")
        if delta_seconds == 0:
            return ()
        player = self.runtime.entity(self.player_id)
        player_position = self.runtime.continuous_position(self.player_id).point
        moved = []

        for state in self.registry.all():
            if state.command is not CompanionCommand.FOLLOW:
                continue
            npc = self.npcs.get(state.npc_id)
            if npc is None or not npc.active or npc.behavior_state is BehaviorState.FLEE:
                continue
            try:
                entity = self.runtime.entity(state.npc_id)
                current = self.runtime.continuous_position(state.npc_id).point
            except KeyError:
                continue
            if not entity.active or entity.position.map_id != player.position.map_id:
                continue
            if math.hypot(
                current.x - player_position.x,
                current.y - player_position.y,
            ) <= self.FOLLOW_DISTANCE:
                continue

            elapsed = self._elapsed.get(state.npc_id, 0.0) + delta_seconds
            if elapsed < self.FOLLOW_INTERVAL:
                self._elapsed[state.npc_id] = elapsed
                continue
            self._elapsed[state.npc_id] = elapsed - self.FOLLOW_INTERVAL

            map_definition = self.runtime.map_definition(player.position.map_id)
            goals = []
            for direction in HexDirection:
                target_cell = LocalHexPosition.from_hex_coord(
                    player.position.cell.to_hex_coord().neighbor(direction)
                )
                target = EntityPosition(player.position.map_id, target_cell)
                if not map_definition.has_cell(target_cell) or map_definition.is_blocked(target_cell):
                    continue
                if not self.runtime.occupancy.can_enter(target, excluding=state.npc_id):
                    continue
                edge_validator = None
                if self.physics_snapshot is not None:
                    edge_validator = lambda source, destination, body=npc.physics_body: (
                        self.physics_snapshot.can_reach_cell(source, destination, body)
                    )
                path = self.runtime.path_to(
                    state.npc_id, target_cell, edge_validator=edge_validator,
                )
                if path is not None and len(path) > 1:
                    goals.append((len(path), target_cell.q, target_cell.r, path))
            if not goals:
                continue
            path = min(goals, key=lambda item: (item[0], item[1], item[2]))[3]
            result = self.runtime.move_to(state.npc_id, path[1])
            if result.success:
                moved.append(state.npc_id)
        return tuple(moved)


__all__ = ["CompanionCommandService"]
