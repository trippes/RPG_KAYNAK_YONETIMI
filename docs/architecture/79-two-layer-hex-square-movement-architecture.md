# Eldoria — İki Katmanlı Altıgen Dünya ve Kare Hareket Izgarası Mimarisi

**Tarih:** 23 Kasım 2026  
**Hedef dal:** `experiment/map-cleanup`  
**Durum:** Mimari plan — uygulama başlamadı  
**Karar:** Altıgen dünya kanonik kalır; kare hareket ızgarası oyuncu ve NPC'lerin birincil navigasyon katmanıdır; aktörlerin fiziksel konumu sürekli dünya koordinatlarında kalır.


> **Bağlayıcı güncelleme — 23 Kasım 2026:** Bu planın ilk sürümündeki “axial A* dünya ölçeğinde kaba rota/kalıcı fallback, kare grid yerel rota” yorumu geçersizdir. Yeni ve öncelikli karar 81 numaralı mimari karar belgesindedir: kare grid oyuncu ve NPC hareketinin birincil navigasyon uzayıdır; axial A* yalnızca geçiş döneminde karşılaştırma veya geçici fallback olabilir. Kare grid, yalnızca hexlerin içine bölünmüş yerel alt-ızgara değildir.

---

## 1. Yönetici özeti

Eldoria'nın altıgen harita sistemi dünya topolojisinin, arazi sahipliğinin, kaynakların, yapıların, bölge kurallarının ve kayıt verisinin tek doğruluk kaynağı olmaya devam edecektir. Bunun üzerine, aynı dünya geometrisini örten daha ince bir kare ızgara eklenecektir. Kare ızgara, hareket alanını örneklemek ve oyuncu/NPC için birincil rota graph'ını üretmek için kullanılacaktır.

Oyuncu veya NPC kare hücre merkezlerine taşınmayacaktır. Gerçek aktör konumu kesirli `WorldPoint(x, y)` koordinatlarında tutulacak; hız, ivme, çarpışma ve hareket entegrasyonu sürekli düzlemde çalışacaktır.

Bu karar, kullanıcının önerdiği iki katmanlı dünya fikrini mevcut kod tabanının zaten sahip olduğu sürekli hareket ve fizik altyapısıyla birleştirir. Yeni bir fizik motoru veya ikinci bir konum otoritesi oluşturulmayacaktır.

**Temel ilke:** Altıgenler dünyayı tanımlar; kare ızgara hareket alanını örnekler ve rota aramasını destekler; sürekli koordinatlar aktörün gerçek konumunu ve hareketini belirler.

## 2. Mevcut kod tabanının denetiminden çıkanlar

Bu plan, `experiment/map-cleanup` dalında incelenen mevcut bileşenleri temel alır:

| Mevcut bileşen | Bugünkü sorumluluğu | Mimari karardaki yeri |
|---|---|---|
| `HexMapDefinition` | Kanonik altıgen harita ve geçerli hücre maskesi | Dünya geometrisinin otoritesi olarak kalır |
| `HexWorldRuntime` | Aktör kimliği, sürekli konum ve türetilmiş axial hücre/occupancy | Aktör konumunun ve hex sahipliğinin otoritesi olarak kalır |
| `ContinuousEntityPosition` / `WorldPoint` | Harita kapsamlı kesirli konum | Fiziksel konumun tek temsili |
| `MovementIntegrator` | Hız, ivme, yavaşlama ve hedefe yaklaşma | Ortak hareket çekirdeği |
| `ContinuousPlayerMovementController` | Oyuncu hareketini fizik ve runtime commit'iyle birleştirir | Oyuncu kontrol adaptörü; genişletilecek |
| `HexPhysicsSnapshot` | Altıgen haritadan statik çarpışma geometrisi üretir | Kesin çarpışma doğrulamasının kaynağı |
| `resolve_continuous_motion` | Süpürmeli sürekli çarpışma çözümü | Son fiziksel hareket doğrulaması |
| `UniformGridIndex` | Seyrek uzamsal hash / broadphase aday sorgusu | Aktör ve nesne sorguları için korunur |
| `HexPathfinder` | Axial altıgen graf üzerinde deterministik A* | Geçiş döneminde karşılaştırma/geçici fallback; kalıcı ana navigasyon değildir |
| `DynamicActorCollisionResolver` | Oyuncu-NPC itişi ve aktör çakışmaları | Aynı fizik koordinatlarında çalışmaya devam eder |
| `NPCAvoidanceSystem` | Mevcut hex tabanlı kaçınma rotası | Aşamalı olarak ince navigasyon katmanına bağlanır |
| `HexGameplayView` | Pygame sunumu ve input entegrasyonu | Koordinat ve sunum adaptörü; fizik otoritesi olmayacak |

