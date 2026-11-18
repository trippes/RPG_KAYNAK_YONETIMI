# Harita Sistemi Temizliği — Ayrıntılı Teknik Plan

| Alan | Değer |
|---|---|
| Çalışma dalı | `experiment/map-cleanup` |
| Kaynak dal | `demo_eldoria` |
| Başlangıç commit'i | `7d53d431d5c3639fd95d273de9043b64483a5125` |
| Genel plan | [51-map-system-cleanup-general-plan.md](51-map-system-cleanup-general-plan.md) |
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

### 16.1 — Baseline ve characterization (teknik inceleme tamamlandı; manuel kabul bekliyor)

- Başlangıç HEAD'i, 16 harita JSON'unun gerçek schema sürümleri, map ID'leri, hex world ve placement içerikleri kaydedildi.
- CI run `44411974271` Linux ve Windows işlerinde başarılı; test/derleme/paketleme/smoke kapsamı raporda kayıtlıdır.
- Normal oynanabilir akışın bugün kare dünya üzerinde olduğu; H tuşunun bağımsız ve geçici hex runtime açtığı kod/test üzerinden doğrulandı.
- `HexWorldView.enter()` oyuncuyu hex başlangıç hücresine yeniden kaydediyor; `leave()` runtime'ı atıyor. Hex konumu ana actor state'ine yazılmıyor ve tekrar girişte korunmuyor.
- NPC, kaynak, market, kare map transition, save/restore, paketleme ve release verification bağımlılıkları raporlandı.
- Ayrıntı: [Aşama 16.1 Baseline Raporu](53-map-cleanup-phase-16-1-baseline.md).
- Yerel Windows `--play`, H geçişi ve save/load görsel kabulü kullanıcı tarafından henüz yapılmadı.
**Kapı:** Manuel kabul tamamlanmadan 16.1 tamamen kapanmaz. Hex runtime sahipliği çözülmeden kare harita dosyaları kaldırılmaz.

### 16.2 — Harita verisi sınıflandırması ve tek kare haritanın seçimi

- Map JSON dosyalarının gerçek schema sürümleri, ID'leri ve içerikleri listelenir.
- Altıgen ana dünya haritaları ile kare harita adayları ayrılır.
- Kare harita adaylarından tek korunacak easter egg haritası, bağımlılık ve içerik kanıtıyla seçilir.
- Kalan kare harita dosyalarının manifest, kod, test, asset, placement ve save referansları raporlanır.
- Kırık/boşta kalan referanslar raporlanır; otomatik düzeltme yapılmaz.
**Kapı:** Tek kare easter egg haritası, hex gameplay authoritative state'e geçişin kapsamı ve NPC/kaynak/market/quest/save referanslarının yeni sahipliği kararlaştırılmadan kesin seçilemez. Bugünkü dokuz kare harita aktif starter gameplay'in bağımlılığıdır; hex entegrasyonu öncesi sekiz haritayı kaldırmak mevcut oynanışı ve save uyumluluğunu bozar. Bu nedenle bu aşamada yalnızca aday ve migration envanteri hazırlanır; silme/deprecation yapılmaz.

### 16.3 — Runtime sahipliği ve sahne sınırları

- Ana altıgen dünya için authoritative konum/runtime zinciri belgelenir.
- Kare easter egg haritası için gereken minimum runtime/UI bağımlılıkları belirlenir.
- Kare ve hex sistemler arasında koordinat/state paylaşımının gerekip gerekmediği değerlendirilir; varsayılan karar paylaşmamak ve koordinat dönüştürmemektir.
- İleride tek bir giriş/çıkış gerekirse sahne sınırı adaptörünün sözleşmesi belgelenir; bu aşamada ürün erişim yöntemi uygulanmaz.
- Belirsiz ownership varsa önce küçük bir mimari ADR yazılır; uygulama ayrı onaya bırakılabilir.
**Kapı:** Ana dünya state'i ile tek kare sahnenin sorumlulukları çakışmasız olmalı.

### 16.4 — Render/UI sorumluluk sadeleştirmesi

- Ekran/viewport/camera ve world transform çağrı zinciri çıkarılır.
- Normal gameplay'in altıgen dünya görünümüne ait yolu ile kare easter egg'in minimum sunum yolu ayrıştırılır.
- Geçici H-key bridge davranışı ürün gereksinimiyle karşılaştırılır; bu aşamada varsayılan olarak silinmez.
- Render-side cache ile gameplay state ayrımı test edilir.
**Kapı:** Ana oyun giriş/kamera/harita görüntüsü ve korunacak kare harita sunumu için regresyon kanıtı olmalı.

### 16.5 — Güvenli refactor ve deprecation

