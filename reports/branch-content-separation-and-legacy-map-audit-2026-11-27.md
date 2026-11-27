# experiment/map-cleanup — İçerik Ayrışması, Content Editor Altyapısı ve Kare Harita Bağımlılık Denetimi

**Tarih:** 27 Kasım 2026  
**Denetlenen dal:** `experiment/map-cleanup`  
**Denetim başlangıç commit'i:** `5e9e6a408a56d0bf1026b8ee37a0550817d6f5fe`  
**Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
**Çalışma türü:** Salt okunur mimari inceleme; kaynak kodu, test, içerik veya yapılandırma değişikliği yapılmadı.  
**Amaç:** Oyun/runtime kodu ile içerik verisinin ayrışma düzeyini, gelecekteki ELDORIA CONTENT EDITOR için mevcut altyapıyı ve eski kare harita mimarisinin temizlenme durumunu değerlendirmek.

---

## 1. Yönetici özeti

**Genel karar: Temel içerik/runtime ayrımı kurulmuş; sunum içeriği için Content Editor altyapısının önemli bölümü hazır. Ancak “oyundaki bütün içerik türleri editör servisinden güvenle düzenlenebilir” seviyesine henüz ulaşılmamış. Eski kare harita veri modeli ve eski kare harita gameplay akışı temizlenmiş görünüyor. Buna karşılık kare ızgara navigasyonu hâlâ kodda ve CI'da bulunuyor; bu, 23 Kasım tarihli mimari karara göre eski kare harita değil, hex dünyadan türetilen yeni ve kasıtlı hareket katmanıdır.**

Başlıca sonuçlar:

1. İçerik paketleri `content/` altında JSON manifest ve veri dosyaları olarak tutuluyor. Demo ve hareket test paketleri ayrılmış; harita tanımları, sunum asset kataloğu/yerleşimleri ve gameplay yerleşimleri birbirinden ayrılmış.
2. `PresentationContentService` ve `PresentationContentStore`, gelecekteki editörün Pygame penceresine veya oyun runtime'ına doğrudan bağlanmadan içerik okuma, doğrulama, kaydetme ve eski sunum formatını dönüştürme işlemlerini yapabilmesi için anlamlı bir temel sağlıyor.
3. Bu servislerin yazma kapsamı şu an **sunum asset kataloğu ve harita üzerindeki sunum yerleşimleriyle** sınırlı. NPC, görev, kaynak, gameplay placement, harita tanımı/geçişleri ve gameplay kuralları için eşdeğer düzenleme/kayıt API'si bu yüzeyde görünmüyor.
4. `application/content_loader.py`, sunum katalog modellerini `game_ui.assets` paketinden içe aktarıyor. Bu, UI bağımsız editör servisi hedefi açısından katman yönü sorunu: Application içerik yükleyicisi, UI paketine bağımlı kalıyor.
5. Demo paketinde asset kataloğunun referans verdiği dört PNG dosyası depo ağacında bulunmuyor. Yükleyici bu tür görsel dosya sorunlarını fatal olmayan tanı olarak ele alıyor; dolayısıyla paket yüklenebilirken içerik eksik kalabilir.
6. Eski kare harita JSON'ları, kare harita katalog/runtime dosyaları ve eski ana oyun kare harita ekranı mevcut ağaçta görünmüyor. Demo paketinin yalnızca `starting_valley` hex haritasını kullandığını doğrulayan regresyon testi var.
7. `SquareGrid` kodu ve kare-grid CI/benchmark/testleri hâlâ mevcut. Bunlar eski kare harita sistemiyle karıştırılmamalı: yeni karar belgesi kare grid'i hex dünya üzerine türetilen birincil navigasyon katmanı olarak tanımlıyor.
8. Mimari belgelerde güncel kodla çelişen tarihsel ifadeler var. Özellikle Aşama 8 planı, eski dal adı ve “uygulama başlamadı” durumunu koruyor; bazı eski içerik ve harita belgeleri kaldırılmış kare harita/legacy dosyalardan hâlâ güncelmiş gibi söz ediyor.

