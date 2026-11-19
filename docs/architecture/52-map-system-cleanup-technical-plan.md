# Harita Sistemi Temizliği — Ayrıntılı Teknik Plan

| Alan | Değer |
|---|---|
| Çalışma dalı | `experiment/map-cleanup` |
| Kaynak dal | `demo_eldoria` |
| Başlangıç commit'i | `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Genel plan | [51-map-system-cleanup-general-plan.md](51-map-system-cleanup-general-plan.md) |
| Hex runtime migration | [54-hex-runtime-authoritative-gameplay-migration.md](54-hex-runtime-authoritative-gameplay-migration.md) |
| Durum | Kullanıcı onayı alındı; 16.1 teknik baseline tamamlandı; görsel test gerekmiyor |

## 1. Teknik karar özeti

Bu temizliğin hedefi iki harita sistemini eşit ölçekte yaşatmak veya kare haritayı altıgen sisteme dönüştürmek değildir.

**Ana oyun haritası:** Altıgen (axial) dünya sistemi, ana oyunun tek yetkili dünya/harita sistemi olacaktır. Oyuncunun normal dünya dolaşımı, dünya yerleşimleri, haritalar arası ana oyun geçişleri ve ilgili runtime sorumlulukları bu sistemde toplanacaktır.

**Kare harita easter egg'i:** Kare harita sistemi, gelecekte detaycı oyuncuların keşfedebileceği tek ve sabit bir harita olarak korunacaktır. Bu bir ikinci ana dünya sistemi değildir. Yalnızca o tek haritayı yüklemek, göstermek ve ileride ayrıca kararlaştırılacak sınırlı etkileşimi desteklemek için gereken asgari kod/veri tutulacaktır.

Kare harita easter egg'i için mimari sınırlar:

- Tam olarak bir kare harita içeriği korunacaktır. Hangi mevcut haritanın temel alınacağı, 16.1–16.2 envanterinde gerçek JSON içerikleri ve bağımlılıkları incelendikten sonra belirlenecektir; dosya adına bakılarak seçim yapılmayacaktır.
- Kare harita için yeni harita kataloğu, çoklu harita ağı, harita editörü, prosedürel üretim veya genel amaçlı genişletilebilir harita platformu geliştirilmeyecektir.
- Kare haritanın kendi yerel `(x, y)` koordinatları korunabilir; bu koordinatlar axial `(q, r)` dünya koordinatlarına çevrilmeyecek ve ortak bir koordinat modeline zorlanmayacaktır.
- Kare harita kendi başına ikinci bir dünya simülasyonu, dünya saati, kaynak döngüsü, NPC yaşam simülasyonu veya bağımsız save dünyası hâline getirilmeyecektir.
- Kare haritaya giriş/çıkış biçimi ürün/tasarım kararıdır. Teknik mimari, ileride tek bir kontrollü erişim noktası veya sahne geçişi eklenmesine izin verebilir; fakat bu temizlik aşamasında erişim yöntemi ve hikâye açıklaması tasarlanmayacaktır.
- Kare harita ile ana altıgen dünya arasında doğrudan konum/state paylaşımı kurulmayacaktır. Gerekirse yalnızca açıkça tanımlanmış sahne sınırı/erişim adaptörü kullanılacaktır.
- Tek kare harita için zorunlu olmayan eski kare dünya kodları, harita dosyaları ve testler bağımlılık kanıtı toplandıktan sonra deprecate/remove adayı olacaktır. Silme kararı otomatik değildir.

İlk kaynak incelemesi iki paralel yerel harita modelini doğruluyor:

- Schema v1 kare harita: `world/map_definition.py`, `world/map_loader.py`, `world/map_catalog.py`.
- Schema v2 axial altıgen harita: `application/hex_map_definition.py`.
- İçerik paketi yükleyici: `application/content_loader.py`.
- Altıgen dünya yerleşimi: `application/world_map_definition.py` ve `content/demo_eldoria/world.json`.
- Altıgen hareket/runtime: `application/hex_world_runtime.py`, `hex_movement_rules.py`, `hex_occupancy.py`, `hex_pathfinding.py`, `hex_transition_service.py`.
- Kare dünya/konum grafı ve eski runtime: `world/`, `core/world/`.
- UI tarafında kare ve altıgen yollar: `game_ui/screens/main_screen.py`, `map_screen.py`, `game_ui/hex_world_view.py`.

