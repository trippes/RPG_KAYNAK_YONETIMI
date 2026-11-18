# Aşama 14.1 — Depo ve Mimari Denetim Raporu

> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Denetlenen HEAD:** `9de839ca2bbd3405060b207c8465b5051224b836`  
> **Tarih:** 18 Kasım 2026  
> **Durum:** TAMAMLANDI  
> **Kapsam:** Aşama 14 onaylı genel planı; içerik veri çekirdeği ve gelecekteki ELDORIA CONTENT EDITOR hazırlığı. Editör arayüzü bu aşamanın kapsamında değildir.

## 1. Denetim özeti

Depoda gelecekteki içerik altyapısı için önemli yapı taşları zaten vardır: immutable dünya/harita modelleri, katı JSON doğrulaması, deterministik serileştirme, güvenli dosya yazımı, ayrı runtime snapshot biçimi, çevresel nesne tanım/yerleşim/sahne modelleri ve prosedürel çizim altyapısı.

Ancak bu parçalar henüz tek bir içerik üretim ve harita belgesi sistemine bağlanmamıştır. En önemli boşluk, prosedürel profillerin görsel sonuçlarının büyük ölçüde Python çizim kodunda tanımlı olmasıdır. Mevcut sistem profil yüzeyleri üretebilir; fakat profilin çizim bileşenleri, katmanları ve geometrisi kullanıcı tarafından düzenlenebilir, taşınabilir içerik verisi olarak saklanamaz.

Bu nedenle Aşama 14'ün teknik yönü yalnızca mevcut profil parametrelerini JSON'a yazmak olmamalıdır. Gelecekteki editörün gerçekten çizebilmesi ve düzenleyebilmesi için **Pygame'den bağımsız, sürümlü, katmanlı ve vektör tabanlı bir görsel içerik belgesi** oluşturulmalıdır. Mevcut Pygame renderer bu belgeyi Surface'e dönüştüren bir adaptör olarak kalmalıdır.

## 2. Denetim kapsamı ve yöntem

GitHub üzerinden laboratuvar dalının recursive dosya ağacı ve aşağıdaki alanlar incelendi:

- `pyproject.toml`, Laboratuvar CI ve Core Quality workflow'ları.
- `world/`, `world/persistence/`, harita ve runtime JSON şema belgeleri.
- `environment/` domain modelleri ve bunların fizik/render adaptörleri.
- `rendering/procedural/` geometri, canvas, bileşen, palet, profil, seed ve cache modülleri.
- İlgili unit, integration, acceptance ve architecture-boundary testleri.
- Başlangıç haritası örnek JSON'u ve Aşama 13 teknik/kapanış belgeleri.

Context7 ile Pygame Surface/alpha davranışı ve Python 3.11 JSON parse/serialize davranışı güncel dokümantasyondan kontrol edildi. Pygame Surface bir görsel/pixel nesnesidir; per-pixel alpha gibi sunum özellikleri taşır. Bu nedenle Surface nesnelerinin kalıcı içerik modeli olarak saklanması yerine saf veri belgesinden üretilmesi önerilir. Python JSON varsayılan olarak yinelenen nesne anahtarlarında son değeri tutabilir ve standart dışı NaN/Infinity değerlerini kabul edebilir; mevcut laboratuvar persistence katmanı bunları açıkça reddederek daha güvenli bir örüntü sunmaktadır.

## 3. Mevcut mimari bulguları

### 3.1 Dünya ve harita modeli — güçlü temel

İlgili dosyalar:

- `src/hex_world_lab/world/map_definition.py`
- `src/hex_world_lab/world/identity.py`
- `src/hex_world_lab/world/map_registry.py`
- `src/hex_world_lab/world/cell.py`
- `src/hex_world_lab/geometry/coordinates.py`

`HexMapDefinition` immutable bir harita tanımıdır; `WorldId`, `MapId`, `HexLayout` ve axial hücre verilerini taşır. Hücre sözlüğü defensive copy ve read-only mapping ile korunur. `MapRegistry` harita kataloğunu ve yüklü harita tanımlarını birbirinden ayırır. `WorldPoint` sürekli dünya koordinatlarını, `AxialCoord` hex hücre koordinatlarını temsil eder.

