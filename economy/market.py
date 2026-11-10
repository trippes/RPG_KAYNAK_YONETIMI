"""Location-scoped market offers and deterministic stock rotation."""

from dataclasses import dataclass, field

from resources import Inventory, Quantity, ResourceType, ResourceUnit
from .currency import Money
from .prices import PriceBook


TICKS_PER_GAME_DAY = 86_400


@dataclass(frozen=True)
class MarketCatalogEntry:
    resource_type: ResourceType
    base_price: Money
    min_quantity: int
    max_quantity: int

    def __post_init__(self):
        if not isinstance(self.resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        if not isinstance(self.base_price, Money):
            raise TypeError("base_price must be Money.")
        if self.min_quantity <= 0 or self.max_quantity < self.min_quantity:
            raise ValueError("Market catalog quantities must be positive and ordered.")


@dataclass
class MarketProfile:
    market_id: str
    location_id: str
    npc_id: str
    merchant_id: str
    inventory_id: str
    restock_interval: int
    catalog: tuple[MarketCatalogEntry, ...]
    visible_products: int = 4
    last_restock_cycle: int = -1
    demand: dict[str, int] = field(default_factory=dict)

    def __post_init__(self):
        for value, name in ((self.market_id, "market_id"), (self.location_id, "location_id"),
                            (self.npc_id, "npc_id"), (self.merchant_id, "merchant_id"),
                            (self.inventory_id, "inventory_id")):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string.")
        if isinstance(self.restock_interval, bool) or not isinstance(self.restock_interval, int) or self.restock_interval <= 0:
            raise ValueError("restock_interval must be a positive integer.")
        if isinstance(self.visible_products, bool) or not isinstance(self.visible_products, int) or self.visible_products <= 0:
            raise ValueError("visible_products must be a positive integer.")
        self.catalog = tuple(self.catalog)
        if not self.catalog or any(not isinstance(item, MarketCatalogEntry) for item in self.catalog):
            raise ValueError("A market profile requires valid catalog entries.")
        if len({item.resource_type for item in self.catalog}) != len(self.catalog):
            raise ValueError("Market catalog resource types must be unique.")
        if not isinstance(self.demand, dict) or any(
            not isinstance(key, str) or not key.strip()
            or isinstance(value, bool) or not isinstance(value, int) or value < 0
            for key, value in self.demand.items()
        ):
            raise ValueError("Market demand must map resource IDs to non-negative integers.")


@dataclass(frozen=True)
class MarketOffer:
    offer_id: str
    seller_id: str
    resource_type: ResourceType
    quantity: int
    unit_price: Money
    inventory_id: str | None = None
    expires_at: int | None = None
    market_id: str = "default"

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
        if not isinstance(self.market_id, str) or not self.market_id.strip():
            raise ValueError("market_id must be a non-empty string.")


class Market:
    def __init__(self, prices: PriceBook | None = None, profiles=()):
        self.prices = prices if prices is not None else PriceBook()
        self._offers: dict[str, MarketOffer] = {}
        self._profiles: dict[str, MarketProfile] = {}
        for profile in profiles:
            self.register_profile(profile)

    def register_profile(self, profile: MarketProfile) -> MarketProfile:
        if not isinstance(profile, MarketProfile):
            raise TypeError("profile must be MarketProfile.")
        if profile.market_id in self._profiles:
            raise ValueError(f"Duplicate market profile: {profile.market_id}")
        self._profiles[profile.market_id] = profile
        return profile

    def profile(self, market_id: str) -> MarketProfile | None:
        return self._profiles.get(market_id)

    def profiles(self) -> tuple[MarketProfile, ...]:
        return tuple(self._profiles[key] for key in sorted(self._profiles))

    def profile_for_npc(self, npc_id: str) -> MarketProfile | None:
        return next((profile for profile in self._profiles.values() if profile.npc_id == npc_id), None)

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
        return sum(offer.quantity for offer in self._offers.values()
                   if offer.inventory_id == inventory_id and offer.resource_type == resource_type
                   and offer.offer_id != excluding)

    def expire(self, current_tick: int) -> tuple[MarketOffer, ...]:
        expired = tuple(offer for offer in self._offers.values()
                        if offer.expires_at is not None and offer.expires_at <= current_tick)
        for offer in expired:
            self._offers.pop(offer.offer_id, None)
        return tuple(sorted(expired, key=lambda offer: offer.offer_id))

    def restock(self, market_id: str, inventory: Inventory, current_tick: int) -> tuple[MarketOffer, ...]:
        profile = self._profiles.get(market_id)
        if profile is None:
            raise KeyError(f"Unknown market profile: {market_id}")
        if not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        if isinstance(current_tick, bool) or not isinstance(current_tick, int) or current_tick < 0:
            raise ValueError("current_tick must be a non-negative integer.")
        cycle_length = profile.restock_interval * TICKS_PER_GAME_DAY
        cycle = current_tick // cycle_length
        if cycle <= profile.last_restock_cycle:
            return self.offers(market_id)

        for offer in tuple(self._offers.values()):
            if offer.market_id == market_id:
                self._offers.pop(offer.offer_id, None)
        for resource_type, quantity in inventory.snapshot():
            inventory.remove(resource_type, quantity)

        catalog = profile.catalog
        start = cycle % len(catalog)
        rotated = catalog[start:] + catalog[:start]
        expiry = (cycle + 1) * cycle_length
        for index, entry in enumerate(rotated[:profile.visible_products]):
            span = entry.max_quantity - entry.min_quantity + 1
            quantity = entry.min_quantity + ((cycle + index * 3) % span)
            variation = ((cycle + index) % 5 - 2) * 5
            demand_pressure = min(20, profile.demand.get(entry.resource_type.value, 0) * 5)
            supply_pressure = (
                ((entry.max_quantity - quantity) * 10 // (span - 1)) - 5
                if span > 1 else 0
            )
            price_adjustment = max(-20, min(30, variation + demand_pressure + supply_pressure))
            price_amount = max(1, entry.base_price.amount * (100 + price_adjustment) // 100)
            inventory.add(entry.resource_type, Quantity(quantity, ResourceUnit.ITEM))
            self.publish(MarketOffer(
                f"{market_id}:{cycle}:{entry.resource_type.value}", profile.merchant_id,
                entry.resource_type, quantity, Money(price_amount, entry.base_price.currency),
                profile.inventory_id, expiry, market_id,
            ))
        profile.last_restock_cycle = cycle
        profile.demand = {
            resource_id: amount - 1
            for resource_id, amount in profile.demand.items()
            if amount > 1
        }
        return self.offers(market_id)

    def record_purchase(self, market_id: str, resource_type: ResourceType, quantity: int) -> None:
        profile = self._profiles.get(market_id)
        if profile is None:
            raise KeyError(f"Unknown market profile: {market_id}")
        if not isinstance(resource_type, ResourceType):
            raise TypeError("resource_type must be ResourceType.")
        if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
            raise ValueError("purchase quantity must be a positive integer.")
        key = resource_type.value
        profile.demand[key] = min(100, profile.demand.get(key, 0) + quantity)

    def offers(self, market_id: str | None = None) -> tuple[MarketOffer, ...]:
        values = self._offers.values()
        if market_id is not None:
            values = (offer for offer in values if offer.market_id == market_id)
        return tuple(sorted(values, key=lambda offer: offer.offer_id))