**Önerilen durum etiketi:**  
- İçerik verisinin dosya/paket düzeyinde ayrılması: **Büyük ölçüde tamamlandı**  
- Sunum içeriği için editör altyapısı: **Temel servis ve güvenli kayıt hazır; kapsam sınırlı**  
- Tüm gameplay içeriği için editör altyapısı: **Eksik**  
- Eski kare harita gameplay mimarisinin kaldırılması: **Kod ve içerik ağacı bakımından tamamlanmış görünüyor**  
- Kare-grid hareket katmanının kaldırılması: **Gerekli değil; güncel mimari kararın parçası**  
- Dokümantasyon tutarlılığı: **Düzeltme gerekiyor**

## 2. Denetim yöntemi ve kapsam sınırı

Denetim, GitHub üzerindeki `experiment/map-cleanup` dalının gerçek ref'i üzerinden yürütüldü; varsayılan dal veya başka bir deney dalı kullanılmadı.

Başlangıç commit'i `5e9e6a408a56d0bf1026b8ee37a0550817d6f5fe`. Recursive Git tree sonucu **1.032 ağaç girdisi ve 940 dosya blob'u** gösterdi; ağaç yanıtı kesilmemişti. Tüm dosya yolları envanterlendi. İçerik ayrımı, paket yükleme, servis/store, gameplay yerleştirme, runtime, ana giriş, paketleme, kare-grid, mimari sözleşmeler ve bunlara ilişkin test/CI dosyalarının kaynak içerikleri hedefli olarak incelendi.

**Önemli sınır:** Bu çalışma yerel çalışma kopyasında 940 dosyanın tamamını tek tek açıp satır satır inceleyen bir IDE/repository taraması değildir. GitHub üzerinden tam ağaç ve mimari açıdan belirleyici dosyalar incelendi; tüm dosya içeriklerinde tam statik analiz, yerel Pytest/Ruff çalıştırması veya gerçek Pygame penceresi manuel testi yapılmadı. Bu nedenle rapor, “940 dosyanın her satırı incelendi” iddiasında bulunmaz. Tespitler doğrudan okunan kaynak ve test kanıtlarına dayanır; çalıştırılmayan kontroller başarılı sayılmamıştır.

## 3. Mevcut içerik paketinin yapısı

Ağaçta iki içerik paketi var:

- `content/demo_eldoria/`
- `content/movement_test/`

Paket seçimi `content/active_package.json` üzerinden yapılıyor. Her pakette `manifest.json`, JSON veri dosyaları ve hex harita dizini bulunuyor.

Demo paketinin manifesti şu ayrımı açıkça kuruyor:

- `files`: starter, NPC, quest, resource, character, gameplay rules, item ve container tanımları.
- `maps`: `hex_maps`
- `asset_catalog`: `asset_catalog.json`
- `map_placements`: `placements`
- `gameplay_placements`: `gameplay_placements`

Hareket test paketinde de `hex_maps` ve `gameplay_placements` ayrı; sunum asset kataloğu ve map placement tanımları bulunmuyor. Bu ayrım, test paketinin gereksiz sunum varlıkları taşımamasını sağlıyor.

### 3.1. Olumlu mimari ayrımlar

- NPC tanımları ile NPC'nin haritadaki gameplay konumu aynı veri dosyası olmak zorunda değil.
- Kaynak düğümü tanımları ile gameplay placement ayrı tutulabiliyor.
- Görev, item, container ve gameplay rules dosyaları manifest üzerinden bildiriliyor.
- Hex harita tanımı ayrı bir veri kümesi.
- Görsel asset metadata'sı ile harita üzerindeki sunum nesnesi yerleşimleri ayrılmış.
- `GameplayPlacementCatalog`, harita kimliği ve axial hücre konumunu doğrulayarak gameplay yerleşimlerini paket içinden yükleyebiliyor.
- `ContentPackage` tek yükleme sonucunda veri dosyalarını, hex harita tanımlarını, sunum katalog/yerleşim snapshot'larını ve gameplay placement kataloğunu bir araya getiriyor.

Bu yapı, oyunun aynı runtime kodunu farklı içerik paketleriyle başlatabilmesi için doğru yönde bir temel.

### 3.2. Kalan kavramsal ayrım