**Sonuç:** Gelecekteki harita belgesi mevcut `HexMapDefinition` modelini kopyalamamalı veya ikinci bir hex koordinat sistemi tanımlamamalıdır. Var olan model yeni belge formatının temel harita bileşeni olarak yeniden kullanılmalıdır.

### 3.2 Harita ve runtime persistence — güvenli ama kapsamı sınırlı

İlgili dosyalar:

- `docs/MAP_JSON_SCHEMA_V1.md`
- `docs/RUNTIME_JSON_SCHEMA_V1.md`
- `src/hex_world_lab/world/persistence/map_validator.py`
- `map_serializer.py`, `map_deserializer.py`, `file_storage.py`
- `runtime_validator.py`, `runtime_serializer.py`, `runtime_deserializer.py`, `runtime_file_storage.py`

Harita JSON v1; kimlik, ad, hex layout ve hücre verilerini saklar. Bilinmeyen alanları reddeder, koordinat tekrarlarını denetler, boolean değerleri integer yerine kabul etmez, finite number kontrolü yapar. Dosya yükleme immutable harita modelini oluşturur; dünya registry'sine yan etki yapmaz.

Runtime snapshot v1 ise tek haritanın sparse hücre override'larını ayrı tutar ve temel haritanın kanonik JSON serileştirmesi üzerinden SHA-256 fingerprint kontrolü yapar. JSON dosya katmanı duplicate key ve NaN/Infinity reddi uygular. Kaydetme create/replace modlarıyla güvenli geçici dosya ve atomik yayınlama yaklaşımını kullanır.

**Sınır:** Bu iki şema da çevresel nesne/yapı tanımları veya harita üzerindeki yerleşimleri saklamaz. Harita v1'i doğrudan genişletmek mevcut sözleşmeyi kırma riski taşır. Yeni içerik sistemi ayrı, açık tür ve sürüm alanları olan bir `MapContentDocument` zarfı kullanmalıdır. Eski harita JSON v1 dosyaları geriye uyumlu kalmalıdır.

### 3.3 Çevresel nesne domain modeli — önemli yapı taşları mevcut

İlgili dosyalar:

- `environment/definition.py`
- `environment/placement.py`
- `environment/scene.py`
- `environment/presentation.py`

Mevcut modelde:
- `EnvironmentalObjectDefinition` tekrar kullanılabilir tanımı, asset key'i, normalized anchor/depth ve isteğe bağlı collider'ı taşır.
- `EnvironmentalObjectPlacement` instance kimliğini, definition referansını, world/map kimliğini ve `WorldPoint` konumunu taşır.
- `EnvironmentalObjectScene` definition/placement kimliklerini ve referans bütünlüğünü doğrular; immutable ve deterministik sıralıdır.
- `environment_obstacles()` yalnızca açıkça tanımlı collider'ları fizik katmanına aktarır.
- `environment_sprite_visuals()` görsel DTO'larını üretir.

**Sınır:** Bu scene için JSON serileştirme yoktur ve scene mevcut harita belgesine bağlı değildir. Placement şu an yalnızca konum taşır; rotasyon/ölçek dönüşümü mevcut render/fizik sözleşmesinde tanımlı değildir. Definition, prosedürel profilin parametrelerini, çizim geometrisini, paletini veya üretim seed'ini içermez.

**Karar:** Var olan modeller korunmalı ve yeni içerik çekirdeğiyle adaptör üzerinden ilişkilendirilmelidir. Görsel tanım ile collider ayrımı korunmalı; collider çizim geometrisinden otomatik türetilmemelidir.

### 3.4 Prosedürel grafik — çizim altyapısı var, çizim verisi eksik

İlgili dosyalar:

- `rendering/procedural/geometry.py`
- `canvas.py`
- `components.py`
- `palette.py`
- `variation.py`
- `profiles.py`
- `cache.py`
- `rendering/_procedural_environment_legacy.py`

