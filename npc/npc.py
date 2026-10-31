"""NPC aggregate and deterministic registry."""
from __future__ import annotations
from dataclasses import dataclass, field
from .behavior import BehaviorController, BehaviorState
from core.domain.spatial import Position

@dataclass
class NPC:
    npc_id: str
    name: str
    role: str = "civilian"
    faction_ids: tuple[str, ...] = ()
    location_id: str | None = None
    behavior: BehaviorController = field(default_factory=BehaviorController)
    active: bool = True
    position: Position = field(default_factory=Position)

    def __post_init__(self):
        for value, name in ((self.npc_id, "npc_id"), (self.name, "name"), (self.role, "role")):
            if not isinstance(value, str) or not value.strip(): raise ValueError(f"{name} must be non-empty.")
        self.faction_ids = tuple(self.faction_ids)
        if not isinstance(self.behavior, BehaviorController): raise TypeError("behavior must be BehaviorController.")
        if not isinstance(self.position, Position): raise TypeError("position must be Position.")
    @property
    def behavior_state(self): return self.behavior.state

class NPCRegistry:
    def __init__(self, npcs=()): self._npcs = {}; [self.add(npc) for npc in npcs]
    def add(self, npc):
        if not isinstance(npc, NPC): raise TypeError("npc must be NPC.")
        if npc.npc_id in self._npcs: raise ValueError("Duplicate NPC ID.")
        self._npcs[npc.npc_id] = npc
    def get(self, npc_id): return self._npcs.get(npc_id)
    def all(self): return tuple(self._npcs[k] for k in sorted(self._npcs))
    def remove(self, npc_id): return self._npcs.pop(npc_id)

__all__ = ["NPC", "NPCRegistry", "BehaviorState"]
