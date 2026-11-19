"""Device-independent movement mode identifiers."""

from enum import Enum


class MovementMode(Enum):
    """Select the movement speed profile independently of direction."""

    NORMAL = "normal"
    RUNNING = "running"
    STEALTH = "stealth"
