# Aşama 13 — Teknik Mimari ve Uygulama Planı

> **Belge türü:** Teknik plan  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Genel plan:** [PHASE-13-GENERAL-PLAN.md](PHASE-13-GENERAL-PLAN.md)  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — 18 KASIM 2026  
> **Uygulama durumu:** Başlamadı; bu belge kod değişikliği izni değildir.

## 1. Teknik hedef

Aşama 12'nin tekil çizim fonksiyonları, ortak ve test edilebilir bir prosedürel grafik katmanına ayrılacaktır. Yeni katman; saf geometri/parametre hesapları, Pygame Surface üretimi, paletler, deterministik varyasyon, yeniden kullanılabilir çizim bileşenleri ve çevresel nesne profillerini birbirinden ayıracaktır.

Mevcut `EnvironmentalObjectDefinition`, `EnvironmentalObjectPlacement`, `EnvironmentalObjectScene`, fizik adaptörleri, render snapshot DTO'ları, renderer ve dünya konum sözleşmeleri korunacaktır. Yeni grafik sistemi mevcut çevresel nesne domain modelini yeniden tanımlamayacaktır.

## 2. Depo denetiminden çıkan mevcut durum

İncelenen dal HEAD: `91b1112bcce505d7d6c0b95cb4a7d3b55317b16c`.

### 2.1 Mevcut görsel üretim

- `rendering/procedural_environment.py` içinde `EnvironmentArtPalette`, `_surface`, `_finish` ve doğrudan Pygame çizim çağrılarıyla ağaç/kaya/çalı üretiliyor.
- Her profil kendi yerel koordinat/çizim yardımcılarını tanımlıyor; ortak geometri ve bileşen API'si henüz bulunmuyor.
- Yüzeyler `pygame.SRCALPHA` ile 3x supersampling kullanılarak oluşturuluyor ve `pygame.transform.smoothscale` ile son boyuta indiriliyor.
- `environment_assets.py` üç Surface'i üretip renderer'a `SpriteAsset` ve normalize anchor değerleriyle kaydediyor.
- Mevcut testler raster dosyası yüklenmediğini, üç yüzeyin deterministik olduğunu, alpha kanalını, ölçüleri ve palet etkisini kontrol ediyor.

### 2.2 Mevcut domain/presentation sınırı

- `environment/` domain paketi Pygame bağımlılığı taşımıyor.
- Görsel tanım, yerleşim ve sahne immutable veri sınıflarıyla temsil ediliyor.
- `environment_obstacles()` yalnızca açıkça tanımlanmış collider'ları fizik adaptörüne aktarıyor.
- `environment_sprite_visuals()` anchor/depth bilgisiyle render DTO'su oluşturuyor.
- `environment_debug_visuals()` sprite/canopy bounds ve anchor tanılamasını sağlıyor.
- Renderer sprite Y-sort, görsel bounds culling, F3 collider ve F4 çevresel bounds/debug akışını zaten destekliyor.

### 2.3 Kalite altyapısı

- Laboratuvar `pyproject.toml` dosyası Pytest'i `test` extra'sında tanımlıyor; laboratuvar CI tam test paketini `python -m pytest -q` ile çalıştırıyor.
- Laboratuvar CI şu anda Ruff kurulumu, Ruff yapılandırması veya Ruff kontrol adımı içermiyor.
- Kök `pyproject.toml` ve Core Quality akışı ayrı; Core Quality release doğrulaması çalıştırıyor. Laboratuvar kapsamı için ana test iş akışı `hex-world-lab-ci.yml`.
- Bu nedenle Ruff, Aşama 13'te yalnızca raporlanan araç olarak bırakılmayacak; laboratuvar kapsamına kontrollü biçimde eklenecek. Mevcut kodun tamamına toplu format/lint uygulamak bu aşamanın kapsamı olmayacak.

## 3. Önerilen hedef paket yapısı

Yeni kod, mevcut `rendering` paketinin altında `procedural` alt paketinde tutulacaktır. Bu konum, Pygame'e bağlı sunum kodunun dünya domain katmanına sızmasını önler.

