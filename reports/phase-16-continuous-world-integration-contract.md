# Aşama 16 — Teknik Aktarım Sözleşmesi

**Tarih:** 2026-11-19  
**Çalışma dalı:** `experiment/map-cleanup`  
**Dayanak:** `reports/phase-16-laboratory-capability-inventory.md` ve `reports/phase-16-main-game-architecture-ownership-audit.md`.

**Nitelik:** Bu belge mimari sözleşmedir; uygulama değildir. Bu commit oyun kodunu, kayıt şemasını veya bağımlılıkları değiştirmez.

## 1. Değişmez ilkeler

1. Laboratuvar bağımsız referans/deney ortamı olarak kalır. Laboratuvar paketinden ana oyuna çalışma zamanı bağımlılığı taşınmaz.
2. Yeni ve paralel dünya runtime'ı, aktör registry'si, harita registry'si, kamera veya save sistemi kurulmaz; mevcut Eldoria sahipleri evrimleştirilir.
3. Kararlı aktör kimliğinin tek sahibi `WorldActorRegistry`'dir. Spatial sistemler aynı `actor_id` değerini kullanır; ikinci bir EntityId otoritesi oluşturulmaz.
4. Sürekli dünya konumu tek yetkili mekânsal konum olur. Hex hücresi, occupancy ve pathfinding konumu bu sürekli konumdan türetilir.
5. Mevcut harita tanımı, terrain/movement kuralları, A* pathfinding, haritalar arası geçiş, NPC/resource/container domain sahipliği ve diyalog akışı korunur.
6. Yetkili hareket/fizik canonical simulation tick üzerinden yürütülür. Pygame frame delta yalnızca tick yürütme zamanlaması ve sunum içindir.
7. Kayıt şeması açık sürümleme ve migration olmadan değiştirilmez; eski kayıtlar sessizce dönüştürülmez.
8. Yalnızca onaylı player collider radius 8 world unit olarak kullanılabilir. NPC ve prop fizik ölçüleri uydurulmaz.
9. Yeni oynanış özelliği, içerik veya demo aktarımı yapılmaz. Yalnızca mevcut laboratuvar teknik kabiliyetleri taşınır.

## 2. Koordinat ve konum sözleşmesi

### 2.1 Kanonik dünya koordinatı

Ana oyunun mevcut geometrisi korunarak kanonik oyun dünya koordinatı **Eldoria y-aşağı (y-down) düzlemi** olacaktır.

- Birim: mevcut dünya/pixel birimi.
- +X sağa, +Y aşağı.
- Hex yönelimi: pointy-top.
- `hex_size = 32.0`; merkezden köşeye yarıçaptır.
- Hücre merkezi dönüşümü mevcut `core.domain.spatial.hex_geometry.axial_to_pixel` formülüdür:
  - x = size × √3 × (q + r/2)
  - y = size × 1.5 × r

Bu karar, ana oyunun `WorldTransform` ve `hex_geometry` koduyla uyumludur. Laboratuvarın matematiksel y-yukarı koordinat modeli ana oyunun kanonik modeli yapılmayacaktır. Yansıma/yön dönüşümü köprüsü yerel geometri aktarımı tamamlandığında kaldırılmalıdır.

Harita tanımlarında axial (0,0) dışında map origin/offset kullanımı olup olmadığı tüm üretim haritalarında doğrulanmalıdır. Kaynakta doğrulanmadan yeni offset katmanı eklenmez.

### 2.2 Sürekli konum değeri

`core.domain.spatial` içinde mevcut `EntityPosition(map_id, cell)` sözleşmesini tamamlayan map-scoped immutable sürekli konum değeri tanımlanmalıdır. Nihai sınıf adı mevcut adlandırma/tip kuralları incelenerek seçilir; bu belgede kavramsal olarak `ContinuousEntityPosition` / `WorldPoint` denir.

Asgari kurallar:
- map_id kapsamı korunur.
- x/y sonlu reel sayı olmalıdır; NaN, Infinity ve bool reddedilir.
- Konum immutable olur ve actor_id taşımaz.
- Hücre çözümleme, mevcut map geometri ve deterministik rounding ile yapılır.
- Önceki hücre yalnızca tam sınır/eşitlik tie-break girdisidir; konum otoritesi değildir.

### 2.3 Hücre ve occupancy

`HexWorldRuntime` sürekli konumun tek runtime sahibi olarak evrimleşir. `HexOccupancyRegistry` bağımsız konum otoritesi olmaktan çıkar; hücre bazlı sorgu görünümünü ve türetilmiş `_by_cell` indeksini korur.

