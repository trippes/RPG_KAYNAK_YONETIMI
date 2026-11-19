"""Device-independent continuous movement modes."""
from enum import Enum


class MovementMode(Enum):
    """Select a movement profile independently of the requested direction."""

    NORMAL = "normal"
    RUNNING = "running"
    STEALTH = "stealth"
