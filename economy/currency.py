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


# Canonical game denominations. Existing "gold" records remain compatible.
BRONZE_CURRENCY = Currency("bronze")
SILVER_CURRENCY = Currency("silver")
GOLD_CURRENCY = Currency("gold")

CURRENCY_LABELS = {
    "bronze": "bronz sikke",
    "silver": "gümüş sikke",
    "gold": "altın sikke",
}


def currency_name(currency: Currency | str) -> str:
    """Return the Turkish display name for a currency identifier."""
    currency_id = currency.value if isinstance(currency, Currency) else str(currency)
    return CURRENCY_LABELS.get(currency_id, currency_id)