- Sürekli konum → fractional axial → deterministik cube rounding → map hücresi.
- Hücre `valid_cells` maskesi ve mevcut map/movement kurallarıyla doğrulanır.
- Sürekli konum, türetilmiş hücre ve occupancy/spatial index aynı runtime işlemi içinde güncellenir; kısmi commit bırakılmaz.
- Harita geçişinde map_id ve konum birlikte güncellenir.
- Sınır eşitliklerinde deterministik tie-break uygulanır.

## 3. Kabiliyet → mimari katman → değişecek mevcut yapı

| Laboratuvar kabiliyeti | Ana oyundaki hedef sahip | Değişecek mevcut yapı / karar |
|---|---|---|
| Axial/cube geometri, yönelim, komşuluk, mesafe, polygon/tolerance | `core.domain.spatial` | `hex_geometry.py` sürekli koordinat, sınır çözümü ve gerekli geometri yardımcılarıyla genişler. `HexCoord`/`HexDirection` korunur. |
| Sürekli dünya noktası ve entity transform | `core.domain.spatial` + `HexWorldRuntime` | Map-scoped sürekli konum değer nesnesi eklenir; runtime'ın yetkili konumu olur. `EntityPosition` eski hücre tabanlı sözleşme ve migration girdisi olarak korunur. |
| Kamera state/follow/zoom/bounds | `game_ui.world_rendering.camera.HexCamera` | Korunur. Takip hedefi actor runtime'dan gelen render konumudur; kamera authoritative konumu değiştirmez. |
| World ↔ screen transform | `game_ui.world_transform.WorldTransform` | Sürekli world x/y dönüşümü eklenir; axial dönüşümler korunur. Kamera offset/zoom/viewport tek dönüşüm sınırıdır. |
| Uniform grid / quadtree / AABB | `core.domain.spatial` + application adapter | Genel dinamik spatial index boşluğu kapatılır. İndeks actor kimliğini/konumu sahiplenmez, yalnızca AABB kayıtları ve aday sorgularını tutar. Grid veya quadtree seçimi ölçümle yapılır; ikisi birden zorunlu değildir. |
| Physics broadphase | application fizik servisi | Dinamik aktör adayları genel spatial index'ten gelir; statik harita adayları `HexPhysicsSnapshot` kaynaklıdır. |
| Actor identity/registry | `application.actor_system.WorldActorRegistry` | Korunur. `hex_actor_binding.py` içindeki lab EntityId wrap/unwrap kaldırılır; aynı actor_id doğrudan kullanılır. İkinci registry kurulmaz. |
| Entity location/transform | `application.hex_world_runtime.HexWorldRuntime` | `_HexEntityState` ve `HexMovableEntity` sürekli konum/hareket state'ine göre evrimleşir. Kimlik registry'si ayrı kalır. |
| World/map lifecycle | `HexWorldRuntime`, `HexMapDefinition`, `WorldMapDefinition` | Mevcut runtime sürekli konumla genişler. Ayrı lab world/map registry taşınmaz. Map tanımı/topolojisi canonical kaynak kalır. |
| Sparse cell runtime override | mevcut application world runtime | Yalnızca ana oyunda aynı sorumluluğa ihtiyaç doğrulanırsa runtime'a dahil edilir. Gereksiz paralel cell store kurulmaz. |
| Movement intent/mode | application movement service; domain değerleri spatial | Manuel yön ve click-to-move girdileri ortak intent pipeline'ına bağlanır; intent konumu doğrudan değiştirmez. |
| Fixed-step integrator | application simulation update | Hareket her canonical tick'te ilerler. Frame delta authoritative fizik integrasyonuna doğrudan verilmez. |
| Terrain/movement profile/blocked cell | `HexWorldRuntime` + `MovementRules` | Mevcut hücre geçişi ve terrain kuralları korunur; sürekli hareket bunları atlayamaz. |
| A* / click-to-move | `HexPathfinder`, `HexWorldRuntime` | Korunur. Pathfinder hücre rotası/waypoint üretir; sürekli fizik integratörü olmaz. |
| Static hex collision geometry | `application.hex_physics_bridge.HexPhysicsSnapshot` | Sahiplik korunur; lab geometri/fizik tipleri yerel Eldoria tipleriyle değiştirilir. Kaynak canonical map definition'dır. |
| Dynamic body/shape | core spatial domain + application physics | Lab body/shape/vector tipleri yerel karşılıklarla değiştirilir. Yalnızca player radius 8 onaylıdır; NPC/prop ölçüleri belirlenmez. |
| Continuous collision resolution | application physics solver | `resolve_cell_step` hücre merkezi adım kontrolüdür, genel continuous solver sayılmaz. Broadphase → narrowphase → continuous resolution pipeline'ı yerel olarak kurulur. |
| Interaction profile/range/priority/target query | application interaction service | `HexGameplayView` içindeki `_npc_at_screen_position` ve hücre taraması UI'dan çıkarılır. Adaylar index ile daraltılır, sonra mesafe/profile/priority doğrulanır. |
| Input/dialogue/context menu | UI input adapter + application interaction | Screen koordinatı `WorldTransform.screen_to_world` ile world koordinata çevrilir. Sol tık mevcut diyalogu açar. Sağ tık boş aksiyon menüsü kabuğunu açar; aksiyon eklenmez. |
| Render snapshot/visibility/depth | `game_ui.world_rendering` | Render read-only snapshot/view kullanır. `HexCharacterRenderer`, `HexTerrainRenderer`, `DepthSorter` sunum sahibi kalır. Interpolation authoritative state'i değiştirmez. |
| Content/world/entity adapters | mevcut content + application binding servisleri | `ContentPackage`, `HexMapDefinition`, `GameplayPlacementCatalog`, NPC/resource/container domain sahipleri korunur. Lab demo içerikleri taşınmaz. |
| Map/runtime persistence | `application.hex_world_persistence` + `GameSaveDocument` | `HexWorldSnapshot` sürekli konum için sürümlü genişler; dış zarf migration zinciriyle uyumlu evrilir. |
| Atomic save/storage | `SaveJsonCodec` + `GameSaveFileAdapter` | Tek mevcut save hattı korunur. Lab doğrulama/atomik yazma ilkeleri mevcut codec/adapter içinde karşılanır; ikinci save deposu açılmaz. |
| Lab package imports | application bridge/binding tüketicileri | `hex_actor_binding.py`, `hex_world_geometry_bridge.py`, `hex_physics_bridge.py` ve diğer tüm tüketiciler yerel tiplere geçirilir. En son `pyproject.toml` içindeki `hex_world_lab*` keşfi kaldırılır. |

