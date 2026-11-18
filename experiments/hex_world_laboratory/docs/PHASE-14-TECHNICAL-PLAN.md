# Aşama 14 — Teknik Mimari ve Uygulama Planı

> **Belge türü:** Teknik plan  
> **Genel plan:** [PHASE-14-GENERAL-PLAN.md](PHASE-14-GENERAL-PLAN.md)  
> **Denetim:** [PHASE-14.1-AUDIT-REPORT.md](../reports/PHASE-14.1-AUDIT-REPORT.md)  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Denetlenen başlangıç HEAD:** `9de839ca2bbd3405060b207c8465b5051224b836`  
> **Durum:** KULLANICI ONAYLADI — TEKNİK UYGULAMA TAMAMLANDI, MANUEL KABUL BEKLENİYOR  
> **Uygulama:** 14.2–14.8 otomatik teknik kapsamı uygulandı; kullanıcı masaüstü kabul kapısı bekleniyor.

## 1. Teknik hedef

Aşama 14, gelecekte ayrı bir masaüstü uygulaması olarak geliştirilecek **ELDORIA CONTENT EDITOR** için ortak içerik veri çekirdeğini hazırlayacaktır. Editörün kendisi bu aşamada yapılmayacaktır.

Teknik hedef, mevcut beş prosedürel profilin yalnızca adını ve parametrelerini saklamak değildir. Gelecekte kullanıcının bir ağacı, kayayı veya binayı oluşturan çizim parçalarını seçip düzenleyebilmesi için **Pygame'den bağımsız, katmanlı ve vektör tabanlı VisualDocument** modeli oluşturulacaktır. Aynı belgeyi ileride masaüstü editörü açıp düzenleyebilecek, oyun runtime'ı ise Pygame adaptörü üzerinden çizebilecektir.

Bu çekirdek üç temel belgeyi tanımlar:

1. **ContentLibraryDocument:** Yeniden kullanılabilir içerik tanımları ve görsel çizim belgeleri.
2. **MapContentDocument:** Mevcut hex haritası ve o haritada yer alan içerik örnekleri.
3. **VisualDocument:** Katmanlar, çizim öğeleri, geometri, palet, anchor ve kaynak üretim bilgisi.

Mevcut `HexMapDefinition`, `EnvironmentalObjectScene`, fizik şekilleri, renderer ve harita JSON v1 korunacaktır. Yeni modeller mevcut sistemlere adaptörlerle bağlanacaktır.

## 2. Mimari kararlar

### 2.1 Paket sınırı

Yeni içerik domain'i `src/hex_world_lab/content/` altında bulunacaktır.

- Content modelleri immutable ve Pygame'siz olacaktır.
- JSON doğrulama/serileştirme content persistence altında bulunacaktır.
- Pygame Surface üretimi yalnızca `rendering/` altında kalacaktır.
- Physics collider verisi açık, tür etiketli veri olarak saklanacaktır; görsel öğelerden otomatik collider üretilmeyecektir.
- Yeni masaüstü uygulaması ileride content modelleri ve persistence API'lerini doğrudan kullanabilecektir.

### 2.2 Vektör çizim belge modeli

İlk sürümde aşağıdaki primitive türleri desteklenecektir:

- `polygon`: sıralı 2D noktalar.
- `ellipse`: x, y, width, height.
- `circle`: merkez ve yarıçap.
- `polyline`: sıralı noktalar, çizgi kalınlığı ve açık/kapalı bilgisi.

Belge sözleşmesi:
- pozitif `logical_size`,
- normalize edilmiş `ground_anchor` ve `depth_anchor`,
- benzersiz ve kararlı layer ID'leri,
- benzersiz ve kararlı element ID'leri,
- açık `order` alanıyla deterministik katman sırası,
- palette token tablosu,
- öğelerin fill/stroke palette token referansları,
- primitive'e özel geometri alanları,
- isteğe bağlı generator provenance (profile ID/sürümü, seed ve parametreler).

