# Eldoria — Modüler Yapı ve İnşa Sistemi
## Aşama 0: Mevcut Mimari Envanteri ve Sınır Doğrulaması

- **Durum:** Kullanıcı tarafından kabul edildi; Aşama 0 kapatıldı
- **Hedef dal:** `experiment/map-cleanup`
- **Kapsam referansı:** `docs/architecture/90-modular-building-construction-system-roadmap.md`
- **İnceleme türü:** Salt okunur kaynak kodu ve test envanteri
- **Uygulama değişikliği:** Yok

> Bu rapor yalnızca yol haritasının Aşama 0 kapsamını kaydeder. Yeni yapı sistemi kodu, veri sözleşmesi veya uygulama tasarımı içermez. Sonraki aşamalara ait kararları erkenden sabitlemez.

## 1. Amaç ve sınır

Aşama 0'ın amacı, gelecekteki modüler yapı sisteminin mevcut Eldoria mimarisiyle temas edeceği sınırları kaynak kod ve testler üzerinden belirlemektir. Bu aşamada mevcut oyun davranışı değiştirilmez; yapı sistemi uygulanmaz.

İnceleme şu dokuz alanla sınırlandırılmıştır:

1. Hex dünya haritası ve koordinatlar
2. WorldPoint ve dünya koordinatları
3. Renderer ve kamera
4. Fizik ve çarpışma
5. Spatial index
6. Entity sahipliği ve yaşam döngüsü
7. GameplayService
8. Content sistemi
9. Save/Load sistemi

## 2. Mevcut mimari envanteri

### 2.1 Hex dünya ve koordinat sözleşmeleri

İlgili kaynaklar:
- `core/domain/spatial/hex_coord.py`
- `core/domain/spatial/world_point.py`
- `core/domain/spatial/continuous_position.py`
- `application/hex_map_definition.py`
- `application/world_map_definition.py`
- `application/hex_world_runtime.py`

Gözlem:
- `HexCoord` altıgen hücre koordinatını temsil eder.
- `WorldPoint` sürekli dünya konumunu temsil eder.
- `ContinuousEntityPosition` sürekli konumu harita kimliğiyle ilişkilendirir.
- Hex harita tanımları hücre ve harita verisini; dünya haritası tanımı haritalar arası dünya ilişkisini taşır.
- `HexWorldRuntime` aktörlerin sürekli konum ve occupancy/runtime ilişkilerini yönetir.

Sınır sonucu: Hex dünya koordinatları ile sürekli dünya konumları farklı kavramlardır ve birlikte çalışırlar. Yol haritasındaki hex dünya kanonikliği korunmalıdır. Gelecekteki inşa koordinatlarının bu sözleşmelerin yerine geçirilmesi için bu envanterde dayanak yoktur.

### 2.2 Dünya koordinatı ve dönüşüm

İlgili kaynaklar:
- `core/domain/spatial/world_point.py`
- `game_ui/world_rendering/hex_gameplay_view.py`
- `game_ui/world_rendering/camera.py`

Gözlem:
- Domain katmanında sürekli dünya noktası tanımlıdır.
- Görsel katmanda dünya ve ekran koordinatı dönüşümleri ile kamera dönüşümü bulunur.
- Kod tabanında dünya konumu ile görsel/piksel temsili ayrı sorumluluklardadır.

Açık doğrulama konusu: Dünya birimi, render ölçeği ve inşa hassasiyeti arasında tek ve bağlayıcı bir ölçek eşitliği bu aşamada sabitlenmemiştir. Yol haritası uyarınca bunlar Aşama 1'de mevcut sözleşmeler karşılaştırılarak ele alınmalıdır; Aşama 0 bu konuda sayısal karar vermez.

### 2.3 Renderer ve kamera

İlgili kaynaklar:
- `game_ui/world_rendering/hex_gameplay_view.py`
- `game_ui/world_rendering/scene_object.py`
- `game_ui/world_rendering/scene_object_pipeline.py`
- `game_ui/world_rendering/camera.py`

