# Aşama 16 — Laboratuvar Teknik Kabiliyet Envanteri

**Denetim tarihi:** 2026-11-19  
**Laboratuvar dalı:** `experiment/hex-world-laboratory`  
**Ana oyun çalışma dalı:** `experiment/map-cleanup`  
**Kapsam:** Laboratuvarda mevcut olan teknik altyapının ana Eldoria oyunundaki karşılıklarını ve aktarım boşluklarını belirlemek.  
**Bu raporun niteliği:** Envanter ve mimari durum tespiti; uygulama veya özellik geliştirme raporu değildir.

## 1. Yönetici özeti

Laboratuvar, yalnızca serbest hareket ve çarpışma fiziğinden oluşmuyor. Geometri, kamera, mekânsal indeksler, varlık kimliği ve dönüşümleri, etkileşim hedeflemesi, dünya/harita yaşam döngüsü, harita ve runtime kalıcılığı, içerik/çevre nesnesi adaptörleri, render snapshot'ları, görünürlük sorguları ve sabit simülasyon tick koordinasyonu içeriyor.

Ana oyunda bu sistemlerin bir bölümü zaten kısmen kullanılıyor. Ancak ana oyun laboratuvarın bağımsız paketine doğrudan bağlı ve bazı temel veriler hâlâ hücre tabanlı. Bu nedenle bugünkü durum, laboratuvar kabiliyetlerinin ana oyuna bütünüyle aktarılması değildir.

**En önemli mimari fark:** Laboratuvarda varlık konumu sürekli dünya koordinatıdır (`WorldPoint`); altıgen hücre bu konumdan türetilir. Ana oyunun mevcut oyuncu/NPC/nesne runtime'ında ise konum `EntityPosition(map_id, cell)` biçiminde hücre tabanlıdır. Ana oyundaki son yumuşak hareket, hücreler arasında görsel interpolasyondur; sürekli konumu yetkili oyun durumu hâline getirmez.

**Aktarım ilkesi:** Laboratuvar kodu ana oyuna bir bağımlılık olarak taşınmayacak. Gerekli davranışlar Eldoria'nın kendi alan modelleri ve uygulama servisleri içinde yerel olarak kurulacak. Laboratuvar, bağımsız referans ve doğrulama ortamı olarak kalacak. Demo uygulamaları, demo döngüleri ve laboratuvara özgü örnek içerik ana oyuna taşınmayacak.

## 2. Laboratuvar modül envanteri

### 2.1 Geometri

**Modüller:** `geometry/coordinates.py`, `orientation.py`, `layout.py`, `transforms.py`, `distance.py`, `neighbors.py`, `polygon.py`, `tolerance.py`.

**Mevcut kabiliyetler:**
- Değişmez axial (`q,r`), cube (`q,r,s`) ve sürekli `WorldPoint(x,y)` değer nesneleri.
- Flat-top ve pointy-top yönelimleri, yarıçap ve orijin içeren ortak `HexLayout`.
- Axial/cube/world dönüşümleri; kesirli axial koordinat ve deterministik cube rounding.
- Hücre sınırında eşit uzaklık durumunda önceki hücreyi koruyan deterministik seçim.
- Hex komşuları, topolojik mesafe, dünya mesafesi, poligon ve sayısal tolerans işlemleri.

**Ana oyun karşılığı:** `core.domain.spatial` altındaki axial/hücre sözleşmeleri ve `game_ui/world_transform.py`; laboratuvar ile ana oyun arasındaki y-yönü ve axial baz dönüşümleri `application/hex_world_geometry_bridge.py` içinde.

**Boşluk/risk:** Ana oyunun alan konumu hâlâ ayrık hücre. Geometri köprüsü laboratuvar sınıflarını doğrudan import ediyor ve Eldoria'nın y-aşağı koordinatını laboratuvarın matematiksel y-yukarı koordinatına yansıtıyor. Bu dönüşümün tek, testli ve ana oyuna ait bir sahibi olmalı; ikinci bir koordinat doğrusu/konum sahibi oluşturulmamalı.

**Yerel hedef:** Ana oyunun spatial domain katmanı; UI yalnızca domain dönüşümlerini kullanmalı. Hücre koordinatı, sürekli konumun yerine geçmemeli.

