# Aşama 4 — Sürekli Hareket Sistemi Teknik Mimari Planı

> **Belge türü:** Teknik mimari ve uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — Aşama 4.1–4.7.6 teknik çalışmaları tamamlandı; masaüstü kabulini bekliyor  
> **Tarih:** 16 Kasım 2026 — Tick mimarisi uyum revizyonu  
> **Ön koşul:** Aşama 4 Genel Planı kullanıcı tarafından onaylandı.

---

## 1. Teknik hedef ve tasarım kararı özeti

Aşama 4 sonunda bir hareketli varlık, altıgen hücrelerin merkezlerine sıçramadan dünya düzleminde kesintisiz hareket edebilmelidir. Hareketin gerçek konumu tek bir sürekli koordinat olarak tutulacak; hangi hex hücresinde bulunduğu bu konumdan türetilecektir.

Kod incelemesinde mevcut geometri paketinde `WorldPoint(x, y)` bulunduğu doğrulanmıştır. Aynı işi yapan ikinci bir `WorldPosition` sınıfı oluşturulmayacaktır.

**Tick mimarisi için ana karar:** Hareket paketi kendi oyun saatini, tick sayacını veya bağımsız bir zaman biriktiricisini üretmeyecektir. Hareket, ana simülasyon orkestrasyonunun verdiği her simülasyon tick'inde bir kez çalıştırılacaktır. Bir tick'in hareket süresi `1 / 60` saniyedir. Böylece hareket, Eldoria'nın 60 TPS zaman sözleşmesine bağlanır; render FPS'i hareket hızını değiştirmez.

Mevcut ana projede:
- `core.time.Tick`, canonical simülasyon zamanını temsil eden değişmez ve negatif olmayan tick değeridir.
- `core.simulation.SimulationRuntime`, `advance_to(Tick)` / `advance_by(Tick)` ile mantıksal simülasyon zamanını ilerletir.
- Eski `time_system/tick.py` içinde `TICKS_PER_SECOND = 60` tanımı bulunur.
- Mimari belgeler `core.time.Tick` ve `SimulationRuntime` yapısını canonical 2.x zaman sınırı olarak tanımlar; eski `time_system.Tick` uyumluluk API'sidir.

Önemli uygulama ayrıntısı: Mevcut `SimulationRuntime.advance_to()` hedef tick'e toplu ilerleyebilir ve tick listener'larını ilerleme sonunda çağırır. Bu listener mekanizması, her ara tick'te hareketi birer kez çalıştıran 60 Hz oyun döngüsü değildir. Bu nedenle hareketi doğrudan bir `advance_to()` listener'ına bağlamak yanlış olur. İleride ana oyun entegrasyonunda, simülasyon orkestratörü her canonical tick için hareket sistemini açıkça çağırmalıdır.

Laboratuvar bağımsız paket olma kuralını korur. Bu nedenle laboratuvar kodu ana oyundan `core.time.Tick` import etmez ve ikinci bir Tick sınıfı da tanımlamaz. Laboratuvar sınırında tick kimliği ana sistemdeki `Tick.value` değerine karşılık gelen tam sayı olarak taşınır. Ana oyuna entegrasyon aşamasında ince bir adaptör bu değeri sağlar.

Önerilen temel kararlar:
1. **Konum:** Mevcut `geometry.WorldPoint` authoritative fiziksel konumdur.
2. **Birim:** Dünya uzunluk birimi, ilgili haritanın `HexLayout.radius` değerinin kullandığı birimdir. Hız dünya birimi/saniyedir.
3. **Hareket modeli:** İlk sürüm sabit hızlıdır; ivme, sürtünme ve atalet yoktur.
4. **Zaman:** Hareket her canonical simülasyon tick'inde tam bir kez `1 / 60` saniyelik adımla ilerler.
5. **Zaman sahipliği:** Tick üretimi ve gerçek-zaman/tick eşlemesi Movement'in değil, üst seviye Simulation/Application döngüsünün sorumluluğudur.
6. **Girdi:** Pygame adaptörü hareket niyeti üretir; hareket çekirdeği Pygame'i import etmez.
7. **Hex eşleştirmesi:** Hücre tespiti mevcut `world_to_axial` fonksiyonuyla yapılır; önceki hücre tie-break için taşınır.
8. **Harita sınırı:** Bu aşamada çarpışma veya sınırda durdurma yoktur. Konum korunur; haritada bulunmayan hücre sonucu `None` olur.

