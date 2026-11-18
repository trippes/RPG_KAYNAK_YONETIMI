# Harita Sistemi Temizliği — Ayrıntılı Teknik Plan

| Alan | Değer |
|---|---|
| Çalışma dalı | `experiment/map-cleanup` |
| Kaynak dal | `demo_eldoria` |
| Başlangıç commit'i | `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Genel plan | [51-map-system-cleanup-general-plan.md](51-map-system-cleanup-general-plan.md) |
| Durum | Teknik plan — uygulama öncesi onay bekliyor |

## 1. Teknik karar özeti

Bu aşama, legacy harita kodunu körlemesine silme veya altıgen sistemi hemen varsayılan yapma çalışması değildir. Hedef, mevcut ana oyun davranışını koruyarak sorumlulukları, veri sözleşmelerini ve runtime sahipliğini açık hâle getirmektir.

İlk kaynak incelemesi iki paralel yerel harita modelini doğruluyor:

- Schema v1 kare harita: `world/map_definition.py`, `world/map_loader.py`, `world/map_catalog.py`.
- Schema v2 axial altıgen harita: `application/hex_map_definition.py`.
- İki modeli ve dünya haritasını bir araya getiren paket yükleyici: `application/content_loader.py`.
- Altıgen dünya yerleşimi: `application/world_map_definition.py` ve `content/demo_eldoria/world.json`.
- Altıgen hareket/runtime: `application/hex_world_runtime.py`, `hex_movement_rules.py`, `hex_occupancy.py`, `hex_pathfinding.py`, `hex_transition_service.py`.
- Kare dünya/konum grafı ve eski runtime: `world/`, `core/world/`.
- UI tarafında kare ve altıgen yollar: `game_ui/screens/main_screen.py`, `map_screen.py`, `game_ui/hex_world_view.py`.

İlk karar: v1 kare ve v2 altıgen içerik biçimlerinden hangisinin kalıcı olacağına, mevcut oyun akışları ve save/asset bağımlılıkları ölçülmeden karar verilmeyecek. Bir süre iki formatı destekleyen loader/adaptör gerekebilir.

## 2. Başlangıç deposu ve kanıt sınırı

Dal `demo_eldoria` HEAD `7d53d431d5c3639fd95d273de9043b64483a5125` commit'inden çıkarılmıştır. İlk ağaç taramasında 605 repository path kaydı görüldü; bunun içinde 16 map JSON dosyası (14 schema-v1 kare harita ve 8? no: schema ayrımı dosya içeriği doğrulanarak sayılacak; ilk listede toplam 16 dosya), iki hex placement JSON ve harita sistemiyle ilişkili çok sayıda test/modül vardır.

> Not: Dosya adlarından schema türü çıkarılmayacak. Her JSON dosyasının gerçek `schema_version` alanı ve içeriği envanter aşamasında okunup tabloya kaydedilecek. Dosya sayısı da her envanter güncellemesinde yeniden hesaplanacak.

Ağaç taraması ve sınırlı kaynak dosya okumaları, plan hazırlığı için kullanılmıştır. Henüz test komutu çalıştırılmadı; bu nedenle başlangıç test sonucu veya görsel kabul iddiası yoktur.

## 3. Katman bazlı teknik envanter

### 3.1 Veri ve içerik paketi

İncelenecek dosyalar:
- `content/demo_eldoria/manifest.json`
- `content/demo_eldoria/maps/*.json`
- `content/demo_eldoria/world.json`
- `content/demo_eldoria/placements/*.json`
- `content/demo_eldoria/asset_catalog.json`
- `content/demo_eldoria/presentation_assets.json`
- `application/content_loader.py`
- `application/world_map_definition.py`
- `application/hex_map_definition.py`
- `world/map_definition.py`, `world/map_loader.py`, `world/map_catalog.py`

