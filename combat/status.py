"""Status duration primitives."""

def tick_statuses(statuses: dict[str, int]) -> dict[str, int]:
    if not isinstance(statuses, dict): raise TypeError("statuses must be a dict.")
    return {key: value - 1 for key, value in statuses.items() if value > 1}
