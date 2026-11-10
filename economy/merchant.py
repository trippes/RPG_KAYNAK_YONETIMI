"""Merchant identity and economic ownership boundary."""

from resources import Inventory, ResourceType


class Merchant:
    def __init__(
        self,
        merchant_id: str,
        inventory: Inventory | None = None,
        account_id: str | None = None,
        inventory_id: str | None = None,
        *,
        npc_id: str | None = None,
        accepted_resources=(),
        buyback_rate: int = 50,
    ):
        if not isinstance(merchant_id, str) or not merchant_id.strip():
            raise ValueError("merchant_id must be a non-empty string.")
        if inventory is not None and not isinstance(inventory, Inventory):
            raise TypeError("inventory must be Inventory.")
        if npc_id is not None and (not isinstance(npc_id, str) or not npc_id.strip()):
            raise ValueError("npc_id must be a non-empty string when provided.")
        resources = tuple(accepted_resources)
        if any(not isinstance(resource, ResourceType) for resource in resources):
            raise TypeError("accepted_resources must contain ResourceType values.")
        if len(set(resources)) != len(resources):
            raise ValueError("accepted_resources must be unique.")
        if isinstance(buyback_rate, bool) or not isinstance(buyback_rate, int) or not 1 <= buyback_rate <= 100:
            raise ValueError("buyback_rate must be between 1 and 100.")
        self.merchant_id = merchant_id
        self.inventory = inventory if inventory is not None else Inventory()
        self.account_id = account_id or merchant_id
        self.inventory_id = inventory_id
        self.npc_id = npc_id
        self.accepted_resources = resources
        self.buyback_rate = buyback_rate