### 2.2 Kamera ve dünya-ekran dönüşümleri

**Modüller:** `camera/state.py`, `coordinates.py`, `transform.py`, `bounds.py`, `follow.py`, `controller.py`.

**Mevcut kabiliyetler:**
- Viewport, merkez ve zoom içeren değişmez kamera durumu.
- Dünya/ekran dönüşümü.
- Zoom alt/üst sınırı ve adımlı zoom.
- Üstel sönümleme ile kare hızından bağımsız hedef takibi.
- Harita sınırları ve sınır politikası (serbest veya haritaya sabitleme).

**Ana oyun karşılığı:** `game_ui/world_rendering/camera.py` içindeki `HexCamera` ve `game_ui/world_transform.py`. Ana kamera yumuşak takip, kenar kaydırma ve harita sınırına sabitleme yapıyor.

**Boşluk/risk:** Ana kamera işlevsel bir karşılığa sahip; fakat laboratuvarın bağımsız kamera durum/transform sözleşmesiyle aynı API ve sorumluluk sınırında değil. Geçişte kamera merkezinin, zoom'un, viewport'un ve y-yönü dönüşümünün iki yerde ayrı ayrı yönetilmesine izin verilmemeli.

**Yerel hedef:** `game_ui/world_rendering` sunum katmanı. Kamera oyun dünyasının konumunu değiştirmemeli; yalnızca görüntü dönüşümünü yönetmeli.

### 2.3 Mekânsal indeksler ve fizik broadphase

**Modüller:** `spatial/entry.py`, `_bounds.py`, `protocols.py`, `grid.py`, `quadtree.py`; ayrıca `physics/broadphase.py`, `physics/spatial_adapter.py`, `entities/spatial_index.py`.

**Mevcut kabiliyetler:**
- AABB tabanlı genel mekânsal sorgu sözleşmesi.
- Seyrek Uniform Grid / spatial hash; ekleme, güncelleme, silme ve tam AABB kesişim filtresi.
- Sabit köklü Quadtree; kapasite/ağaç derinliği, ebeveyn düğümde kalan sınır aşan kayıtlar.
- Deterministik sıralı aday sonuçları.
- Fizik broadphase aday toplama ve indeksli aday sağlayıcı protokolü.
- Varlıklar için harita kapsamlı grid; gövde veya etkileşim yarıçapından AABB türetimi.
- İndeks sonuçlarını doğrusal taramayla karşılaştıran diferansiyel test yaklaşımı.

**Ana oyun karşılığı:** `application/hex_physics_bridge.py` içindeki `ObstacleSpatialIndex` ve laboratuvar fizik adapter'ları. Ana uygulama aktörlerinin tam dünya-konum indekslemesi henüz laboratuvardaki varlık indeksinin yerel karşılığı değildir.

**Boşluk/risk:** Ana oyun laboratuvarın indeks ve fizik türlerine doğrudan bağlı. Hareketli aktörlerin indeks güncellemesi, harita etkinleştirme/devre dışı bırakma ve fizik aday sorgusu tek bir yaşam döngüsünde tutarlı olmalı. Aynı varlığın hem ayrı actor index hem entity index içinde mükerrer yetkili kaydı olmamalı.

**Yerel hedef:** Genel AABB/grid/quadtree domain altyapısı ana oyuna ait spatial modülde; fizik broadphase fizik servisinde; varlık indeksi tek bir actor/entity registry adaptöründe.

### 2.4 Varlık kimliği, kayıt defteri ve transform

**Modüller:** `entities/identity.py`, `kind.py`, `entity.py`, `transform.py`, `registry.py`, `presentation.py`, `spatial_index.py`.

**Mevcut kabiliyetler:**
- Kararlı `EntityId` ve varlık türleri.
- Dünya/harita kapsamlı `EntityLocation`; sürekli `WorldPoint` konumu.
- Dönüş açısı içeren `EntityTransform`.
- Immutable `EntityRecord`; gövde ve etkileşim profilini ilişkilendirebilme.
- Dünya ve harita kayıtlarını doğrulayan `EntityRegistry`; kimlik, harita ve dünya uyuşmazlığı kontrolleri.
- Harita bazında varlık listesi, aktif/pasif durumu ve mekânsal indeks adaptörü.