Layer görünürlüğü/lock gibi editör UI durumları bu aşamada saklanmayacaktır; bunlar editör uygulamasının kullanıcı arayüzü state'idir. İçerik belgesinde yalnızca runtime'da çizimi etkileyen kalıcı veri bulunacaktır.

### 2.3 İçerik tanımı ve yerleşim ayrımı

- `ContentDefinition` bir kez tanımlanan varlıktır: ID, ad, kategori, VisualDocument, anchor/bounds metadata ve isteğe bağlı collider.
- `ContentPlacement` bu varlığın bir haritadaki belirli örneğidir: instance ID, content ID ve dünya konumu.
- `ContentLibrary` benzersiz içerik tanımlarını tutar.
- `MapContentDocument` bir `HexMapDefinition` ile yerleşim örneklerini bir arada tutar.
- Map document doğrulaması her placement content ID'sinin verilen ContentLibrary içinde bulunduğunu doğrular.

Aşama 14 placement v1 yalnızca konumu saklayacaktır. Rotation/scale alanları, mevcut SpriteVisual, renderer ve physics collider akışları bunları uçtan uca desteklemediği için eklenmeyecektir. Veri biçiminde kullanılmayan dönüşüm alanı saklamak yasaktır. Bu ihtiyaç, renderer ve collision transform desteğiyle birlikte sonraki aşamada ele alınacaktır.

### 2.4 Collider sözleşmesi

Collider yalnızca açık fizik tanımından gelir. JSON tagged union:

- Circle: `type: "circle"`, radius, center x/y.
- Convex polygon: `type: "convex_polygon"`, ordered vertices.

Deserialize aşamasında mevcut `CircleShape`, `ConvexPolygonShape` ve `Vector2` modellerine dönüştürülür. Mevcut physics validator'ları son geometrik doğrulamayı yapar. Collider olmaması geçerli bir içerik durumudur. VisualDocument alpha bounds veya polygon çizimi otomatik collider üretmez.

### 2.5 Sürümleme ve geriye uyumluluk

- Content library: `schema_version: 1`, `kind: "eldoria_content_library"`.
- Map content document: `schema_version: 1`, `kind: "eldoria_map_document"`.
- VisualDocument kendi `document_version: 1` alanını taşır.
- Mevcut MAP JSON v1 ve RUNTIME SNAPSHOT v1 değiştirilmez.
- MapContentDocument içindeki `map` alanı mevcut map schema v1 payload'ını aynen içerir.
- Bilinmeyen alanlar, yinelenen ID'ler, bilinmeyen primitive/shape türleri ve desteklenmeyen sürümler reddedilir.
- Otomatik migration bu aşamada yapılmaz; desteklenmeyen sürüm açık hata üretir. Migration tasarımı daha sonraki bir aşamada ayrı onaylanır.

## 3. Önerilen dosya yapısı

### 3.1 Yeni content domain

```text
src/hex_world_lab/content/
    __init__.py
    values.py                 # immutable JSON freeze/thaw ve ortak doğrulama
    drawing.py                # Point, style, primitive, layer, VisualDocument
    definition.py             # ContentDefinition ve kategori
    placement.py              # ContentPlacement
    library.py                # ContentLibrary ve ID/reference invariants
    map_document.py           # MapContentDocument
    collision.py              # collider JSON/domain adaptasyon sözleşmesi
    persistence/
        __init__.py
        errors.py
        library_validator.py
        library_serializer.py
        library_deserializer.py
        map_document_validator.py
        map_document_serializer.py
        map_document_deserializer.py
        file_storage.py
```

### 3.2 Rendering adaptörü

```text
src/hex_world_lab/rendering/procedural/
    document_renderer.py      # VisualDocument -> Pygame SRCALPHA Surface
    document_profiles.py      # tree/rock/bush/grass/flower built-in belge üreticileri
```