Kontroller:
1. Manifestteki her path'in paket kökü içinde kaldığı ve gerçek dosyaya karşılık geldiği doğrulanır.
2. Tüm map ID'leri paket genelinde benzersiz olmalıdır.
3. Her transition hedefi var olan haritaya işaret etmelidir; aktif/pasif ve tek yön/çift yön semantiği kaydedilir.
4. World map yerleşimlerinin referans verdiği map ID'leri ve axial koordinatları doğrulanır.
5. Kare harita koordinatları `(x, y)`, hex koordinatları `(q, r)` olarak ayrı tutulur; veri dönüşümü açık adaptör/migration olmadan yapılmaz.
6. Asset ve placement kayıtlarının map ID, asset ID ve anchor referansları doğrulanır.
7. Mevcut içerik dosyaları değişiklik öncesi baseline olarak saklanır; normalize/format-only JSON yazımı da ayrıca diff ile gözden geçirilir.

### 3.2 Dünya ve domain/runtime

İncelenecek dosyalar:
- `world/local_map.py`, `world/location.py`, `world/map.py`, `world/movement.py`
- `core/world/world.py`, `core/world/world_id.py`, `core/world/world_manager.py`, `core/world/legacy_runtime.py`
- `application/world_map_definition.py`
- `application/hex_world_runtime.py`, `application/hex_transition_service.py`
- `core/domain/spatial/` içindeki `EntityPosition`, `LocalHexPosition`, `WorldHexPosition`, `HexCoord` ve geometry sözleşmeleri.

Kontroller:
- `WorldMap` konum grafı ile `WorldMapDefinition` axial dünya yerleşimi aynı kavram gibi kullanılmamalı.
- `EntityPosition(map_id, cell)` ile world/location actor konumları arasındaki dönüşüm ve sahiplik açıkça belgelenmeli.
- Hareketin authoritative kaynağı tek bir runtime olmalı; UI veya renderer ikinci bir konum state'i üretmemeli.
- Harita unload/load, aktif dünya, dormant actor ve save/restore davranışları ayrı ayrı izlenmeli.
- Pathfinding veya hareket algoritmaları yalnızca temizlik hedefiyle değiştirilmemeli; yalnızca sorumluluk sınırı ve test kapsamı ele alınmalı.

### 3.3 UI, kamera ve render

İncelenecek dosyalar:
- `game_ui/screens/main_screen.py`, `game_ui/screens/map_screen.py`
- `game_ui/hex_world_view.py`
- `game_ui/camera.py`, `game_ui/world_transform.py`
- `game_ui/world_rendering/`
- `game_ui/renderer.py`, `game_ui/scaled_renderer.py`

Kontroller:
- Kare harita ekranının halen aktif gameplay yolu olup olmadığı çağrı zinciriyle doğrulanır.
- `MainScreen` içindeki H tuşuyla altıgen dünyaya giriş/çıkış yolu ve geçici portal/bridge davranışı belgelenir.
- Altıgen görünümün player/entity konumunu nasıl okuduğu ve hareketi hangi servise ilettiği izlenir.
- Kamera, viewport, world transform ve screen coordinate dönüşümleri ayrı sorumluluklar olarak korunur.
- Render işlemi authoritative simülasyon state'ini değiştirmemelidir.
- Görsel varlıklar ve sahne yerleşimleri mevcut catalog/store sözleşmeleri üzerinden okunmalı; ikinci bir writer yaratılmamalıdır.

### 3.4 Test envanteri

Asgari test kümeleri:
- `tests/test_world/`: map definition/loader, transitions, world/map manager, runtime separation, mixed map package.
- `tests/test_application/`: content loader, hex runtime, movement, world object placement, presentation content service/store, persistence/session.
- `tests/test_game_ui/`: main screen/map data/transitions, hex view/camera, renderer, placement/asset catalog, world transform.
- `tests/test_foundation/`: hex coordinate/geometry, local/world hex position, position.
- `tests/test_architecture/`: core/world boundary and world model boundary.
- `tests/test_compatibility/`: legacy world clock/scheduler/runtime adapters and migration tooling.
- `tests/test_persistence/`: save/restore contracts and document bridge.

Her testin hangi sözleşmeyi koruduğu ve hangi refactor sonrası gerekli olduğu test matrisiyle eşleştirilir. Testi olmayan davranış, kaldırma için otomatik izin sayılmaz; önce characterization test yazılır.

## 4. Uygulama fazları ve değişiklik kapıları