```text
src/hex_world_lab/
├── environment/
│   ├── definition.py                 # mevcut domain tanımı; korunur
│   ├── placement.py                  # mevcut yerleşim; korunur
│   ├── scene.py                      # mevcut sahne; korunur
│   └── presentation.py                # mevcut domain → fizik/render adaptörleri; korunur
└── rendering/
    ├── procedural_environment.py     # geriye uyumlu facade
    ├── environment_assets.py          # profil Surface'lerini renderer'a kaydeder
    └── procedural/
        ├── __init__.py
        ├── geometry.py               # saf yerel 2D geometri ve dönüşümler
        ├── canvas.py                 # mantıksal canvas, alpha Surface, ölçekleme
        ├── palette.py                # renk rolleri, paletler ve rampalar
        ├── variation.py              # seed normalizasyonu ve yerel RNG
        ├── components.py             # tekrar kullanılabilir çizim bileşenleri
        ├── profiles.py               # profil/parametre tanımları ve üreticiler
        └── cache.py                  # ölçümle gerekçelendirilmiş Surface cache
```

### Paket sorumlulukları

| Modül | Sorumluluk | Bağımlılık kuralı |
|---|---|---|
| `geometry.py` | Yerel 2D nokta, bounds, nokta dönüşümü, ölçek/döndürme ve şekil geometrisi | Pygame ve dünya domain'i import etmez |
| `canvas.py` | Mantıksal ölçü, supersampling, şeffaf Surface oluşturma, çizim koordinatı dönüşümü ve final ölçekleme | Pygame'e bağlıdır; geometry yardımcılarını kullanır |
| `palette.py` | RGB doğrulaması, renk rolü, rampalar ve immutable paletler | Pygame ve renderer import etmez |
| `variation.py` | Açık seed'den yerel deterministik RNG/parametre örnekleme | Global random state kullanmaz veya değiştirmez |
| `components.py` | Dal, yaprak kütlesi, gövde/kök, kaya faseti, çalı kütlesi, çim ve çiçek gibi tekrar kullanılabilir çizim parçaları | Canvas ve palette API'si üzerinden çalışır |
| `profiles.py` | Profil kimliği, mantıksal ölçüler, anchor/depth metadata, palet, seed/parametre ve bileşen bileşimi | Environment domain sınıflarını değiştirmez |
| `cache.py` | Profil girdisinden Surface üretimi ve bounded cache | Yalnızca render/procedural katmanında Pygame Surface tutar |

Bu yapı ilk uygulama öncesinde 13.1 denetimiyle tekrar doğrulanacaktır. Denetim, gereksiz soyutlama tespit ederse dosyalar birleştirilebilir; fakat domain/Pygame sınırı ve deterministik üretim şartı gevşetilemez.

## 4. Veri ve üretim akışları

### 4.1 Profil → Surface → Renderer

```text
ProceduralProfile + Palette + Parameters + Seed
                    |
                    v
             Profile Builder
                    |
                    v
          Reusable Components
                    |
                    v
          Procedural Canvas (SRCALPHA)
                    |
                    v
        Supersampling / Final Surface
                    |
                    v
           Bounded Surface Cache
                    |
                    v
          environment_assets.py
                    |
                    v
        SpriteAsset + normalized anchor
                    |
                    v
          PygameWorldRenderer
```

Surface üretimi oyun frame döngüsünde yapılmayacaktır. Profil/parametre/seed girdisi hazırlanırken veya asset kayıt aşamasında bir kez üretilecek; renderer yalnızca kayıtlı Surface'i blit edecektir.

### 4.2 World placement ve collider akışı

```text
EnvironmentalObjectScene
       |                         |
       v                         v
environment_sprite_visuals   environment_obstacles
       |                         |
       v                         v
SpriteVisual                 Explicit Collider
       |                         |
       v                         v
World Renderer               Physics Adapter
```