### Önemli mevcut durum

Kod tabanı yalnızca hücreden hücreye hareket etmiyor: `HexWorldRuntime` sürekli konumları saklıyor; `MovementIntegrator` kesirli dünya koordinatlarında hız/ivme hesaplıyor; `ContinuousPlayerMovementController` statik fizik ve dinamik aktör çarpışmalarından sonra sonucu runtime'a commit ediyor.

Bununla birlikte, navigasyonun önemli bölümü hâlâ axial altıgen komşulukları ve hücre adımları üzerinden kurulmuş durumda. Görsel sunumdaki enterpolasyon da fiziksel hareketin yerine geçmemeli. Yeni mimarinin odak noktası bu nedenle yeni bir hareket motoru yazmak değil; mevcut sürekli hareket çekirdeğini daha serbest ve daha hassas bir navigasyon katmanıyla beslemektir.

## 3. Hedef mimari ve sahiplik sınırları

### 3.1 Katman A — Kanonik altıgen dünya

Altıgen dünya değiştirilmeyecek.

- `HexMapDefinition` ve `valid_cells` dünya alanının geçerli sınırını belirler.
- Axial `(q, r)` koordinatları hücre kimliği ve arazi sahipliği için kullanılır.
- Arazi geçiş kuralları, dünya geçişleri, kaynaklar, yapılar, görevler ve içerik verileri hex hücrelerine bağlı kalır.
- Bir aktörün hangi hex hücreye ait olduğu, sürekli konumundan türetilir; ayrı bir hareket ızgarası bu sahipliği değiştiremez.
- Save/load sözleşmesinde kare ızgara hücre kimliği saklanmaz. Gerekli konum verisi mevcut kanonik map kimliği ve sürekli dünya konumudur; hex hücre sahipliği bu konumdan yeniden türetilir.

### 3.2 Katman B — Türetilmiş kare hareket ızgarası

Kare ızgara, kanonik haritadan üretilen ve gerektiğinde yeniden oluşturulabilen bir projection/cache olacaktır.

Her kare hücre en az şu türetilmiş veriyi taşıyabilir:

- Harita kimliği ve tam sayı `grid_x, grid_y` koordinatları.
- Hücre merkezinin dünya koordinatı.
- Merkezin sahibi olan axial hex hücresi (veya sınır hücrelerinde kesişen hex kümesi).
- Navigasyon durumu: geçilebilir, engelli, kısmi/kenar hücresi.
- Arazi maliyeti ve hareket profiline bağlı ek maliyetler.
- Statik engel / dar geçit / geçici engel bitleri.
- İsteğe bağlı komşuluk ve chunk kimliği.

Kare ızgara **kanonik harita verisi değildir**. Hex harita değiştiğinde veya ilgili cache geçersizleştiğinde yeniden oluşturulabilir. Başlangıçta tüm dünya için dev bir yoğun dizi kurmak yerine yalnızca harita sınırları içindeki gerekli hücreleri üreten, chunk'lara ayrılmış ve seyrek saklanabilen bir yapı tercih edilir.

### 3.3 Katman C — Sürekli aktör hareketi ve fizik

- Aktörün gerçek konumu `WorldPoint(x, y)` olarak kalır.
- Hız ve ivme `MovementState` içinde tutulur.
- Oyuncu input'u, NPC steering'i ve hedefe yürüme aynı hareket entegratörünü kullanır.
- Kare ızgara rota/alan sorgusu sağlar; aktörü kare merkezine çekmez.
- `HexPhysicsSnapshot` ve mevcut swept-circle çözümü son çarpışma doğrulamasını yapar.
- Hareketin sonucu `HexWorldRuntime.set_continuous_position` benzeri mevcut atomik runtime sınırından commit edilir.
- Görsel rig, kamera ve ayak kilidi gerçek dünya konumu/hızı üzerinden güncellenir.