Mevcut altyapı saf yerel 2D geometriyi Pygame Surface üretiminden ayırır. Çizim bileşenleri polygon, ellipse, polyline ve circle gibi primitifleri destekler. Palet ve RGB doğrulaması vardır. Seed normalizasyonu BLAKE2b ve yerel `random.Random` kullanır; global random state değiştirilmez. Surface cache bounded LRU olarak hem öğe sayısı hem tahmini byte maliyetiyle sınırlıdır.

Beş profil vardır: tree, rock, bush, grass, flower. Tree/rock/bush görselleri legacy çizim fonksiyonlarından üretilir ve Aşama 12 görsel eşitliği test edilir. Grass/flower deterministik seed ile çizilir. `ProceduralProfile` şu an yalnızca key, logical size ve anchor metadata'sı taşır; profil geometrisinin tamamı saklanabilir veri değildir. Palet sınıfı legacy rendering modülündedir. Cache Pygame Surface nesnelerini tutar.

**Ana boşluk:** Mevcut `components.py` çizim fonksiyonlarıdır; çizim öğelerini temsil eden kalıcı bir veri modeli değildir. Bu nedenle gelecekteki masaüstü editörün şekilleri seçip düzenleyebilmesi için katmanlar, öğe kimlikleri, geometri, stil ve anchor verisi taşıyan bir vector drawing document gereklidir.

### 3.5 Mimari sınırlar ve kalite altyapısı

- `environment/` domain paketi Pygame import etmez.
- `world`, `geometry`, `physics`, `simulation` çekirdek paketlerinde Pygame yasağı AST tabanlı testle korunur.
- Rendering adaptörlerinin simulation/domain paketlerine bağımlılığı architecture-boundary testleriyle sınırlandırılmıştır.
- Laboratuvar Python >=3.11 hedefler; bağımlılıklar Pygame, test extra'sında Pytest, quality extra'sında Ruff'tır.
- Laboratuvar CI tam Pytest suite, Ruff kapsamı, persistence benchmarkları, Phase 12/13 görsel kanıtları ve çeşitli benchmarklar çalıştırır.
- Core Quality Linux ve Windows doğrulamasında laboratuvar Ruff kontrolleri de yer alır.

**Sonuç:** Yeni `content/` çekirdeği Pygame ve GUI bağımlılığı taşımamalıdır. Pygame yalnızca `rendering/` adaptöründe kalmalıdır. Aşama 14'te GUI framework veya masaüstü pencere bağımlılığı eklenmesine gerek yoktur.

## 4. Önemli mimari boşluklar

| No | Boşluk | Etkisi |
|---:|---|---|
| 1 | Kalıcı, katmanlı çizim belge modeli yok | Gelecekte şekil/katman düzenleme doğrudan mümkün değil |
| 2 | Profil geometrisi kod içinde sabit | JSON'a yalnızca profil adı/seed yazmak gerçek düzenlenebilirlik sağlamaz |
| 3 | Environment scene persistence yok | Nesne tanımları ve harita yerleşimleri kaydedilip yeniden açılamıyor |
| 4 | Map v1 yalnızca hex hücrelerini saklıyor | Yapı ve nesne yerleşimleri harita dosyasında temsil edilmiyor |
| 5 | İçerik kütüphanesi/registry yok | İçerik kimliği ve referans çözümleme ortak bir katmanda değil |
| 6 | Collider serialization sözleşmesi yok | Fiziksel alanlar güvenli ve tür etiketli içerik verisi olarak saklanamıyor |
| 7 | Placement transform sözleşmesi yok | Rotasyon/ölçek gelecekteki render/fizik desteğiyle birlikte ayrıca tasarlanmalı |
| 8 | İçerik ve renderer arasında veri adaptörü yok | Profil verisi doğrudan kod fonksiyonlarına bağlı |

## 5. Önerilen teknik mimari

Aşama 14 teknik planı aşağıdaki ayrımı temel almalıdır:

1. **Content domain:** Pygame'siz immutable içerik modelleri; içerik kimliği, kategori, görsel belge, palet, çizim katmanları ve çizim öğeleri.
2. **Content library:** Tekrarsız kimlikler ve referans bütünlüğü taşıyan içerik koleksiyonu.
3. **Map content document:** Mevcut `HexMapDefinition` + içerik instance yerleşimlerini bir araya getiren yeni belge zarfı. Eski map JSON v1 değişmeden kalır.
4. **Content persistence:** Ayrı, sürümlü JSON şemaları; strict validation, duplicate key/NaN reddi, deterministic serialization ve güvenli create/replace.
5. **Rendering adapter:** Doğrulanmış drawing document'ı Pygame Surface'e dönüştürür; cache kanonik belge içeriğinin fingerprint'iyle çalışır.
6. **Physics adapter:** Collider yalnızca açık collision tanımından üretilir; görsel öğelerin bounds/alpha verisi fizik şekli sayılmaz.
7. **Future desktop editor:** Yalnızca content domain ve persistence API'lerini kullanır; Pygame laboratuvar penceresine veya oyun runtime'ına bağımlı olmaz.

### Vektör belge için başlangıç primitifleri

Mevcut çizim API'leriyle uyumlu ve gelecekte düzenlenebilir bir ilk belge şu öğeleri desteklemelidir:
- polygon,
- ellipse,
- circle,
- polyline.

Belge ayrıca logical size, ground/depth anchor, sıralı layers, kararlı layer/element ID'leri, fill/stroke style ve palette token referanslarını taşımalıdır. Karmaşık çizim, bu primitiflerin katmanlar ve bileşimler halinde bir araya getirilmesiyle oluşturulabilir. Raster paint, animation timeline ve 3D model bu aşamaya eklenmemelidir.

## 6. Riskler ve teknik plan için öneriler

- **Mevcut görsel regresyon:** Tree/rock/bush için pixel regression korunmalı; yeni belge renderer'ı mevcut görünümü koruyamıyorsa geçiş kontrollü ve kanıtlı olmalıdır.
- **Şema erken donması:** Content ve map document şemaları v1 olarak açıkça belgelenmeli; bilinmeyen alanlar reddedilmeli, migration stratejisi ayrı tanımlanmalıdır.
- **Renderer bağımlılığı:** Domain belgesi Pygame Surface veya pygame.Rect içermemelidir.
- **Collider yanlış türetimi:** Collision şekli tagged union (circle/polygon) olarak açıkça saklanmalı ve physics adapter'a dönüştürülmelidir.
- **Eski map formatını bozma:** `MAP_JSON_SCHEMA_V1.md` ve mevcut serializer davranışı korunmalıdır.
- **Aşırı genelleme:** Bu aşamada sadece doğrulanmış primitive ailesi ve mevcut beş profil uygulanmalı; arbitrary scripting/plugin sistemi eklenmemelidir.
- **Placement dönüşümü:** Rotation/scale alanları mevcut renderer/fizik uyumluluğu kanıtlanmadan saklanmamalı; teknik plan bu alanları kapsam dışı bırakmalı veya tam uçtan uca destek şartıyla ayrıca gerekçelendirmelidir.

## 7. Denetim sonucu

Aşama 14 için teknik uygulamaya geçmeye yetecek temel mevcut; ancak sadece mevcut procedural profile JSON parametrelerini saklamak uzun vadeli editör hedefini karşılamaz. Teknik plan, **kalıcı vektör çizim belgesi + içerik kütüphanesi + map-content belgesi + strict persistence + Pygame/physics adaptörleri** üzerine kurulmalıdır.

Bu rapor denetim bulgularını kaydeder. Teknik plan ayrı kullanıcı onayına sunulacaktır. Teknik plan onaylanana kadar kod değişikliği yapılmayacaktır.

## 8. Denetim referansları

- `docs/MAP_JSON_SCHEMA_V1.md`
- `docs/RUNTIME_JSON_SCHEMA_V1.md`
- `docs/PHASE-13-TECHNICAL-PLAN.md`
- `src/hex_world_lab/world/`
- `src/hex_world_lab/world/persistence/`
- `src/hex_world_lab/environment/`
- `src/hex_world_lab/rendering/procedural/`
- `tests/unit/test_architecture_boundaries.py`
- `.github/workflows/hex-world-lab-ci.yml`
- `.github/workflows/core-quality.yml`