Procedural profile yalnızca görsel metadata ve Surface üretir. Collider, profile çiziminden veya alpha piksel sınırından türetilmez. Fizik şekli mevcut `EnvironmentalObjectDefinition.collider` alanında açıkça tanımlanmaya devam eder.

## 5. Teknik sözleşmeler

### 5.1 Geometri ve koordinat

- Geometri koordinatları nesneye özel yerel 2D koordinatlardır; `WorldPoint` veya `WorldScreenTransform` yerine geçmez.
- Geometri yardımcıları immutable tuple/dataclass benzeri saf girdiler ve saf dönüşler kullanır.
- Mantıksal canvas boyutu, çıktı Surface boyutu ve supersampling ölçeği ayrı alanlar olarak tanımlanır.
- Ölçekleme yalnızca canvas finalizasyonunda uygulanır; profil bileşenleri mantıksal koordinatlarda çalışır.
- Döndürme/ölçekleme merkezleri ve dönüş sırası açıkça tanımlanır.
- Bounds hesapları çizim alanının dışına taşan bileşenleri de kapsayacak şekilde doğrulanır.
- Geçersiz ölçü, NaN/sonsuz değer, negatif yarıçap, yetersiz çokgen noktası ve geçersiz ölçek erken hata verir.

### 5.2 Canvas ve Pygame Surface

- Çıktı yüzeyleri per-pixel alpha destekli `pygame.SRCALPHA` yüzeyleridir.
- Çizim primitive'leri Pygame adaptöründe çalışır; saf geometri modülüne Pygame import edilmez.
- Supersampling ölçeği profilin keyfi bir sabiti olmayacak; canvas/üretim parametresi olacaktır. Varsayılan başlangıç değeri Aşama 12'de doğrulanan 3 olarak korunur.
- Final Surface boyutları tam ve pozitif tamsayı olmalıdır.
- Display başlatılmadan Surface üretimi ve headless CI davranışı test edilir.
- Alpha korunumu ve smoothscale sonucu test edilir. `convert_alpha()` yalnızca aktif display formatına bağlılık yaratmadan ve gerçek blit benchmark'ı ile gerekçelendirilirse kullanılacaktır.
- Surface üretimi ve pixel erişimi render frame'i içinde yapılmayacaktır.

### 5.3 Palet ve renk rampası

- RGB kanalları bool olmayan tamsayı ve 0–255 aralığında olmalıdır.
- Paletler immutable olacaktır.
- Renk rolleri en az shadow, base/mid, light ve accent kavramlarını destekleyecektir; her profil tüm rolleri kullanmak zorunda değildir.
- Renk rampası üretimi saf ve deterministik olacaktır.
- Palet değişikliği Surface piksel rengini etkileyebilir; profil ölçüsü, anchor, depth metadata ve collider'ı değiştiremez.
- Ağaç/kaya/çalı varsayılan paletlerinin mevcut görünümü regresyon referansı olacaktır.

### 5.4 Seed ve deterministik varyasyon

- Her üretim çağrısı açık bir seed alacaktır; seed verilmezse profilin belgelenmiş sabit varsayılanı kullanılacaktır.
- Seed girdisi bool olmayan int veya normalize edilmiş string kimlik olabilir; kabul edilen tipler tek API sözleşmesinde sabitlenecektir.
- String seed normalizasyonu Python `hash()` kullanmayacak; süreçler arası değişmeyen sabit algoritma ile yapılacaktır.
- Her üretim kendi yerel RNG nesnesini kullanacak; modül seviyesindeki global `random` durumu okunmayacak/değiştirilmeyecektir.
- Aynı profil sürümü + parametreler + palet + seed + canvas ayarları aynı görsel çıktıyı vermelidir.
- Farklı seed'ler yalnızca izin verilen parametre aralıklarında varyasyon üretmelidir.
- Seed tek başına instance ID yerine geçmez; instance kimliği, profil ve seed'in nerede saklanacağı sonraki persistence aşamalarına bırakılır.

### 5.5 Profil ve bileşen sözleşmesi

