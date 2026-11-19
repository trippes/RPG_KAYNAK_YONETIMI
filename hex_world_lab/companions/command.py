"""Explicit companion intent commands; these values do not move entities."""
from enum import Enum
class CompanionCommand(Enum):
    FOLLOW = "follow"
    WAIT = "wait"
    RETURN = "return"
