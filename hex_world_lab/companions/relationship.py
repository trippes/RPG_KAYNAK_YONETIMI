"""Immutable player-to-NPC companion relationship."""
from dataclasses import dataclass
from hex_world_lab.entities import EntityId
from hex_world_lab.geometry import WorldPoint
from .command import CompanionCommand
@dataclass(frozen=True, slots=True)
class CompanionRelationship:
    player_id: EntityId
    companion_id: EntityId
    command: CompanionCommand = CompanionCommand.FOLLOW
    command_revision: int = 0
    wait_position: WorldPoint | None = None
    def __post_init__(self) -> None:
        if not isinstance(self.player_id,EntityId) or not isinstance(self.companion_id,EntityId):
            raise TypeError("relationship endpoints must be EntityId values")
        if not isinstance(self.command,CompanionCommand): raise TypeError("command must be a CompanionCommand")
        if isinstance(self.command_revision,bool) or not isinstance(self.command_revision,int) or self.command_revision < 0:
            raise ValueError("command_revision must be a non-negative integer")
        if self.wait_position is not None and not isinstance(self.wait_position,WorldPoint):
            raise TypeError("wait_position must be a WorldPoint or None")
        if self.command is not CompanionCommand.WAIT and self.wait_position is not None:
            raise ValueError("wait_position is only valid for WAIT")