### 16.1 — Baseline ve characterization (yalnızca okuma + test)
- Başlangıç commit'i ve içerik dosyalarının envanteri kaydedilir.
- Windows yerel kurulumda mevcut test komutları kullanıcı tarafından çalıştırılır; CI'da Linux/Windows sonuçları alınır.
- Oynanabilir giriş, aktif paket seçimi, başlangıç haritası, H tuşu hex geçişi, dünya haritası penceresi ve save/load akışları gözlemlenir.
- Kritik davranışlar için eksik characterization/regression testleri eklenir.
**Kapı:** Baseline test/oynanış durumu belgelenmeden refactor başlamaz.

### 16.2 — İçerik şeması ve harita grafı denetimi
- Map JSON dosyalarının gerçek schema sürümleri ve ID'leri listelenir.
- Kare harita geçişleri ile hex map transition/world placement ilişkileri karşılaştırılır.
- Kırık/boşta kalan referanslar raporlanır; otomatik düzeltme yapılmaz.
- V1/v2 coexistence loader davranışı test edilir.
**Kapı:** Her içerik dosyası için keep/migrate/deprecate kararı ve gerekçesi bulunur.

### 16.3 — Runtime sahipliği ve adaptör sınırları
- Kare actor/world movement ile hex runtime arasındaki geçiş zinciri belgelenir.
- Konumun her modda hangi nesnede authoritative olduğu saptanır.
- Dönüşüm fonksiyonları varsa saf ve tek yönlü sözleşmelerle test edilir.
- Belirsiz ownership varsa önce küçük bir mimari ADR yazılır; uygulama ayrı onaya bırakılabilir.
**Kapı:** Player location, map ID ve save/restore sorumlulukları çakışmasız olmalı.

### 16.4 — Render/UI sorumluluk sadeleştirmesi
- Ekran/viewport/camera ve world transform çağrı zinciri çıkarılır.
- Geçici H-key bridge davranışı ürün gereksinimiyle karşılaştırılır; bu aşamada varsayılan olarak silinmez.
- Render-side cache ile gameplay state ayrımı test edilir.
**Kapı:** Mevcut giriş, kamera ve harita görüntüsü davranışı için regresyon kanıtı olmalı.

### 16.5 — Güvenli refactor ve deprecation
- Bir seferde tek bir sorumluluk veya küçük modül grubu değiştirilir.
- Önce public API ve import kullanım haritası çıkarılır.
- Gerekli ise compatibility facade/adaptör eklenir.
- Kullanılmayan olduğu kanıtlanan kod önce deprecation/uyarı veya test dışı bırakma adımına alınır; silme ayrı commit olur.
- Her commit sonrası hedef test kümesi ve sonra tam test paketi çalıştırılır.
- Veri migration gerekiyorsa idempotent, yedekli ve dry-run destekli tasarlanır; migration bu planın otomatik varsayımı değildir.
**Kapı:** Her kaldırma için çağrı/import kanıtı, test kanıtı ve rollback yolu bulunmalı.

### 16.6 — Tam regresyon ve kullanıcı kabulü
- Temiz kurulum ve paketleme doğrulanır.
- Tüm Pytest suite, Ruff ve GitHub Actions kalite akışları çalışır.
- Kare harita ve altıgen dünya içeriklerinin beklenen şekilde yüklenmesi doğrulanır.
- Harita geçişi, oyuncu konumu, çarpışma, etkileşim, yerleşim, kamera, save/load ve mevcut gameplay loop kontrol edilir.
- Kullanıcı görsel test checklist'ini tamamlar.
**Kapı:** CI ve manuel kabul birlikte başarılı olmalı.

### 16.7 — Kapanış ve entegrasyon sözleşmesi
- Temizlenen/kalan legacy bileşenler listelenir.
- Harita veri şeması, runtime authority, koordinat dönüşümü, render adapter ve asset ownership kararları kaydedilir.
- Laboratuvar A15 raporundaki altı entegrasyon blocker'ının hangilerinin çözüldüğü ve hangilerinin entegrasyon aşamasına kaldığı eşleştirilir.
- "Hazır / koşullu hazır / hazır değil" kararı verilir.
**Kapı:** Kullanıcı kapanış kabulü olmadan sonraki entegrasyon aşaması açılmaz.

