# Location-Based Dynamic Markets

## Purpose

Markets are world content attached to a physical location and a merchant NPC. The player reaches a merchant, starts a dialogue, and selects the merchant's market option. The market window is opened as a managed gameplay window over the persistent world surface. There is no global market tab or market keyboard shortcut.

## Runtime ownership

- `MarketProfile` defines a market's identity, location, merchant NPC, merchant account, inventory registry key, restock interval, visible product count, and catalog.
- `MarketOffer` carries a `market_id`; offer queries can be scoped to one market.
- Each merchant owns a dedicated inventory registered in `SessionBundle.inventories`. The `Merchant.inventory` reference is rebound to that canonical inventory after save restoration.
- `GameplayService.market_offers(market_id)` checks that the hero is in the profile's registered location before it exposes offers.
- Purchases use the existing atomic `TradeService` path. Resource transfer and ledger debit/credit remain in the economy domain.

## Dynamic stock

A market's restock cycle is derived from the simulation calendar. The current game-time contract uses 60 simulation ticks per second and a 24-minute real-time day:

`cycle = current_tick // (restock_interval_days * 86_400)`

Within a cycle, stock remains stable. When the cycle advances, the market clears its previous resource stock and offers, rotates the configured catalog, and deterministically derives stock quantities from the cycle. Prices combine a small cycle variation, available supply, and persisted purchase-demand pressure; demand pressure decays after each restock. This avoids nondeterministic tests while ensuring different locations can expose different assortments and prices. Reopening a market during the same game day never replenishes stock.

## Content definition

The optional `markets` array in `data/starter_content.json` contains one record per market. Each record includes:

- `market_id`, `location_id`, `npc_id`, `npc_name`, and `npc_role`
- `merchant_id` and `inventory_id`
- `restock_interval` (in game days) and `visible_products`
- `position` and a dialogue definition with a choice whose action is `open_market`
- `catalog` entries containing `resource_type`, `base_price`, `min_quantity`, and `max_quantity`

Merchant NPCs and their dialogues are registered after character creation, together with their market profiles. The opening/character-creation phase remains free of gameplay merchant entities.

## Persistence

Market profiles, catalog definitions, restock-cycle state, market-scoped offers, merchant account metadata, and merchant inventory IDs are stored in the existing economy snapshot. Physical inventory quantities continue to be stored by the existing session inventory persistence. On restore, the merchant's runtime inventory reference is rebound to the inventory with the matching registry ID.

## Current starter markets

- Village stalls: general resources, wood, iron ore, water, and bread.
- Village inn: food and drink focused assortment.

These are starter content examples. Additional markets are data records, not hardcoded UI branches.