## 4. Koordinat dönüşümü ve hücre sahipliği

Harita şu anda pointy-top axial geometri ve 32 dünya birimi hex yarıçapı kullanmaktadır. Dönüşüm tek bir geometri modülünde kalmalıdır; renderer, NPC AI ve navigasyon kendi formüllerini kopyalamamalıdır.

Gerekli saf API sözleşmesi:

- `world_to_hex(WorldPoint) -> LocalHexPosition`
- `hex_to_world(LocalHexPosition) -> WorldPoint`
- `world_to_grid(WorldPoint, cell_size) -> GridCoord`
- `grid_to_world(GridCoord, cell_size) -> WorldPoint`
- `grid_cell_coverage(GridCoord) -> HexCoverage`

Mevcut `world_point_to_hex` ve axial dönüşüm yardımcıları yeniden kullanılmalı; eşdeğer ikinci dönüşüm yazılmamalıdır.

### Hex sınırları

Bir kare hücre tek bir altıgenin içinde kalmak zorunda değildir. Özellikle hex sınırlarını kesen karelerde yalnızca merkez noktasının sahibi olan hex'e bakmak güvenli değildir.

Geçilebilirlik kararı için:
1. Kare hücrenin merkezi ve gerekli örnekleme noktaları kanonik hex haritaya çevrilir.
2. Harita maskesi dışındaki noktalar geçilemez sayılır.
3. Kare hücrenin alanı farklı arazi sınıflarına taşıyorsa hücre konservatif biçimde engelli/kısmi işaretlenir veya ilgili hareket profili için en yüksek geçiş maliyeti atanır.
4. Gerçek aktör geçişi, kare hücre etiketine güvenerek kabul edilmez; swept collider çözümü kesin doğrulamayı yapar.

Bu kural harita dışına taşmayı, ince duvarların köşesinden geçmeyi ve geçilemeyen hex sınırlarını kare örnekleme hatasıyla aşmayı önler.

## 5. Kare ızgara çözünürlüğü ve komşuluk

Mevcut hex yarıçapı 32 dünya birimidir. İlk prototipte iki çözünürlük karşılaştırılacaktır:

- **16 dünya birimi:** Her hex çapında yaklaşık dört hücrelik daha kaba örnekleme; düşük bellek ve sorgu maliyeti.
- **8 dünya birimi:** Daha ince yerel navigasyon ve engel temsili; daha yüksek hücre sayısı ve rota arama maliyeti.

Bu değerler nihai karar değildir. Benchmark ve dar geçit kabul testleriyle seçilecektir. Grid çözünürlüğü aktör hızını, konum hassasiyetini veya fizik collider yarıçapını belirlemez.

İlk sürüm 8 komşulu kare grafı değerlendirebilir; ancak çapraz geçişte iki ortogonal komşu hücre de geçilebilir olmalıdır. Aksi hâlde köşeden kesme oluşur. Daha kesin yaklaşım, her grid kenarını aktörün collider boyutuna göre fizik snapshot ile doğrulamaktır. Komşu kenar maliyeti gerçek dünya merkez mesafesi ve arazi maliyetinden hesaplanır; diagonal kenar düz kenardan daha uzun olduğu için eşit maliyet verilmez.

Kare ızgara üzerinde A* araması, hücre merkezlerine taşınma anlamına gelmez. Rota noktaları sürekli koordinatlara çevrilir; rota yumuşatma yalnızca fizik snapshot tarafından doğrulanan segmentlerde yapılır.

## 6. Navigasyon stratejisi: kare grid birincil ve fizik doğrulamalı

Hedef mimaride kare grid, oyuncu ve NPC'ler için tüm mesafelerde birincil navigasyon graph'ıdır. Yol bulma, hedef hücre, komşuluk, rota maliyeti ve waypoint üretimi kare grid üzerinden yapılır. Hex A* kalıcı bir global koridor veya ana rota katmanı olarak korunmaz.

Önerilen akış:

