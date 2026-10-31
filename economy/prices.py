"""Price quotes; market mutation is kept in :mod:`economy.market`."""

from dataclasses import dataclass
from resources import ResourceType
from .currency import Currency, Money


@dataclass(frozen=True)
class Price:
    resource_type: ResourceType
    money: Money

    def __post_init__(self):
        if not isinstance(self.resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        if not isinstance(self.money, Money):
            raise TypeError("money must be Money.")


class PriceBook:
    def __init__(self):
        self._prices: dict[tuple[str, Currency], Price] = {}

    def set(self, resource_type: ResourceType, money: Money) -> Price:
        price = Price(resource_type, money)
        self._prices[(resource_type.value, money.currency)] = price
        return price

    def get(self, resource_type: ResourceType, currency: Currency) -> Price | None:
        return self._prices.get((resource_type.value, currency))

    def prices(self) -> tuple[Price, ...]:
        return tuple(sorted(self._prices.values(), key=lambda item: (item.resource_type.value, item.money.currency.value)))