Mevcut `geometry.py`, `canvas.py`, `components.py`, `palette.py`, `variation.py` ve `cache.py` kullanılmaya devam edecektir. Mevcut `profiles.py` dış API'si geriye uyumlu tutulacaktır; profil oluşturma içeride VisualDocument üretip renderer adaptörüne geçecek şekilde dönüştürülecektir.

### 3.3 Testler ve belgeler

```text
tests/unit/test_content_drawing.py
tests/unit/test_content_definition.py
tests/unit/test_content_library.py
tests/unit/test_content_placement.py
tests/unit/test_content_map_document.py
tests/unit/test_content_persistence/
    test_library_validator.py
    test_library_round_trip.py
    test_map_document_round_trip.py
    test_file_storage.py
tests/unit/test_content_rendering_adapter.py
tests/integration/test_content_map_rendering.py
tests/acceptance/test_phase_14_content_documents.py
docs/CONTENT_LIBRARY_JSON_SCHEMA_V1.md
docs/MAP_CONTENT_JSON_SCHEMA_V1.md
```

Dosya listesi denetim sonrası hedef mimaridir; uygulama sırasında ek değişiklik gerekirse iş paketi raporunda gerekçelendirilir.

## 4. Veri sözleşmeleri

### 4.1 VisualDocument

Önerilen JSON şekli (temsili):

```json
{
  "document_version": 1,
  "logical_size": [132, 168],
  "ground_anchor": [0.5, 0.94],
  "depth_anchor": [0.5, 0.80],
  "palette": {
    "leaf_shadow": [34, 83, 48, 255],
    "leaf_mid": [54, 112, 57, 255],
    "bark": [83, 47, 31, 255]
  },
  "layers": [
    {
      "layer_id": "trunk",
      "order": 10,
      "elements": [
        {
          "element_id": "trunk-main",
          "shape": {
            "type": "polygon",
            "points": [[49, 151], [54, 111], [72, 48], [87, 151]]
          },
          "style": {"fill": "bark"}
        }
      ]
    }
  ],
  "generator": {
    "profile_id": "tree",
    "profile_version": 1,
    "seed": 0
  }
}
```

Bu örnek yalnızca alan ilişkisini gösterir; gerçek ağaç çizim geometrisi uygulama sırasında mevcut görselden aktarılacak ve regression testleriyle doğrulanacaktır. Palette token'ı bulunmayan renk referansı reddedilir. Geometri değerleri sonlu sayılar olmalı; ölçüler ve primitive alanları shape türüne göre doğrulanmalıdır.

### 4.2 ContentLibraryDocument

Üst düzey alanlar:
- `schema_version`
- `kind`
- `library_id`
- `definitions[]`

Her definition:
- `content_id`
- `name`
- `category` (ilk sürümde `environmental_object` veya `structure`)
- `visual_document`
- `collider` (null veya tagged collider)
- `metadata` (JSON uyumlu, derin immutable)

Structure kategorisi bu aşamada yeni bina çizim seti veya yapı oyun mekaniği sağlamaz. Aynı vektör primitive/layer belge sistemiyle yapı içeriğinin ileride tanımlanabilmesini sağlar.

### 4.3 MapContentDocument

Üst düzey alanlar:
- `schema_version`
- `kind`
- `map`: mevcut MAP JSON schema v1 payload
- `placements[]`

Her placement:
- `instance_id`
- `content_id`
- `position: {x, y}`

World/map kimlikleri map payload'ından alınır; placement JSON'unda gereksiz tekrar edilmez. Her placement instance ID'si belge içinde benzersiz olmalıdır. Content ID referansı library içinde çözülmelidir. Position mevcut `WorldPoint` kurallarına göre sonlu olmalıdır.

## 5. Serialization ve dosya güvenliği