1. Hedef dünya koordinatı kanonik hex harita maskesi ve kare-grid coverage açısından doğrulanır.
2. Başlangıç ve hedef dünya noktaları kare-grid hücrelerine dönüştürülür; aktörün gerçek sürekli konumu değiştirilmez.
3. Kare-grid A* tüm rota graph'ını arar. Harita boyutu arttığında chunk/cache optimizasyonu aynı kare-grid topolojisinin üzerinde çalışır; hex A* ile ikinci bir kalıcı rota hiyerarşisi kurulmaz.
4. Diagonal geçişlerde iki ortogonal komşu hücrenin geçilebilirliği ve gerçek collider genişliği doğrulanır; köşeden kesme engellenir.
5. Rota waypoint'leri kare hücre merkezlerinden sürekli dünya koordinatlarına çevrilir. Rota yumuşatma yalnızca swept physics tarafından doğrulanan segmentlerde yapılır.
6. Fizik snapshot ve mevcut swept-circle çözümü her gerçek hareket adımının son güvenlik doğrulamasıdır.
7. Hedef, harita veya dinamik engel durumu değiştiğinde kare-grid rotası yeniden değerlendirilir.

Axial A* yalnızca geçiş sırasında eski ve yeni yaklaşımın karşılaştırılması veya geçici güvenli fallback için tutulabilir. Bu geçici kullanım, kare-grid birincil navigasyon hedefini değiştirmez ve nihai mimari sözleşme olarak kalıcılaştırılmaz.

## 7. Fizik ve çarpışma sözleşmesi

Mevcut fizik motoru yeniden yazılmayacaktır.

- Oyuncu collider'ı için mevcut onaylı yarıçap 8 dünya birimidir; bu değer sessizce değiştirilmez.
- NPC ve statik prop collider ölçüleri yalnızca açık içerik/aktör metadata'sından alınır; tahmin edilmez.
- Kare ızgara collision sonucu üretmez; yalnızca aday/rota üretir.
- Son hareket, `HexPhysicsSnapshot.resolve_motion` / mevcut swept-circle çözümüyle statik geometriye karşı doğrulanır.
- Dinamik aktör çarpışması mevcut `DynamicActorCollisionResolver` üzerinden sürer; aday toplama mevcut spatial index ile yapılır.
- Hızlı hareketlerde tünelleme önlemek için hareket displacement'ı swept çözümüne verilir. Grid hücrelerine adım adım teleport yapılmaz.
- Çarpışma çözümü hareketi kısaltırsa velocity, gerçekten uygulanmış displacement üzerinden güncellenir.
- Map boundary ve geçersiz hex alanı fiziksel olarak kapalı kalır.

Kare navigasyon ızgarası ile mevcut `UniformGridIndex` aynı şey değildir. İlki yürünebilir alanı ve rota graph'ını temsil eder; ikincisi AABB tabanlı broadphase aday sorgusudur. İki yapı birbirinin yerine kullanılmamalıdır.

## 8. Oyuncu ve NPC ortak hareket hattı

### Oyuncu

- WASD/ok input'u dünya yön vektörüne dönüştürülür ve normalize edilir.
- `MovementIntegrator` hızlanma/yavaşlama ve yön değişimini hesaplar.
- Statik fizik ve dinamik aktör çarpışması uygulanır.
- Sonuç tek runtime konum otoritesine commit edilir.
- Kamera ve humanoid animasyon gerçek konum, hız ve yaw üzerinden güncellenir.

### NPC

- Davranış sistemi hedef/niyet üretir; hareket fiziğini kendisi uygulamaz.
- NPC hedefi kare navigasyon grafında rota üretir.
- Steering waypoint yönünü ve hız hedefini belirler.
- Aynı `MovementIntegrator` ve fizik sözleşmesi kullanılır.
- NPC-NPC ayrışma, oyuncu itişi ve kaçınma ayrı sorumluluklar olarak kalır ancak aynı sürekli koordinat düzleminde çalışır.
- Uzak NPC'ler için daha düşük sıklıkta AI/navigasyon güncellemesi uygulanabilir; fiziksel görünür aktörlerin çarpışma güvenliği korunur.

Oyuncu ve NPC için iki farklı hız/konum/çarpışma otoritesi oluşturulmayacaktır.

## 9. Animasyon ve sunum bağlantısı

Animasyon fizik hareketini yönetmez; hareket sonucunu yorumlar.