- Önce tek kare harita için gereken minimum kare sistem yüzeyi belirlenir.
- Çoklu kare harita katalogları, gereksiz dünya grafı/runtime bileşenleri ve kullanılmayan kare içerikler ancak bağımlılıkları kanıtlanırsa deprecation/remove adayı olur.
- Bir seferde tek bir sorumluluk veya küçük modül grubu değiştirilir.
- Önce public API ve import kullanım haritası çıkarılır; gerekiyorsa compatibility facade/adaptör eklenir.
- Kullanılmayan olduğu kanıtlanan kod önce deprecation/uyarı veya test dışı bırakma adımına alınır; silme ayrı commit olur.
- Her commit sonrası hedef test kümesi ve sonra tam test paketi çalıştırılır.
- Veri migration gerekiyorsa idempotent, yedekli ve dry-run destekli tasarlanır; migration bu planın otomatik varsayımı değildir.
**Kapı:** Her kaldırma için çağrı/import/save kanıtı, test kanıtı ve rollback yolu bulunmalı; tek kare easter egg çalışır durumda kalmalı.

### 16.6 — Tam regresyon ve kullanıcı kabulü

- Temiz kurulum ve paketleme doğrulanır.
- Tüm Pytest suite, Ruff ve GitHub Actions kalite akışları çalışır.
- Ana altıgen dünya ve içerik paketinin beklenen şekilde yüklendiği doğrulanır.
- Kare easter egg için yalnızca seçilmiş tek haritanın yüklenmesi ve hedeflenen sunumunun çalışması doğrulanır.
- Harita geçişi, oyuncu konumu, çarpışma, etkileşim, yerleşim, kamera, save/load ve mevcut gameplay loop kontrol edilir.
- Eski save referansları ve kare harita uyumluluğu ayrıca değerlendirilir.
- Görsel kabul testi istenmez; yalnızca değişen kodun otomatik testleri, statik analizi ve CI sonuçları değerlendirilir.
**Kapı:** CI ve manuel kabul birlikte başarılı olmalı.

### 16.7 — Kapanış ve entegrasyon sözleşmesi

- Ana altıgen dünya mimarisi ve korunacak tek kare harita easter egg yüzeyi belgelenir.
- Temizlenen/kalan legacy bileşenler listelenir.
- Harita veri şeması, runtime authority, koordinat sınırı, render adapter ve asset ownership kararları kaydedilir.
- Laboratuvar A15 raporundaki altı entegrasyon blocker'ının hangilerinin çözüldüğü ve hangilerinin entegrasyon aşamasına kaldığı eşleştirilir.
- "Hazır / koşullu hazır / hazır değil" kararı verilir.
**Kapı:** Kullanıcı kapanış kabulü olmadan sonraki entegrasyon aşaması açılmaz.

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
7. **Test kapsama boşluğu:** UI'da manuel olarak görülen bazı davranışlar için otomatik characterization test gerekebilir.
8. **Easter egg erişimi:** Nerede/nasıl bulunacağı ve sahneye giriş/çıkış biçimi ürün tasarımıdır; teknik temizlik bunu varsaymamalıdır.

## 10. Uygulama durumu ve sıralama kapısı

Kullanıcı teknik planın uygulanmasını onayladı. Aşama 16.1 teknik baseline incelemesi yapıldı ve [53 numaralı rapora](53-map-cleanup-phase-16-1-baseline.md) kaydedildi. Henüz hiçbir harita kodu, JSON içeriği, asset, save schema veya UI akışı değiştirilmedi.

**Kritik sıralama çakışması:** Ürün hedefi ana oyunda hex, tek kare easter egg iken mevcut uygulamanın ana gameplay'i kare sistem üzerinde çalışıyor; hex görünümü ise actor konumunu sahiplenmeyen geçici bir runtime. Bu nedenle "önce kare sistemi tek haritaya indir, sonra hex entegrasyonu yap" sırası güvenli değildir. Hex gameplay entegrasyonu ve içerik/save sahipliği çözülmeden kare haritaları tek dosyaya indirmek mevcut oyunu kırar. Bu bağımlılık kullanıcıyla netleştirilmeden 16.2'de tek harita seçimi ve 16.5'te kare runtime kaldırma adımlarına geçilmeyecektir.

Kullanıcı görsel test istemediğini açıkça belirtti. Bundan sonra `--play` manuel kontrolü istenmeyecek; teknik kararlar kod, bağımlılık grafı, Pytest, Ruff, paketleme ve GitHub Actions ile doğrulanacaktır. Sıralama kapısı, mevcut runtime sahipliği ve içerik/save bağımlılıkları esas alınarak teknik plan içinde çözülecektir. Korunan dallar değiştirilmeyecektir.
