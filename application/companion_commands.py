"""Follow/wait command execution for NPC companions."""
from __future__ import annotations

import math

from core.domain.physics import CircleShape, Vector2
from core.domain.spatial import EntityPosition, HexDirection, LocalHexPosition, WorldPoint
from npc import (
    BehaviorState, CompanionCommand, CompanionRegistry, NPCRegistry,
)


class CompanionCommandService:
    FOLLOW_INTERVAL = 0.25
    FOLLOW_DISTANCE = 64.0
    FOLLOW_SPEED = 90.0

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
        self._targets = {}

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
        self._targets.pop(npc_id, None)
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
        self._elapsed.pop(npc_id, None)
        self._targets.pop(npc_id, None)
        return self.registry.set_command(npc_id, command, wait_position)

    def _select_follow_target(self, npc_id, player):
        map_definition = self.runtime.map_definition(player.position.map_id)
        goals = []
        for direction in HexDirection:
            target_cell = LocalHexPosition.from_hex_coord(
                player.position.cell.to_hex_coord().neighbor(direction)
            )
            target = EntityPosition(player.position.map_id, target_cell)
            if not map_definition.has_cell(target_cell) or map_definition.is_blocked(target_cell):
                continue
            if not self.runtime.occupancy.can_enter(target, excluding=npc_id):
                continue
            npc = self.npcs.get(npc_id)
            edge_validator = None
            if self.physics_snapshot is not None:
                edge_validator = lambda source, destination, body=npc.physics_body: (
                    self.physics_snapshot.can_reach_cell(source, destination, body)
                )
            path = self.runtime.path_to(
                npc_id, target_cell, edge_validator=edge_validator,
            )
            if path is not None and len(path) > 1:
                goals.append((len(path), target_cell.q, target_cell.r, path))
        if not goals:
            return None
        return min(goals, key=lambda item: (item[0], item[1], item[2]))[3][1]

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
            npc_id = state.npc_id
            if state.command is not CompanionCommand.FOLLOW:
                self._targets.pop(npc_id, None)
                self._elapsed.pop(npc_id, None)
                continue
            npc = self.npcs.get(npc_id)
            if npc is None or not npc.active or npc.behavior_state is BehaviorState.FLEE:
                self._targets.pop(npc_id, None)
                continue
            try:
                entity = self.runtime.entity(npc_id)
                current = self.runtime.continuous_position(npc_id).point
            except KeyError:
                continue
            if not entity.active or entity.position.map_id != player.position.map_id:
                self._targets.pop(npc_id, None)
                continue
            distance_to_player = math.hypot(
                current.x - player_position.x,
                current.y - player_position.y,
            )
            if distance_to_player <= self.FOLLOW_DISTANCE:
                self._targets.pop(npc_id, None)
                self._elapsed.pop(npc_id, None)
                continue

            elapsed = self._elapsed.get(npc_id, 0.0) + delta_seconds
            if npc_id not in self._targets or elapsed + 1e-12 >= self.FOLLOW_INTERVAL:
                self._targets[npc_id] = self._select_follow_target(npc_id, player)
                elapsed = max(0.0, elapsed - self.FOLLOW_INTERVAL) if elapsed >= self.FOLLOW_INTERVAL else 0.0
            self._elapsed[npc_id] = elapsed

            target_cell = self._targets.get(npc_id)
            if target_cell is None:
                continue

            if self.physics_snapshot is None:
                result = self.runtime.move_to(npc_id, target_cell)
                if result.success:
                    moved.append(npc_id)
                continue

            if self.physics_snapshot.map_id != entity.position.map_id:
                continue
            body = npc.physics_body
            if not body.enabled or not isinstance(body.collider, CircleShape):
                continue
            target_point = self.physics_snapshot.cell_center(target_cell)
            dx, dy = target_point.x - current.x, target_point.y - current.y
            distance = math.hypot(dx, dy)
            if distance <= 1e-8:
                self._targets.pop(npc_id, None)
                continue
            step_distance = min(distance, self.FOLLOW_SPEED * delta_seconds)
            displacement = Vector2(
                dx / distance * step_distance,
                dy / distance * step_distance,
            )
            resolution = self.physics_snapshot.resolve_motion(
                current, displacement, body,
            )
            if resolution.unresolved_penetration > 1e-7:
                raise RuntimeError(
                    f"Companion '{npc_id}' follow left unresolved static penetration."
                )
            target = WorldPoint(
                current.x + resolution.applied_displacement.x,
                current.y + resolution.applied_displacement.y,
            )
            if target == current:
                self._targets.pop(npc_id, None)
                continue
            result = self.runtime.set_continuous_position(npc_id, target)
            if result.success:
                moved.append(npc_id)
                if step_distance >= distance - 1e-8:
                    self._targets.pop(npc_id, None)
        return tuple(sorted(set(moved)))


__all__ = ["CompanionCommandService"]
