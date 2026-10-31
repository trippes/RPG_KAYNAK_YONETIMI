"""Attack action primitives."""
from .damage import calculate_damage

def resolve_attack(attacker_id: str, defender_id: str, attack: int, defense: int):
    return {"attacker_id": attacker_id, "defender_id": defender_id, "damage": calculate_damage(attack, defense)}
