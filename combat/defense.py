"""Defense primitives."""
from .damage import calculate_damage

def mitigate_damage(raw_damage: int, defense: int) -> int:
    return calculate_damage(raw_damage, defense)