- Profil tanımı en az profil anahtarı, mantıksal ölçü, anchor/depth metadata, palet, parametre doğrulayıcıları ve üretim fonksiyonunu kapsar.
- Profil, fizik collider'ı içermez.
- Bileşenler küçük ve tek sorumluluklu tutulur; örneğin bir yaprak kümesi çizer, ağaç profilinin tamamını yönetmez.
- Bir bileşenin ortak API'ye alınması için en az iki profil veya gerçek bir tekrar kullanım ihtiyacı gösterilmelidir.
- Sadece tek profile özgü sanatsal ayrıntılar profil içinde kalabilir.
- Mevcut `build_environment_surfaces()` ve `EnvironmentArtPalette` import yolları testler/başka çağıranlar açısından geriye uyumlu facade olarak korunacaktır.

### 5.6 Surface cache

- Cache anahtarı profil kimliği/sürümü, doğrulanmış parametreler, palet değerleri, seed ve canvas ölçeğini kapsamalıdır.
- Cache sınırsız büyüyemez; kapasite hem öğe sayısı hem yaklaşık Surface byte maliyetiyle sınırlandırılacaktır.
- Cache hit, miss, üretim süresi ve tahmini bellek ölçülebilir olmalıdır.
- Pygame Surface mutable olduğu için cache'ten dönen Surface'ler kayıt sonrası salt-okunur kabul edilecek; üretim kodu veya renderer bu Surface'leri değiştirmeyecektir. Bu kural test ve API dokümantasyonuyla korunacaktır.
- Cache invalidation/clear ve limit aşımında LRU/eviction davranışı test edilecektir.
- Cache'in kendisi performans kazancı sağlamıyorsa kaldırılabilir; cache kullanımı aşama hedefi değil, ölçüm sonucudur.

## 6. Profil kapsamı ve görsel kabul hedefi

İlk sürümde en az beş profil bulunacaktır:

1. Ağaç — gövde, kök, dal, yaprak kütlesi ve ışık vurguları.
2. Kaya — dış siluet, ana yüzey, faset/gölge ve küçük yüzey vurguları.
3. Çalı — örtüşen organik kütleler ve ışık vurguları.
4. Çim kümesi — farklı boylarda saplar/yapraklar ve zemin teması.
5. Çiçek/bitki kümesi — sap, yaprak ve küçük çiçek başı bileşenleri.

Ağaç/kaya/çalı, Aşama 12'nin görsel kabul referansını koruyacak. Yeni çim/çiçek profilleri yalnızca örnek olsun diye birbirinin renk değiştirmiş kopyası olmayacak; farklı bileşen bileşimleri ve silhouette profilleri gösterecek.

Yeni profillerin collider'ı varsayılan olarak `None` olabilir. Bir profilin fiziksel engel olması istenirse collider ayrıca açıkça tanımlanır; görsel şekilden otomatik oluşturulmaz.

## 7. Dosya değişiklik planı

### Yeni dosyalar

| Dosya | Amaç |
|---|---|
| `src/hex_world_lab/rendering/procedural/__init__.py` | Kontrollü public API |
| `.../geometry.py` | Saf yerel geometri |
| `.../canvas.py` | Pygame Surface/canvas üretimi |
| `.../palette.py` | Palet ve renk rampası |
| `.../variation.py` | Seed ve yerel RNG |
| `.../components.py` | Tekrar kullanılabilir çizim bileşenleri |
| `.../profiles.py` | Beş profil ve profil üretim sözleşmesi |
| `.../cache.py` | Bounded Surface cache |
| `tests/unit/test_procedural_geometry.py` | Geometri birim testleri |
| `tests/unit/test_procedural_canvas.py` | Canvas/Surface/alpha testleri |
| `tests/unit/test_procedural_palette.py` | Palet/rampa testleri |
| `tests/unit/test_procedural_variation.py` | Seed/determinism testleri |
| `tests/unit/test_procedural_components.py` | Bileşen geometri/parametre testleri |
| `tests/unit/test_procedural_profiles.py` | Profil/ölçü/anchor testleri |
| `tests/unit/test_procedural_cache.py` | Cache sınır/anahtar/eviction testleri |
| `scripts/render_phase_13_scenes.py` | Beş profil için görsel kanıt üretimi |
| `benchmarks/benchmark_phase_13_procedural_art.py` | Profil üretimi ve cache benchmark'ı |

