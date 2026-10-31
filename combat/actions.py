"""Serializable combat action records."""
from dataclasses import dataclass

@dataclass(frozen=True)
class CombatAction:
    action_id: str
    actor_id: str
    target_id: str
    action_type: str = "attack"

    def __post_init__(self):
        if not all(isinstance(value, str) and value.strip() for value in (self.action_id, self.actor_id, self.target_id, self.action_type)):
            raise ValueError("Combat action fields must be non-empty strings.")
