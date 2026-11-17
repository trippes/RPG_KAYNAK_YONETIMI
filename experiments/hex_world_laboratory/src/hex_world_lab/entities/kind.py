"""Kinds shared by player, NPC, and resource entities."""
from enum import Enum
class EntityKind(Enum):
    PLAYER = "player"
    NPC = "npc"
    RESOURCE = "resource"