Paketin dosyalara ayrılmış olması, her dosyanın editör tarafından değiştirilebilir olduğu anlamına gelmiyor. Mevcut servis API'si sunum içeriğine odaklı. Gameplay JSON dosyaları oyun tarafından yüklenip doğrulanabiliyor; ancak bu raporda bunları güvenli şekilde düzenleyen, doğrulayan ve atomik kaydeden eşdeğer bir genel authoring API'si doğrulanmadı.

## 4. ELDORIA CONTENT EDITOR için mevcut altyapı

### 4.1. Mevcut bileşenler

| Bileşen | Dosya | Mevcut rol | Değerlendirme |
|---|---|---|---|
| Paket yükleyici | `application/content_loader.py` | Manifest, veri JSON'ları, hex haritalar, sunum katalogları ve gameplay placement yükleme/doğrulama | Güçlü temel; UI bağımlılığı var |
| Paket modeli | `ContentPackage` içinde | Yüklenmiş ve doğrulanmış paket snapshot'ı | Doğru yönde |
| Gameplay placement kataloğu | `application/gameplay_placement_catalog.py` | NPC/resource/container gibi gameplay varlıklarının axial yerleşim verisi | Ayrı veri sınırı mevcut |
| Sunum içerik servisi | `application/presentation_content_service.py` | Paket okuma, asset/placement sorgulama, taslak doğrulama, kaydetme ve migration facade'i | Editör için önemli ve UI-neutral API |
| Sunum içerik store'u | `application/presentation_content_store.py` | Güvenli dosya yazımı, staged package doğrulaması, migration | Güçlü güvenli kayıt temeli |
| Asset kataloğu | `game_ui/assets/asset_definition.py` ve ilgili paket | Asset metadata modeli/yükleyicisi | Konumlandırma/katman sorunu var |
| Scene placement kataloğu | `game_ui/assets/placement_catalog.py` ve ilgili paket | Harita bazlı sunum yerleşimleri | Konumlandırma/katman sorunu var |

### 4.2. Güvenli kayıt yaklaşımı

`PresentationContentStore` uygulamasında şu korumalar bulunuyor:

- Yazma öncesinde paket geçici bir staging dizinine kopyalanıyor.
- Taslak veri staging alanına yazılıyor.
- Tam paket normal `load_content_package` doğrulamasından geçiriliyor.
- Başarılı doğrulamadan sonra hedef dosyalar atomik/yerine koyma yaklaşımıyla yayımlanıyor.
- Paket manifesti ve dosya yolları kontrol ediliyor.
- Paket kapsamlı dosya kilidi kullanılıyor.
- Asset kataloğu ile map placement kaynakları birlikte tanımlı olmalı; yarım split manifest reddediliyor.
- Eski birleşik sunum formatından split formata açık migration mevcut.
- Migration önce kaynak paketi, sonra üretilen paketin tamamını doğruluyor; geçersiz/çakışan legacy içeriği sessizce dönüştürmüyor.

Bu, ileride editörün “Kaydet” işlemi için doğru yaklaşım. Editörün dosyaları doğrudan yazması yerine bu store/service API'sini kullanması gerekir.

### 4.3. Servisin şu an sunduğu kapsam

`PresentationContentService` şu yetenekleri sunuyor:

- Paket yükleme.
- Asset kataloğunu yükleme/listeleme/tekil asset sorgulama.
- Harita bazında sunum placement sorgulama.
- Paket, asset katalog taslağı ve map placement taslağı doğrulama.
- Asset kataloğu kaydetme.
- Map placement kaydetme.
- Legacy sunum içeriğinin migration durumunu sorgulama ve migration çalıştırma.

Bu API, asset browser ve çevre nesnesi yerleştirme editörünün veri tarafı için anlamlıdır. Ancak ELDORIA CONTENT EDITOR hedefi yalnızca çevre görseli yerleştirmekten ibaret değilse aşağıdaki alanlarda eşdeğer authoring API'si ayrıca tasarlanmalıdır:

- Hex harita geometrisi, valid cell mask, terrain, blocked cell ve map transition düzenleme.
- NPC tanımı, davranış/patrol verisi ve gameplay placement.
- Resource node tanımı, üretim/yenilenme kuralları ve gameplay placement.
- Quest, objective, reward, quest giver ve diyalog bağlantıları.
- Item, container, başlangıç içeriği ve gameplay rules.
- Market, merchant, recipe/facility ve diğer oyun sistemi tanımları.
- Paketler arası referans/ID kontrolü, şema sürüm yükseltme ve migration.