## 5. Korumalı sözleşmeler

Aşağıdakiler açık karar olmadan değiştirilemez:
- `content/demo_eldoria/manifest.json` paket sözleşmesi ve path güvenliği.
- Kare map schema v1 ve hex map schema v2'nin mevcut okuma davranışı.
- Map/world/transition/entity kimlikleri.
- Başlangıç konumu ve harita geçiş semantiği.
- `EntityPosition`, `LocalHexPosition`, `WorldHexPosition` ve axial koordinatların anlamı.
- Save document sürümü, restore sırası, actor/world bağları.
- Asset catalog ve scene placement referansları.
- Public GameplayService API ve `main.py --play` giriş akışı.

Bu sözleşmelerin değiştirilmesi gerekiyorsa versioned migration, compatibility window ve rollback planı ayrıca hazırlanır.

## 6. Kabul/test matrisi

| Alan | Test/kanıt | Kabul ölçütü |
|---|---|---|
| Paket yükleme | content loader tests + tüm paket | manifest ve tüm referanslar doğrulanır |
| Kare harita | world map tests | gerekli v1 haritalar okunur ve geçişler tutarlı |
| Altıgen harita | hex loader/runtime tests | tüm v2 haritalar ve world placements geçerli |
| Geçişler | square + hex transition tests | hedef map/cell ve yön kuralları korunur |
| Konum sahipliği | movement/runtime tests | tek authoritative state; UI kopya state üretmez |
| Çarpışma/occupancy | movement/occupancy tests | mevcut hareket engelleri ve occupancy korunur |
| Görsel sunum | game_ui tests + manuel kontrol | kamera, viewport, terrain, actor ve placements doğru |
| Kayıt/yükleme | persistence/session tests | mevcut save'ler bozulmadan restore edilir |
| Paketleme | clean install / release verification | paketlenmiş içerik yüklenir |
| Mimari sınırlar | architecture tests | domain/application/UI import sınırları korunur |
| Kalite | Pytest, Ruff, GitHub Actions | ilgili bütün zorunlu işler başarılı |

## 7. Geri alma stratejisi

- Her mantıksal değişiklik ayrı commit; büyük dosya taşıma ve davranış değişikliği aynı commit'te birleştirilmez.
- JSON migration öncesi kaynak dosyalar commit ile korunur; migration dry-run çıktısı gözden geçirilir.
- Bir aşama başarısız olursa son yeşil commit'e dönülür; sonraki aşamaya geçilmez.
- Temizlik dalı başarısız olsa bile `demo_eldoria`, `main` ve laboratuvar dalı değişmeden kalır.
- Aşama kapanışında temizleme dalı birleştirilmeden önce kullanıcıya diff özeti ve test kanıtı sunulur.

## 8. Açık riskler

1. **İki harita modelinin eşzamanlı varlığı:** Square v1 ve hex v2 yalnızca dosya formatı farkı değil; farklı runtime/position ownership içeriyor.
2. **Geçici UI bridge:** H-key hex giriş/çıkışı test/demo kolaylığı için eklenmiş olabilir; ürün akışı netleşmeden kaldırılmamalı.
3. **Legacy world manager:** `core/world` ile `application` world/runtime sorumluluklarının tam sınırı import ve call graph ile kanıtlanmalı.
4. **Asset/placement paralelliği:** Combined `presentation_assets.json` ile ayrılmış `asset_catalog.json` + `placements/` backward compatibility yolu birlikte mevcut.
5. **Save uyumluluğu:** Harita ID veya actor konum biçimi değişirse restore ve eski save'ler etkilenebilir.
6. **Test kapsama boşluğu:** UI'da manuel olarak görülen bazı davranışlar için otomatik characterization test gerekebilir.

## 9. Uygulama öncesi karar

Bu belge teknik planı tanımlar; henüz hiçbir harita kodu, JSON içeriği, asset, save schema veya UI akışı değiştirilmemiştir. Temizlik uygulamasına başlamak için kullanıcının bu ayrıntılı teknik planı ayrıca onaylaması gerekir.