**Ana oyun karşılığı:** `application/actor_system.py` içindeki `WorldActorRegistry` kimlik ve gameplay ilişkilerini tutuyor; `application/hex_world_runtime.py` hücre konumu/occupancy yönetiyor. `application/hex_actor_binding.py` bu sistemleri laboratuvar `EntityId` ve fizik türleriyle bağlıyor.

**Boşluk/risk:** Ana oyunda aktör kimliği ile hücre konumu farklı sahiplerde olsa da binding katmanı laboratuvar kimliğine bağımlı. Hedef mimaride tek kararlı Eldoria kimliği olmalı; konum, aktiflik, gameplay ilişkileri ve fizik gövdesi ayrı sorumluluklarla ama aynı kimliğe bağlı kalmalı. Laboratuvar `EntityRecord` yapısını kopyalayıp ikinci registry kurmak doğru değil.

**Yerel hedef:** Eldoria actor/entity domain sözleşmeleri ve mevcut `WorldActorRegistry`; konum sahibi sürekli dünya konumu olacak şekilde evrimleştirilmeli.

### 2.5 Etkileşim ve hedef seçimi

**Modüller:** `interaction/profile.py`, `range.py`, `selection.py`, `target_query.py`.

**Mevcut kabiliyetler:**
- Etkileşim yarıçapı, hedeflenebilirlik, etiketler ve seçim önceliği.
- Sürekli dünya mesafesi ve ayrıca açıkça ayrı tutulan hex topolojik menzil.
- Mekânsal indeksle aday daraltma; sonra kesin mesafe/etiket kontrolü.
- Öncelik, mesafe ve kararlı kimlik ile deterministik hedef sıralaması.
- Aktiflik, dünya/harita eşleşmesi ve etkileşim türüne göre menzil doğrulaması.

**Ana oyun karşılığı:** `game_ui/world_rendering/hex_gameplay_view.py` içinde NPC'yi ekran konumundan hücreye çevirip o hücrede arama yapma ve mevcut diyalog/context-menu davranışları.

**Boşluk/risk:** Ana oyun NPC seçimi şu anda hücre eşleşmesine dayanıyor; laboratuvarın dünya mesafeli hedef sorgusu ana oyunda yerel olarak mevcut değil. Sağ tık menüsü boş kabuk olarak kalmalı; NPC başına eylemler içerik tanımlanınca belirlenecek. Bu envanter, yeni etkileşim eylemi ekleme izni değildir.

**Yerel hedef:** Uygulama etkileşim servisi; girdiden gelen ekran koordinatı önce kamera dönüşümüyle dünya koordinatına çevrilmeli, sonra hedef sorgusu yapılmalı. Sol tık mevcut diyalog akışını korumalı.

### 2.6 Dünya, harita ve runtime

**Modüller:** `world/identity.py`, `cell.py`, `map_definition.py`, `map_registry.py`, `world.py`, `world_view.py`, `runtime.py`, `movement_context.py`, `movement_resolution.py`.

**Mevcut kabiliyetler:**
- Dünya/harita/hücre kimliklerinin açık kapsamlandırılması.
- Immutable harita tanımı; mevcut hücrelerin açıkça listelenmesi ve olmayan hücre için ayrı sorgu/hata davranışı.
- Harita kayıt, yükleme/boşaltma ve dünya görünümü.
- Harita hücrelerini değiştirmeden tutan temel tanım ile yalnızca değişen hücre alanlarını saklayan sparse runtime override ayrımı.
- Sürekli dünya noktasından hücre çözümleme; önceki hücre yalnızca sınır eşitliği bağlayıcısı.
- Harita yüklenmiş mi ve hücre gerçekten mevcut mu doğrulaması.
- Hareket çözümlemesinde dünya/harita/hücre bağlamının korunması.

**Ana oyun karşılığı:** `application/hex_map_definition.py`, `application/hex_world_runtime.py`, world-map tanımları, occupancy ve pathfinding servisleri.

**Boşluk/risk:** Ana oyunun runtime'ı şu anda hücre hareketini ve occupancy'yi yetkili kabul ediyor. Laboratuvarın sparse hücre override davranışıyla ana oyunun içerik tanımı/runtime durumu aynı şey değil. İçerik tanımı değiştirilemez temel veri, runtime ise oyun sırasında değişen durum olarak ayrı kalmalı. Harita geçişi ve A* mevcut oyun sözleşmelerini korumalı.

