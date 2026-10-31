"""Composition root for economy runtime state."""

from .ledger import Ledger
from .market import Market
from .persistence import EconomySnapshot
from .merchant import Merchant


class Economy:
    """Coordinates economic state without owning physical resource rules."""

    def __init__(self, ledger: Ledger | None = None, market: Market | None = None, merchants=None):
        self.ledger = ledger if ledger is not None else Ledger()
        self.market = market if market is not None else Market()
        self.merchants: dict[str, Merchant] = dict(merchants or {})

    def register_merchant(self, merchant: Merchant) -> Merchant:
        if merchant.merchant_id in self.merchants: raise ValueError(f"Duplicate merchant ID: {merchant.merchant_id}")
        self.merchants[merchant.merchant_id] = merchant
        return merchant

    def snapshot(self) -> EconomySnapshot:
        return EconomySnapshot.from_runtime(self.ledger, self.market, self.merchants)