Bu envanter, mevcut kare modüllerin tamamının easter egg için gerekli olduğu anlamına gelmez. Nihai koruma kümesi tek haritanın gerçek yükleme/gösterim/etkileşim bağımlılıklarıyla sınırlandırılacaktır.

## 2. Başlangıç deposu ve kanıt sınırı

Dal `demo_eldoria` HEAD `7d53d431d5c3639fd95d273de9043b64483a5125` commit'inden çıkarılmıştır. Uygulama başlangıç HEAD'i `1705497305339675df25928c7272eb9b10aba7a2` olarak kaydedilmiştir. GitHub recursive tree yanıtı 607 girdi içerir (`truncated=false`). İçerik paketindeki 16 map JSON'un gerçek schema alanları okunmuştur: 9 adet schema v1 kare harita ve 7 adet schema v2 axial hex harita. İki hex placement JSON'u ve bir hex world JSON'u vardır.

Kesin içerik envanteri, çalışma zamanı bulguları ve CI kanıtı [Aşama 16.1 Baseline Raporu](53-map-cleanup-phase-16-1-baseline.md) içinde tutulur.

GitHub Actions Core quality run `44411974271`, bu HEAD'de Linux/Python 3.11 ve Windows/Python 3.12 işlerinde başarılıdır. Bu workflow Pytest, compileall, wheel paketleme/izole yükleme ve application smoke çalıştırır. Workflow'da Ruff adımı yoktur. Bu çalışma için yerel Windows görsel testi gerekmiyor; davranış değişikliği olmayan teknik temizlik otomatik test ve CI ile doğrulanacaktır.

## 3. Hedef mimari ve teknik sınırlar

### 3.1 Ana altıgen dünya — yetkili sistem

- Ana oyun haritaları ve dünya yerleşimleri axial altıgen sözleşmelerini kullanır.
- `application/hex_world_runtime.py` ve ilgili servislerin hareket, occupancy, geçiş ve dünya state'i üzerindeki sahipliği envanterle doğrulanır.
- `WorldMapDefinition` ile legacy `WorldMap` aynı kavrammış gibi ele alınmaz; ana oyun için hangisinin yetkili olduğu ve eski adaptörlerin gerekliliği belgelenir.
- UI, kamera ve renderer yalnızca authoritative gameplay state'i okur; ikinci bir hareket/konum state'i üretmez.
- Ana oyun save/restore sözleşmesi ve mevcut içerik paketi yükleme akışı korunur veya değişiklik gerekiyorsa sürümlü migration ile ele alınır.

### 3.2 Tek kare harita — sınırlı easter egg

Envanter sonucunda mevcut kare haritalar arasından tek bir içerik seçilecek veya mevcut içerik güvenle sadeleştirilerek tek bir harita hâline getirilecektir. Seçim gerekçesi; veri bütünlüğü, görsel/oynanış değeri, mevcut referanslar ve save uyumluluğuna dayanacaktır.

Korunabilecek asgari parçalar, gerçek bağımlılık grafiğine göre belirlenecektir:

- Tek harita için gerekli veri tanımı ve doğrulama.
- Tek harita verisini okuyacak en küçük loader yolu.
- Haritayı göstermek için gereken çizim/UI yolu.
- Tasarım daha sonra etkileşim gerektirirse, yalnızca bu harita için gerekli sınırlı etkileşim sözleşmesi.
- Tek haritanın tanımlayıcı kimliği ve varsa güvenli erişim/çıkış sınırı.

Kapsam dışında:

- Birden fazla kare harita yüklemek veya kare haritalar arasında genel geçiş ağı.
- Genel amaçlı kare dünya kataloğu/manager'ı; tek harita için zorunlu olduğu kanıtlanmadıkça korunmayacaktır.
- Kare dünya üzerinde bağımsız simülasyon, kaynak üretimi, NPC AI, zaman döngüsü veya yeni ekonomi.
- Kare/hex koordinat dönüşüm katmanı.
- Harita editörü, prosedürel kare harita üretimi, yeni kare harita içerikleri.
- Kare haritayı ana dünya haritası veya alternatif oyun modu olarak sunmak.