**Yerel hedef:** Ana oyun `application` dünya servisleri ve `core` spatial domain. Sürekli konum yetkili; hücre verisi sorgu/occupancy/pathfinding için türetilmiş görünüm olmalı.

### 2.7 Kayıt ve yükleme

**Laboratuvar modülleri:** `world/persistence/map_serializer.py`, `map_deserializer.py`, `map_validator.py`, `file_storage.py`, `runtime_serializer.py`, `runtime_deserializer.py`, `runtime_validator.py`, `runtime_file_storage.py`, `errors.py`, `runtime_errors.py`. İçerik belgeleri için ayrıca `content/persistence/codec.py`, `file_storage.py`, `errors.py`.

**Laboratuvar kabiliyetleri:**
- Map schema v1 için katı, yan etkisiz JSON doğrulama.
- Deterministik serialization ve immutable map modeline deserialize.
- Yinelenen JSON anahtarlarını ve standart dışı NaN/Infinity değerlerini reddetme.
- Açık create/replace modu; aynı dizinde geçici dosya, fsync ve atomik yayımlama.
- Runtime snapshot'ta yalnızca değişmiş hücre alanlarını saklama.
- Runtime snapshot'ın world/map kimliğini ve temel haritanın SHA-256 parmak izini doğrulama.
- Restore öncesi tüm payload doğrulaması; dosya/şema/harita uyuşmazlığı için tipli hatalar.

**Önemli sınır:** İncelenen laboratuvar kalıcılık paketi harita tanımı ve hücre runtime override'larını kapsıyor. Laboratuvar `EntityRegistry` için tam bir varlık/oyuncu konum kayıt sistemi bulunmuyor. Bu nedenle laboratuvarın sürekli aktör konumlarını zaten kaydettiği varsayılmamalı.

**Ana oyun karşılığı:** `application/save_document.py` içindeki `GameSaveDocument` dış zarfı (mevcut sürüm 3), `save_codec.py`, `save_file_adapter.py`, `game_application.py`; ayrıca `application/hex_world_persistence.py` içindeki `rpg-hex-world` schema v1 `HexWorldSnapshot`.

**Boşluk/risk:** Ana oyunun hex snapshot'ı entity `map_id + q/r` hücresini, movement profile, aktiflik, occupancy blokları ve NPC patrol indekslerini saklıyor. Sürekli `WorldPoint`, hız/velocity ve laboratuvar hareket state'i mevcut hex snapshot sözleşmesinde yer almıyor. Dış save şeması v3 ve hex-world şeması v1 korunmalı; yeni konum modelinin kaydı için açık sürümleme, migration ve eski kayıtlarla uyumluluk tasarlanmalı. Harita geometrisi içerik sahibi olmaya devam etmeli; save içine gereksiz kopyalanmamalı.

**Yerel hedef:** Mevcut `GameSaveDocument` ve `HexWorldSnapshot` mimarisi. Yeni alanların kapsamı, varsayılanları ve migration davranışı belirlenmeden kayıt koduna dokunulmayacak.

### 2.8 Hareket, fizik ve simülasyon

**Modüller:** `movement/config.py`, `intent.py`, `mode.py`, `state.py`, `vector.py`, `integrator.py`; `physics/body.py`, `shapes.py`, `obstacle.py`, `broadphase.py`, `narrowphase.py`, `contacts.py`, `solver.py`, `continuous.py`, `hex_geometry.py`; `simulation/movement_system.py`, `collision_aware_movement_system.py`, `movement_cell_tracker.py`, `tick_coordinator.py`.

**Mevcut kabiliyetler:**
- Intent, yön vektörü, hareket modu ve immutable hareket state ayrımı.
- Normal, running ve stealth hız çarpanları.
- Dünya birimi/saniye cinsinden sürekli hareket integrasyonu.
- Sabit 60 Hz tick ile aktör başına ardışık tick doğrulaması.
- Circle ve convex polygon gövdeler; şekil dönüşümü.
- Broadphase aday sorgusu, narrowphase çarpışma, contact manifold ve deterministik çözüm.
- Sürekli circle sweep, time-of-impact, duvar boyunca kayma ve çözüm tanılama değerleri.
- Hareketten sonra hücre takibi; render ve wall-clock sahipliğinin simülasyondan ayrılması.
- Tick hata sonrası güvenli devam için pending tick checkpoint.

