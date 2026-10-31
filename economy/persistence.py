"""Runtime-free economy snapshot and JSON-compatible codec."""

from dataclasses import dataclass
from typing import Mapping

from .currency import Currency, Money
from .ledger import Ledger
from .market import Market, MarketOffer
from .prices import PriceBook
from .merchant import Merchant
from resources import ResourceType


ECONOMY_SCHEMA = "rpg-economy"
ECONOMY_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class EconomySnapshot:
    accounts: tuple[tuple[str, str, int], ...]
    currencies: tuple[str, ...]
    prices: tuple[tuple[str, str, int], ...]
    offers: tuple[dict[str, object], ...]
    merchants: tuple[dict[str, object], ...] = ()
    schema: str = ECONOMY_SCHEMA
    schema_version: int = ECONOMY_SCHEMA_VERSION

    @classmethod
    def from_runtime(cls, ledger: Ledger, market: Market, merchants=None) -> "EconomySnapshot":
        if not isinstance(ledger, Ledger) or not isinstance(market, Market):
            raise TypeError("ledger and market must be their economy runtime types.")
        accounts = tuple((account, currency.value, amount) for account, currency, amount in ledger.accounts())
        prices = tuple((price.resource_type.value, price.money.currency.value, price.money.amount)
                       for price in market.prices.prices())
        currencies = tuple(sorted({currency for _, currency, _ in accounts} | {currency for _, currency, _ in prices}))
        offers = tuple({"offer_id": offer.offer_id, "seller_id": offer.seller_id,
                        "resource_type": offer.resource_type.value, "quantity": offer.quantity,
                        "currency": offer.unit_price.currency.value, "unit_price": offer.unit_price.amount,
                        "inventory_id": offer.inventory_id, "expires_at": offer.expires_at}
                       for offer in market.offers())
        merchants = tuple({"merchant_id": merchant.merchant_id, "account_id": merchant.account_id, "inventory_id": merchant.inventory_id} for merchant in (merchants or {}).values())
        return cls(accounts, currencies, prices, offers, merchants)

    def restore(self) -> tuple[Ledger, Market]:
        """Restore validated economy state into fresh runtime objects."""
        ledger = Ledger()
        market = Market()
        currencies = {value: Currency(value) for value in self.currencies}
        for account_id, currency_id, amount in self.accounts:
            currency = currencies.setdefault(currency_id, Currency(currency_id))
            if amount < 0:
                raise ValueError("Economy account balances cannot be negative.")
            ledger.credit(account_id, Money(amount, currency), "restore")
        for resource_id, currency_id, amount in self.prices:
            currency = currencies.setdefault(currency_id, Currency(currency_id))
            market.prices.set(ResourceType(resource_id), Money(amount, currency))
        for data in self.offers:
            currency_id = str(data["currency"])
            currency = currencies.setdefault(currency_id, Currency(currency_id))
            market.publish(MarketOffer(
                str(data["offer_id"]), str(data["seller_id"]),
                ResourceType(str(data["resource_type"])), int(data["quantity"]),
                Money(int(data["unit_price"]), currency), data.get("inventory_id"), data.get("expires_at"),
            ))
        merchants = {item["merchant_id"]: Merchant(item["merchant_id"], account_id=item.get("account_id"), inventory_id=item.get("inventory_id")) for item in self.merchants}
        return ledger, market, merchants

    def to_dict(self) -> dict[str, object]:
        return {"schema": self.schema, "schema_version": self.schema_version,
                "accounts": [{"account_id": a, "currency": c, "amount": n} for a, c, n in self.accounts],
                "currencies": list(self.currencies),
                "prices": [{"resource_type": r, "currency": c, "amount": n} for r, c, n in self.prices],
                "offers": list(self.offers), "merchants": list(self.merchants)}

    @classmethod
    def from_dict(cls, data: Mapping[str, object]) -> "EconomySnapshot":
        if not isinstance(data, Mapping) or data.get("schema") != ECONOMY_SCHEMA or data.get("schema_version") != 1:
            raise ValueError("Unsupported economy snapshot schema.")
        try:
            accounts = tuple((str(x["account_id"]), str(x["currency"]), int(x["amount"])) for x in data["accounts"])
            currencies = tuple(str(x) for x in data["currencies"])
            prices = tuple((str(x["resource_type"]), str(x["currency"]), int(x["amount"])) for x in data["prices"])
            offers = tuple(dict(x) for x in data["offers"])
            merchants = tuple(dict(x) for x in data.get("merchants", ()))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError("Malformed economy snapshot.") from error
        return cls(accounts, currencies, prices, offers, merchants)
