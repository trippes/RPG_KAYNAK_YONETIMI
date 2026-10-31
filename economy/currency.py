"""Currency and money value objects."""

from dataclasses import dataclass
from core.foundation import Identifier


@dataclass(frozen=True, order=True)
class Currency(Identifier):
    """Stable unit of account, separate from physical resources."""


@dataclass(frozen=True, order=True)
class Money:
    amount: int
    currency: Currency

    def __post_init__(self) -> None:
        if isinstance(self.amount, bool) or not isinstance(self.amount, int):
            raise TypeError("Money amount must be an integer.")
        if self.amount < 0:
            raise ValueError("Money amount cannot be negative.")
        if not isinstance(self.currency, Currency):
            raise TypeError("currency must be Currency.")

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"