Easter egg'in oyuncuya nasıl sunulacağı, nerede bulunacağı ve hangi hikâye/ödül/etkileşimi içereceği bu teknik temizlik planının dışındadır. Bu ayrıntılar daha sonraki içerik tasarımında kararlaştırılacaktır.

### 3.3 Koordinat ve sahne sınırı

- Kare harita içindeki hücre adresi `(x, y)`; ana altıgen dünya koordinatı axial `(q, r)` olarak kalır.
- Piksel/screen koordinatları her iki modelin de sunum katmanında kalır; domain koordinatı olarak saklanmaz.
- Kare harita ile hex dünya arasında otomatik veya örtük koordinat dönüşümü yapılmaz.
- İleride erişim/çıkış gerekirse, iki sistem arasında yalnızca açık bir sahne geçiş sözleşmesi kurulur. Oyuncu konumunun hangi sistemde authoritative olduğu geçiş sırasında tanımlanır; aynı anda iki runtime konumun sahibi olamaz.
- Tek kare haritanın kendi içinde gerekli değilse `EntityPosition`, `LocalHexPosition`, `WorldHexPosition` ve `HexCoord` türleri kare sisteme taşınmaz.

### 3.4 İçerik, asset ve save sahipliği

İncelenecek dosyalar:
- `content/demo_eldoria/manifest.json`
- `content/demo_eldoria/maps/*.json`
- `content/demo_eldoria/world.json`
- `content/demo_eldoria/placements/*.json`
- `content/demo_eldoria/asset_catalog.json`
- `content/demo_eldoria/presentation_assets.json`
- `application/content_loader.py`
- `application/world_map_definition.py`, `application/hex_map_definition.py`
- `world/map_definition.py`, `world/map_loader.py`, `world/map_catalog.py`

Kontroller:

1. Manifestteki her path'in paket kökü içinde kaldığı ve gerçek dosyaya karşılık geldiği doğrulanır.
2. Altıgen ana dünya map ID'leri ve transition hedefleri doğrulanır.
3. Tek kare easter egg haritasının ID'si, içeriği ve asset/placement referansları belirlenir.
4. Kullanılmayan diğer kare map JSON dosyalarının kod, test, manifest, içerik ve save referansları aranır.
5. Eski save'lerde birden fazla kare map ID'sine referans bulunup bulunmadığı araştırılır. Gerekli uyumluluk kararı verilmeden dosya veya ID kaldırılmaz.
6. `AssetCatalog`, `ScenePlacementCatalog`, `PresentationContentService` ve `PresentationContentStore` ana oyun içerik hattının sahipleridir; laboratuvar modeliyle karşılaştırılmadan çoğaltılmaz veya silinmez.
7. Kaynak içerikler değişiklik öncesi baseline olarak saklanır; JSON normalize/format-only yazımı da ayrıca diff ile gözden geçirilir.

## 4. Katman bazlı teknik envanter

### 4.1 Dünya ve domain/runtime

İncelenecek dosyalar:
- `world/local_map.py`, `world/location.py`, `world/map.py`, `world/movement.py`
- `core/world/world.py`, `core/world/world_id.py`, `core/world/world_manager.py`, `core/world/legacy_runtime.py`
- `application/world_map_definition.py`
- `application/hex_world_runtime.py`, `application/hex_transition_service.py`
- `core/domain/spatial/` içindeki `EntityPosition`, `LocalHexPosition`, `WorldHexPosition`, `HexCoord` ve geometry sözleşmeleri.

Kontroller:
- Kare modüllerin hangilerinin yalnızca tek haritayı yüklemek/göstermek için gerekli olduğu import/call graph ile kanıtlanır.
- Tek kare haritanın ihtiyaç duymadığı çoklu map catalog, world manager, transition graph ve legacy runtime bileşenleri sadeleştirme adayıdır.
- Ana altıgen dünyanın authoritative hareket/konum kaynağı tek olmalıdır.
- Harita unload/load, dormant actor ve save/restore davranışları ana oyun açısından izlenir.
- Pathfinding veya hareket algoritmaları yalnızca temizlik hedefiyle değiştirilmez.