- UTF-8 JSON; deterministic key sorting, indentation ve final newline.
- `allow_nan=False`; parse sırasında `parse_constant` ile NaN/Infinity reddi.
- `object_pairs_hook` ile duplicate JSON object key reddi.
- Şema validator'ları unknown/missing field, yanlış tip, bool-as-int, finite number, duplicate ID ve broken reference kontrolü yapar.
- Dosya parse/validation tamamlanmadan hiçbir registry veya runtime state değiştirilmez.
- Save API varsayılan `create`; mevcut dosyayı ezmez.
- Açık `replace` işlemi aynı dizindeki geçici dosyadan atomik replace kullanır; geçici dosya hata durumunda temizlenir.
- Hatalı içerik dosyası mevcut geçerli library/map state'ini değiştirmez.
- Mevcut map/runtime persistence kodu ilk uygulamada refactor edilmeyecektir; yeni content persistence kendi public API'sini ve hata tiplerini sağlar. Ortak helper'a taşıma ancak duplication ölçülüp ayrı regresyon riski değerlendirildikten sonra yapılabilir.

## 6. Runtime ve mevcut mimari adaptörleri

### 6.1 VisualDocument renderer

`document_renderer.py`:
1. Yalnızca doğrulanmış VisualDocument kabul eder.
2. Layer'ları `order` ve belge sırasına göre deterministik çizer.
3. Palette token'larını RGBA'ya çözer.
4. Polygon/ellipse/circle/polyline öğelerini mevcut canvas/components API'leriyle Surface'e çizer.
5. Pygame display açılmadan SRCALPHA Surface üretebilir.
6. Content domain nesnesini değiştirmez.

### 6.2 Beş mevcut profilin geçişi

- Tree/rock/bush geometrisi mevcut legacy fonksiyonlardan VisualDocument katmanlarına aktarılır.
- Grass/flower seed tabanlı geometri üretimi aynı yerel RNG sözleşmesini kullanır; rastgele seçilen koordinatlar VisualDocument öğelerine yazılır.
- `generator` metadata'sı profil ID/sürümü ve seed'i korur.
- `build_environment_profile(s)` public API'leri Surface döndürmeye devam eder; içeride belge üretimi + document renderer + cache akışına delege eder.
- Ağaç/kaya/çalı mevcut pixel regression testleri korunur. Tam eşitlik mümkün olmazsa fark sessizce kabul edilmez; görsel fark raporlanır ve kullanıcı kabulü istenir.

### 6.3 Environment ve physics adaptörleri

- ContentDefinition, mevcut `EnvironmentalObjectDefinition` modeline çevrilir.
- ContentPlacement, mevcut `EnvironmentalObjectPlacement` modeline çevrilir.
- Mevcut `EnvironmentalObjectScene` ve `environment_sprite_visuals()` / `environment_obstacles()` akışı korunur.
- Renderer asset key olarak kararlı content ID kullanabilir.
- Collider yalnızca content tanımındaki açık collider alanından üretilir.
- VisualDocument geometri değişimi collider'ı değiştirmez; bunun için ayrı collision düzenlemesi gerekir.

## 7. İş paketleri ve uygulama sırası

### 14.1 — Depo ve mimari denetimi
Tamamlandı. Bulgular `reports/PHASE-14.1-AUDIT-REPORT.md` içindedir.

### 14.2 — İçerik modeli ve veri sözleşmeleri
- ContentDefinition, ContentPlacement, ContentLibrary ve MapContentDocument immutable modelleri.
- VisualDocument, palette, layer ve primitive tipleri.
- Collider tagged union ve mevcut physics shape adaptörü.
- Model invariant'ları ve architecture-boundary testleri.
- JSON schema belgelerinin kesinleştirilmesi.

### 14.3 — İçerik serileştirme ve sürümleme
- Library ve map-content validator/serializer/deserializer.
- Strict JSON parse ve deterministic output.
- Save/load create/replace güvenliği.
- Round-trip ve bozuk/uyumsuz belge testleri.