**Sonuç:** Sunum içerik editörü altyapısı var; genel oyun içerik editörü altyapısı kısmi.

## 5. Tespit edilen sorunlar ve riskler

### BULGU C-01 — Application içerik yükleyicisinin UI paketine bağımlılığı

**Önem:** Yüksek  
**Dosya:** `application/content_loader.py`  
**Kanıt:** Sunum snapshot'ı oluşturulurken `game_ui.assets.asset_definition` içinden `AssetCatalog`, `game_ui.assets.placement_catalog` içinden `ScenePlacementCatalog` ve bunların hata sınıfları import ediliyor.

Application katmanındaki paket yükleyicisi, içerik paketini doğrulamak için UI paketinin içinde bulunan modelleri kullanıyor. Modeller Pygame'den bağımsız olsa bile bağımlılık yönü ters: içerik/application katmanı, UI paketinin iç organizasyonuna bağlı.

**Etkisi:**
- Content Editor ayrı bir masaüstü uygulaması veya farklı UI teknolojisiyle yazılırsa bu UI paketini dolaylı olarak taşımak zorunda kalabilir.
- UI paketinin yeniden düzenlenmesi paket yükleme/doğrulama katmanını etkileyebilir.
- İçerik şeması ve authoring modellerinin sahipliği belirsizleşir.

**Önerilen çözüm yönü:** Asset ve placement veri modellerinin sahipliği UI'dan bağımsız bir content/domain veya content/application paketine taşınmalı. Renderer/UI yalnızca bu modelleri tüketmeli. Bu rapor kapsamında kod değişikliği yapılmadı.

### BULGU C-02 — Authoring API yalnızca sunum içeriğini kapsıyor

**Önem:** Yüksek  
**Dosyalar:** `application/presentation_content_service.py`, `application/presentation_content_store.py`, `application/gameplay_placement_catalog.py`

Servisin yazma uçları asset kataloğu ve sunum map placement'larıyla sınırlı. Gameplay placement kataloğu yükleniyor ve doğrulanıyor; fakat aynı serviste gameplay placement kaydetme/taslak doğrulama uçları görünmüyor. NPC, quest, resource, item, container, map definition ve gameplay rules dosyaları için de bu servis üzerinden düzenleme/kayıt sözleşmesi yok.

**Etkisi:** Mevcut API ile editörün çevre asset'lerini ve sunum yerleşimlerini düzenleyen ilk sürümü yapılabilir; ancak dünyayı ve oynanış içeriğini baştan sona yöneten tam bir Content Editor yapılamaz.

**Önerilen çözüm yönü:** Editör kapsamı “Presentation Authoring” ve “Gameplay/World Authoring” olarak ayrılmalı. Her içerik ailesi için ortak paket doğrulama ve atomik kayıt altyapısını kullanan, ama kendi şema/referans kurallarını uygulayan servisler tanımlanmalı. Gameplay placement yazma API'si öncelikli eksiklerden biridir.

### BULGU C-03 — Eksik PNG dosyaları paket doğrulamasını fatal olarak durdurmuyor

**Önem:** Orta  
**Dosyalar:** `content/demo_eldoria/asset_catalog.json`, `content/demo_eldoria/assets/`, `application/content_loader.py`

Asset kataloğu şu dosyalara referans veriyor:
- `assets/rock_large.png`
- `assets/shrub_green.png`
- `assets/wildflower.png`
- `assets/workbench.png`

Recursive tree'de demo assets dizininde yalnızca `tree_test.png` ve `tree_parts_atlas.png` görünüyor (ayrıca atlas JSON'u var). Yukarıdaki dört PNG depo içinde yok.

`content_loader.py` yorumunda eksik/bozuk PNG'lerin fatal olmayan katalog tanısı olarak bırakıldığı ve renderer fallback'inin çalışabildiği açıkça belirtilmiş.