### 4.2 UI, kamera ve render

İncelenecek dosyalar:
- `game_ui/screens/main_screen.py`, `game_ui/screens/map_screen.py`
- `game_ui/hex_world_view.py`
- `game_ui/camera.py`, `game_ui/world_transform.py`
- `game_ui/world_rendering/`
- `game_ui/renderer.py`, `game_ui/scaled_renderer.py`

Kontroller:
- Kare harita ekranının mevcut gameplay yolundaki rolü ve tek harita easter egg'i için gereken minimum UI yolu ayrıştırılır.
- `MainScreen` içindeki H tuşuyla altıgen dünyaya giriş/çıkış yolu ve geçici bridge davranışı incelenir; ürün akışı netleşmeden körlemesine silinmez.
- Nihai mimaride normal gameplay'in altıgen dünya yolunu kullanması; kare harita yolunun ise yalnızca tek easter egg sahnesiyle sınırlı olması hedeflenir.
- Kamera, viewport, world transform ve screen coordinate dönüşümleri ayrı sorumluluklar olarak korunur.
- Render işlemi authoritative simülasyon state'ini değiştirmemelidir.
- Görsel varlıklar ve sahne yerleşimleri mevcut catalog/store sözleşmeleri üzerinden okunmalıdır.

### 4.3 Test envanteri

Asgari test kümeleri:
- `tests/test_world/`: kare harita tanımı/loader testleri; tek harita koruma kapsamı belirlendikten sonra çoklu harita varsayımları ayrıştırılır.
- `tests/test_application/`: content loader, hex runtime, movement, world object placement, presentation content service/store, persistence/session.
- `tests/test_game_ui/`: main screen/map data/transitions, hex view/camera, renderer, placement/asset catalog, world transform.
- `tests/test_foundation/`: hex coordinate/geometry, local/world hex position, position.
- `tests/test_architecture/`: core/world boundary ve world model boundary.
- `tests/test_compatibility/`: legacy world clock/scheduler/runtime adapters ve migration tooling.
- `tests/test_persistence/`: save/restore sözleşmeleri ve document bridge.

Test hedefleri:
- Ana altıgen dünya için mevcut çoklu harita/dünya davranışları ve içerik referansları korunur.
- Kare harita testleri, korunacak tek haritanın yüklenmesi, veri bütünlüğü ve gerekli sunum/etkileşim davranışıyla sınırlandırılır.
- Silinecek eski kare harita altyapısı için önce characterization test ve bağımlılık kanıtı oluşturulur.
- Testi olmayan davranış, kaldırma için otomatik izin sayılmaz.

## 5. Uygulama fazları ve değişiklik kapıları

### 16.1 — Baseline ve characterization (teknik inceleme tamamlandı)

- Başlangıç HEAD'i, 16 harita JSON'unun gerçek schema sürümleri, map ID'leri, hex world ve placement içerikleri kaydedildi.
- CI run 44411974271 Linux ve Windows işlerinde başarılı; test/derleme/paketleme/smoke kapsamı raporda kayıtlıdır.
- Normal oynanabilir akışın bugün kare dünya üzerinde olduğu; H tuşunun bağımsız ve geçici hex runtime açtığı kod/test üzerinden doğrulandı.
- HexWorldView.enter() oyuncuyu hex başlangıç hücresine yeniden kaydediyor; leave() runtime'ı atıyor. Hex konumu ana actor state'ine yazılmıyor ve tekrar girişte korunmuyor.
- NPC, kaynak, market, kare map transition, save/restore, paketleme ve release verification bağımlılıkları raporlandı.
- Ayrıntı: [Aşama 16.1 Baseline Raporu](53-map-cleanup-phase-16-1-baseline.md).
- Görsel kabul bu teknik temizlik aşamasında istenmez.

**Kapı:** Teknik baseline raporu ve CI kanıtı mevcuttur. Hex runtime sahipliği çözülmeden kare harita dosyaları kaldırılmaz.

### 16.2 — Altıgen runtime'ın authoritative ana oyun sistemi olması