## 4. Hareket ve fizik pipeline sözleşmesi

Yetkili simülasyon sırası:

1. Input/AI hareket intent'i üretir; intent konumu değiştirmez.
2. Aktiflik, world/map kapsamı, movement profile ve mevcut movement rules doğrulanır.
3. Manuel yön veya pathfinder waypoint'i displacement/velocity isteğine çevrilir.
4. Integratör hareketi canonical tick başına ilerletir.
5. Statik ve dinamik broadphase adayları toplanır.
6. Narrowphase gerçek şekillerle çakışmayı doğrular.
7. Continuous solver displacement'i çözer; tünelleme ve engel içinden geçme testlerle engellenir.
8. Son konum map maskesi, terrain ve movement kurallarıyla doğrulanır.
9. Sürekli konum + hücre + occupancy + spatial index aynı işlemde commit edilir.
10. Render snapshot authoritative state'ten üretilir; interpolation yalnızca görseldir.

Laboratuvardaki hız, ivme, sürtünme, clamp ve solver parametreleri kaynak kodundan tek tek doğrulanarak aktarılır. Bu entegrasyon kapsamında oyuncu hareket hissini değiştirecek yeni parametreler uydurulmaz.

**Tick frekansı:** `core.time.Tick` non-negative integer tick değerini tanımlar; bu sınıf tek başına saniyedeki tick Hz değerini sabitlemez. Uygulama öncesi gerçek tick frekansı ve scheduler/update giriş noktası mevcut simulation config üzerinden doğrulanmalıdır. Sabit adım zorunludur; bu rapor 60 Hz veya başka bir sayı varsaymaz.

## 5. Kamera, render ve etkileşim sınırı

- `HexCamera` yalnızca sunum kamerasıdır.
- `WorldTransform` screen/world dönüşümünün tek sahibidir; y ekseni yansıtan ikinci bridge kalıcı mimaride bulunmaz.
- `HexGameplayView` input ve render orkestrasyonu yapar; hedef seçme/menzil/öncelik kuralı içermez.
- Interaction service ekran koordinatı değil world koordinatı ve world/map kapsamı alır.
- Adaylar spatial index ile daraltılır; kesin dünya mesafesi, aktiflik, world/map, profile/tag ve deterministik priority-distance-actor_id sırasıyla seçilir.
- NPC sol tık → mevcut diyalog akışı korunur.
- NPC sağ tık → boş menü kabuğu korunur.
- Render ve depth sorting authoritative runtime'ı değiştiremez.

## 6. Persistence ve migration

Mevcut `GameSaveDocument` schema v3 ve `HexWorldSnapshot` schema v1 sessizce değiştirilmez.

