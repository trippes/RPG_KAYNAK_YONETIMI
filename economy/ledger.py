"""Deterministic account balances and append-only economic entries."""

from dataclasses import dataclass
from .currency import Currency, Money


@dataclass(frozen=True)
class LedgerEntry:
    entry_id: str
    account_id: str
    amount: Money
    direction: str
    reason: str
    counterparty_id: str | None = None


class Ledger:
    """Owns money balances; it never owns physical resource inventory."""

    def __init__(self) -> None:
        self._balances: dict[tuple[str, Currency], int] = {}
        self._entries: list[LedgerEntry] = []
        self._next_entry = 1

    def balance(self, account_id: str, currency: Currency) -> Money:
        self._validate_account(account_id)
        if not isinstance(currency, Currency):
            raise TypeError("currency must be Currency.")
        return Money(self._balances.get((account_id, currency), 0), currency)

    def credit(self, account_id: str, money: Money, reason: str = "credit", counterparty_id: str | None = None) -> LedgerEntry:
        self._validate_account(account_id)
        self._validate_money(money)
        key = (account_id, money.currency)
        self._balances[key] = self._balances.get(key, 0) + money.amount
        return self._record(account_id, money, "credit", reason, counterparty_id)

    def debit(self, account_id: str, money: Money, reason: str = "debit", counterparty_id: str | None = None) -> LedgerEntry:
        self._validate_account(account_id)
        self._validate_money(money)
        key = (account_id, money.currency)
        current = self._balances.get(key, 0)
        if money.amount > current:
            raise ValueError("Insufficient currency balance.")
        self._balances[key] = current - money.amount
        return self._record(account_id, money, "debit", reason, counterparty_id)

    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def accounts(self) -> tuple[tuple[str, Currency, int], ...]:
        return tuple(sorted((account, currency, amount) for (account, currency), amount in self._balances.items()))

    def _record(self, account_id, money, direction, reason, counterparty_id):
        entry = LedgerEntry(f"ledger:{self._next_entry:08d}", account_id, money, direction, reason, counterparty_id)
        self._next_entry += 1
        self._entries.append(entry)
        return entry

    @staticmethod
    def _validate_account(account_id: str) -> None:
        if not isinstance(account_id, str) or not account_id.strip():
            raise ValueError("account_id must be a non-empty string.")

    @staticmethod
    def _validate_money(money: Money) -> None:
        if not isinstance(money, Money):
            raise TypeError("money must be Money.")