Bu kararlar plan önerisidir; uygulama başlamadan önce kullanıcı onayına sunulur.

## 2. Mevcut mimariyle uyum

İncelenen mevcut dosyalar ve kullanılacak sözleşmeler:

| Mevcut dosya / API | Mevcut sorumluluk | Aşama 4'te kullanım |
|---|---|---|
| `geometry/coordinates.py — WorldPoint` | Sonlu, kesirli dünya koordinatı | Hareketli varlığın gerçek konumu |
| `geometry/layout.py — HexLayout` | Yönelim, circumradius ve origin | Dünya birimi ve hücre yerleşimi |
| `geometry/transforms.py — world_to_axial` | Dünya noktasından axial hücre seçimi | Mevcut hücrenin bulunması |
| `world/identity.py — WorldId, MapId, CellAddress` | Dünya/harita/hücre kimliği | Hareket bağlamının doğru haritaya bağlanması |
| Ana proje `core/time/tick.py — Tick` | Canonical simülasyon tick değeri | Entegrasyon sınırında tick kimliğinin kaynağı |
| Ana proje `core/simulation/runtime.py — SimulationRuntime` | Mantıksal simülasyon ilerletme ve tick listener yönetimi | Üst seviye zaman orkestrasyonunun mevcut sözleşmesi; doğrudan 60 Hz callback olarak kullanılmayacak |
| Ana proje `time_system/tick.py — TICKS_PER_SECOND` | 60 tick/saniye sabiti (1.x uyumluluk zaman modeli) | 60 TPS tasarım kararının kaynak doğrulaması |

Ana oyunun `core.time.Tick` ve `SimulationRuntime` kodu laboratuvara bağımlılık olarak eklenmeyecektir. Laboratuvarın bağımsız kurulabilir/test edilebilir olması korunur. Ana projeye aktarım sırasında adaptör, canonical `Tick.value` değerini laboratuvar hareket sisteminin beklediği tick numarasına dönüştürür.

`SimulationRuntime.advance_to(target)` birden fazla tick ilerleyebilir. Hareket sistemi bu çağrının sonunda yalnızca bir defa çalıştırılamaz; aradaki tick'ler atlanmış olur. Ana oyun entegrasyonunda orkestratör, sürekli hareket gerektiren her tick'i sırayla işleyip hareket sistemine birer kez iletmelidir. Toplu zaman atlatma/offline progression gibi işlemler ayrı bir politika gerektirir ve Aşama 4 kapsamı dışındadır.

Aşama 3'ün harita kayıt/yükleme ayrımı korunur. Hareket sistemi kayıtlı fakat belleğe yüklenmemiş haritayı kendiliğinden yüklemez.

## 3. Katman ve bağımlılık yönü

Önerilen bağımlılık akışı:

```text
Application / Simulation Orchestrator
        |
        | canonical tick başına bir çağrı
        v
MovementSystem.step(tick_number, intent)
        |
        v
Movement Core -----> WorldPoint
        |
        v
World/Hex Resolver -----> HexLayout + world_to_axial
        |
        v
CellAddress / current cell result

Pygame Input Adapter ------> MovementIntent
Render Loop ---------------> yalnızca state okur
```

Kurallar:
- `movement` paketi `pygame`, `application`, `rendering`, `camera` veya ana oyunun `core.time` paketini import edemez.
- Movement kendi tick sayacını, oyun saatini veya gerçek zaman biriktiricisini yönetmez.
- Üst seviye orkestratör, her simülasyon tick'i için hareket adımını tam bir kez çağırır.
- Pygame girdi adaptörü güncel tuş durumundan `MovementIntent` üretir; bu niyet ilgili simülasyon tick'inde tüketilir.
- Render/prototip katmanı state'i yalnızca okur; hareket state'ini doğrudan değiştiremez.
- Laboratuvarın bağımsız demo döngüsü, yalnızca demo/test amacıyla gerçek zamanı 60 TPS adım çağrılarına dönüştürebilir. Bu yardımcı döngü üretim hareket çekirdeğinin parçası veya ana oyunun canonical clock'u değildir.