Yeni snapshot sürümü için:
1. En az actor_id, map_id, continuous x/y ve gerekli mevcut movement/occupancy alanlarının kapsamı tanımlanır.
2. Velocity/acceleration/intent/solver state'in save'e girip girmeyeceği ayrıca kararlaştırılır. Geçici render/interpolation state kaydedilmez.
3. Hex-world için yeni açık schema version; outer save için gerekiyorsa yeni version ve `migrate_save_data` migration adımı eklenir.
4. Eski cell-only kayıt migration'ı map_id + q/r hücre merkezini mevcut Eldoria pointy-top y-down geometri formülüyle continuous x/y'ye çevirir. Kayıtta bulunmayan ara hareket veya velocity uydurulmaz.
5. Migration eski payload'ı değiştirmez; yeni in-memory snapshot üretir. Kalıcı yazım normal save akışında yapılır.
6. Yeni kayıtlar tek `GameSaveDocument` hattından yazılır.
7. Testler eski fixture migration, yeni round-trip, NaN/Infinity, duplicate actor ID, map/world uyuşmazlığı ve restore atomikliğini kapsar.

## 7. Lab bağımlılığını kaldırma sırası

1. `core.domain.spatial` yerel geometri ve continuous coordinate sözleşmesini tamamla.
2. `WorldTransform`'u y-down continuous world coordinate sözleşmesine geçir.
3. `HexWorldRuntime` ve occupancy'yi continuous position tek otorite olacak şekilde evrimleştir.
4. Yerel body/shape, static geometry, dynamic index ve collision pipeline'ı kur; `HexPhysicsSnapshot` lab import'larını kaldır.
5. `WorldActorRegistry` doğrudan actor_id bağını kur; lab EntityId adapter'larını kaldır.
6. Interaction/target query'yi application katmanına taşı.
7. Save snapshot ve migration'ı tamamla.
8. Content/world/render adapter'larındaki kalan lab tüketicilerini kaldır.
9. Tüm repo için `hex_world_lab` import araması, test ve temiz kurulum doğrulaması yap.
10. Sıfır runtime import'u ve sıfır test/package bağımlılığı doğrulandıktan sonra `pyproject.toml` içindeki `hex_world_lab*` package discovery kaldırılır.

Laboratuvar klasörü silinmez; bağımsız referans ortamı olarak kalır.

## 8. Zorunlu test ve kabul ölçütleri

**Geometri:** axial/world round-trip; y-down yön uyumu; hücre merkezleri; kenar/köşe tie-break; map mask; screen/world dönüşüm round-trip.

**Hareket/fizik:** sabit tick ve farklı render FPS'lerinde deterministik sonuç; intent → rules → integrator → collision → commit; statik/dinamik çarpışma; broadphase/brute-force eşdeğerliği; tünelleme, sınır ve çoklu temas; occupancy/index tutarlılığı; harita geçişi.

**Etkileşim/render:** screen→world→target; range/profile/priority/ID tie-break; sol tık diyalog regresyonu; sağ tık boş menü; interpolation authoritative state'i değiştirmez.

**Persistence/bağımlılık:** eski cell-only migration; yeni round-trip; bozuk/non-finite/duplicate/mismatched payload reddi; restore atomikliği; lab import'larının sıfır olması; temiz kurulumda test ve ana oyun başlangıcı.

## 9. Açık doğrulama kapıları — karar uydurulmayacak

1. **Tick Hz ve scheduler bağlantısı:** mevcut `Tick` sınıfı frekans belirtmez; gerçek config ve update sahibi doğrulanmalı.
2. **Hareket parametreleri:** laboratuvarın gerçek default/clamp değerleri kaynak kodundan çıkarılmalı; yeni değer belirlenmemeli.
3. **NPC/prop collider:** ölçüler ve şekiller tanımlı değil; onaylı player radius 8 dışına değer atanmaz.
4. **Velocity persistence:** yüklemede hareketin kaldığı yerden sürmesi mi yoksa aktörün güvenli biçimde durması mı gerektiği kararlaştırılmadan velocity save alanı kesinleştirilmez.
5. **Map origin/offset:** üretim map'lerinde axial origin dışı offset olup olmadığı doğrulanmalı.
6. **Grid mi quadtree mi:** laboratuvar her ikisini içerir; ana oyun workload ölçülmeden ikisi birden zorunlu kılınmaz.
7. **Shape kapsamı:** yalnızca laboratuvarda mevcut ve ana oyunda gerçek tüketicisi olan collider türleri taşınır.

## 10. Nihai mimari kararı

**Kimlik `WorldActorRegistry`'de; sürekli konum ve dünya yaşam döngüsü `HexWorldRuntime`'ta; hücre occupancy türetilmiş registry görünümünde; geometri `core.domain.spatial`'da; statik harita çarpışma kaynağı `HexPhysicsSnapshot`'ta; kamera/screen transform sunum katmanında; etkileşim hedefleme application katmanında; kalıcılık mevcut GameSaveDocument zincirinde kalır.**

Aktarılan şey laboratuvar paketi veya demosu değil, doğrulanmış teknik davranış ve sözleşmelerdir. Bu sözleşme onaylanmadan uygulama koduna geçilmez.