- Yürüme/koşma fazı gerçek kat edilen mesafeden ilerler.
- Idle/walk/run geçişleri gerçek hız ve ivmeden türetilir.
- Yön değişiminde gövde yaw'ı gerçek hareket yönüne yumuşak biçimde yaklaşır.
- Ayak kilidi dünya koordinatındaki gerçek stance temasını kullanır.
- Kamera oyuncunun sürekli sunum konumunu takip eder; hex veya grid merkezine snap etmez.
- Derinlik sıralaması ve çizim katmanı mevcut renderer sözleşmesini korur.

## 10. Performans ve bellek stratejisi

Düşük donanım hedefi nedeniyle kare ızgara tüm harita üzerinde pahalı ve yoğun bir nesne grafı olarak tutulmayacaktır.

- Grid hücre boyutu ve chunk boyutu benchmark ile seçilir.
- Chunk verisi yalnızca aktif harita ve gerekli çevre için üretilir.
- Geçilebilirlik maskesi mümkün olduğunca kompakt bitset/byte array olarak saklanır; her hücre için ağır Python nesnesi zorunlu değildir.
- Statik grid chunk'ları map definition + geometry revision anahtarıyla cache edilir.
- Dinamik aktörler grid hücrelerini fiziksel olarak yeniden yazmaz; mevcut spatial hash index üzerinden sorgulanır.
- A* yalnızca rota gerektiğinde çalışır; her frame yeniden çalıştırılmaz.
- Rota güncellemesi hedef/engel/harita değişimi veya belirlenmiş sapma eşiğiyle tetiklenir.
- Görünür ve yakın aktörler tam hareket/fizik sıklığında; uzaktakiler kontrollü düşük sıklıkta güncellenebilir.
- Cache için üst bellek sınırı ve LRU/eviction politikası tanımlanır.
- Render cache, fizik grid'i veya navigasyon cache'i olarak kullanılmaz.

Benchmark senaryoları: 1, 10, 25 ve 50 aktör; 16 ve 8 birim grid; açık arazi, dar geçit, yoğun engel, NPC kalabalığı ve uzun rota. Ölçümler update p50/p95, rota arama p50/p95, fizik çözümü, grid cache hit/miss, bellek ve toplam frame süresini kapsar.

## 11. Aşamalı uygulama planı

### Aşama 0 — Baseline ve sözleşme doğrulama
- Hedef dal ve mevcut HEAD doğrulanır.
- Mevcut continuous movement, runtime, physics, NPC ve presentation çağrı zinciri tam olarak haritalanır.
- Oyuncu collider 8 birim sözleşmesi ve mevcut save schema korunur.
- Mevcut davranış için test/benchmark baseline kaydedilir.
- Bu aşamada oyun davranışı değiştirilmez.

**Çıkış kapısı:** Mevcut continuous position, hex ownership ve collision commit sırası belgelenmiş olmalı.

### Aşama 1 — Saf grid geometri prototipi
- Grid coordinate/value object ve dönüşüm yardımcıları eklenir.
- WorldPoint → grid → WorldPoint dönüşüm hatası ölçülür.
- Grid hücrelerinin hex sahipliği/coverage hesabı yapılır.
- Harita sınırı ve farklı arazi sınırlarında konservatif walkability üretilir.
- 8 ve 16 birim çözünürlük karşılaştırılır.

**Çıkış kapısı:** Dönüşüm deterministik; harita dışı veya engelli alan yanlışlıkla yürünebilir işaretlenmiyor.

### Aşama 2 — Türetilmiş grid cache
- Grid chunk üreticisi ve cache anahtarı eklenir.
- Cache map geometry revision ile geçersizleştirilir.
- Save dosyasına grid cache yazılmaz.
- Bellek ve üretim maliyeti ölçülür.

**Çıkış kapısı:** Aynı map girdisi aynı grid sonucunu üretir; cache atıldığında doğru biçimde yeniden kurulur.

### Aşama 3 — Kare navigasyon A*
- 8 komşuluk, diagonal corner-cutting engeli ve gerçek mesafe maliyeti uygulanır.
- Hareket profili ve arazi maliyetleri graph kenarlarına yansıtılır.
- Her rota segmenti fizik snapshot ile doğrulanır.
- Kare-grid A* birincil navigasyon sistemi olur. Axial A* yalnızca geçiş döneminde karşılaştırma veya geçici fallback olabilir; kalıcı global rota katmanı değildir.
- Rota sürekli WorldPoint waypoint'lerine dönüştürülür.