### Değiştirilecek dosyalar

| Dosya | Planlanan değişiklik |
|---|---|
| `src/hex_world_lab/rendering/procedural_environment.py` | Eski import/API'leri koruyan facade; profil üretimini yeni pakete delege eder |
| `src/hex_world_lab/rendering/environment_assets.py` | Beş profili asset key ve normalize anchor ile kaydeder |
| `tests/unit/test_procedural_environment_art.py` | Eski üç profil regresyonu ve yeni beş profil doğrulaması |
| `tests/integration/test_environment_object_rendering.py` | Yeni asset'lerin renderer/Y-sort/culling/debug uyumu |
| `tests/acceptance/test_phase_12_environment_scenes.py` | Aşama 12 kanıtının korunması; Aşama 13 için ayrı acceptance testi eklenebilir |
| `experiments/hex_world_laboratory/pyproject.toml` | Ruff kalite extra ve kapsamı sınırlı Ruff ayarları |
| `.github/workflows/hex-world-lab-ci.yml` | Ruff kurulumu/check/format-check, Aşama 13 test/benchmark/görsel kanıt adımları |

Bu liste 13.1 denetiminden sonra kesinleştirilecektir. Başka dosyaya ihtiyaç çıkarsa değişiklik gerekçesi teknik iş paketi raporunda kaydedilir. `environment/definition.py`, `placement.py`, `scene.py`, `presentation.py`, fizik şekilleri ve simülasyon koordinatörlerinde gereksiz değişiklik yapılmayacaktır.

## 8. Test matrisi

| Alan | Test türü | Asgari kanıt |
|---|---|---|
| Geometri | Unit/property-style | dönüşüm, bounds, sınır değerleri ve geçersiz girdi |
| Canvas | Unit | SRCALPHA, mantıksal/final boyut, supersampling, alpha korunumu, headless üretim |
| Palet | Unit | RGB tip/aralık doğrulaması, immutable davranış, ramp uç değerleri |
| Seed | Unit/regression | aynı seed aynı çıktı; farklı seed kontrollü fark; global random state değişmez |
| Bileşen | Unit | parametre sınırları, yerleşim ve bounds |
| Profil | Unit/integration | beş profil, pozitif ölçüler, anchor/depth, profil anahtarı |
| Cache | Unit | hit/miss, anahtar ayrımı, eviction, clear, bellek tahmini |
| Renderer | Integration | sprite registration, Y-sort, culling, normalized anchor, F4 debug |
| Fizik ayrımı | Regression | palet/seed/Surface ölçüsü değişince collider aynı kalır |
| Görsel kabul | Acceptance | ağaç/kaya/çalı regresyonu ve çim/çiçek kanıt sahneleri |
| Kalite | CI | Pytest, Ruff, Linux laboratuvar CI ve Core Quality |

### Determinism test notları

- Piksel çıktısı aynı Python/Pygame/SDL koşulunda byte-for-byte karşılaştırılabilir.
- Linux ve Windows arasında font veya SDL pixel format kaynaklı fark olasılığına karşı ana kabul; seed/parametre/geometry metadata, Surface ölçüsü ve alpha/silhouette gibi semantik kontrollerle yapılacaktır.
- Platformlar arası tam piksel eşitliği yalnızca deneysel olarak kararlı olduğu kanıtlanırsa zorunlu hale getirilecektir.

## 9. Pytest, Ruff ve GitHub Actions politikası

### Pytest

- Laboratuvarın tam suite'i `python -m pytest -q` ile çalıştırılmaya devam edecektir.
- Her iş paketi kendi unit/integration testlerini ekler.
- Aşama 13 kapanışında tüm laboratuvar testleri, mevcut Phase 12 regression/acceptance testleri dahil çalışmalıdır.

### Ruff