Gözlem:
- `HexGameplayView` oyun görünümünü sunar; authoritative gameplay kimliği veya konumunun sahibi olarak tanımlanmamıştır.
- Kamera dünya-görünüm dönüşümünü ve takip davranışını yürütür.
- `SceneObject` ve sahne nesnesi hattı görsel nesne/yerleşim sunumunu sağlar.
- Sahne nesnesinin görsel yerleşimi, tek başına canlı gameplay yapısı veya yapı parçası yaşam döngüsü anlamına gelmez.

Sınır sonucu: Render katmanı yapıların görsel sunumuna bağlanabilecek bir katmandır; yapı kimliği, bileşimi ve authoritative durum deposu olarak değerlendirilmemelidir.

### 2.4 Fizik ve çarpışma

İlgili kaynaklar:
- `core/domain/physics/obstacle.py`
- `core/domain/physics/obstacle_index.py`
- `core/domain/physics/continuous_solver.py`
- `application/hex_physics_bridge.py`
- `application/scene_physics_adapter.py`

Gözlem:
- Statik engel geometrisi fizik domain'inde temsil edilir.
- Engel indeksi fizik sorgularında adayları bulur.
- Sürekli hareket çözücüsü çarpışma çözümünü yürütür.
- Hex fizik köprüsü harita geometrisini fizik tarafına taşır.
- Sahne fizik adaptörü içerik/sahne nesnelerinin çarpışma verisini fizik sistemine aktarır.

Sınır sonucu: Görsel nesne ve fizik geometrisi ayrı sorumluluklardır. Bir nesnenin çizim ölçüsü kendiliğinden authoritative çarpışma geometrisi sayılmamalıdır. Gelecekte yapı parçalarının fizik etkisi mevcut fizik sınırlarına bir adaptasyon/projeksiyon olarak bağlanmalıdır; bu rapor yeni fizik tasarımı tanımlamaz.

### 2.5 Spatial index

İlgili kaynaklar:
- `core/domain/spatial/uniform_grid_index.py`
- `application/hex_world_runtime.py`

Gözlem:
- Uniform grid indeksi harita kapsamlı uzamsal sorgu ve sınır kutusu indekslemesi sağlar.
- İndeks, kimlik/konum yaşam döngüsünün sahibi değildir; kendisine verilen kayıtları sorgulanabilir hale getirir.
- Dünya runtime'ı konum ve occupancy tarafındaki uygulama sorumluluğunu taşır.

Sınır sonucu: Spatial index gelecekte uzamsal sorgularda kullanılabilecek altyapıdır; yapıların authoritative kimlik veya durum deposu değildir.

### 2.6 Entity sahipliği ve yaşam döngüsü

İlgili kaynaklar:
- `core/application/ownership.py`
- `core/application/entity_repository.py`
- `core/entity/entity.py`
- `core/entity/entity_manager.py`
- `application/hex_actor_binding.py`
- `application/hex_world_runtime.py`

Gözlem:
- Entity repository kimlik kayıt/sorgulama sorumluluğu sağlar.
- Dünya üyeliği/ownership hizmetleri entity'nin dünya kapsamındaki sahiplik ilişkisini yönetir.
- Aktör kayıt ve binding bileşenleri aktör kimliği ile dünya runtime konum ilişkisini bağlar.
- Konum/occupancy bilgisi entity kimliğinin kendisiyle aynı kavram değildir.

Sınır sonucu: Kimlik, dünya üyeliği ve uzamsal konum mevcut mimaride ayrıştırılmış sorumluluklardır. Gelecekteki yapı çalışması bu ayrımı korumalıdır.

### 2.7 GameplayService sınırı

İlgili kaynak:
- `application/gameplay_service.py`
- `tests/test_application/test_gameplay_service_boundaries.py`

