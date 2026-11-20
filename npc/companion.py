"""Persistent companion commands and map-local wait state."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from core.domain.spatial import ContinuousEntityPosition


class CompanionCommand(Enum):
    FOLLOW = "follow"
    WAIT = "wait"


@dataclass(frozen=True, slots=True)
class CompanionState:
    npc_id: str
    command: CompanionCommand = CompanionCommand.FOLLOW
    wait_position: ContinuousEntityPosition | None = None

    def __post_init__(self):
        if not isinstance(self.npc_id, str) or not self.npc_id.strip():
            raise ValueError("npc_id must be a non-empty string.")
        if not isinstance(self.command, CompanionCommand):
            raise TypeError("command must be a CompanionCommand.")
        if self.command is CompanionCommand.WAIT:
            if not isinstance(self.wait_position, ContinuousEntityPosition):
                raise TypeError("WAIT companions require a continuous wait position.")
        elif self.wait_position is not None:
            raise ValueError("FOLLOW companions cannot retain a wait position.")


class CompanionRegistry:
    """Own companion membership and command state, never world position."""

    def __init__(self, states=()):
        self._states = {}
        for state in states:
            self.restore(state)

    def add(self, npc_id: str) -> CompanionState:
        if npc_id in self._states:
            raise ValueError(f"NPC is already a companion: {npc_id}")
        state = CompanionState(npc_id)
        self._states[npc_id] = state
        return state

    def set_command(
        self,
        npc_id: str,
        command: CompanionCommand | str,
        wait_position: ContinuousEntityPosition | None = None,
    ) -> CompanionState:
        if npc_id not in self._states:
            raise KeyError(f"Companion not found: {npc_id}")
        command = CompanionCommand(command)
        state = CompanionState(npc_id, command, wait_position)
        self._states[npc_id] = state
        return state

    def get(self, npc_id: str) -> CompanionState | None:
        return self._states.get(npc_id)

    def all(self) -> tuple[CompanionState, ...]:
        return tuple(self._states[key] for key in sorted(self._states))

    def remove(self, npc_id: str) -> CompanionState:
        return self._states.pop(npc_id)

    def restore(self, state: CompanionState) -> CompanionState:
        if not isinstance(state, CompanionState):
            raise TypeError("state must be a CompanionState.")
        if state.npc_id in self._states:
            raise ValueError(f"Duplicate companion: {state.npc_id}")
        self._states[state.npc_id] = state
        return state


__all__ = ["CompanionCommand", "CompanionRegistry", "CompanionState"]