## 4. Hareket veri sözleşmeleri

### 4.1 Vector2

Yeni `movement.Vector2` tipi iki boyutlu yön/vektör değerini temsil edecektir.

Önerilen alanlar:
- `x: float`
- `y: float`

Kurallar:
- Değerler sonlu olmalıdır.
- Nokta ile vektör semantik olarak ayrıdır: `WorldPoint` konum, `Vector2` yön/vektördür.
- Normalizasyon sıfır vektörde güvenli davranır; sıfır vektör sıfır olarak kalır.
- Çapraz hareketin daha hızlı olmaması için normalize edilmiş yön kullanılır.

### 4.2 MovementIntent

Değişmez veri nesnesi olarak yön niyetini taşır.

Önerilen alan:
- `direction: Vector2`

Kurallar:
- Klavye adaptörü ham eksen değerlerini (-1, 0, 1) üretir.
- Hareket çekirdeği yönü normalize eder; böylece iki tuşa aynı anda basılması tek eksen hareketinden hızlı olmaz.
- Niyetin sıfır vektör olması durma talebidir.
- Girdi kaynağı bu veri sözleşmesinin parçası değildir.

### 4.3 MovementConfig

Hareket parametrelerini tek yerde toplar.

Önerilen ilk sürüm alanları:
- `max_speed: float` — dünya birimi/saniye.
- Gerekirse ileride eklenecek parametreler için genişleme alanı; bu aşamada ivme/sürtünme alanları eklenmez.

`max_speed` sonlu ve negatif olmayan bir sayı olmalıdır. Sıfır hız geçerli olup hareketi devre dışı bırakır.

### 4.4 MovementState

Bir hareketli varlığın minimum hareket state'ini tutar.

Önerilen alanlar:
- `position: WorldPoint`
- `velocity: Vector2`

State değişimi tek bir hareket fonksiyonu üzerinden yapılır. Dış katmanlar konumu kendi başlarına güncellemez. İlk modelde hız vektörü, o tick'te hareket niyetinin normalize edilmiş yönü ile `max_speed` çarpımından üretilir. Girdi bırakıldığında hız sıfırlanır.

Bu aşamada tam Entity/Component sistemi kurulmaz. `MovementState` tek bir hareketli aktörün simülasyon girdisi/çıktısıdır; ileride entity sistemine taşınabilecek kadar küçük tutulur.

## 5. Hareket hesaplama modeli

Önerilen saf fonksiyon:

`advance_movement(state, intent, config, delta_seconds) -> MovementState`

Fonksiyon tek bir hareket adımını hesaplar. Üretim çağrısında `delta_seconds` sabiti `1 / 60` olur. Bu değer çağıran simülasyon orkestrasyonu tarafından belirlenir; hareket fonksiyonu gerçek saat okumaz.

İşlem sırası:
1. Girdi ve zaman değerleri doğrulanır.
2. Hareket niyeti normalize edilir.
3. Anlık hız vektörü hesaplanır: `velocity = normalized_direction * max_speed`.
4. Yeni konum hesaplanır: `position += velocity * (1 / 60)`.
5. Yeni state döndürülür; girdi state'i yerinde değiştirilmez.

Önemli davranışlar:
- Konum hücre merkezine yuvarlanmaz.
- Yön değiştirme aynı konumdan devam eder; konum sıçramaz.
- Sıfır niyet, o tick'te hızı sıfırlayıp hareketi durdurur.
- Negatif delta, NaN/Infinity veya geçersiz tipler sessizce kabul edilmez.
- İlk sürümde hız sabit ve anlık değişir. İvme/yavaşlama ayrı tasarım kararıdır.