**Ana oyun karşılığı:** `application/hex_physics_bridge.py` ve `application/hex_actor_binding.py` üzerinden laboratuvar fizik tipleri; `HexWorldRuntime` ise hücre adımı hareketi. `HexGameplayView` içindeki 0.18 saniyelik interpolasyon yalnızca görseldir.

**Boşluk/risk:** Sürekli hareket ana oyunun yetkili runtime'ında henüz yok. Ana oyuncu gövdesi için onaylı collider yarıçapı 8 world unit; NPC ve çevre nesnelerinin collider boyutları belirlenmiş değildir. Yeni boyut varsayımı yapılmayacak.

**Yerel hedef:** Simülasyon hareket sistemi ana oyun domain/application katmanında; fizik çözümü ayrı fizik servisi; 60 Hz tick mevcut canonical tick sahipliğiyle uyumlu. Render interpolasyonu simülasyon konumunun yerine geçmemeli.

### 2.9 Varlık/içerik tanımı, çevre nesneleri ve render

**Modüller:** `content/definition.py`, `library.py`, `placement.py`, `map_document.py`, `collision.py`, `values.py`; `environment/definition.py`, `placement.py`, `scene.py`, `presentation.py`; `rendering/snapshot.py`, `visibility.py`, `pygame_world_renderer.py`, `content_adapters.py`, `environment_assets.py`, `procedural/*`.

**Mevcut kabiliyetler:**
- Yeniden kullanılabilir içerik tanımı ile harita yerleşiminin ayrılması.
- İçerik kimliği, görsel metadata, ground anchor/depth anchor ve isteğe bağlı açık collider.
- Dünya/harita kapsamlı çevre nesnesi yerleşimleri ve doğrulanan scene.
- Görsel bounds ile fizik collider'ının birbirinden ayrılması; yalnızca açık collider fizik engeli olur.
- Render için immutable snapshot DTO'ları; sprite foot/ground anchor, depth anchor, layer priority, collider/debug görselleri.
- Tek kamera transform'u üzerinden Pygame render.
- Görünür hücre sorgusunda konservatif culling (false negative üretmemek için).
- İçerik kütüphanesinden environment/physics/render modellerine açık adaptörler.
- Procedural yüzey üretimi ve cache.

**Ana oyun karşılığı:** `content` ve map content loader/placement modelleri; `game_ui/world_rendering` terrain, character, depth sort ve gameplay view katmanları. Ana oyun zaten kendi görsel varlık ve içerik sahipliğine sahip.

**Boşluk/risk:** Laboratuvarın procedural/demo görsel profilleri veya örnek sahneleri kendiliğinden ana oyuna aktarılmayacak. Aktarılacak olan teknik sözleşmeler: ground/depth anchor, açık collider tanımı, immutable render snapshot, görünürlük sorgusu ve kamera transform disiplinidir. Kullanıcı tarafından onaylanmamış NPC/prop collider ölçüleri türetilmeyecek.

**Yerel hedef:** İçerik tanımları ana oyunun `content` alanında; çevre nesnesi ve render adaptörleri ana oyunun `application`/`game_ui` sınırında. UI/renderer, domain state'i değiştirmemeli.

### 2.10 Girdi, companion komutları ve demo katmanı

**Modüller:** `input/pygame_keyboard.py`; `companions/command.py`, `relationship.py`, `roster.py`; `application/demo_tick_pump.py`, `movement_demo.py`, `entity_demo.py`.

- Girdi adaptörü klavye girdisini movement intent'e çevirir; mod seçimi testlidir.
- Companion prototipi FOLLOW/WAIT/RETURN komutlarını ve WAIT konumunu ilişki state'inde saklar; komut tek başına NPC'yi hareket ettirmez.
- Demo tick pump, demo sahneleri ve demo uygulaması laboratuvarın deney/kanıtlama katmanıdır.

