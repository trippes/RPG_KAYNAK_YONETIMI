"""Level and experience progression."""
from dataclasses import dataclass


@dataclass
class Progression:
    level: int = 1
    experience: int = 0
    unspent_points: int = 0

    def __post_init__(self):
        if self.level < 1 or self.experience < 0 or self.unspent_points < 0:
            raise ValueError("Progression values are out of range.")

    @property
    def experience_to_next_level(self) -> int:
        return self.level * 1000

    def add_experience(self, amount: int) -> int:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError("Experience must be a non-negative integer.")
        self.experience += amount
        levels = 0
        while self.experience >= self.experience_to_next_level:
            self.experience -= self.experience_to_next_level
            self.level += 1
            self.unspent_points += 1
            levels += 1
        return levels