Hareket fonksiyonunun genel amaçlı `delta_seconds` kabul etmesi test edilebilirliği artırır; ancak normal simülasyon yolu yalnızca sabit 1/60 değerini kullanır. Başka delta ile çağırmak, normal oyun tick sözleşmesinin parçası değildir.

## 6. Tick yürütümü ve gerçek zaman eşlemesi

### 6.1 Canonical tick sözleşmesi

- Oyun simülasyon hızı: `60 tick/saniye`.
- Bir hareket tick'i: `1 / 60` saniye.
- Her tick numarası için hareket adımı en fazla bir kez çalıştırılır.
- Hareket sistemi tick numarasının kaynağı değildir; üst katmandan alır.
- Render FPS'i simülasyon tick sayısını veya hareket adımının süresini değiştirmez.

### 6.2 Ana proje ile entegrasyon

Canonical zaman tipi ana projedeki `core.time.Tick`'tir. Laboratuvar bağımsızlığını korumak için hareket çekirdeği bu sınıfı import etmez; entegrasyon adaptörü `Tick.value` değerini tam sayı tick kimliği olarak aktarır.

Mevcut `SimulationRuntime.advance_to()` hedef tick'e toplu ilerleyebildiğinden, sürekli hareketin doğru çalışması için oyun orkestrasyon katmanı ardışık tick'leri tek tek yürütmelidir. `register_tick_listener` yalnızca toplu ilerleme tamamlandığında çağrıldığı için doğrudan hareket güncelleme kancası olarak kullanılmayacaktır.

### 6.3 Laboratuvar demo döngüsü

Görsel demo için gerekirse `application` katmanında bir demo tick pump bulunabilir. Bu yardımcı:
- monotonic gerçek zamanı yalnızca render kareleri arasındaki süreyi ölçmek için kullanır;
- geçen süreyi 1/60 saniyelik tick birikimine dönüştürür;
- her üretilen demo tick'i için `MovementSystem.step()` çağırır;
- kare başına en fazla 8 tick işleyebilir, fakat kalan tick borcunu silmez; sonraki karelere taşır;
- borç miktarını diagnostics alanında raporlar.

Böylece uzun karede simülasyon tick'i atlanmaz. Catch-up sınırı yalnızca tek render karesindeki CPU yükünü sınırlar. Sürekli performans yetersizliğinde borç artabilir; sistem bunu gizlemek yerine ölçer. Simülasyon zamanı sessizce düşürülmez.

Bu demo tick pump, `movement` gibi üretim hareket modüllerinde bulunmaz ve ana oyunun zaman motoru olarak sunulmaz. Ana oyuna geçişte demo pump kaldırılır; canonical simülasyon orkestrasyonu tick'leri sağlar.

### 6.4 Determinizm

Aynı başlangıç state'i ve aynı sıralı `(tick_number, MovementIntent)` girdileri aynı hareket state'ini üretmelidir. Render FPS karşılaştırmaları aynı tick girdisi dizisinin 30/60/120 FPS çizim döngülerinde aynı sonucu verdiğini doğrular. Gerçek zamanlı klavye örneklemesinin farklı render karelerine denk gelmesi ayrı bir input-latency konusu olup bu aşamada ağ senkronizasyonu veya tam input replay garantisi verilmez.

## 7. Klavye adaptörü

Önerilen modül `input/pygame_keyboard.py`.

Sorumlulukları:
- Pygame klavye durumunu okumak.
- WASD ve ok tuşlarından eksen değerleri üretmek.
- Zıt yön tuşları aynı anda basılıysa ilgili ekseni sıfırlamak.
- Ham yönü `MovementIntent` biçimine dönüştürmek.
- Tuş bırakıldığında sıfır yön niyeti üretmek.

Klavye tuş eşlemesi ilk prototipte:
- W / Yukarı: `(0, +1)` (matematiksel dünya ekseninde Y yukarı).
- S / Aşağı: `(0, -1)`.
- A / Sol: `(-1, 0)`.
- D / Sağ: `(+1, 0)`.

