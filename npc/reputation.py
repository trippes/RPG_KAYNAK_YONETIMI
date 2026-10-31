"""Player reputation values and readable reputation tiers."""
from __future__ import annotations

class ReputationLedger:
    def __init__(self, values=None): self._values = dict(values or {})
    def get(self, faction_id: str) -> int: return self._values.get(faction_id, 0)
    def change(self, faction_id: str, amount: int) -> int:
        if not isinstance(amount, int) or isinstance(amount, bool): raise TypeError("amount must be an integer.")
        value = max(-100, min(100, self.get(faction_id) + amount)); self._values[faction_id] = value; return value
    def set(self, faction_id: str, value: int) -> None:
        self._values[faction_id] = max(-100, min(100, value))
    def tier(self, faction_id: str) -> str:
        value = self.get(faction_id)
        return "hostile" if value <= -75 else "unfriendly" if value < -25 else "neutral" if value < 26 else "friendly" if value < 76 else "exalted"
    def snapshot(self) -> dict[str, int]: return dict(sorted(self._values.items()))

__all__ = ["ReputationLedger"]
