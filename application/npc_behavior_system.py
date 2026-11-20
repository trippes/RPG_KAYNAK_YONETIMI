"""Deterministic fixed-step NPC patrol orchestration."""
from __future__ import annotations

import math

from npc import BehaviorState, NPCRegistry
from .dynamic_actor_collision import DynamicActorCollisionResolver


class NPCBehaviorSystem:
    """Advance content-authored patrol routes through HexWorldRuntime pathfinding.

    Route definitions belong to NPC content; route progress belongs to the
    HexWorldRuntime snapshot. Static collision is checked for each path edge,
    and accepted cell changes are committed by the runtime's occupancy owner.
    """

    def __init__(self, npcs: NPCRegistry, runtime, physics_snapshot):
        if not isinstance(npcs, NPCRegistry):
            raise TypeError("npcs must be an NPCRegistry.")
        if runtime is None:
            raise TypeError("runtime is required.")
        self._npcs = npcs
        self._runtime = runtime
        self._physics_snapshot = physics_snapshot
        self._elapsed: dict[str, float] = {}

    def step(self, delta_seconds: float) -> tuple[str, ...]:
        if isinstance(delta_seconds, bool) or not isinstance(delta_seconds, (int, float)):
            raise TypeError("delta_seconds must be a real number.")
        if not math.isfinite(delta_seconds) or delta_seconds < 0:
            raise ValueError("delta_seconds must be finite and non-negative.")
        if delta_seconds == 0:
            return ()

        moved = []
        for npc in self._npcs.all():
            if (
                not npc.active
                or npc.behavior_state is not BehaviorState.PATROL
                or len(npc.patrol_route) < 2
            ):
                self._elapsed.pop(npc.npc_id, None)
                continue
            try:
                entity = self._runtime.entity(npc.npc_id)
            except KeyError:
                continue
            if entity.kind != "npc" or not entity.active:
                continue

            elapsed = self._elapsed.get(npc.npc_id, 0.0) + delta_seconds
            if elapsed < npc.patrol_interval_seconds:
                self._elapsed[npc.npc_id] = elapsed
                continue
            self._elapsed[npc.npc_id] = elapsed % npc.patrol_interval_seconds

            edge_validator = None
            if self._physics_snapshot is not None:
                edge_validator = lambda source, destination, body=npc.physics_body: (
                    self._physics_snapshot.can_reach_cell(source, destination, body)
                )
            result = self._runtime.patrol(
                npc.npc_id, npc.patrol_route, edge_validator=edge_validator,
            )
            if result.success:
                moved.append(npc.npc_id)

        if self._physics_snapshot is not None:
            moved.extend(DynamicActorCollisionResolver(
                self._runtime, self._physics_snapshot,
            ).resolve_npc_pairs({
                npc.npc_id: npc.physics_body
                for npc in self._npcs.all()
                if npc.active and npc.physics_body is not None
            }))
        return tuple(sorted(set(moved)))


__all__ = ["NPCBehaviorSystem"]
