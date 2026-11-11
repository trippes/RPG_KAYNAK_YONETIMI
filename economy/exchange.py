"""Fixed-denomination currency conversion and ledger integration."""

from .currency import BRONZE_CURRENCY, GOLD_CURRENCY, SILVER_CURRENCY, Currency, Money
from .ledger import Ledger


class CurrencyExchange:
    """Convert the game's three coin denominations without fractional coins."""

    BRONZE_PER_SILVER = 60
    SILVER_PER_GOLD = 60
    BRONZE_PER_GOLD = BRONZE_PER_SILVER * SILVER_PER_GOLD
    DENOMINATION_VALUES = {
        BRONZE_CURRENCY: 1,
        SILVER_CURRENCY: BRONZE_PER_SILVER,
        GOLD_CURRENCY: BRONZE_PER_GOLD,
    }

    def convert(self, source: Money, target_currency: Currency) -> Money:
        """Calculate an exact conversion without mutating an account."""
        if not isinstance(source, Money):
            raise TypeError("source must be Money.")
        if not isinstance(target_currency, Currency):
            raise TypeError("target_currency must be Currency.")
        if source.amount <= 0:
            raise ValueError("Currency exchange amount must be positive.")
        source_value = self.DENOMINATION_VALUES.get(source.currency)
        target_value = self.DENOMINATION_VALUES.get(target_currency)
        if source_value is None or target_value is None:
            raise ValueError("Only bronze, silver, and gold coins can be exchanged.")
        if source.currency == target_currency:
            raise ValueError("Currency exchange requires two different currencies.")
        value_in_bronze = source.amount * source_value
        target_amount, remainder = divmod(value_in_bronze, target_value)
        if remainder:
            raise ValueError(
                "This amount cannot be exchanged exactly; fractional coins are not supported."
            )
        return Money(target_amount, target_currency)

    def exchange(
        self, ledger: Ledger, account_id: str, source: Money,
        target_currency: Currency,
    ) -> Money:
        """Convert funds in one account and record both sides in the ledger."""
        if not isinstance(ledger, Ledger):
            raise TypeError("ledger must be Ledger.")
        target = self.convert(source, target_currency)
        ledger.exchange(account_id, source, target)
        return target


__all__ = ["CurrencyExchange"]
