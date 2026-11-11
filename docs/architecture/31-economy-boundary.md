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


## Oyun para birimleri ve sabit kur

Oynanıştaki standart para birimleri bronze, silver ve gold kimlikli bronz,
gümüş ve altın sikkelerdir. CurrencyExchange dönüşüm oranlarını bronz sikkeyi
temel birim alarak uygular:

- 1 bronz = 1 temel birim
- 1 gümüş = 60 bronz
- 1 altın = 60 gümüş = 3.600 bronz

Dönüşüm tam sayı ve kayıpsızdır. Daha büyük birime dönüşümde kaynak miktar
hedef birimin tam katı değilse işlem reddedilir; daha küçük birime dönüşüm
çarpanla yapılır. Ledger.exchange kaynak bakiyesini düşürüp hedef bakiyesini
aynı hesapta artırır ve iki yönlü defter kaydı oluşturur. Dönüşüm oranları
sabit domain kuralıdır; save dosyasına runtime state olarak yazılmaz.

GameplayService.exchange_currency oyun katmanının kullandığı giriş noktasıdır.
Pazar penceresindeki Para Bozdur düğmesi, oyuncuyu altı standart dönüşüm
işlemi sunan Döviz Bürosu penceresine götürür.