Pygame ekran koordinatlarında Y aşağı yönlüdür; adaptörün bu eksen farkını yalnızca girdi yönünde doğru çevirmesi gerekir. Hareket çekirdeğinin matematiksel dünya eksenleri Y yukarı kalır.

Adaptör, Pygame event kuyruğunu tüketen ana uygulama döngüsünün yerine geçmez. Ana döngünün zaten işlediği klavye durumunu okur; event kaybı veya ikinci event loop oluşturmaz.

## 8. Dünya ve hex hücre entegrasyonu

### 8.1 Hareket bağlamı

Bir hareketli aktörün konumu tek başına yeterli değildir; hangi dünya ve harita üzerinde bulunduğu da bilinmelidir. Bu nedenle dünya entegrasyonu için küçük ve açık bir bağlam gerekir.

Önerilen `MovementWorldContext` alanları:
- `world_id: WorldId`
- `map_id: MapId`
- Yüklü `HexMapDefinition` veya onu sağlayan dar bir resolver bağımlılığı.
- `previous_cell: AxialCoord | None` — sınır eşitliğinde kararlı seçim için.

Bağlam oluşturulurken haritanın kayıtlı ve yüklü olduğu doğrulanır. Harita unload edilirse o haritaya bağlı hareket güncellemesi çalıştırılmamalı; otomatik yükleme yapılmamalıdır.

### 8.2 Hücre çözümleme

Önerilen sorgu:

`resolve_current_cell(position, context) -> CellAddress | None`

İşlem:
1. `world_to_axial(position, map.layout, previous_cell)` çağrılır.
2. Dönen axial koordinat `map.get_cell_data(coord)` ile kontrol edilir.
3. Hücre varsa `CellAddress(world_id, map_id, coord)` döner ve previous_cell güncellenir.
4. Hücre haritada yoksa `None` döner; fiziksel konum değiştirilmez.

Önemli ayrım: Geometri en yakın hex koordinatını belirler; haritanın açık hücre kümesi o hücrenin gerçekten var olup olmadığını belirler. Haritada bulunmayan hücreye denk gelmek konumu otomatik olarak harita içine çekmez.

Bu aşamada `is_walkable` ve `has_obstacle` hareketi durdurmak için kullanılmaz. Bu alanlar Aşama 5 çarpışma/fizik tasarımına aittir.

### 8.3 Harita değişimi

Harita değişimi, bu aşamanın ana hareket döngüsünün parçası değildir. Prototip tek bir yüklü harita üzerinde çalışır. Başka haritaya geçiş gerekirse yeni context açıkça oluşturulur; eski haritanın axial hücresi yeni haritaya otomatik taşınmaz. Dünya konumunun haritalar arası dönüşümü bu aşamada tanımlanmaz.

## 9. Önerilen dosya yapısı

Aşağıdaki liste uygulama için hedef dosya sınırıdır. Teknik uygulama sırasında yeni bir ihtiyaç çıkarsa önce kapsam etkisi değerlendirilir.

### Yeni üretim kodu

| Dosya | Sorumluluk |
|---|---|
| `src/hex_world_lab/movement/__init__.py` | Hareket paketinin kontrollü public API'si |
| `src/hex_world_lab/movement/vector.py` | `Vector2`, normalizasyon ve vektör işlemleri |
| `src/hex_world_lab/movement/intent.py` | `MovementIntent` |
| `src/hex_world_lab/movement/config.py` | `MovementConfig` ve hız doğrulaması |
| `src/hex_world_lab/movement/state.py` | `MovementState` |
| `src/hex_world_lab/movement/integrator.py` | Saf `advance_movement` fonksiyonu |
| `src/hex_world_lab/simulation/__init__.py` | Simülasyon public API'si |
| `src/hex_world_lab/application/demo_tick_pump.py` | Yalnızca laboratuvar demosu için gerçek zamanı 60 TPS çağrılarına dönüştürme; kalan tick borcunu koruma |
| `src/hex_world_lab/input/__init__.py` | Girdi adaptörü public API'si |
| `src/hex_world_lab/input/pygame_keyboard.py` | Pygame klavye → MovementIntent adaptörü |
| `src/hex_world_lab/world/movement_context.py` | Yüklü harita bağlamı ve konum-hücre çözümlemesi |