**Etkisi:** Paket şema ve referans bakımından geçerli görünürken editörün asset önizlemesi veya gerçek oyun görseli eksik olabilir. “Paket doğrulandı” sonucu, tüm görsel dosyaların mevcut ve açılabilir olduğu anlamına gelmiyor.

**Önerilen çözüm yönü:** Doğrulama sonucunda asset dosya eksikliği ayrı ve görünür bir severity olarak raporlanmalı. Release/oyun kabulü için “tüm asset dosyaları mevcut” kalite kapısı, geliştirme fallback davranışından ayrılmalı.

### BULGU C-04 — İçerik ve asset modellerinin katman sahipliği belirsiz

**Önem:** Yüksek  
**Dosyalar:** `application/content_loader.py`, `game_ui/assets/asset_definition.py`, `game_ui/assets/placement_catalog.py`, `application/presentation_content_service.py`

C-01 ile bağlantılı olarak asset tanımı ve scene placement modelleri `game_ui.assets` altında; bunları yükleyip paket snapshot'ına dahil eden kod `application` altında. Servis modülü doğrudan Pygame import etmese de tam paket doğrulaması bu UI modellerine transitif bağımlı.

**Etkisi:** “UI-neutral” olmak yalnızca servisin kendi dosyasında Pygame import etmemesiyle sağlanmıyor. Bağımlılık grafiğinin tamamı UI'dan bağımsız olmalı.

**Önerilen çözüm yönü:** UI-neutral sözleşmenin testini yalnızca import metni üzerinden değil, bağımlılık yönü üzerinden kurmak; content modellerinin UI katmanına bağımlı olmadığını ve Application'ın UI paketine ihtiyaç duymadığını doğrulamak.

### BULGU C-05 — Aşama 8 planı ve bazı mimari belgeler güncel durumla çelişiyor

**Önem:** Orta  
**Dosyalar:**
- `reports/phase-8-content-editor-foundation-plan.md`
- `docs/architecture/44-content-pipeline-audit.md`
- `docs/architecture/45-presentation-content-separation.md`
- `docs/architecture/47-content-validation-and-safe-loading.md`
- `docs/architecture/57-legacy-map-system-removal-inventory.md`
- `docs/architecture/58-legacy-map-runtime-dependency-graph.md`
- `docs/architecture/81-square-grid-primary-movement-decision.md`

Örnekler:
- Aşama 8 planının üst bilgisinde çalışma dalı `demo_eldoria`, durum “PLANLANDI — UYGULAMA HENÜZ BAŞLAMADI” olarak kalmış. Oysa 44–49 numaralı belgeler içerik ayrıştırma, doğrulama, güvenli persistence ve servis API aşamalarını uygulanmış sözleşmeler olarak anlatıyor.
- 44/45 belgeleri `presentation_assets.json` birleşik kaynağını güncel paket yapısının parçası gibi anlatıyor. Güncel demo manifesti ise `asset_catalog.json` ve `placements/` ayrımını kullanıyor; recursive tree'de `presentation_assets.json` bulunmuyor.
- 47 numaralı belge, eski kare harita loader'ının değişmeden kaldığını söylüyor; mevcut `application/content_loader.py` hex map dizininde schema-v1 kare harita dosyasını açıkça reddediyor.
- 57/58 belgelerinin tarihsel envanter bölümleri açıkça “önceki durum” diye etiketlenmiş; bu doğru. Ancak bu bölümlere atıf yapan başka planlar güncel durumla karıştırılmamalı.
- Aşama 8 planındaki “kare harita altyapısı korunacak” kararı, daha sonraki cleanup kararıyla çelişiyor. Sonraki 57/58 ve 81 belgeleri esas alınmalı.

**Etkisi:** Yeni geliştirici veya ilerideki editör çalışması yanlış branch, eski şema veya artık mevcut olmayan dosyaları temel alabilir.

**Önerilen çözüm yönü:** Aşama 8 planının üst bilgisi ve eski veri örnekleri güncellenmeli; 44–49 belgelerindeki tarihsel/legacy açıklamalar “geçmiş durum” olarak etiketlenmeli; güncel manifest ve gerçek dosya yolları tek bir güncel mimari referans altında sabitlenmeli.

