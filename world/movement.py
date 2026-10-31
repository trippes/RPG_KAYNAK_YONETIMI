"""Movement value objects shared by application movement services."""

from dataclasses import dataclass
from enum import Enum

from core.time import Tick


class MovementState(Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class MovementActionView:
    action_id: str
    actor_id: str
    world_id: str
    origin_id: str
    destination_id: str
    path: tuple[str, ...]
    start_tick: int
    end_tick: int
    state: str