### Test dosyaları

| Dosya | Kapsam |
|---|---|
| `tests/unit/test_movement_vector.py` | Vektör doğrulama, normalizasyon, sıfır vektör |
| `tests/unit/test_movement_intent.py` | Hareket niyeti doğrulaması |
| `tests/unit/test_movement_state.py` | State doğrulaması ve değişmezlik |
| `tests/unit/test_movement_integrator.py` | Hız, yön, çapraz hareket, durma, konum sürekliliği |
| `tests/integration/test_demo_tick_pump.py` | Demo tick üretimi, kare başına iş sınırı ve kalan tick borcunun korunması |
| `tests/unit/test_pygame_keyboard.py` | Tuş eşlemesi ve zıt/çapraz tuşlar |
| `tests/integration/test_movement_world.py` | WorldPoint → axial → CellAddress, sınır ve harita dışı davranış |
| `tests/integration/test_movement_fps_independence.py` | 30/60/120 FPS eşdeğerliği |
| `tests/integration/test_movement_architecture.py` | Çekirdeğin Pygame import etmediğinin doğrulanması |

### Prototip ve dokümantasyon

| Dosya | Sorumluluk |
|---|---|
| `src/hex_world_lab/application/movement_demo.py` | Tek haritada minimal hareket gözlem prototipi |
| `docs/decisions/ADR-004-MOVEMENT-TIME-AND-UNITS.md` | Dünya birimi, sabit timestep ve ilk hareket modeli kararı |
| `reports/PHASE-04.x-REPORT.md` | Onaylanan alt aşamaların gerçekleşme raporları |
| `reports/PHASE-04-MOVEMENT-REPORT.md` | Aşama genel kapanış raporu |

Prototip dosya yolu mevcut uygulama giriş noktasıyla çakışırsa uygulamaya başlamadan önce dosya ağacı tekrar kontrol edilir; var olan giriş noktası gelişigüzel değiştirilmez.

## 10. Alt aşama ve uygulama sırası

Genel plandaki 4.1–4.6 sırası korunarak şu teknik kapılara ayrılması önerilir:

| Alt aşama | Uygulama | Alt aşama kabul kanıtı |
|---|---|---|
| 4.1 — Konum ve veri sözleşmeleri | Vector2, MovementIntent, MovementConfig, MovementState | Tip doğrulama, immutable state ve birim sözleşmesi testleri |
| 4.2 — Hareket çekirdeği | advance_movement, sabit hız ve normalize yön | Konum/hız/yön/durma unit testleri |
| 4.3 — Tick sözleşmesi | Hareketin dışarıdan verilen ardışık tick başına bir kez çalışması; demo tick pump | 60 TPS adım süresi, yinelenen/atlanan tick davranışı ve kalan tick borcu testleri |
| 4.4 — Klavye adaptörü | Pygame keyboard adapter | Headless/uygun Pygame testleri, tuş kombinasyonları |
| 4.5 — Dünya entegrasyonu | MovementWorldContext ve hücre çözümleyici | İki orientation, sınır tie-break, harita dışı ve yüklü harita testleri |
| 4.6 — Prototip ve kabul | Minimal tek harita hareket demosu, benchmark, regresyon | Görsel inceleme, tam pytest ve CI |

Her alt aşama kendi küçük test ve raporuyla kapanır. Bir alt aşamanın tamamlanması sonraki alt aşamaya otomatik uygulama yetkisi vermez; Aşama 3'teki çalışma biçimi sürdürülür.

## 11. Test ve kabul planı

### 11.1 Unit testler

