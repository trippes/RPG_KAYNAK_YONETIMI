"""Damage calculation primitives."""

def calculate_damage(attack: int, defense: int) -> int:
    if isinstance(attack, bool) or isinstance(defense, bool) or not isinstance(attack, int) or not isinstance(defense, int):
        raise TypeError("attack and defense must be integers.")
    return max(0, attack - defense)