**Çıkış kapısı:** Dar geçit, köşe, sınır ve engel testlerinde fiziksel olarak geçersiz rota üretilmiyor.

### Aşama 4 — Oyuncu entegrasyonu
- Tıklayarak hareket yerel grid rotasını takip eder.
- WASD doğrudan sürekli hareketi sürdürür; grid merkezlerine kilitlenmez.
- Aynı continuous controller, physics ve runtime commit hattı kullanılır.
- Kamera ve görsel enterpolasyon yalnızca sunumda kalır.

**Çıkış kapısı:** Oyuncu serbest yönlerde hareket eder; çarpışma, occupancy, map transition ve input regresyonu yoktur.

### Aşama 5 — NPC entegrasyonu
- NPC davranışı grid rotası ve sürekli steering üretir.
- Takip, bekleme, kaçınma ve devriye aynı motorla yürür.
- NPC-NPC overlap ve oyuncu itişi korunur.
- Dinamik engel değişiminde yerel rota yenilenir.

**Çıkış kapısı:** Oyuncu ve NPC aynı fizik kurallarına tabidir; kalabalık sahnede sıkışma/üst üste binme kabul sınırları içindedir.

### Aşama 6 — Animasyon entegrasyonu
- Rig gerçek velocity, displacement, yaw ve stance verisini alır.
- Yürüme/koşma fazı kat edilen mesafeyle senkronize kalır.
- Ayak kayması, yön dönüşü ve duruş geçişleri manuel kabul edilir.

**Çıkış kapısı:** Görsel animasyon gerçek hareketi izler; fizik hareketini veya konum otoritesini değiştirmez.

### Aşama 7 — Performans, regresyon ve kabul
- Linux/Windows CI, tüm testler ve mimari sınır denetimleri çalıştırılır.
- 1/10/25/50 aktör benchmark'ları çalıştırılır.
- Kullanıcının hedef düşük donanımında gerçek FPS ve frame-time ölçümü yapılır.
- Önceki hex hareketiyle karşılaştırmalı test yapılır.
- Manuel oyun kabulü olmadan aşama kapatılmaz.

## 12. Test ve kabul matrisi

| Alan | Zorunlu senaryo | Kabul koşulu |
|---|---|---|
| Koordinat | Hex ↔ world ↔ grid round-trip | Tanımlı tolerans içinde deterministik |
| Harita sınırı | Grid hücresi hex maskesi dışında | Geçilemez |
| Hex sınırı | Kare hücre iki araziyi kesiyor | Güvenli/konservatif sınıflandırma |
| Serbest hareket | 8 yön ve keyfi açılar | Grid merkezine snap yok |
| Hız | Farklı frame delta değerleri | Eşdeğer gerçek süre için tutarlı mesafe |
| Çarpışma | Duvar, köşe, dar koridor | Collider engelden geçmiyor |
| Tünelleme | Büyük displacement / düşük FPS | Swept collision engeli yakalıyor |
| Navigasyon | Diagonal köşe geçişi | Corner-cutting yok |
| Rota | Engel eklendi/kaldırıldı | Yalnızca gerekli rota bölümü yenileniyor |
| Aktörler | Oyuncu-NPC ve NPC-NPC | Tek fizik düzlemi, kararlı ayrışma |
| Persistence | Save/load ve map transition | Grid cache değil, kanonik konum korunuyor |
| Animasyon | Start/stop/turn/walk/run | Gerçek hız ve mesafeyle senkron |
| Performans | 1/10/25/50 aktör | Hedef cihazda frame-time bütçesi korunuyor |
| Regresyon | Hex occupancy, görev, kaynak, geçiş | Mevcut dünya kuralları bozulmuyor |

### Önerilen ilk performans hedefleri

Bunlar mevcut ölçüm sonucu değil, prototipte doğrulanacak mühendislik hedefleridir:
- Simülasyon adımı için sabit ve sınırlı bir zaman politikası; render FPS'inden bağımsız hareket.
- Grid dönüşüm ve lookup işlemlerinde gereksiz allocation olmaması.
- Normal hareket sırasında global A* çalıştırılmaması.
- 25 aktörlü olağan sahnede navigasyon katmanının frame-time bütçesini ölçülebilir biçimde düşük tutması.
- 50 aktör stres testinde bellek artışının sınırlandırılması ve p95 sıçramalarının raporlanması.