- WorldPoint'in kesirli konumunun aynen korunması.
- Vektör normalizasyonu ve sıfır vektör.
- Negatif, sonsuz ve NaN hız/zaman girdilerinin reddi.
- Tek eksen ve çapraz yönde eşit hız büyüklüğü.
- Girdi bırakıldığında hızın sıfırlanması.
- Yön değişiminde konum sıçramaması.
- Farklı delta sürelerinde beklenen yer değiştirme.
- Fixed timestep biriktiricisinin tam tick sayısı.
- Max step ve düşen zaman politikasının açıkça işlemesi.

### 11.2 Geometry + World entegrasyon testleri

- Flat-top ve pointy-top layout.
- Pozitif ve negatif dünya koordinatları.
- Hücre merkezinden başlama ve hücre sınırını geçme.
- Önceki hücre tie-break davranışı.
- Hücre değişiminde WorldPoint'in değişmeden kalması.
- Harita dışındaki axial koordinat için None.
- Farklı WorldId/MapId bağlamlarının karışmaması.
- Kayıtlı ama yüklenmemiş haritada hareket context'i oluşturulamaması.
- Harita hücre verisinin hareket çekirdeği tarafından değiştirilmemesi.

### 11.3 FPS karşılaştırması

Aynı başlangıç konumu, hız ve sabit hareket niyetiyle aynı toplam simülasyon süresi çalıştırılır:
- 30 render FPS
- 60 render FPS
- 120 render FPS

Son konum farkı, floating-point toleransı içinde olmalıdır. Test hem tek eksen hem normalize edilmiş çapraz hareket için yapılır. Girdi değişimlerinin farklı render karelerine denk geldiği senaryolar deterministik tick testiyle karıştırılmaz.

### 11.4 Performans

Ölçülecekler:
- Tek aktör hareket tick süresi.
- 10, 100 ve 1.000 bağımsız hareket state'i için toplam update süresi.
- Ortalama ve P95 süre.
- Demo tick pump'ın normal ve maksimum catch-up yükü; ana hareket çekirdeğinde saat/accumulator bulunmadığının doğrulanması.
- Hareket döngüsünde map cell koleksiyonu taraması veya gereksiz nesne üretimi olup olmadığı.

Benchmark sonuçları donanım/işletim sistemi/Python sürümü ve commit SHA ile raporlanır. Önceden sabit FPS garantisi konmaz; ölçüm olmadan performans iddiası yapılmaz.

### 11.5 Regresyon ve CI

- Mevcut Aşama 2 geometri testleri.
- Aşama 3 world, JSON map persistence ve runtime persistence testleri.
- Laboratuvarın tam pytest paketi.
- CI Linux ve Windows koşuları.

Hareket çekirdeğinin Pygame import etmediği test edilir. Pygame adaptörü ve görsel prototipin testleri, headless ortamda uygun SDL dummy ayarlarıyla çalıştırılır.

## 12. Kapsam dışı ve açıkça ertelenen işler

Bu teknik planda aşağıdakiler yapılmayacaktır:

- Çarpışma, collider, duvar, engel, duvar boyunca kayma ve tünelleme çözümü.
- Hücre geçilebilirliğine göre hareketi durdurma veya yol bulma.
- İvme, sürtünme, atalet ve animasyon easing'i.
- NPC AI, çoklu actor yönetim sistemi veya tam ECS.
- Kamera, zoom, pan, world-to-screen veya screen-to-world.
- Nihai sprite/karakter animasyonu, render katmanları ve y-sort.
- Çoklu harita geçişi, otomatik map load/unload veya offline progression.
- Kayıt sistemine hareket state'i eklenmesi.
- Ana oyun veya demo dalına entegrasyon.
- Ağ/multiplayer senkronizasyonu.

Bu kapsam dışı maddelerden biri teknik olarak zorunlu görünürse doğrudan eklenmez; etki analizi ve yeni onay istenir.

## 13. Riskler ve azaltma

