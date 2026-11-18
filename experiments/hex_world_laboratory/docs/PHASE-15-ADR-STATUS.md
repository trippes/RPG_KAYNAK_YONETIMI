# Aşama 15.2 — ADR ve Mimari Karar Durum Envanteri

Denetim tarihi: 19 Kasım 2026. Bu belge mevcut kararları izler; yeni karar üretmez.

## 1. Karar envanteri

| ADR | Karar | Durum | Kod/kanıt | Entegrasyon etkisi |
|---|---|---|---|---|
| ADR-001 Hex orientation support | Flat-top ve pointy-top desteklenir; nihai oyun yönelimi bu ADR ile seçilmez | GEÇERLİ | geometry/orientation.py, HexLayout ve geometry testleri | Ana oyunun mevcut axial/pixel konvansiyonuyla eşleştirilmeden yönelim varsayılmamalı |
| ADR-002 Coordinate axes, origin, scale | World X sağa, Y yukarı; axial (0,0) origin; circumradius dünya birimi; ekran dönüşümü sunum katmanında | GEÇERLİ — ÖLÇEK ADAPTÖRÜ GEREKİR | WorldPoint, HexLayout, axial_to_world; ana oyunda WorldTransform.hex_size varsayılanı 32 px | Lab dünya birimi ile ana oyunun piksel ölçeği aynı sayı sayılamaz |
| ADR-003 Rounding and tolerance | En yakın hücre; tam sınırda önceki hücreyi koruma; yedekte deterministic cube rounding; tolerans 1e-9 | GEÇERLİ | world_to_axial, MovementCellTracker ve sınır testleri | Main hücre tabanlı hareketi, sürekli konum takibinin yerine geçmez |
| ADR-008 Spatial index selection | Küçük listelerde linear AABB; büyük/uzun ömürlü sorgularda UniformGrid; Quadtree deneysel; broadphase nihai karar değildir | GEÇERLİ — BAĞLAMIYLA SINIRLI | spatial/grid.py, physics/spatial_adapter.py, entities/spatial_index.py | HexOccupancyRegistry ile aynı problem değildir; kopyalamadan önce workload ölçülmeli |

## 2. Kapanış raporlarıyla doğrulanan kararlar

| Konu | Güncel karar | Kanıt |
|---|---|---|
| Simülasyon zamanı | DemoTickPump 60 TPS zamanlayıcıdır; SimulationTickCoordinator wall-clock ve Pygame bağımsızdır | Aşama 10 raporu ve simulation/tick_coordinator.py |
| Tick sırası | Input → collision-aware movement → cell tracker → entity/spatial sync → tick commit | SimulationTickCoordinator.advance_tick ve Phase 10 testleri |
| Render saflığı | Immutable snapshot; render authoritative entity/spatial state yazmaz | rendering/snapshot.py ve Phase 10 raporu |
| Entity modeli | PLAYER/NPC/RESOURCE ortak kayıt; map-scoped spatial index; companion komutları intent | Aşama 9 raporu ve entities/companions paketleri |
| Spatial | UniformGrid broadphase adaptörü; narrowphase ve exact interaction kararı ayrı | ADR-008 ve Aşama 8/11 raporları |
| Collider | Görsel geometri collider üretmez; collider açıkça tanımlanır | Aşama 12/14 raporları ve content/collision.py |
| Content v1 | VisualDocument, ContentLibrary, MapContentDocument ve JSON v1 strict/deterministic; rotation/scale yok | Aşama 14 raporu ve Content Data API |
| Engine | Pygame korunur; motor değişikliği bu aşamanın konusu değildir | Kullanıcı tarafından onaylanmış kapsam |

## 3. Tarihsel kalan mimari kayıtlar

ARCHITECTURE_SPECIFICATION.md içindeki Aşama 2–5 döneminden kalan bazı AÇIK KARAR listeleri güncel uygulama ve ADR'lerle örtüşmüyor. Yönelim desteği, koordinat/ölçek, sınır tie-break, 60 TPS, collider, kamera ve spatial seçimleri artık salt açık karar değildir. Bu eski kayıtlar tarihsel bağlam olarak korunmalı; güncel durum için bu envanter ve kapanış raporları esas alınmalıdır.

Eski ADR dosyaları silinmez veya geriye dönük değiştirilmez. Mimari sözleşmenin kendisini güncellemek ayrı belge revizyonudur.

## 4. Açık kararlar ve A16 ön koşulları

1. Pygame dağıtımı: Ana oyun ve laboratuvarın aynı runtime ortamında hangi dağıtımı kullanacağı seçilmemiştir. Temiz ortamda API/başlatma doğrulaması ve kullanıcı onayı gerekir.
2. Hareket otoritesi: Lab WorldPoint ile Main EntityPosition(map_id, LocalHexPosition) arasında tek authoritative hareket kaynağı belirlenmelidir.
3. Map/world dönüşümü: Map-local axial, world-level axial ve Lab world/map kimlikleri için açık dönüşüm sözleşmesi gerekir.
4. İçerik otoritesi: Raster AssetCatalog/ScenePlacementCatalog ile vector ContentLibrary/MapContentDocument birlikte yaşayacaksa veri türüne göre tek yazıcı belirlenmelidir.
5. Renderer sahipliği: Main sprite/depth pipeline ile Lab Surface renderer için tek sunum giriş noktası ve adaptör sınırı gerekir.
6. İzometrik hedef: Mevcut affine camera transform nihai izometrik/elevation projeksiyonu değildir; bu hedef A15'te karara bağlanmamıştır.

## 5. Sonuç

Dört ADR kaydı geçerlidir; ikisi ölçek ve kullanım bağlamında adaptasyon gerektirir. Eski mimari sözleşmedeki bazı açık karar listeleri tarihsel kalmıştır. A16'nın güvenli başlaması için altı açık kararın sahibi, kanıtı ve kabul ölçütü belirlenmelidir.

Bu belge yeni mimari karar onaylamaz; mevcut kararların izlenebilir durumunu kaydeder.
