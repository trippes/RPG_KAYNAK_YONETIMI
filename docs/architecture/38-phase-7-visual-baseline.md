# Eldoria — Aşama 7.1 Görsel Altyapı İnceleme Raporu

## Amaç
Aşama 6 sonrasındaki çalışan altıgen dünya korunarak görsel katmanın doğal dünya sunumuna hazırlanması.

## Mevcut durum
- Simülasyon: `application.hex_world_runtime.HexWorldRuntime`.
- Geometri: axial koordinatlar ve `WorldTransform`.
- Kamera: `HexCamera`; takip, kenar kaydırma ve yakınlaştırma.
- Zemin: `HexTerrainRenderer`; hücre verisini görsel sunuma dönüştürür.
- Çevresel nesneler: `AssetCatalog`, `SceneObjectPlacement` ve `SceneObjectRenderer`.
- Derinlik: `DepthSorter.sort_by_depth`.
- İçerik: `content/demo_eldoria/presentation_assets.json`.
- Dünya: merkez harita ve altı komşusundan oluşan yedi haritalı yapı.

## Riskler ve teknik borç
1. Görsel katmanın bazı geçiş işaretleri ve koordinat metinleri teknik geometriyi oyuncuya açığa çıkarıyordu.
2. Tek PNG varlığı çevresel çeşitlilik için yetersizdi; veri modeli yeni varlık türlerini desteklese de eksik görsellerde daha iyi fallback gerekiyordu.
3. Zemin görselleştirmesi hücre tabanlı olduğundan görsel damgaların birbirine bindirilmesi ve görünür alan culling'i korunmalıdır.
4. CI başlangıçta yalnızca Linux doğrulaması içeriyordu; Aşama 7 kapanışı için Windows doğrulaması da gereklidir.

## Mimari karar
Simülasyon koordinatları değiştirilmeyecek. Aşama 7 değişiklikleri yalnızca:
- görsel sunum,
- veri odaklı varlık tanımları,
- pivot/çarpışma metadatası,
- çevresel animasyon ve önbellekleme,
- CI ve regresyon doğrulaması
katmanlarında yapılacaktır.

Bu belge 7.1 envanteridir; sonraki iş paketleri mevcut simülasyon API'lerini yeniden yazmadan ilerler.
