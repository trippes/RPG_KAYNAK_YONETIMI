"""Resolve market spatial anchors through their existing NPC placement."""

from __future__ import annotations

from core.domain.spatial import EntityPosition
from economy import Market, MarketProfile

from .hex_actor_binding import ActorHexBindingError
from .npc_hex_binding import NPCSpatialBindingService
from .hex_world_runtime import HexMovableEntity


class MarketHexAnchorError(ValueError):
    """A market cannot resolve its NPC-backed spatial anchor."""


class MarketHexAnchorService:
    """Resolve a market's position from its associated NPC, without owning one."""

    __slots__ = ("_market", "_npc_binding")

    def __init__(
        self,
        market: Market,
        npc_binding: NPCSpatialBindingService,
    ) -> None:
        if not isinstance(market, Market):
            raise TypeError("market must be a Market")
        if not isinstance(npc_binding, NPCSpatialBindingService):
            raise TypeError("npc_binding must be an NPCSpatialBindingService")
        self._market = market
        self._npc_binding = npc_binding

    def profile(self, market_id: str) -> MarketProfile:
        if not isinstance(market_id, str) or not market_id.strip():
            raise ValueError("market_id must be a non-empty string")
        profile = self._market.profile(market_id)
        if profile is None:
            raise KeyError(f"Market profile not found: {market_id}")
        return profile

    def spatial_entity(self, market_id: str) -> HexMovableEntity:
        profile = self.profile(market_id)
        try:
            return self._npc_binding.spatial_entity(profile.npc_id)
        except (KeyError, ActorHexBindingError) as error:
            raise MarketHexAnchorError(
                f"Market '{market_id}' has no spatially registered NPC "
                f"anchor '{profile.npc_id}'."
            ) from error

    def position(self, market_id: str) -> EntityPosition:
        """Return the current NPC position; no market position is stored."""
        return self.spatial_entity(market_id).position


__all__ = ["MarketHexAnchorError", "MarketHexAnchorService"]
