# Faz 4 — Ekonomi sınırı

## Sorumluluklar

`resources/` fiziksel malların domain'idir:

- `ResourceType`, `ResourceUnit`, `Quantity`;
- `Inventory` ve node stokları;
- gathering, recipe, production ve bunların snapshot'ları.

`economy/` ekonomik mülkiyet ve değer aktarımının domain'idir:

- `Currency` ve integer tabanlı `Money`;
- hesap bakiyeleri ve append-only `Ledger` kayıtları;
- `PriceBook`, `MarketOffer`, `Market` ve `Merchant`;
- para ile fiziksel stok arasındaki açık sınır olan `TradeService`;
- bağımsız `EconomySnapshot` (`rpg-economy`, sürüm 1).

## Bağımlılık yönü

Ekonomi `resources` içindeki public value object ve inventory sözleşmelerini
tüketebilir. Bunun karşılığında `resources` ekonomi, fiyat, merchant veya
currency import etmez. Böylece bir resource üretimi otomatik olarak para
üretmez; ücretli işlem yalnızca açık bir trade/ledger operasyonuyla oluşur.

## Persistence

Ekonomi snapshot'ı mevcut `rpg-gameplay` snapshot'ına gizlice eklenmez. Core
canonical state'e de ekonomi runtime'ı eklenmez. Birleşik save kapsamına
alınması sonraki application entegrasyonunda explicit bir alan, schema sürümü
ve candidate restore doğrulaması gerektirir.
