"""Atomic trade operation joining economy money and resources inventory."""

from dataclasses import dataclass
from resources import Inventory, Quantity, ResourceType
from .currency import Money
from .ledger import Ledger


@dataclass(frozen=True)
class Trade:
    trade_id: str
    buyer_id: str
    seller_id: str
    resource_type: ResourceType
    quantity: Quantity
    total: Money


class TradeService:
    def __init__(self, ledger: Ledger):
        if not isinstance(ledger, Ledger):
            raise TypeError("ledger must be Ledger.")
        self.ledger = ledger
        self._next_id = 1

    def execute(self, buyer_id: str, seller_id: str, buyer_inventory: Inventory, seller_inventory: Inventory,
                resource_type: ResourceType, quantity: Quantity, unit_price: Money) -> Trade:
        if buyer_id == seller_id:
            raise ValueError("Buyer and seller must be different accounts.")
        if not isinstance(buyer_inventory, Inventory) or not isinstance(seller_inventory, Inventory):
            raise TypeError("Trade inventories must be Inventory.")
        if not isinstance(resource_type, ResourceType) or not isinstance(quantity, Quantity):
            raise TypeError("Invalid trade resource or quantity.")
        if not isinstance(unit_price, Money):
            raise TypeError("unit_price must be Money.")
        if quantity.value <= 0:
            raise ValueError("Trade quantity must be positive.")
        if quantity.unit != (seller_inventory.get(resource_type).unit if seller_inventory.get(resource_type) else quantity.unit):
            raise ValueError("Trade quantity unit does not match seller stock.")
        total = Money(quantity.value * unit_price.amount, unit_price.currency)
        seller_inventory.remove(resource_type, quantity)
        # The two mutations below are rolled back if money validation fails.
        buyer_inventory.add(resource_type, quantity)
        try:
            self.ledger.debit(buyer_id, total, "trade", seller_id)
            self.ledger.credit(seller_id, total, "trade", buyer_id)
        except Exception:
            buyer_inventory.remove(resource_type, quantity)
            seller_inventory.add(resource_type, quantity)
            raise
        trade = Trade(f"trade:{self._next_id:08d}", buyer_id, seller_id, resource_type, quantity, total)
        self._next_id += 1
        return trade