- [54 numaralı migration planındaki](54-hex-runtime-authoritative-gameplay-migration.md) tek konum yazarı, runtime lifecycle, occupancy ve render/input sınırı uygulanır.
- HexWorldRuntime aktif oyun oturumunun parçası olur; HexWorldView yalnızca sunum/input adaptörü olarak kalır.
- Aynı entity için paralel kare ve hex konum kaynakları kaldırılır.
- H portal/temporary enter-leave akışı normal oyun akışından çıkarılır.

**Kapı:** Ana oynanış hex runtime'dan konum/hareket okumalı; tek authoritative konum ve occupancy testlerle kanıtlanmalıdır.

### 16.3 — Hex içerik ve gameplay referanslarının entegrasyonu

- Başlangıç konumu, NPC'ler, resource landmark'ları, market/trade partner ve dünya nesnesi referansları axial içerik sözleşmesine geçirilir.
- Quest'lerin NPC/resource ID referansları korunur.
- Kare harita katalogları ana gameplay içerik doğrulamasından ayrılır; tek easter egg sınırında tutulur.

**Kapı:** Starter package kare map catalog olmadan ana hex dünyayı yükleyebilmeli; içerik referans testleri geçmelidir.

### 16.4 — Persistence ve legacy kayıt uyumluluğu

- Axial entity konumları ve occupancy save/restore sözleşmesine alınır.
- Yeni save round-trip ve bozuk referans doğrulamaları eklenir.
- Eski kare save'ler için açık migration/recovery politikası test edilmeden map dosyaları kaldırılmaz.

**Kapı:** Yeni hex save/load ve legacy kayıt güvenliği otomatik testlerle kanıtlanmalıdır.

### 16.5 — Ana oyun UI/render akışını hex runtime'a bağlama

- MainScreen normal oyun akışında hex runtime'ı kullanır; portal akışı kaldırılır.
- GameWindow pencere sistemi korunur; renderer runtime state'ini değiştirmez.
- Kare sistem ana gameplay çağrı zincirinden ayrılır; easter egg geçici olarak korunur.

**Kapı:** Otomatik input/render/transition testleri geçmelidir.

### 16.6 — Kare sistemi tek easter egg'e indirme

- Tek korunacak kare easter egg haritası bağımlılık ve içerik kanıtıyla seçilir.
- Diğer sekiz kare harita ve kullanılmayan kare world graph/runtime modülleri, kod/import/content/save/test referansları sıfırlandıktan sonra kaldırılır.
- Kare (x,y) koordinat modeli kendi sınırında kalır; hex koordinatlarına dönüştürülmez.

**Kapı:** Hex ana oyun kare map catalog olmadan çalışır; tek easter egg ayrı yüklenir; eski save politikası güvenlidir.

### 16.7 — Tam otomatik regresyon ve teknik kabul

- Temiz kurulum, Pytest, Ruff, compileall, wheel ve release verification çalıştırılır.
- Ana hex dünya, içerik, geçiş, hareket, NPC/resource/market/quest/container etkileşimleri ve save/load doğrulanır.
- Tek kare easter egg'in yükleme ve sunum testleri çalıştırılır.
- Linux/Python 3.11 ve Windows/Python 3.12 CI işleri başarılı olmalıdır.
- Görsel kabul testi istenmez.

**Kapı:** Otomatik kalite ve paketleme kapılarının tamamı başarılı olmalıdır.

### 16.8 — Kapanış ve entegrasyon sözleşmesi

- Ana altıgen dünya mimarisi ve korunacak tek kare harita easter egg yüzeyi belgelenir.
- Temizlenen/kalan legacy bileşenler listelenir.
- Harita veri şeması, runtime authority, koordinat sınırı, render adapter ve asset ownership kararları kaydedilir.
- Laboratuvar A15 raporundaki altı entegrasyon blocker'ının hangilerinin çözüldüğü ve hangilerinin entegrasyon aşamasına kaldığı eşleştirilir.
- Hazır / koşullu hazır / hazır değil kararı verilir.

**Kapı:** Teknik kapanış raporu, otomatik doğrulama kanıtı ve branch koruma denetimi olmadan sonraki entegrasyon aşaması açılmaz; demo_eldoria'ya merge için kullanıcı onayı korunur.

