"""Market offers and explicit market state."""

from dataclasses import dataclass
from resources import ResourceType
from .currency import Money
from .prices import PriceBook, Price


@dataclass(frozen=True)
class MarketOffer:
    offer_id: str
    seller_id: str
    resource_type: ResourceType
    quantity: int
    unit_price: Money
    inventory_id: str | None = None
    expires_at: int | None = None

    def __post_init__(self):
        if not self.offer_id or not self.seller_id:
            raise ValueError("Offer and seller IDs are required.")
        if not isinstance(self.resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        if isinstance(self.quantity, bool) or not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("Offer quantity must be a positive integer.")
        if not isinstance(self.unit_price, Money):
            raise TypeError("unit_price must be Money.")
        if self.inventory_id is not None and (not isinstance(self.inventory_id, str) or not self.inventory_id.strip()):
            raise ValueError("inventory_id must be a non-empty string when provided.")
        if self.expires_at is not None and (isinstance(self.expires_at, bool) or not isinstance(self.expires_at, int) or self.expires_at < 0):
            raise ValueError("expires_at must be a non-negative integer when provided.")


class Market:
    def __init__(self, prices: PriceBook | None = None):
        self.prices = prices if prices is not None else PriceBook()
        self._offers: dict[str, MarketOffer] = {}

    def publish(self, offer: MarketOffer) -> MarketOffer:
        if offer.offer_id in self._offers:
            raise ValueError(f"Duplicate market offer: {offer.offer_id}")
        self._offers[offer.offer_id] = offer
        return offer

    def get(self, offer_id: str) -> MarketOffer | None:
        return self._offers.get(offer_id)

    def withdraw(self, offer_id: str) -> MarketOffer:
        try:
            return self._offers.pop(offer_id)
        except KeyError as error:
            raise KeyError(f"Unknown market offer: {offer_id}") from error

    def reserved_quantity(self, inventory_id: str, resource_type: ResourceType, excluding: str | None = None) -> int:
        return sum(
            offer.quantity for offer in self._offers.values()
            if offer.inventory_id == inventory_id
            and offer.resource_type == resource_type
            and offer.offer_id != excluding
        )

    def expire(self, current_tick: int) -> tuple[MarketOffer, ...]:
        expired = tuple(offer for offer in self._offers.values() if offer.expires_at is not None and offer.expires_at <= current_tick)
        for offer in expired: self._offers.pop(offer.offer_id, None)
        return tuple(sorted(expired, key=lambda offer: offer.offer_id))

    def offers(self) -> tuple[MarketOffer, ...]:
        return tuple(sorted(self._offers.values(), key=lambda offer: offer.offer_id))
