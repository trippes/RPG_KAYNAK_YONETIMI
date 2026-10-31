"""Deterministic initiative ordering."""

def order_initiative(combatant_ids, scores=None) -> tuple[str, ...]:
    scores = scores or {}
    ids = tuple(combatant_ids)
    if len(set(ids)) != len(ids): raise ValueError("Combatant IDs must be unique.")
    return tuple(sorted(ids, key=lambda item: (-scores.get(item, 0), item)))