Depoda laboratuvar için şu an Ruff yapılandırması veya CI adımı bulunmuyor. Aşama 13 kapsamında:
- Laboratuvar `pyproject.toml` içinde Python 3.11 hedefi ve 100 karakter satır uzunluğu başlangıç ayarı önerilir.
- İlk lint kapsamı yeni procedural paket, bu paketin facade/asset adaptörleri ve Aşama 13 testleriyle sınırlı tutulur.
- Başlangıç kural kümeleri `E4`, `E7`, `E9`, `F` ve `I` olarak önerilir; 13.1 baseline denetiminde gerçek kodla doğrulanır.
- CI'da `ruff check` ve `ruff format --check` çalıştırılır; otomatik düzeltme/format komutu CI'da çalıştırılmaz.
- Bu kapsamda Ruff hataları build'i başarısız kılan kalite kapısı olacaktır. Var olan laboratuvar dosyalarının tamamına toplu format uygulanmayacaktır.
- Ruff sürümü kalite extra'sında sabit bir uyum aralığıyla yönetilecek; CI ve yerel talimat aynı komutları kullanacaktır.

### GitHub Actions

- `hex-world-lab-ci.yml` laboratuvar test/benchmark/görsel kanıtının ana akışı olmaya devam eder.
- Aşama 13 adımları ayrı ve anlaşılır step adlarıyla eklenir.
- Ruff kontrolü testlerden önce veya bağımsız bir kalite step'i olarak çalışır.
- Linux CI otomatik kanıt sağlar; mevcut Core Quality Linux/Windows matrisinin başarılı olması ayrıca kontrol edilir.
- CI artifact'leri beş profilin PNG sahnelerini, benchmark JSON'unu ve Pytest JUnit raporunu içerir.
- CI başarısı kullanıcı masaüstü görsel kabulünün yerine geçmez.

## 10. Benchmark tasarımı

Benchmark ayrı süreçte veya sabit koşullarda, en az üç tekrar ile çalıştırılır. Ham oturum değerleri ve medyan raporlanır.

Ölçümler:
1. Her profil için cold generation süresi.
2. Aynı girdide cache hit süresi.
3. Farklı seed/parametre ile cache miss üretim süresi.
4. 10 / 100 / 1.000 profil isteğinde toplam üretim süresi.
5. Cache öğe sayısı, yaklaşık Surface byte maliyeti ve eviction sayısı.
6. Profil başına mantıksal/çıktı Surface boyutu.

Mutlak FPS veya donanımdan bağımsız süre hedefi konulmayacaktır. Cache'in kazancı maliyetinden düşükse cache kaldırılır veya daha dar kapsamda tutulur. Benchmark, test doğruluğunun yerine geçmez.

## 11. İş paketlerinin teknik sırası

1. **13.1 Denetim ve baseline:** Kod, test, CI, Ruff kapsamı ve görsel referanslar kesinleştirilir.
2. **13.2 Geometri/canvas sözleşmesi:** Saf geometri ve Pygame Surface sınırı uygulanır.
3. **13.3 Palet/renk rampaları:** Mevcut EnvironmentArtPalette uyumlu biçimde taşınır/genişletilir.
4. **13.4 Seed ve parametre sözleşmesi:** Deterministik yerel RNG ve profil parametre doğrulaması eklenir.
5. **13.5 Bileşen kütüphanesi:** Ortak çizim bileşenleri eklenir.
6. **13.6 Profil dönüşümü:** Ağaç/kaya/çalı yeni API'ye taşınır; çim/çiçek profilleri eklenir.
7. **13.7 Cache/renderer/kanıt:** Ölçümle cache kararı, asset registration ve debug/renderer doğrulaması yapılır.
8. **13.8 Tam doğrulama:** Pytest, Ruff, CI, benchmark, görsel artifact, kullanıcı manuel kabulü ve kapanış raporu.

İş paketleri gerektiğinde küçük alt adımlara ayrılabilir; fakat sıra, önce sözleşme sonra uygulama ilkesiyle korunur.

## 12. Teknik riskler ve kararlar