## 6. Korumalı sözleşmeler

Aşağıdakiler açık karar olmadan değiştirilemez:

- `content/demo_eldoria/manifest.json` paket sözleşmesi ve path güvenliği.
- Ana altıgen harita schema/ID/transition/world placement sözleşmeleri.
- Seçilecek tek kare easter egg haritasının schema, ID ve gerekli veri alanları.
- `EntityPosition`, `LocalHexPosition`, `WorldHexPosition` ve axial koordinatların anlamı.
- Ana oyun başlangıç konumu ve harita geçiş semantiği.
- Save document sürümü, restore sırası, actor/world bağları ve eski save uyumluluğu.
- Asset catalog ve scene placement referansları.
- Public GameplayService API ve `main.py --play` giriş akışı.

Kullanılmayan kare harita dosyalarının kaldırılması ancak tek harita kararı, save referans incelemesi, dependency kanıtı, test ve rollback planı sonrasında yapılabilir. Bu belge, tek kare haritanın kimliğini envanter tamamlanmadan varsaymaz.

## 7. Kabul/test matrisi

| Alan | Test/kanıt | Kabul ölçütü |
|---|---|---|
| Paket yükleme | content loader tests + tüm paket | manifest ve ana dünya referansları doğrulanır |
| Ana altıgen dünya | hex loader/runtime tests | ana dünya haritaları ve world placements geçerli |
| Tek kare easter egg | square loader + UI tests | yalnızca seçilen tek kare harita gerekli asgari yolla yüklenir/gösterilir |
| Kare harita kapsamı | dependency/import/save audit | ikinci bir kare harita veya genel kare dünya altyapısına gereksiz bağımlılık kalmaz |
| Geçiş/sahne sınırı | transition + characterization tests | ana dünya akışı korunur; varsa easter egg sınırı açık ve tekil |
| Konum sahipliği | movement/runtime tests | ana dünyada tek authoritative state; kare sahneyle örtük state paylaşımı yok |
| Çarpışma/occupancy | movement/occupancy tests | ana dünya hareket engelleri ve occupancy korunur |
| Görsel sunum kodu | Değişiklik yoksa test gerekmez; renderer değişirse ilgili render/unit testleri | Teknik temizlik görsel davranışı değiştirmez |
| Kayıt/yükleme | persistence/session tests | eski save'ler bozulmaz; kare map referansları güvenle ele alınır |
| Paketleme | clean install / release verification | gerekli hex içerikleri ve tek kare easter egg pakete dahil |
| Mimari sınırlar | architecture tests | domain/application/UI import sınırları korunur |
| Kalite | Pytest, Ruff, GitHub Actions | ilgili bütün zorunlu işler başarılı |

## 8. Geri alma stratejisi

- Her mantıksal değişiklik ayrı commit; büyük dosya taşıma ve davranış değişikliği aynı commit'te birleştirilmez.
- JSON migration öncesi kaynak dosyalar commit ile korunur; migration dry-run çıktısı gözden geçirilir.
- Kare harita silme/deprecation işlemleri, tek harita seçimi ve save referans denetiminden ayrı commit'lerde yapılır.
- Bir aşama başarısız olursa son yeşil commit'e dönülür; sonraki aşamaya geçilmez.
- Temizlik dalı başarısız olsa bile `demo_eldoria`, `main` ve laboratuvar dalı değişmeden kalır.
- Aşama kapanışında temizleme dalı birleştirilmeden önce kullanıcıya diff özeti ve test kanıtı sunulur.

## 9. Açık riskler

