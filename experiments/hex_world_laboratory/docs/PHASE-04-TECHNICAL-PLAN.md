# Aşama 4 — Sürekli Hareket Sistemi Teknik Mimari Planı

> **Belge türü:** Teknik mimari ve uygulama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** TEKNİK PLAN — KULLANICI ONAYI BEKLİYOR  
> **Tarih:** 16 Kasım 2026  
> **Ön koşul:** Aşama 4 Genel Planı kullanıcı tarafından onaylandı.

---

## 1. Teknik hedef ve tasarım kararı özeti

Aşama 4 sonunda bir hareketli varlık, altıgen hücrelerin merkezlerine sıçramadan dünya düzleminde kesintisiz hareket edebilmelidir. Hareketin gerçek konumu tek bir sürekli koordinat olarak tutulacak; hangi hex hücresinde bulunduğu bu konumdan türetilecektir.

Kod incelemesinde önemli bir mevcut altyapı tespit edilmiştir: Aşama 2 geometri paketinde `WorldPoint(x, y)` zaten kesirli dünya koordinatını temsil ediyor. Bu nedenle aynı işi yapan ikinci bir `WorldPosition` sınıfı oluşturulmayacaktır. Genel planın kullandığı “WorldPosition” kavramı, uygulamada mevcut `WorldPoint` tipiyle karşılanacaktır. Böylece iki farklı konum tipinin zamanla birbirinden ayrışması önlenir.

Önerilen temel kararlar:

1. **Konum:** Mevcut `geometry.WorldPoint` authoritative fiziksel konumdur.
2. **Birim:** Dünya uzunluk birimi, ilgili haritanın `HexLayout.radius` değerinin kullandığı birimdir. Hız birimi dünya birimi/saniyedir.
3. **İlk hareket modeli:** Sabit hız; hareket niyeti varsa seçilen yön boyunca `max_speed`, girdi yoksa sıfır hız. İlk sürümde ivme, sürtünme ve atalet yoktur.
4. **Zaman:** Simülasyon sabit 1/60 saniyelik adımlarla ilerler. Render FPS'i simülasyon adımının uzunluğunu değiştirmez.
5. **Girdi:** Pygame klavye adaptörü yalnızca yön niyeti üretir; hareket çekirdeği Pygame'i import etmez.
6. **Hex eşleştirmesi:** Hücre tespiti yalnızca mevcut `world_to_axial` fonksiyonuyla yapılır. Önceki hücre bilgisi sınır eşitliğinde mevcut tie-break sözleşmesini korumak için taşınır.
7. **Harita sınırı:** Bu aşamada çarpışma veya sınırda durdurma yoktur. Konum haritanın dışına çıkabilir; hücre sorgusu haritada bulunmayan konum için `None` verir. Bu davranış Aşama 5 fizik sistemiyle karıştırılmaz.

Bu kararlar plan önerisidir; uygulama başlamadan önce kullanıcı onayına sunulur.

## 2. Mevcut mimariyle uyum

İncelenen mevcut dosyalar ve kullanılacak sözleşmeler:

| Mevcut dosya / API | Mevcut sorumluluk | Aşama 4'te kullanım |
|---|---|---|
| `geometry/coordinates.py — WorldPoint` | Sonlu, kesirli dünya koordinatı | Hareketli varlığın gerçek konumu |
| `geometry/layout.py — HexLayout` | Yönelim, circumradius ve origin | Dünya birimi ve hücre yerleşimi |
| `geometry/transforms.py — world_to_axial` | Dünya noktasından axial hücre seçimi | Mevcut hücrenin bulunması |
| `geometry/transforms.py — axial_to_world` | Hücre merkezini dünya koordinatına çevirme | Test ve prototip başlangıç konumları |
| `world/identity.py — WorldId, MapId, CellAddress` | Dünya/harita/hücre kimliği | Hareket bağlamının doğru haritaya bağlanması |
| `world/map_registry.py — MapRegistry.get_map` | Yüklü harita tanımına erişim | Harita layout ve hücre varlığı sorgusu |
| `world/map_definition.py — HexMapDefinition` | Değişmez harita, layout ve hücre kümesi | Konumun harita içindeki hücreyle eşleştirilmesi |
| `world/world_view.py — HexWorldView` | Runtime dahil güncel hücre verisi | Hareket için gereken hücre verisine ihtiyaç doğarsa salt-okunur sorgu |