### 14.4 — Doğrulama ve içerik registry/kütüphanesi
- Benzersiz content ID ve placement ID kontrolü.
- ContentLibrary lookup ve referans çözümleme.
- MapContentDocument referential integrity.
- Unknown content, duplicate IDs ve eksik referansların güvenli reddi.

### 14.5 — Runtime adaptörü ve mevcut profil uyumluluğu
- VisualDocument -> Surface renderer.
- Beş profilin veri tabanlı belge üreticilerine dönüşümü.
- Environment/physics adapter bağlantısı.
- Cache key için canonical document fingerprint.
- Mevcut görsel ve collider regresyonları.

### 14.6 — Harita ve yerleşim altyapısı
- MapContentDocument ve placement persistence'in bütünleştirilmesi.
- Yerleşim ekleme/güncelleme/kaldırma işlemleri için GUI'siz application/domain API.
- ContentLibrary referans çözümlemesi ve map scope doğrulaması.
- Mevcut harita v1 dosyalarıyla geriye uyumluluk.
- Harita editörü, fare input'u veya çizim arayüzü yok.

### 14.7 — Bütünleşme, regresyon ve editör hazırlık raporu
- Demo sahnesinin yeni ContentLibrary/MapContentDocument yolunu kullanması.
- Eski API'lerin gerektiği yerde uyumluluk facade'ı olarak korunması.
- Runtime ve renderer mimari sınır testleri.
- ELDORIA CONTENT EDITOR için API kullanım örnekleri ve açık kalan yetenekler.

### 14.8 — Bütünleşik doğrulama ve kabul
- Tam Pytest, Ruff, Linux/Windows CI.
- Serialization, corruption, determinism, renderer regression ve collider independence testleri.
- Benchmark ve PNG artifact üretimi.
- Kullanıcının mevcut demo ve görsel regresyon kabulü.
- Kapanış raporu ve Master Plan güncellemesi.

## 8. Test matrisi

| Alan | Testler |
|---|---|
| VisualDocument | primitive tipleri, sonlu geometri, pozitif ölçü, anchor aralığı, benzersiz layer/element ID |
| Palette/style | RGBA kanal tipi/aralığı, palette token referansı, eksik token reddi |
| ContentDefinition | ID, kategori, görsel belge, collider tipi |
| ContentLibrary | benzersiz ID, deterministik sıralama, lookup, immutable state |
| ContentPlacement | ID, content ref, WorldPoint finite değerleri |
| MapContentDocument | world/map scope, duplicate instance, unknown content ref |
| Persistence | round-trip, unknown/missing field, duplicate key, NaN/Infinity, schema version, atomic create/replace |
| Renderer | her primitive, layer order, alpha, headless Surface, palette token |
| Profile regression | tree/rock/bush pixel parity; grass/flower same-seed determinism |
| Physics separation | visual edit/seed/palette değişimi collider değerini değiştirmez |
| Integration | content library + map doc -> environment scene -> render/physics adapter |
| Architecture | content domain Pygame/GUI import etmez; rendering adapter content modelini okur, world/simulation state'ini değiştirmez |

## 9. CI, Ruff ve benchmark

- Laboratuvarın mevcut `python -m pytest -q` suite'i korunur.
- Ruff mevcut quality extra ve CI adımlarına eklenen yeni content/rendering dosyalarını kapsar; eski dosyalar topluca formatlanmaz.
- `hex-world-lab-ci.yml` ve `core-quality.yml` yeni testleri çalıştırır.
- Content persistence benchmarkı 100/1.000/10.000 content definition ve placement ölçeklerinde parse/validate/serialize maliyetini ölçer.
- Renderer benchmarkı 5 built-in profil ve tekrar eden cache hit/miss için ölçüm yapar.
- Mutlak donanım bağımsız süre eşiği konulmaz; önceki aşamalarla karşılaştırılabilir medyan ve bellek tahmini raporlanır.
- CI artifact'leri schema fixture'ları, görsel PNG'ler, benchmark JSON ve JUnit raporunu içerir.

