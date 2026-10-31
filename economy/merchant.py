"""Merchant identity and economic ownership boundary."""

from resources import Inventory


class Merchant:
    def __init__(self, merchant_id: str, inventory: Inventory | None = None, account_id: str | None = None, inventory_id: str | None = None):
        if not isinstance(merchant_id, str) or not merchant_id.strip():
            raise ValueError("merchant_id must be a non-empty string.")
        if inventory is not None and not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        self.merchant_id = merchant_id
        self.inventory = inventory if inventory is not None else Inventory()
        self.account_id = account_id or merchant_id
        self.inventory_id = inventory_id