Aşama 3'ün harita kayıt/yükleme ayrımı korunur. Hareket sistemi kayıtlı fakat belleğe yüklenmemiş haritayı kendiliğinden yüklemez. Hareket bağlamı yalnızca açıkça seçilmiş ve yüklü harita için oluşturulur.

`HexWorldRuntime.require_loaded_map` mevcut olsa da runtime sınıfının hareket katmanının harita erişim servisi olarak kullanılmasına gerek yoktur. Harita tanımına erişim için `MapRegistry.get_map` kullanılmalı; hareket çekirdeği registry'yi doğrudan bilmemelidir.

## 3. Katman ve bağımlılık yönü

Önerilen bağımlılık akışı:

```text
Pygame Keyboard Adapter
        |
        v
MovementIntent (saf veri)
        |
        v
Fixed-Step Simulation
        |
        v
Movement Core -----> WorldPoint
        |
        v
Continuous Position
        |
        v
World/Hex Resolver -----> HexLayout + world_to_axial
        |
        v
CellAddress / current cell result
```

Kurallar:

- `movement` paketi `pygame`, `application`, `rendering` veya `camera` import edemez.
- `simulation` paketi hareket fonksiyonlarını çağırır; hareket çekirdeğine zamanlayıcı veya pencere bağımlılığı sokmaz.
- `input` adaptörü Pygame olaylarını okur ve yalnızca `MovementIntent` üretir.
- `world` entegrasyonu, konumun hangi haritaya ait olduğunu ve hangi hücreye denk geldiğini çözer; hareket matematiğini yeniden yazmaz.
- Render/prototip katmanı state'i yalnızca okur. Hareket state'ini doğrudan değiştiremez.
- Geometri ve dünya paketlerinin mevcut API'leri, gerekçe ve ayrı onay olmadan geriye dönük uyumsuz biçimde değiştirilmez.

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

İşlem sırası:

1. Girdi ve zaman değerleri doğrulanır.
2. Hareket niyeti normalize edilir.
3. Anlık hız vektörü hesaplanır: `velocity = normalized_direction * max_speed`.
4. Yeni konum hesaplanır: `position += velocity * delta_seconds`.
5. Yeni state döndürülür; girdi state'i yerinde değiştirilmez.

Önemli davranışlar:
- Konum hücre merkezine yuvarlanmaz.
- Yön değiştirme aynı konumdan devam eder; konum sıçramaz.
- Sıfır niyet, aynı tick'te hızı sıfırlayıp hareketi durdurur.
- Negatif delta, NaN/Infinity veya geçersiz tipler sessizce kabul edilmez.
- İlk sürümde hız sabit ve anlık değişir. İvme/yavaşlama sonradan eklenecekse ayrı tasarım kararı ve kullanıcı onayı gerekir.

**Neden ilk sürümde ivme yok?** Önce doğru konum, hız birimi, çapraz yön ve zaman davranışını kanıtlamak gerekir. İvme eklemek kontrol hissi ve fizik parametreleri doğurur; çarpışma aşamasından önce gereksiz karmaşıklık yaratır. Sabit hız modeli kabul testlerini netleştirir ve daha sonra ivmeli modele geçişi engellemez.

## 6. Sabit zaman adımı ve büyük gecikme politikası

### 6.1 Seçim

Sabit simülasyon adımı önerilir:

- `FIXED_DELTA_SECONDS = 1 / 60`
- Render döngüsü her karede geçen gerçek süreyi simülasyon zaman biriktiricisine ekler.
- Biriken süre bir veya daha fazla sabit tick'e ulaştığında hareket çekirdeği o sabit süreyle çalıştırılır.
- Render 30 FPS ise tipik olarak kare başına iki tick; 60 FPS ise bir tick; 120 FPS ise her iki render karesinde bir tick çalışır.