## 10. Manuel kabul

Kullanıcıdan masaüstü editör testi istenmeyecektir. Kabul adımları:
1. Laboratuvar tek launcher ile açılır.
2. Beş mevcut profilin görseli önceki kabul edilmiş görünümleri korur.
3. ContentLibrary ve MapContentDocument örnekleri kaydedilip yeniden yüklendiğinde aynı içerik ve yerleşimleri verir.
4. Harita üzerine yerleştirilmiş örnekler doğru konum ve Y-sort ile görünür.
5. F3 collider ve F4 anchor/bounds debug davranışları korunur.
6. Görsel belge değişikliği collider'ı değiştirmez.
7. Hatalı içerik yükleme mevcut demo/world state'ini bozmaz.
8. Kamera, harita ve simülasyon davranışında regresyon oluşmaz.

## 11. Kapsam dışı

- ELDORIA CONTENT EDITOR masaüstü uygulaması veya GUI framework.
- Harita çizme/hex hücre boyama/harita düzenleme arayüzü.
- Fareyle nesne yerleştirme, sürükleme veya silme UI'si.
- Pixel/raster paint editor, bezier/curve editor, animation timeline veya 3D modelleme.
- Rotation/scale placement transform desteği.
- Yeni bina setleri veya oyun mekaniği; yalnızca aynı primitive/layer modeliyle yapı içeriğini temsil edebilme.
- Collider çizim editörü; collider yalnızca veri olarak tanımlanır.
- NPC AI, pathfinding, gathering/economy veya main-game integration.

## 12. Onay kapısı

Bu teknik plan kullanıcı tarafından 18 Kasım 2026 tarihinde onaylanmıştır. 14.2–14.8 uygulaması yalnızca `experiment/hex-world-laboratory` dalında yürütülmüştür; `main` ve `demo_eldoria` dallarına commit/merge yapılmamıştır. Resmî kapanış, otomatik doğrulama ve kullanıcı masaüstü kabulü tamamlandığında yapılacaktır.


## 13. Uygulama durumu — 18 Kasım 2026

- 14.2: Immutable VisualDocument, primitive/layer/style/palette sözleşmeleri; ContentDefinition, ContentLibrary, ContentPlacement ve MapContentDocument tamamlandı.
- 14.3: Content Library JSON v1 ve Map Content JSON v1 strict codec/file storage tamamlandı. Duplicate key, NaN/Infinity, unknown/missing field ve unsupported version reddedilir.
- 14.4: Stable ID, duplicate identity, palette token ve content reference çözümlemesi tamamlandı.
- 14.5: Beş profilin vektör belge üretimi eklendi. Eski Surface API'leri aynı kalırken artık VisualDocument + Pygame renderer üzerinden üretim yapar; ağaç/kaya/çalı pixel parity ve grass/flower seed determinism testleri korunur. Bounded cache, content ID asset registration ve açık collider adaptörleri eklendi.
- 14.6: MapContentDocument placement add/update/remove ve mevcut map v1 wrapper persistence tamamlandı.
- 14.7: Built-in beş profil ContentLibrary, map preview entegrasyonu, environment scene/render/physics adapter bağlantıları ve ELDORIA CONTENT EDITOR API hazırlık belgesi tamamlandı.
- 14.8: Tam pytest, Ruff, Linux/Windows CI, benchmark ve PNG artifact doğrulaması yürütülüyor. Kullanıcı manuel kabul kontrol listesi eklendi.
- Bilinçli sınır: Beş built-in profilin collider alanı varsayılan olarak null; görselden collider türetilmez. Oyun/Content Editor ihtiyacına göre collider ayrı açık veri olarak yazılır.
- GUI, masaüstü editör, fareyle harita düzenleme, rotation/scale ve ana oyuna entegrasyon yapılmadı.
