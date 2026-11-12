# Eldoria — Aşama 2: Altıgen Yerel Harita Veri Modeli

**Durum:** Kod ve testler eklendi; Linux ve Windows CI doğrulamaları başarıyla tamamlandı.  
**Harita şeması:** JSON schema_version 2.  
**Content package manifest:** schema_version 1 olarak korunur.

## Domain türleri
- HexCoord geometri matematiğidir; harita kimliği ve geçerlilik bilmez.
- LocalHexPosition immutable yerel koordinat türüdür. HexCoord dönüşümü açık metotlarla yapılır.
- HexCell position, terrain_id ve blocked taşır.
- HexMapDefinition valid_cells maskesini authoritative kaynak kabul eder; bounds yalnızca türetilmiş bilgidir.
- HexMapFeature bir veya daha fazla geçerli hücreyi tanımlar.
- HexLandmarkDefinition tek bir geçerli hücreye ve opsiyonel resource_node_id bağlantısına sahiptir.
- HexMapTransition kaynak hücreleri, altı yön, hedef kimliği, giriş yönü/hücreleri, active ve traversal_mode alanlarını taşır.

## Maske
valid_cells sonlu, boş olmayan axial hücre kümesidir. Delikler, girintiler, koridorlar ve kopuk adalar geçerlidir. Haritada bulunmayan hücre ile mevcut blocked hücre ayrı sorgulanır. Hash tabanlı frozenset ve immutable mapping kullanılır.

## JSON ve yükleme
Schema v1 kare haritalar MapDefinition olarak kalır. Schema v2 altıgen haritalar HexMapDefinition olarak parse edilir. load_map_catalog aynı klasörde iki türü deterministik keşfeder. ContentPackage.map_definitions yalnızca kare haritaları; hex_map_definitions yalnızca altıgen haritaları içerir. Map ID ve transition ID çakışmaları reddedilir. Legacy geçiş doğrulaması kare haritalar arasında korunur. Hex transition hedefi ve reciprocal bağlantı Aşama 3'e bırakılır.

## Sınırlar
Oyuncu/NPC hareketi, renderer, kamera, pathfinding, WorldHexPosition, save migration, dokuz mevcut haritanın dönüşümü ve fiziksel mesafe kuralları bu aşamada uygulanmaz.