Bu yaklaşım, hareketin render FPS'e doğrudan bağlanmasını önler ve aynı simülasyon tick dizisiyle tekrarlanabilir sonuç sağlar.

### 6.2 Gecikme koruması

Tek karede uzun süre duraklama, sınırsız sayıda tick çalıştırılmasına neden olmamalıdır.

Önerilen koruma:
- Tek render karesinden kabul edilen süre en fazla 0.25 saniye.
- Tek render karesinde en fazla 8 simülasyon tick'i.
- Bu sınırlar nedeniyle işlenemeyen fazla süre sessizce biriktirilmez; düşürülen süre ölçüm/diagnostic alanında raporlanır.
- Normal çalışma koşullarında (30/60/120 FPS) bu koruma devreye girmemelidir.

Bu politika, donma sonrası “spiral of death” olarak bilinen giderek artan simülasyon yükünü sınırlar. Zaman düşürme davranışı bir kabul testiyle açıkça kanıtlanır; oyun içi zamanın ne kadar atlandığı prototip teşhisinde gösterilir.

### 6.3 Determinizm sınırı

Aynı başlangıç state'i ve aynı tick sırasına bağlanmış hareket niyeti dizisi aynı sonucu üretmelidir. Farklı render FPS testleri, aynı niyetin aynı toplam simülasyon süresince korunduğu senaryoları karşılaştırır.

Klavye girdisinin render kareleri arasında değiştiği anlarda tick sınırına hangi niyetin yetiştiği doğal olarak farklılaşabilir. Bu nedenle bu aşamada ağ senkronizasyonu veya tam input replay sistemi vaat edilmez. Deterministik doğrulama, sabit tick girdileri üzerinden yapılır.

## 7. Klavye adaptörü

Önerilen modül `input/pygame_keyboard.py`.

Sorumlulukları:
- Pygame klavye durumunu okumak.
- WASD ve ok tuşlarından eksen değerleri üretmek.
- Zıt yön tuşları aynı anda basılıysa ilgili ekseni sıfırlamak.
- Ham yönü `MovementIntent` biçimine dönüştürmek.
- Tuş bırakıldığında sıfır yön niyeti üretmek.

Klavye tuş eşlemesi ilk prototipte:
- W / Yukarı: y pozitif? **Hayır** — dünya ekseninde Y yukarı olduğundan W = `(0, +1)`.
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
| `src/hex_world_lab/simulation/fixed_step.py` | Sabit tick biriktirici, adım sınırı ve düşen süre ölçümü |
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
| `tests/unit/test_fixed_step.py` | Biriktirme, 1/60 tick, max step ve düşen süre |
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
| 4.3 — Zaman sistemi | FixedStepAccumulator, tick sınırı ve gecikme politikası | 30/60/120 FPS, büyük delta ve deterministik tick testleri |
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
- Fixed-step biriktiricisinin normal ve maksimum catch-up yükü.
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
| Render delta ile doğrudan hareket | FPS'e göre hız farkı | Fixed timestep |
| Uzun duraklama sonrası çok fazla tick | CPU yükünün katlanması | 0.25s frame clamp ve 8 tick sınırı |
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

## 16. Onay kapısı ve mevcut durum

Bu belge teknik uygulama planıdır; henüz uygulama izni değildir.

Uygulama öncesi kullanıcıdan açık onay beklenen kararlar:
- Mevcut `WorldPoint` tipinin sürekli fiziksel konum olarak kullanılması.
- Dünya biriminin `HexLayout.radius` ile aynı ölçekte olması; hızın dünya birimi/saniye tanımlanması.
- İlk sürümde ivmesiz, sabit hızlı hareket modeli.
- 1/60 sabit simülasyon adımı; 0.25 saniye frame clamp ve kare başına en fazla 8 tick.
- Harita dışı konumda hareketin engellenmemesi; hücre sonucunun `None` olması.
- Bu belgede belirtilen dosya sınırları, alt aşama sırası ve test kabul ölçütleri.

**Durum:** TEKNİK MİMARİ PLAN SUNULDU — KULLANICI ONAYI BEKLENİYOR. Onay gelmeden kod, test, prototip veya mimari değişiklik uygulanmayacaktır.