Gözlem:
- GameplayService oturum kapsamındaki gameplay işlemlerini koordine eden uygulama katmanıdır.
- İlgili işlemler mevcut servis/runtime bileşenlerine devredilir.
- Bu incelemede GameplayService'in bütün domain durumlarını kendisinin sahiplenmesi gerektiğine dair bir dayanak bulunmamıştır.

Sınır sonucu: Gelecekte GameplayService entegrasyon koordinasyonu için değerlendirilebilir; yapı domain kurallarının veya authoritative yapı durumunun otomatik sahibi olarak kabul edilmemelidir.

### 2.8 Content sistemi

İlgili kaynaklar:
- `application/content_pack.py`
- `application/content_loader.py`
- `application/hex_map_definition.py`
- `tests/test_application/test_content_pack.py`

Gözlem:
- İçerik paketleri manifest ve veri dosyaları üzerinden yüklenir.
- İçerik tanımları sürüm ve doğrulama sınırlarına sahiptir.
- Harita, sahne/görsel yerleşim ve gameplay yerleşimi farklı veri sorumlulukları taşır.
- İncelenen mevcut sözleşmelerde genel modüler yapı tanımı ve canlı yapı örneği için tamamlanmış bir yapı sistemi sözleşmesi tespit edilmemiştir.

Sınır sonucu: Mevcut content loader gelecekte tanım verilerinin yüklenmesi için entegrasyon noktası olabilir. Bu aşamada yeni content şeması önerilmemiş veya eklenmemiştir.

### 2.9 Save/Load sistemi

İlgili kaynaklar:
- `application/save_document.py`
- `application/save_file_adapter.py`
- `application/hex_world_persistence.py`
- `tests/test_application/test_unified_save_document.py`

Gözlem:
- Birleşik kayıt belgesi sürümlü veri taşır.
- Hex dünya ve aktör snapshot/persistence sorumlulukları ayrıdır.
- Dosya adaptörü kayıt dosyasına yazma ve geri yükleme akışını yönetir.
- İncelenen mevcut kayıt sözleşmelerinde modüler yapı örnekleri ve yapı parçası bağlantı durumları için tamamlanmış bir persistence modeli tespit edilmemiştir.

Sınır sonucu: Mevcut kayıt belgesi ve persistence hattı gelecekte entegrasyon noktasıdır. Yapı kayıt şeması bu aşamada tasarlanmamıştır.

## 3. Mimari sınırların özeti

| Alan | Mevcut authoritative/sorumlu katman | Gelecekteki entegrasyon açısından sınır |
|---|---|---|
| Hex hücre | Hex koordinat ve harita domain'i | Kanonik dünya modeli korunur |
| Sürekli konum | WorldPoint ve world runtime | İnşa koordinatıyla kavramsal olarak karıştırılmaz |
| Görsel sunum | Gameplay view, camera, scene object pipeline | Yapı durumunun sahibi değildir |
| Çarpışma | Physics domain ve physics adapter/bridge | Görsel ölçü otomatik fizik geometrisi değildir |
| Uzamsal sorgu | Uniform grid index | Kimlik veya durum deposu değildir |
| Kimlik/sahiplik | Entity repository ve ownership servisleri | Konumdan ayrı tutulur |
| Gameplay koordinasyonu | GameplayService | Domain aggregate yerine geçmez |
| İçerik tanımı | Content pack/loader | Mevcut şema sınırları korunur |
| Kayıt | Save document ve persistence adaptörleri | Yeni kayıt modeli henüz tanımlanmamıştır |

## 4. İlgili test envanteri

İnceleme sırasında aşağıdaki test dosyaları ilgili sınırların doğrulanması için belirlendi:

- `tests/test_spatial/test_continuous_world_geometry.py`
- `tests/test_spatial/test_uniform_grid_index.py`
- `tests/test_spatial/test_native_collision_solver.py`
- `tests/test_application/test_ownership.py`
- `tests/test_application/test_entity_repository.py`
- `tests/test_application/test_hex_world_runtime.py`
- `tests/test_application/test_hex_physics_bridge.py`
- `tests/test_application/test_scene_physics_adapter.py`
- `tests/test_application/test_gameplay_service_boundaries.py`
- `tests/test_application/test_unified_save_document.py`
- `tests/test_application/test_content_pack.py`
- `tests/test_application/test_gameplay_service.py`

**Test yürütme notu:** Bu rapor hazırlanırken yerel test komutu çalıştırılmadı. GitHub Actions üzerinde incelenen commit için aşağıdaki işler başarılı sonuçlanmıştı:
- Core quality: `verify` ve `verify-windows`
- Eldoria CI: Python 3.11/3.12 Ubuntu ve Windows test işleri ile Pygame headless smoke test

CI sonuç bağlantıları:
- https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/46043664830
- https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/46043664919

Bu CI kayıtları ilgili commit'in doğrulamasıdır; bu raporun eklenmesinden sonra testlerin yeniden çalıştırıldığı anlamına gelmez.

## 5. Aşama 0 bulguları ve açık noktalar

1. Hex dünya, sürekli dünya konumu ve render koordinat dönüşümü ayrı sorumluluklardır.
2. Render nesnesi ve fizik engeli farklı temsillerdir; biri diğerinin yerine geçmez.
3. Spatial index sorgu altyapısıdır; entity veya yapı sahipliği değildir.
4. Entity kimliği, dünya üyeliği ve uzamsal konum ayrıştırılmıştır.
5. GameplayService uygulama koordinasyonu yapar; domain durum deposu olarak ele alınmamalıdır.
6. Content ve Save/Load altyapılarında gelecekte entegrasyon yapılabilecek sürümlü sınırlar vardır.
7. Mevcut envanterde genel modüler yapıların canlı durumunu, parça bağlantılarını ve yaşam döngüsünü uçtan uca yöneten tamamlanmış bir sistem tespit edilmemiştir.
8. Dünya birimi/render ölçeği/inşa hassasiyeti arasında sayısal karar verilmemiştir. Bu karar yol haritasında belirtilen sonraki aşamanın incelemesine bırakılmıştır.

## 6. Aşama 0 çıkış ölçütü değerlendirmesi

| Çıkış ölçütü | Değerlendirme |
|---|---|
| Mevcut sistemlerin sorumluluk sınırlarının kaynak kodla incelenmesi | İncelendi |
| İlgili test dosyalarının belirlenmesi | Belirlendi |
| Gelecekteki entegrasyon noktalarının kaydedilmesi | Kaydedildi |
| Mevcut gameplay davranışının değiştirilmemesi | Bu çalışma kapsamında kod değişikliği yapılmadı |
| Aşama 0 raporunun kullanıcı tarafından kabulü | 27.11.2026 tarihinde kabul edildi |
| Aşama 0'ın resmî kapanışı | Tamamlandı |
| Aşama 1'e geçiş | Ayrı ve açık kullanıcı talimatı bekleniyor |

## 7. Kapsam ve değişiklik kaydı

Bu rapor dışında hiçbir kaynak kod, test, içerik dosyası, yapılandırma veya oyun davranışı değiştirilmemiştir. Yeni sınıf, API, veri sözleşmesi, koordinat standardı veya yapı sistemi uygulanmamıştır.

Bu belge yalnızca `docs/architecture/90-modular-building-construction-system-roadmap.md` yol haritasının Aşama 0 çalışmasını kayıt altına alır. Yol haritasının kapsamı genişletilmemiştir. Çalışma yalnızca `experiment/map-cleanup` dalına aittir.

**Kapanış kaydı (27.11.2026):** Kullanıcı raporu incelediğini ve kabul ettiğini açıkça bildirmiştir. Bu onayla Aşama 0 resmen kapatılmıştır. Aşama 1 otomatik olarak başlatılmamıştır; yalnızca kullanıcının ayrı ve açık talimatıyla başlayacaktır.