### BULGU C-06 — Gameplay içerik yükleme/kurulum kodu büyük ve çok sorumluluklu

**Önem:** Orta  
**Dosyalar:** `application/content_pack.py` (yaklaşık 1.681 satır), `application/gameplay_service.py` (yaklaşık 3.111 satır), `application/content_loader.py`

`content_pack.py`, JSON içerik doğrulamasından starter içerik yorumlamaya, çok sayıda domain nesnesi kurmaya ve gameplay kayıt/bağlantılarına uzanan geniş bir yüzeye sahip. `GameplayService` de hareket, NPC, ekonomi, kaynak, üretim, görev, diyalog, savaş ve oturum yaşam döngüsü gibi geniş bir facade yüzeyi sunuyor.

Bu durum tek başına içerik ayrımının başarısız olduğunu kanıtlamaz: içerik verisi dosyalarda, runtime nesneleri ise kodda kalabilir. Ancak editör kapsamı büyüdükçe tüm içerik ailelerinin aynı büyük kurulum/service yüzeylerine bağlanması değişiklik riskini artırır.

**Önerilen çözüm yönü:** Yeni özellik eklemeden önce içerik aileleri bazında küçük, test edilebilir parser/validator/assembler sınırları çıkarılmalı. Bu bir yeniden yazım önerisi değildir; yalnızca yeni authoring servislerinin mevcut büyük modüllere daha fazla sorumluluk yüklemesini önleme tavsiyesidir.

## 6. Eski kare harita mimarisi denetimi

### 6.1. Temizlenmiş görünen parçalar

Recursive tree'de eski kare harita gameplay dosyaları ve veri kataloğu görünmüyor. Özellikle önceki mimarideki `world/map_catalog.py`, kare harita `LocalMapDefinition`/legacy movement akışı, eski `main_screen.py` kare harita oyun ekranı ve eski dokuz kare harita JSON paket yapısı mevcut ağaçta bulunmuyor.

Güncel içerik dosyaları:
- `content/demo_eldoria/hex_maps/starting_valley.json`
- `content/movement_test/hex_maps/movement_test_arena.json`

`tests/test_world/test_mixed_map_package.py` içindeki `test_demo_package_has_no_legacy_square_or_hex_demo_maps`, demo paketinin hex map registry'sinin yalnızca `starting_valley` içerdiğini ve eski world-map graph tanımının bulunmadığını doğruluyor.

`application/content_loader.py` içindeki `_load_hex_maps`, schema version 1 dosyalarını “Legacy square-map schema is no longer supported” hatasıyla reddediyor; yalnızca schema version 2 hex map tanımlarını kabul ediyor.

`application/game_application.py` eski kare-map position/placement içeren save dosyalarını sessizce axial konuma çevirmiyor; açık hata mesajıyla reddediyor. Bu, eski koordinatları yanlış yorumlamayı önleyen doğru bir uyumluluk sınırı.

### 6.2. Kalan kare-grid kodu: eski harita değil, yeni navigasyon katmanı

Aşağıdaki dosyalar hâlâ mevcut:

- `application/square_grid_cache.py`
- `application/square_grid_click_move_route.py`
- `application/square_grid_coverage.py`
- `application/square_grid_pathfinding.py`
- `core/domain/spatial/square_grid.py`
- `tests/test_application/test_square_grid_cache.py`
- `tests/test_application/test_square_grid_click_move_route.py`
- `tests/test_application/test_square_grid_coverage.py`
- `tests/test_application/test_square_grid_pathfinding.py`
- `tests/test_foundation/test_square_grid_geometry.py`
- Kare-grid benchmark scriptleri ve iki GitHub Actions workflow'u.

Bunlar eski kare harita veri modelinin geri kaldığını tek başına göstermez. `docs/architecture/81-square-grid-primary-movement-decision.md` açıkça şu kararı veriyor: **Hex dünya kanonik veri/geometri katmanı; kare grid ise hex geometri üzerinden türetilen birincil oyuncu/NPC navigasyon katmanı.** Kare grid verisi harita geometrisinden türetiliyor ve kayda yazılmıyor; sürekli dünya konumu physics/runtime tarafından korunuyor.