| Risk | Etki | Önlem |
|---|---|---|
| WorldPoint ve WorldPosition için iki ayrı tip yaratılması | Konum sözleşmesinde ikilik | Mevcut WorldPoint'i kullanmak |
| Dünya biriminin belirsiz kalması | Hız değerlerinin anlamsızlaşması | Hızı layout radius ile aynı dünya birimi/saniye olarak tanımlamak |
| Y ekseninin girdi adaptöründe ters çevrilmesi | Kontrollerin yanlış yönlenmesi | Matematiksel Y yukarı kuralını test etmek |
| Hareketin kendi saatini üretmesi | Ana oyun tick'iyle zaman ayrışması | Her canonical tick'te dışarıdan tek adım çağrısı |
| Uzun kare sonrası catch-up yükü | Tek karede CPU sıçraması | Demo pump'ta kare başına en fazla 8 tick; kalan borcu koruma ve ölçme |
| Hücre sınırında titreşim | Hücre bilgisinin kararsız değişmesi | previous_cell tie-break sözleşmesini kullanmak |
| Harita dışı konumun sessizce düzeltilmesi | Fiziksel konumda sıçrama | Konumu koruyup cell result olarak None vermek |
| Pygame'in core'a sızması | Headless test ve yeniden kullanım kaybı | Bağımlılık yönü testi |
| Gereksiz soyutlama | Küçük hareket işinin karmaşıklaşması | Tek aktör state'i ve saf fonksiyonla başlamak |

## 14. Geri dönüş ve değişiklik sınırı

- Her alt aşama ayrı, küçük ve gözden geçirilebilir commit ile tamamlanır.
- Yeni movement/simulation/input dosyaları bağımsız tutulur.
- Geometry ve Stage 3 world/persistence kodu mümkün olduğunca salt-okunur tüketilir.
- Mevcut geometri veya dünya API'sinde değişiklik zorunlu hale gelirse o alt aşama durdurulur; gerekçe ve etki kullanıcıya sunulur.
- Bir alt aşama başarısız olursa yalnız o alt aşamanın commit'i geri alınabilecek şekilde sınırlandırılır; branch geçmişi kullanıcı onayı olmadan yeniden yazılmaz.
- `main` ve `demo_eldoria` dallarına yazılmaz, merge/cherry-pick yapılmaz.

## 15. Beklenen teslimatlar

1. Hareket veri tipleri ve saf Python hareket çekirdeği.
2. Sabit timestep simülasyon sürücüsü.
3. Pygame klavye adaptörü.
4. WorldPoint → axial → CellAddress entegrasyonu.
5. Minimal hareket gözlem prototipi.
6. Unit, integration, FPS karşılaştırma, mimari ve regresyon testleri.
7. Benchmark sonuçları.
8. Gerekli ADR ve alt aşama raporları.
9. Aşama 4 genel kapanış raporu.

## 16. Onay kapısı ve gerçekleşen durum

Bu teknik mimari plan, kod uygulamasından önce kullanıcı tarafından 16 Kasım 2026 tarihinde onaylanmıştır. Plan kapsamındaki sürekli hareket çekirdeği, sabit tick entegrasyonu, klavye adaptörü, world/hex hücre takibi, Pygame kabul prototipi ve hareket modları Aşama 4.1–4.7.6 boyunca uygulanmış ve otomatik doğrulamalardan geçirilmiştir.

Teknik doğrulama kanıtları:
- Laboratuvar test paketi: 505 başarılı.
- Core Quality Linux ve Windows: 1.968'er başarılı.
- Hareket, harita persistence ve runtime persistence benchmark adımları başarılı.
- Hareket benchmark sonuçları Aşama 4.7.6 kapanış raporunda kayıtlıdır.
- Mimari sınır testi, geometry/movement/simulation/world çekirdeğinin Pygame'e bağımlı olmadığını denetler.

Gerçek Pygame masaüstü kabulü kullanıcı kararıyla Aşama 4 genel kapanışına ertelenmiştir. Bu nedenle teknik planın uygulanmış olması Aşama 4'ün genel kabul edildiği veya kapandığı anlamına gelmez.

**Mevcut durum:** Teknik uygulama ve otomatik doğrulama tamamlandı. Sıradaki genel kapı, kullanıcının gerçek bilgisayarında `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md` listesini çalıştırması ve Aşama 4 genel kapanışını kabul etmesidir.