**Ana oyun karşılığı:** Pygame event/input ve mevcut actor/NPC uygulama akışları. Yoldaş komutları ileride oyun kapsamına girdiğinde mevcut Eldoria NPC/companion mimarisiyle uyarlanmalıdır; laboratuvar demo roster'ı taşınmamalı.

**Sınır:** Demo launcher, demo tick pump, demo world, test görsel içerikleri ve laboratuvar sahneleri ana oyuna aktarım kapsamı değildir.

## 3. Test envanteri ve doğrulama kanıtları

Laboratuvarda aşağıdaki test grupları bulunduğu doğrulandı:

- **Unit:** geometri/koordinat, mesafe, komşular, tolerans, kamera controller/follow/transform, movement intent/mode/config/state/integrator, collision-aware movement, physics body/placement/broadphase/continuous/narrowphase/solver/hex geometry, spatial indexes, entity-interaction-companions, world identity/map definition/map registry/runtime/world view, map/runtime persistence, content persistence/adapters, environment definitions/placements/presentation, Pygame keyboard, render visibility/order/subpixel/sprite anchor/procedural asset tests.
- **Integration:** uygulama lifecycle, entity-world lifecycle, map ve runtime persistence, geometry consistency, keyboard movement flow, movement tick contract, movement world integration, movement demo camera/FPS/render/lifecycle, Pygame world renderer, environment object rendering.
- **Acceptance:** Phase 12 environment scenes, Phase 14 content documents ve render visual scenes.
- **Stress:** entity spatial stress ve simulation geometry stress.

Önemli test örnekleri:
- `test_coordinates.py`, `test_transforms.py`, `test_distance.py`, `test_neighbors.py`
- `test_camera_controller.py`, `test_camera_follow_bounds.py`, `test_camera_transform.py`
- `test_spatial_indexes.py` (grid/quadtree için rastgele sorguların doğrusal referansla karşılaştırılması)
- `test_entities_interaction_companions.py`
- `test_world/test_map_definition.py`, `test_world/test_map_registry.py`, `test_world/test_runtime.py`
- `test_persistence/test_file_storage.py`, `test_runtime_file_storage.py`, `test_runtime_serializer.py`, `test_runtime_validator.py`
- `test_entity_world_lifecycle.py`, `test_map_persistence.py`, `test_runtime_persistence.py`, `test_movement_tick_contract.py`

Bu envanter GitHub'daki test dosyalarını ve amaçlarını tespit eder; laboratuvar test paketinin bu oturumda yeniden çalıştırıldığı anlamına gelmez. Bu raporda test sonucu veya yeni CI başarısı iddia edilmemektedir.

## 4. Ana oyunla bağımlılık ve sahiplik denetimi

Ana oyun çalışma dalında:
- `pyproject.toml` paket keşfine `hex_world_lab*` dahil edilmiş durumda.
- `application/hex_world_geometry_bridge.py`, laboratuvar geometri ve dünya kimliği tiplerini doğrudan import ediyor.
- `application/hex_physics_bridge.py`, laboratuvar vektör, fizik, çarpışma ve obstacle index tiplerini doğrudan import ediyor.
- `application/hex_actor_binding.py`, laboratuvar `EntityId` ve `BodyDefinition` tiplerini doğrudan import ediyor.

Bu, laboratuvarın yalnızca dışarıdan referans olarak tutulmadığını; ana oyunun runtime bağımlılık grafiğine girdiğini gösterir. Bu bağımlılık, hedef mimari için geçici kabul edilmelidir.

**Güvenli ayrıştırma kuralı:** Bu importlar şimdi silinmeyecek. Önce her davranışın Eldoria'daki yerel karşılığı kurulacak, tüm tüketiciler taşınacak ve testler doğrulanacak. Ancak bundan sonra `hex_world_lab` paket keşfinden ve ana oyun runtime bağımlılıklarından çıkarılabilir. Laboratuvarın bağımsız deney dalı/dizini korunur.

## 5. Aktarım önceliği ve bağımlılık sırası