Dolayısıyla:
- Eski kare harita JSON, kare harita dünya grafiği ve eski kare map gameplay akışı kaldırılmış olmalı.
- Yeni `SquareGridCoord` ve kare-grid pathfinding, güncel hareket mimarisinin parçası olarak korunmalı.
- Bu iki kavram aynı “square map” başlığı altında değerlendirilip topluca silinmemeli.

### 6.3. Eski kare koordinat izlerinin kalan kullanımı

`game_application.py` içinde legacy save verisinin kare harita konum/placement taşıdığını tespit edip reddeden hata metinleri var. Bu, aktif kare harita bağımlılığı değil, eski kayıtların güvenli reddi için uyumluluk koruması.

`application/content_loader.py` schema-v1 harita girdisini reddediyor. Bu da eski harita loader'ı değil, eski formatın yanlışlıkla yeni paket içine girmesini engelleyen doğrulama kapısı.

**Kare harita temizliği kararı:** Eski kare harita gameplay sistemi içerik ağacı ve mevcut kaynak dosya envanterinde temizlenmiş görünüyor. Yeni kare-grid navigasyon kodu ise güncel mimari karar gereği korunmalı. Eski save reddi ve schema-v1 reddi de kaldırılmamalı; bunlar güvenlik/uyumluluk bariyerleridir.

## 7. Test, CI ve doğrulama durumu

İlgili regresyon/test yüzeylerinden görülenler:

- `tests/test_world/test_mixed_map_package.py`: demo paketinde yalnızca tek canonical hex harita bulunduğunu ve legacy world graph olmadığını kontrol ediyor.
- `tests/test_application/test_gameplay_service_boundaries.py`: game_ui dosyalarının `service.application` / `application.holder` kaçışlarını ve GameplayService üzerinde genel `application` erişim noktasını yasaklıyor.
- İçerik loader, asset catalog, placement catalog, content service/store ve migration testleri mevcut.
- Gameplay placement, hex map, hex runtime ve persistence için ayrı test grupları var.
- Kare-grid geometri, coverage, cache, click route ve A* için ayrı testler mevcut.

Önceki mimari belgelerde belirli commit'ler için Eldoria CI ve Core Quality başarıları kaydedilmiş. Örneğin Aşama 4 kapanış belgesi `578556d01aab34f33af3b3516599dd191e3bd3a3` için Eldoria CI 5/5 ve Core Quality 2/2 başarılı olduğunu bildiriyor. A3.5 için de ayrı başarılı CI kayıtları belgelenmiş.

**Ancak denetlenen mevcut HEAD `5e9e6a4...` için GitHub birleşik commit-status sorgusu herhangi bir status kaydı döndürmedi.** Bu nedenle önceki commit'lerin yeşil CI kayıtlarını mevcut HEAD'in CI başarısı gibi sunmuyorum. Bu incelemede yerel test/ruff çalıştırılmadı.

## 8. Önceliklendirilmiş iyileştirme listesi

Bu liste uygulama talimatı değildir; rapor bulgularının çözüm sırasına ilişkin öneridir. Bu denetimde hiçbir madde uygulanmadı.

| Öncelik | Konu | Gerekçe |
|---|---|---|
| P0 | Asset/placement model sahipliğini `game_ui` dışına almak | Application → UI bağımlılığı, editörün bağımsızlığını zedeliyor |
| P0 | Gameplay placement için validate/save servis sınırı tanımlamak | Tam Content Editor'ün dünyayı düzenlemesi için gerekli |
| P1 | Gameplay içerik aileleri için ortak staged validation/write altyapısı | NPC, quest, resource, item, map ve rules kayıtlarının güvenli düzenlenmesi |
| P1 | Asset dosyası varlığı için ayrı release doğrulama kapısı | Eksik PNG'lerin geçerli paket içinde sessiz fallback'e dönüşmesi |
| P1 | Aşama 8 planı ve eski content belgelerini güncellemek | Yanlış dosya/branch/şema üzerinden geliştirme yapılmasını önlemek |
| P2 | `content_pack.py` sorumluluklarını aşamalı ayırmak | Yeni içerik aileleri eklendikçe monolitik kurulum riskini azaltmak |
| P2 | Mevcut HEAD için CI/test kanıtını yenilemek | Önceki commit'lerin başarısı güncel HEAD'i kanıtlamıyor |