1. **Tek kare haritanın seçimi:** Mevcut kare map JSON'larından hangisinin korunacağı içerik ve bağımlılık incelemesiyle belirlenmelidir.
2. **Legacy kare runtime kapsamı:** Tek harita için gereken loader/render kodu ile gereksiz çoklu dünya altyapısı ilk bakışta iç içe olabilir.
3. **Geçici UI bridge:** H-key hex giriş/çıkışı test/demo kolaylığı için eklenmiş olabilir; ürün akışı netleşmeden kaldırılmamalı.
4. **Legacy world manager:** `core/world` ile `application` world/runtime sorumluluklarının tam sınırı import ve call graph ile kanıtlanmalı.
5. **Asset/placement paralelliği:** Combined `presentation_assets.json` ile ayrılmış `asset_catalog.json` + `placements/` backward compatibility yolu birlikte mevcut.
6. **Save uyumluluğu:** Eski save'lerde artık korunmayacak kare map ID'leri varsa açık migration/compatibility kararı gerekir.
7. **Test kapsama boşluğu:** UI/render davranışında değişiklik yapılırsa manuel kontrol yerine otomatik characterization/render testleri eklenmelidir.
8. **Easter egg erişimi:** Nerede/nasıl bulunacağı ve sahneye giriş/çıkış biçimi ürün tasarımıdır; teknik temizlik bunu varsaymamalıdır.

## 10. Uygulama durumu ve sıralama kararı

Kullanıcı, altıgen runtime'ın ana oyun entegrasyonunun kare haritaların son temizliğinden önce yapılmasını onayladı. Bu karar [54 numaralı migration planında](54-hex-runtime-authoritative-gameplay-migration.md) ayrıntılandırılmıştır. Uygulama sırası 16.2 runtime sahipliği, 16.3 içerik/gameplay referansları, 16.4 persistence, 16.5 UI entegrasyonu, 16.6 tek kare easter egg temizliği ve 16.7 otomatik teknik doğrulamadır.

Kullanıcı görsel test istemediğini açıkça belirtti. --play manuel kontrolü istenmeyecek; teknik kararlar kod, bağımlılık grafı, Pytest, Ruff, paketleme ve GitHub Actions ile doğrulanacaktır. Kare save konumları için örtük kare→hex dönüşümü yapılmayacak. Korunan dallar değiştirilmeyecektir.

## 11. Kullanıcı kararı eki — 2026-11-19 (önceki faz sıralamasını geçersiz kılar)

### 11.1 Demo NPC/resource içeriği sıfırlanacak

Kullanıcının kararıyla mevcut dört NPC kaydı ve yirmi iki kaynak düğümü yeni Hex sistemine taşınmayacaktır. Bunlar eski harita demo içeriği olarak kaldırılacaktır. Bunlara bağlı eski quest tanımları, NPC diyalog kayıtları, NPC'ye bağlı pazar ve demo yerleşimleri de kaldırılacaktır. Yeni Hex dünya entegrasyonundan sonra NPC, kaynak düğümü, görev, diyalog ve pazar içerikleri yeni dünya tasarımına göre sıfırdan yazılacaktır.

Bu bir domain mekaniklerinin silinmesi değildir. NPC, kaynak düğümü, toplama, diyalog, quest, ekonomi, market, envanter ve persistence altyapıları korunur. Temizlik yalnızca eski demo içerik verilerini, eski map ID/koordinat referanslarını ve bunlara özgü doğrulama/fixture varsayımlarını kaldırır.

### 11.2 Bağlayıcı uygulama sırası

Bu ek, belgenin önceki 16.2–16.6 faz sıralamasını geçersiz kılar:

1. Eski dokuz kare harita sistemi ve eski yedi haritalı Hex demo/portal içeriği tamamen temizlenir.
2. Eski NPC/resource/quest/dialogue/market demo kayıtları ve eski harita konum referansları kaldırılır.
3. Kare harita runtime, eski demo Hex portalı ve bunların paket/test/CI bağımlılıkları kaldırılır.
4. Eski kare save verileri için açık sürüm/reddetme/geri kazanım politikası belirlenir; (x, y) hiçbir zaman (q, r) olarak yorumlanmaz.
5. Bu temizlik teknik test kapılarından geçtikten sonra laboratuvar Hex mimarisi bu dala entegre edilir.
6. Yeni Hex dünya içerikleri — oyuncu başlangıcı, NPC, kaynak, görev, diyalog ve pazar — entegrasyon sonrasında sıfırdan oluşturulur.

Tek kare easter egg kararı, eski kare harita altyapısını korumaz. Gerekirse daha sonra bağımsız ve minimal bir kare sahne olarak yeniden tasarlanır.