| Risk | Teknik karar/önlem |
|---|---|
| Fazla soyutlama | Birden çok profilde kanıtlanan davranış ortak bileşen olur |
| Pygame'in domain'e sızması | Pygame yalnızca rendering/procedural katmanında |
| Global random state bozulması | Yerel RNG, açık seed ve state regression testi |
| Cache anahtarı çakışması | Profil sürümü, palette, parametre, seed ve canvas ölçüsü anahtarda |
| Cache Surface mutasyonu | Surface kayıt sonrası salt-okunur sözleşmesi |
| Pixel-perfect platform farkı | Semantik test + kontrollü görsel kanıt |
| Eski import yollarının kırılması | `procedural_environment.py` facade olarak korunur |
| Collider'ın görselden türemesi | Domain collider'ı açık fizik tanımı olarak kalır |
| Ruff'ın eski kodu topluca bozması | Başlangıç kapsamı yeni paket ve dokunulan dosyalarla sınırlı |
| Render frame'inde üretim maliyeti | Surface üretimi asset hazırlama/registration aşamasında yapılır |

## 13. Manuel kabul senaryoları

Kullanıcı masaüstünde şu kontrolleri yapacaktır:

1. Laboratuvar yalnızca `python -m hex_world_lab` ile açılır.
2. Ağaç, kaya ve çalı Aşama 12'de kabul edilen görünümünü korur.
3. Çim ve çiçek/bitki kümeleri birbirinden ayırt edilebilir görünür.
4. Nesneler farklı konumlarda doğru Y-sort sırasına girer.
5. Kamera hareketi/zoom ve pencere boyutu değişiminde anchor ve culling bozulmaz.
6. F3 collider overlay fiziksel alanı göstermeye devam eder.
7. F4 anchor/bounds overlay doğru görsel ve depth alanlarını gösterir.
8. Ağaçta yaprak/canopy alanından geçiş ve gövde/root engeli; kayada kabul edilmiş tam engel alanı korunur.
9. Yeni dekoratif profiller açık collider verilmedikçe oyuncuyu engellemez.
10. Farklı seed ile kontrollü görsel çeşitlilik görülür; aynı seed tekrar üretildiğinde aynı profil görünür.
11. Görsel değişkenlik fiziksel çarpışma alanını değiştirmez.
12. Pencere kapat/aç, harita ve simülasyon davranışlarında yeni regresyon oluşmaz.

## 14. Kabul ve kapanış kapıları

Teknik plan onaylandıktan sonra uygulama başlayabilir. Aşama ancak:
- tüm yeni ve mevcut laboratuvar testleri başarılı,
- Ruff check ve format check başarılı,
- laboratuvar CI ve Core Quality CI başarılı,
- benchmark ve görsel artifact'ler üretildi,
- kullanıcı masaüstü kabulünü verdi,
- kapanış raporu ve Master Plan güncellemesi tamamlandı
şartlarıyla kapatılır.

## 15. Onay ve uygulama durumu

Kullanıcı teknik planı 18 Kasım 2026 tarihinde onayladı. Aşama 13 uygulaması bu onay sınırları içinde başlatılmıştır. 13.1 mevcut altyapı denetimi tamamlandı; ayrıntılar [PHASE-13.1-AUDIT-REPORT.md](../reports/PHASE-13.1-AUDIT-REPORT.md) belgesindedir. Sıradaki iş paketi 13.2 — saf geometri ve Pygame canvas sözleşmesidir. Teknik kapsamı değiştiren yeni kararlar ayrıca kullanıcı onayı gerektirir.

## 16. Dal güvenliği

- Yalnızca `experiment/hex-world-laboratory` dalı kullanılacaktır.
- `main` ve `demo_eldoria` dallarına commit veya merge yapılmayacaktır.
- Her yazma işleminden önce dal HEAD'i ve hedef dosya SHA/varlık durumu kontrol edilir.
- Her yazma işleminde branch açıkça belirtilir; sonrasında yeni HEAD ve korunan dalların HEAD'leri doğrulanır.