## 9. Nihai cevaplar

**Ana oyun kodları ile içerikler tamamen ayrışmış mı?**  
Dosya/paket düzeyinde önemli ölçüde ayrışmış. Oyun davranışı ve runtime kodu Python modüllerinde; başlangıç, NPC, quest, resource, item, container, gameplay rules, harita, gameplay placement ve presentation verileri ayrı içerik dosyalarında. Runtime, manifest üzerinden seçilen paketi yükleyip domain/runtime nesnelerine dönüştürüyor. Ancak “tamamen ayrışma”yı içerik ailelerinin tümünün UI bağımsız, düzenlenebilir ve güvenli yazılabilir servislerle yönetilmesi olarak tanımlarsak henüz tamam değil. Özellikle presentation modelinin `game_ui` altında olması ve gameplay içerik yazma API'lerinin eksikliği bu kararı engelliyor.

**ELDORIA CONTENT EDITOR için altyapı kurulmuş mu?**  
Evet, ilk ve önemli temel kurulmuş: manifest, schema sürümü, asset katalog, sunum placement ayrımı, paket doğrulama, güvenli staged persistence, migration ve UI-neutral facade mevcut. Hayır, tüm editör kapsamı hazır değil: servis esasen presentation asset/placement düzenliyor; gameplay/world authoring servisleri henüz aynı seviyede değil.

**Eski kare harita bağımlılıkları temizlenmiş mi?**  
Eski kare harita gameplay ve veri modeli mevcut dosya ağacında temizlenmiş görünüyor. Eski schema-v1 haritalar reddediliyor, eski save koordinatları dönüştürülmeden reddediliyor. Kare-grid kodu kalmış olsa da bu yeni hex tabanlı hareket/navigasyon katmanıdır; kaldırılmamalı.

**Şu an kod değişikliği yapılmalı mı?**  
Hayır. Önce C-01/C-02 için hedef mimari ve kapsam kararı netleştirilmeli; ardından küçük, ölçülebilir işler açılmalı. Bu rapor yalnızca denetim çıktısıdır.

---

## 10. İncelenen temel dosyalar

**İçerik ve runtime:**  
`application/content_loader.py`, `application/content_pack.py`, `application/gameplay_placement_catalog.py`, `application/presentation_content_service.py`, `application/presentation_content_store.py`, `application/gameplay_service.py`, `application/hex_world_initializer.py`, `application/hex_world_runtime.py`, `application/game_application.py`, `main.py`.

**İçerik örnekleri:**  
`content/active_package.json`, `content/demo_eldoria/manifest.json`, `content/demo_eldoria/asset_catalog.json`, `content/demo_eldoria/placements/empty.json`, `content/demo_eldoria/gameplay_placements/starting_valley.json`, `content/demo_eldoria/hex_maps/starting_valley.json`, `content/movement_test/manifest.json` ve ilgili paket veri dosyaları.

**Mimari belgeler:**  
`docs/architecture/24-legacy-architecture-cleanup-roadmap.md`, `34-content-data-contract.md`, `44-content-pipeline-audit.md`, `45-presentation-content-separation.md`, `47-content-validation-and-safe-loading.md`, `48-presentation-content-safe-persistence.md`, `49-presentation-content-service-api.md`, `57-legacy-map-system-removal-inventory.md`, `58-legacy-map-runtime-dependency-graph.md`, `60-eldoria-main-game-architecture-contract.md`, `69-phase-16-gameplay-placement-catalog.md`, `71-phase-16-content-driven-hex-world-initialization.md`, `79-two-layer-hex-square-movement-architecture.md`, `81-square-grid-primary-movement-decision.md`, `reports/phase-8-content-editor-foundation-plan.md`.

**Test ve CI:**  
`tests/test_world/test_mixed_map_package.py`, `tests/test_application/test_gameplay_service_boundaries.py`, içerik loader/catalog/service/store testleri, gameplay placement/hex world testleri, kare-grid testleri ve `.github/workflows/` altındaki ilgili CI/benchmark tanımları.

**Denetim sonucu:** Rapor dışında hiçbir dosya değiştirilmedi.
