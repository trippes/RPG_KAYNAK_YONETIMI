"""NPC aggregate and deterministic registry."""
from __future__ import annotations

from dataclasses import dataclass, field
import math

from core.domain.spatial import LocalHexPosition

from core.domain.physics import CircleShape, PhysicsBodyDefinition

from .behavior import BehaviorController, BehaviorState


@dataclass
class NPC:
    npc_id: str
    name: str
    role: str = "civilian"
    faction_ids: tuple[str, ...] = ()
    behavior: BehaviorController = field(default_factory=BehaviorController)
    active: bool = True
    physics_body: PhysicsBodyDefinition | None = None
    patrol_route: tuple[LocalHexPosition, ...] = ()
    patrol_interval_seconds: float = 0.5

    def __post_init__(self):
        for value, name in ((self.npc_id, "npc_id"), (self.name, "name"), (self.role, "role")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty.")
        self.faction_ids = tuple(self.faction_ids)
        route = tuple(self.patrol_route)
        if any(not isinstance(point, LocalHexPosition) for point in route):
            raise TypeError("patrol_route must contain LocalHexPosition values.")
        if route and len(route) < 2:
            raise ValueError("patrol_route must contain at least two waypoints.")
        self.patrol_route = route
        interval = self.patrol_interval_seconds
        if isinstance(interval, bool) or not isinstance(interval, (int, float)):
            raise TypeError("patrol_interval_seconds must be a positive finite number.")
        if not math.isfinite(interval) or interval <= 0:
            raise ValueError("patrol_interval_seconds must be a positive finite number.")
        self.patrol_interval_seconds = float(interval)
        if not isinstance(self.behavior, BehaviorController):
            raise TypeError("behavior must be BehaviorController.")
        if self.physics_body is None:
            self.physics_body = PhysicsBodyDefinition(
                body_id=self.npc_id,
                collider=CircleShape(radius=4.0),
            )
        elif not isinstance(self.physics_body, PhysicsBodyDefinition):
            raise TypeError("physics_body must be PhysicsBodyDefinition or None.")
        elif self.physics_body.body_id != self.npc_id:
            raise ValueError("NPC physics body ID must match npc_id.")

    @property
    def behavior_state(self):
        return self.behavior.state


class NPCRegistry:
    def __init__(self, npcs=()):
        self._npcs = {}
        for npc in npcs:
            self.add(npc)

    def add(self, npc):
        if not isinstance(npc, NPC):
            raise TypeError("npc must be NPC.")
        if npc.npc_id in self._npcs:
            raise ValueError("Duplicate NPC ID.")
        self._npcs[npc.npc_id] = npc

    def get(self, npc_id):
        return self._npcs.get(npc_id)

    def all(self):
        return tuple(self._npcs[k] for k in sorted(self._npcs))

    def remove(self, npc_id):
        return self._npcs.pop(npc_id)


__all__ = ["NPC", "NPCRegistry", "BehaviorState"]