Kesin milisaniye hedefleri baseline ve hedef donanım ölçümünden sonra belirlenecektir; CI makinesi sonucu kullanıcı bilgisayarının performans garantisi değildir.

## 13. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| Kare hücrenin hex sınırını yanlış sınıflandırması | Coverage örneklemesi + kesin swept physics doğrulaması |
| Grid çözünürlüğünün fazla bellek tüketmesi | Chunk, seyrek cache, bitset ve çözünürlük benchmark'ı |
| Diagonal köşeden geçiş | İki ortogonal hücre ve collider segment doğrulaması |
| İki konum otoritesi oluşması | Yalnızca HexWorldRuntime continuous position sahibi |
| Grid ile physics farklı sonuç üretmesi | Grid yalnızca aday/rota; physics kesin karar |
| NPC ve oyuncu farklı hareket etmesi | Ortak MovementIntegrator ve physics sözleşmesi |
| Save formatının gereksiz büyümesi | Grid türetilmiş cache; persistence dışında |
| Yeni sistemin mevcut hareketi bozması | Aşamalı feature gate ve axial fallback |
| Düşük FPS'de tünelleme | Swept collision ve sınırlı fixed-step politikası |
| Kare ızgaranın altıgen dünyanın görsel/stratejik yapısını değiştirmesi | Dünya verisi ve renderer hex tabanlı kalır |

## 14. Açık kararlar

Uygulama öncesi prototip ve benchmark ile karara bağlanacak noktalar:

1. 8 mi 16 dünya birimi mi; gerekirse farklı katmanlarda farklı çözünürlük.
2. Kare navigasyonun yalnızca yerel rota mı, yoksa tüm harita A*'ı mı taşıyacağı.
3. Chunk boyutu ve cache ömrü.
4. Kare hücre walkability üretiminde örnekleme sayısı ve konservatif sınır kuralı.
5. NPC uzaklık/LOD eşikleri ve rota yenileme sıklığı.
6. Fixed-step simülasyon frekansı ve maksimum catch-up adımı.

Bu kararlar ölçüm olmadan sabitlenmeyecektir.

## 15. Uygulama dışı bırakılanlar

- Hex harita sistemini kare haritaya dönüştürmek.
- Aktörleri kare hücre merkezlerine kilitlemek.
- İkinci bir authoritative entity registry veya position store kurmak.
- Mevcut physics solver'ı veya `UniformGridIndex`'i kare navigasyon ızgarasıyla değiştirmek.
- Save schema'ya türetilmiş grid hücrelerini eklemek.
- NPC collider boyutlarını tahmin etmek.
- Animasyon rig'ini hareket otoritesi hâline getirmek.
- Kullanıcı kabulü olmadan hareket aşamasını tamamlandı saymak.

## 16. Son mimari kararı

Eldoria için önerilen mimari, **Hex World + Derived Square Navigation Grid + Continuous Movement/Physics** üçlüsüdür.

Bu, kullanıcının iki katmanlı dünya önerisini korur; mevcut continuous movement, physics, spatial hash ve runtime sahipliğini yeniden kullanır. Kare ızgara serbest hareketin kendisi değildir ve aktörleri kare adımlara bağlamaz. Sürekli koordinat sistemi hareketin tek fiziksel kaynağı olmaya devam eder.

**Uygulama sırası:** Önce mevcut hareket hattının baseline doğrulaması, ardından saf grid geometri prototipi; performans ve sınır testleri başarılı olmadan oyuncu/NPC entegrasyonuna geçilmez.

---

## Kaynaklar ve teknik dayanak

- Pygame Vector2 / zaman tabanlı hareket ve vektör işlemleri: https://www.pygame.org/docs/ref/math.html
- Pygame Rect ve çarpışma yardımcıları: https://www.pygame.org/docs/ref/rect.html
- Red Blob Games — Hexagonal Grids: https://www.redblobgames.com/grids/hexagons/
- Red Blob Games — A* Introduction: https://www.redblobgames.com/pathfinding/a-star/introduction.html
- Eldoria mevcut mimari: `docs/architecture/72-phase-16-hex-pathfinding-and-player-navigation.md`, `77-phase-16-player-physics-movement-integration.md`, `78-phase-16-smooth-hex-player-presentation.md`
