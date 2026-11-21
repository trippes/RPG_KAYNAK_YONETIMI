"""Deterministic fixed-step NPC patrol orchestration."""
from __future__ import annotations

import math

from core.domain.physics import CircleShape, Vector2
from core.domain.spatial import WorldPoint
from npc import BehaviorState, NPCRegistry
from .npc_simulation_metrics import timed_npc_step


class NPCBehaviorSystem:
    """Advance content-authored patrol routes with pathfinding and continuous physics.

    Route definitions belong to NPC content; waypoint progress belongs to
    HexWorldRuntime and is included in the unified hex-world save snapshot.
    """

    def __init__(self, npcs: NPCRegistry, runtime, physics_snapshot):
        if not isinstance(npcs, NPCRegistry):
            raise TypeError("npcs must be an NPCRegistry.")
        if runtime is None:
            raise TypeError("runtime is required.")
        self._npcs = npcs
        self._runtime = runtime
        self._physics_snapshot = physics_snapshot

    @timed_npc_step("npc_patrol")
    def step(self, delta_seconds: float) -> tuple[str, ...]:
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, (int, float)):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds) or delta_seconds < 0:
            raise ValueError("delta_seconds must be finite and non-negative.")
        if delta_seconds == 0:
            return ()

        moved = []
        metrics = getattr(self._runtime, "metrics", None)
        for npc in self._npcs.all():
            if metrics is not None:
                metrics.increment("patrol_registry_scanned")
            if (
                not npc.active
                or npc.behavior_state is not BehaviorState.PATROL
                or len(npc.patrol_route) < 2
            ):
                continue
            if metrics is not None:
                metrics.increment("patrol_eligible")
            try:
                entity = self._runtime.entity(npc.npc_id)
                current = entity.continuous_position.point
            except KeyError:
                continue
            if entity.kind != "npc" or not entity.active:
                continue

            edge_validator = None
            if self._physics_snapshot is not None:
                if self._physics_snapshot.map_id != entity.position.map_id:
                    continue
                def edge_validator(source, destination, body=npc.physics_body):
                    return self._physics_snapshot.can_reach_cell(
                        source, destination, body,
                    )
            waypoint = self._runtime.patrol_target(
                npc.npc_id, npc.patrol_route,
            )
            if entity.position.cell == waypoint:
                # The actor may have crossed into the waypoint hex before
                # reaching its center. Continue the final in-cell movement.
                next_cell = waypoint
            else:
                path = self._runtime.path_to(
                    npc.npc_id, waypoint, edge_validator=edge_validator,
                )
                if path is None or len(path) < 2:
                    continue
                next_cell = path[1]
            if self._physics_snapshot is None:
                result = self._runtime.move_to(npc.npc_id, next_cell)
                if result.success:
                    moved.append(npc.npc_id)
                continue

            body = npc.physics_body
            if not body.enabled or not isinstance(body.collider, CircleShape):
                continue
            target = self._physics_snapshot.cell_center(next_cell)
            dx, dy = target.x - current.x, target.y - current.y
            distance = math.hypot(dx, dy)
            if distance <= 1e-8:
                continue
            # The authored interval is the nominal time to traverse one hex edge.
            edge_distance = math.sqrt(3.0) * self._runtime.HEX_SIZE
            speed = edge_distance / npc.patrol_interval_seconds
            step_distance = min(distance, speed * delta_seconds)
            resolution = self._physics_snapshot.resolve_motion(
                current,
                Vector2(dx / distance * step_distance, dy / distance * step_distance),
                body,
            )
            if resolution.unresolved_penetration > 1e-7:
                raise RuntimeError(
                    f"NPC '{npc.npc_id}' patrol left unresolved static penetration."
                )
            destination = WorldPoint(
                current.x + resolution.applied_displacement.x,
                current.y + resolution.applied_displacement.y,
            )
            if destination == current:
                continue
            result = self._runtime.set_continuous_position(
                npc.npc_id, destination,
            )
            if result.success:
                moved.append(npc.npc_id)

        return tuple(sorted(set(moved)))


__all__ = ["NPCBehaviorSystem"]