1. **Sahiplik ve sözleşmeler:** Eldoria entity kimliği, sürekli world position, harita/world scope ve koordinat bazını tekilleştir.
2. **Geometri:** Lab importlarını kaldıracak yerel axial/world transform, sınır tie-break ve tolerans sözleşmeleri.
3. **Kamera/render koordinatları:** Sürekli dünya konumu ve kamera dönüşümünü ana oyunda aynı koordinat sözleşmesine bağla.
4. **Hareket ve tick:** Intent/config/mode/integrator ve mevcut canonical tick ile sabit adım; render state'den bağımsız.
5. **Fizik:** Gövde/şekil, broadphase, narrowphase, sweep/solver ve collision world; yalnızca onaylanmış collider verileriyle.
6. **Mekânsal indeks ve entity lifecycle:** Kayıt, hareket güncellemesi, harita unload/reload ve sorgu tutarlılığı.
7. **Etkileşim:** Ekran→dünya dönüşümü, hedef sorgusu, gerçek mesafe ve mevcut NPC diyalog akışına adaptasyon.
8. **Dünya/çevre/render snapshot:** İçerik ile yerleşim ayrımı, ground/depth anchor, görünürlük ve render saflığı.
9. **Kayıt/yükleme:** Sürekli konum ve ilgili runtime state için açık şema kararı, migration, eski kayıt testleri ve atomic save uyumu.
10. **Bağımlılık temizliği:** Ana oyundaki tüm `hex_world_lab` importları ve paket keşfi ancak yerel karşılıklar doğrulandıktan sonra kaldırılır.

Bu sıra teknik bağımlılıkları ifade eder; yeni özellik yol haritası değildir.

## 6. Koruma kuralları

- Çalışma yalnızca `experiment/map-cleanup` dalında yapılır.
- `experiment/hex-world-laboratory` referans/deney dalıdır; değiştirilmez.
- `demo_eldoria` ve `main` korumalı hedef dallardır; açık onay olmadan merge yapılmaz.
- Kare/hücre tabanlı konumdan sürekli world position'a geçiş açık ve testli olmalı; iki yetkili konum kaynağı birlikte yaşatılmamalı.
- Axial baz/y-yönü dönüşümü tek bir yerel domain sözleşmesinde tanımlanmalı.
- Oyuncu collider yarıçapı 8 world unit olarak onaylıdır. NPC ve statik çevre collider ölçüleri onaylı değildir.
- NPC sol tık mevcut diyalog ekranını açar. Sağ tık boş aksiyon menüsü kabuğu olarak kalır; NPC başına eylemler şimdilik eklenmez.
- Save schema veya migration sessizce değiştirilmez.
- Laboratuvar demo ekranı, demo launcher, ayrı game loop ve deneysel içerik ana oyuna taşınmaz.
- Bu aşamada yeni oynanış özelliği, içerik veya kapsam genişlemesi yapılmaz.

## 7. Açık teknik kararlar — uygulamadan önce

1. Sürekli world position'ın Eldoria domain modelindeki kesin sahibi ve koordinat birimi.
2. Dünya koordinatlarının yönü ve mevcut y-aşağı Pygame sunumuyla tek dönüşüm sınırı.
3. Hareket simülasyon tick'inin mevcut canonical tick sistemiyle bağlanma noktası.
4. Oyuncu dışındaki actor/NPC/prop collider verilerinin nereden ve hangi onayla sağlanacağı.
5. Harita hücre occupancy/pathfinding sorgularının sürekli konumdan türetilme kuralları.
6. Mevcut `rpg-game-save` v3 ve `rpg-hex-world` v1 ile sürekli konum için migration/geriye uyumluluk kararı.
7. Lab'daki entity persistence eksikliği nedeniyle entity transform, movement state ve velocity için ana oyunun hangi verileri kalıcı saklayacağı.

## 8. Sonuç

Laboratuvar envanterinin ana alanları tespit edilmiştir. En büyük aktarım boşluğu, laboratuvarın sürekli dünya-konumlu entity/movement modelinin ana oyunda hâlâ hücre-merkezli runtime ve laboratuvar köprüleri üzerinden temsil edilmesidir. Geometri, kamera, spatial index, entity, interaction, world, rendering ve persistence kabiliyetleri tek tek eşleştirilmiştir.

**Bu rapor entegrasyonun tamamlandığını söylemez.** Envanterden sonraki iş, açık teknik kararları mimari sözleşmeye dönüştürmek ve ardından yerel Eldoria karşılıklarını küçük, testli adımlarla uygulamaktır. Hiçbir uygulama değişikliği bu raporla birlikte yapılmamıştır.
