"""Declarative quest rewards."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Reward:
    experience: int = 0
    currency: int = 0
    items: tuple[tuple[str, int], ...] = ()
    reputation: tuple[tuple[str, int], ...] = ()
    def __post_init__(self):
        if self.experience < 0 or self.currency < 0: raise ValueError("Rewards cannot be negative.")
        if any(amount < 0 for _, amount in self.items): raise ValueError("Item rewards cannot be negative.")

__all__ = ["Reward"]
