# Eldoria — Hareket Mimarisi ve Performans Teknik Denetimi

> **Durum:** Denetim raporu — uygulama yapılmadı  
> **İncelenen dal:** `experiment/map-cleanup`  
> **Denetim taban commit'i:** `3121c4dc355d44d1a43a775d894081aae16e8b2a`  
> **Tarih:** 20 Kasım 2026  
> **Kapsam:** Kaynak kodu, testler, proje yapılandırması, GitHub Actions ve Pygame-ce dokümantasyonu  
> **Kısıt:** Bu denetim sırasında kaynak kodu değiştirilmedi; dosya silinmedi/taşınmadı; test, CI veya oyun yapılandırması değiştirilmedi.

---

## 1. Yönetici özeti

Eldoria'nın mevcut hareket mimarisi, temel fizik ve dünya koordinatı sorumluluklarını Pygame çizim katmanından ayıran, sabit zaman adımı kullanan ve statik/dinamik çarpışmayı farklı sorumluluklarda ele alan sağlam bir başlangıç sunuyor. WASD ve yön tuşları, çapraz hareket normalizasyonu, koşma/gizlilik modları, statik engel çarpışması ve NPC itişi için anlamlı test kapsamı mevcut.

Bununla birlikte sistem, modern ve akıcı bir RPG hareket deneyimi için henüz tamamlanmış değil. En önemli teknik bulgular şunlardır:

1. **İvmelenme ve yavaşlama yok:** Aktif hareket integratörü istenen yön ve hız çarpanını doğrudan uygular. Tuşa basınca tam hıza geçiş, tuş bırakınca anlık duruş ve yön değişiminde ani vektör dönüşü oluşur.
2. **Fare hedefi için yol tekrar hesaplanıyor:** `HexGameplayView.click_move_intent()` her çağrıda `runtime.path_to()` çağırıyor. Bu fonksiyonun fizik adımlarında tekrar çağrılması, hedef değişmedikçe gereksiz yol sorgusu riski oluşturuyor.
3. **Fizik catch-up sınırı yok:** `FixedStepAccumulator.advance()` birikmiş süreyi adımlara dönüştürürken kare başına maksimum adım sayısı uygulamıyor. Uzun karelerden sonra çok sayıda fizik adımı çalışması ve yükün büyümesi riski var.
4. **Oyuncu render interpolasyonu eksik:** Oyuncu görsel konumu son fizik konumuna eşitleniyor. Fizik 60 Hz iken render FPS'i değiştiğinde fizik adımları arasında görsel hareket sürekliliği garanti edilmiyor.
5. **Nesne yaşam döngüsü maliyeti:** Hareket kontrolcüsü güncelleme çağrısı sırasında, dinamik çarpışma çözümleyicisi de hareket adımı sırasında yeniden oluşturuluyor.
6. **Harita render hazırlığında tekrarlı tam taramalar:** Hücre sıralaması, dünya merkezlerinin hesaplanması ve görünürlük taraması her render çağrısında yapılıyor.
7. **Performans gözlemlenebilirliği eksik:** `render_stats` arayüzü bulunmasına rağmen `_last_render_stats` gerçek render sayaçlarıyla güncellenmiyor.
8. **Kalite kontrol kapsamı:** CI başarılı olsa da Ruff'ın açık dosya listesi `hex_world_lab` paketinin tamamını kapsamıyor. İki hareket mimarisi arasında da uzun vadeli sözleşme/tek kaynak belirsizliği var.

**Genel karar:** Hareket sistemini baştan yazmak gerekmiyor. Mevcut domain hareket sözleşmesi, sabit zaman adımı ve çarpışma mimarisi korunmalı; önce ölçüm altyapısı kurulmalı, ardından hareket fiziği, fare navigasyonu, interpolasyon ve render maliyeti kanıta dayalı biçimde iyileştirilmeli.

### Denetim sınırları ve güven düzeyi

- İnceleme yalnızca yukarıda belirtilen dalın taban commit'ine aittir. Başka dallardaki kodlar bu raporun mevcut durum kanıtı olarak kullanılmamıştır.
- Kaynak kodundan doğrudan görülen davranışlar **kesin kod bulgusu** olarak işaretlenmiştir.
- Gerçek FPS/CPU profili alınmadığı için kod yapısından çıkarılan maliyetler **olası darboğaz** olarak sınıflandırılmıştır.
- Kullanıcının bilgisayarındaki FPS düşüşlerinin kaynağı bu incelemeyle belirlenmiş değildir.
- Yerel makinede pytest/Ruff çalıştırılmamıştır. Test ve kalite sonuçları mevcut GitHub Actions kayıtlarından alınmıştır.
- Context7 ile Pygame-ce dokümantasyonu sorgulanmıştır; dokümantasyon doğrulaması belirli API davranışları içindir, proje performansının ölçümü değildir.

---

## 2. İncelenen mimari

### 2.1 Aktif oyun hareket akışı

Aktif oyun tarafında görülen temel sorumluluk zinciri şöyledir:

```text
PygameMovementInput
        |
        v
MovementIntent
        |
        v
FixedStepAccumulator / GameplayStepClock
        |
        v
ContinuousPlayerMovementController
        |
        v
MovementIntegrator
        |
        v
HexPhysicsSnapshot
        |
        v
DynamicActorCollisionResolver
        |
        v
HexWorldRuntime / dünya konumu
        |
        v
HexGameplayView / kamera / render
```

Bu ayrımın temel avantajı, giriş cihazının fizik kurallarını doğrudan belirlememesidir. Klavye girdisi bir hareket niyetine dönüştürülür; fizik adımı bu niyeti işler; dünya ve sunum katmanları sonucu kullanır.

### 2.2 İlgili dosyalar ve sorumlulukları

| Dosya | İncelenen sorumluluk |
|---|---|
| `game_ui/movement_input.py` | WASD/yön tuşları, Shift, Alt ve hareket niyeti |
| `core/domain/movement/integrator.py` | Hareket yönü, hız ve konum entegrasyonu |
| `core/domain/movement/config.py` | Hareket profili/hız yapılandırması |
| `core/domain/movement/state.py` | Hareket durumu |
| `application/continuous_player_movement.py` | Sürekli oyuncu hareketi, fizik ve çarpışma koordinasyonu |
| `application/gameplay_step_clock.py` | Sabit zaman adımı/birikmiş süre yönetimi |
| `application/dynamic_actor_collision.py` | Hareketli aktör çarpışma çözümü |
| `game_ui/game_window.py` | Oyun döngüsü ve hareket güncellemesinin çağrılması |
| `game_ui/world_rendering/hex_gameplay_view.py` | Fare hedefi, oyuncu görsel konumu, NPC görselleri ve dünya render akışı |
| `game_ui/world_rendering/camera.py` | Kamera takibi, yumuşatma ve sınırlandırma |
| `game_ui/world_rendering/terrain_renderer.py` | Terrain hücrelerinin çizimi |
| `game_ui/world_rendering/depth_sorter.py` | Derinlik sıralama sorumluluğu |
| `game_ui/world_rendering/scene_object_pipeline.py` | Sahne nesnelerinin render hazırlığı |
| `hex_world_lab/` | Ayrıştırılmış simülasyon, hareket, kamera ve render laboratuvarı |

### 2.3 İki hareket mimarisi

Depoda hem `core/domain/movement/` hem de `hex_world_lab/movement/` altında benzer kavramlar bulunuyor. Her iki tarafta da MovementIntegrator, MovementConfig, MovementIntent ve MovementState benzeri sorumluluklar yer alıyor.

Bu durum tek başına hata değildir: laboratuvar paketi yeni mimariyi deneyen ayrı bir alan olabilir. Ancak hangi sözleşmenin üretim oyunu için esas kabul edildiği, hangi parçaların aktif oyun döngüsüne taşındığı ve iki tarafın davranışlarının nasıl eşit tutulacağı açıkça belgelenmelidir.

**Öneri:** `core/domain/movement` aktif oyunun kanonik hareket sözleşmesi olarak korunmalı; `hex_world_lab` içindeki başarılı tasarımlar doğrudan kopyalanmak yerine kontrollü geçiş ve ortak davranış testleriyle değerlendirilmelidir. Nihai sahiplik kararı proje sahibinin onayına tabidir.

---

## 3. Hareket sistemi denetimi

### 3.1 Klavye hareketi

İncelenen giriş katmanı `game_ui/movement_input.py` içerisindeki `PygameMovementInput` sorumluluğudur.

| Özellik | Kod/test incelemesi |
|---|---|
| WASD | Destekleniyor |
| Yön tuşları | Destekleniyor |
| Birden fazla tuşa aynı anda basma | Destekleniyor |
| Çapraz hareket normalizasyonu | Domain hareket hesabında mevcut |
| Tuş basılı tutulduğunda sürekli hareket | Basılı tuş durumundan üretiliyor |
| Tuş bırakıldığında hareket niyetinin kalkması | Destekleniyor |
| Pencere odağı kaybı | Girdi durumunun temizlenmesine yönelik davranış mevcut |
| Shift koşma | Destekleniyor |
| Alt gizlilik | Toggle davranışı destekleniyor |

Girdi katmanının temel yaklaşımı uygundur. Pygame-ce dokümantasyonu da sürekli hareket için `pygame.key.get_pressed()` durum sorgusunun olay kuyruğundaki tek seferlik KEYDOWN olayından farklı olarak tutulmuş tuş durumunu okumak için kullanılmasını açıklar. Kritik olayların (ör. tıklama/tuş olayı) kaybolmaması gereken yerlerde olay kuyruğu yine işlenmelidir.

**Hareket hissi eksikliği giriş katmanında değil, hız entegrasyonundadır.** Tuş bırakıldığında giriş niyeti sıfırlansa da fizik katmanında yumuşak frenleme uygulanmıyor.

### 3.2 İvmelenme, yavaşlama ve yön değiştirme

**Bulgu MOV-01 — Yüksek önem**

- **Dosya/fonksiyon:** `core/domain/movement/integrator.py`, `MovementIntegrator.step()`
- **Kanıt:** Hareket yönü normalize edilerek hareket profili/hız çarpanıyla doğrudan konum hesabına aktarılıyor. Önceki hız vektörünü hedef hıza doğru kademeli yaklaştıran bir ivmelenme/frenleme süreci görülmüyor.
- **Oyuncu deneyimi:** Tuşa basıldığında anlık hızlanma, tuş bırakıldığında anlık durma ve yön değişiminde keskin geçiş.
- **Performans:** Doğrudan performans sorunu değil.
- **Öneri:** Hareket durumunda hız vektörünü koruyan bir model; ivmelenme, frenleme ve yön değiştirme için ayrı parametreler. Mod değişimi hedef hızı değiştirir, hız vektörünü bir karede sıçratmaz.
- **Test:** Başlangıçtan maksimum hıza ulaşma süresi, tuş bırakma sonrası durma mesafesi, ters yöne geçişte hız eğrisi, farklı fizik adımı bölünmelerinde eşdeğer sonuç.

İvmelenme tasarımında yalnızca skaler hız değil, iki boyutlu hız vektörü ele alınmalıdır. Aksi takdirde yön değiştirme sırasında hızın büyüklüğü ve yönü arasında tutarsız geçişler oluşabilir.

### 3.3 Sabit zaman adımı

**Bulgu MOV-03 — Yüksek önem**

- **Dosya/fonksiyon:** `application/gameplay_step_clock.py`, `FixedStepAccumulator.advance()`
- **Kanıt:** Birikmiş süre sabit adımlara dönüştürülüyor; kare başına yürütülebilecek maksimum fizik adımı sınırı görülmüyor.
- **Olumlu yön:** Fizik zamanlaması render FPS'inden ayrılmış ve 60 Hz hedef adım kullanılıyor.
- **Risk:** Bir kare uzun süre durursa birikmiş süre çok sayıda ardışık fizik adımına dönüşebilir. Bu, sonraki kareyi de uzatarak catch-up yükünü büyütebilir (spiral-of-death riski).
- **Öneri:** Maksimum catch-up adımı ve açık bir gecikme politikası belirlenmeli. Fazla birikmiş süreyi sınırsız biçimde simüle etmek yerine kontrollü sınırlandırma yapılmalı. Duraklatma/odak kaybı davranışı ayrıca tanımlanmalı.
- **Test:** 100 ms, 500 ms ve 1.000 ms yapay kare gecikmesi; maksimum fizik adımı sayısı; simülasyon zamanı farkı; pause/resume sonrasında birikmiş sürenin davranışı.

60 Hz için teorik fizik adımı:

[
Delta t = rac{1}{60} approx 0.01667 	ext{ saniye}
]

### 3.4 Fizik ve render ayrımı / interpolasyon

**Bulgu MOV-04 — Orta önem**

- **Dosya/fonksiyon:** `game_ui/world_rendering/hex_gameplay_view.py`, `_sync_continuous_visual()` ve ilgili update akışı.
- **Kanıt:** Oyuncunun görsel konumu son fizik konumuyla eşitleniyor; fizik adımları arasında önceki ve sonraki fizik snapshot'larından render interpolasyonu uygulanmıyor.
- **Oyuncu deneyimi:** Render FPS'i fizik frekansından farklı olduğunda oyuncu hareketi basamaklı algılanabilir.
- **Performans:** CPU darboğazı olduğu kanıtlanmadı; konu görsel süreklilik.
- **Öneri:** Fizik durumunun önceki ve güncel konumunu koruyup render aşamasında accumulator alpha ile görsel interpolasyon yapmak. Render interpolasyonu fizik/dünya gerçek konumunu değiştirmemeli.
- **Test:** 30/60/120/144 FPS render döngülerinde aynı fizik simülasyon süresi için aynı fizik sonucu; görsel konumun iki fizik snapshot'ı arasında kalması; çarpışma ve kamera sınırlarında sıçrama olmaması.

Kamera ve oyuncu aynı zaman örneğini kullanmalıdır. Oyuncu interpolasyonu uygulanırken kamera son fizik konumunu takip ederse görsel ayrışma veya mikro titreşim görülebilir. Bu nedenle oyuncu ve kamera render hedefi birlikte tasarlanmalıdır.

### 3.5 Dinamik çarpışma

- **Dosya:** `application/dynamic_actor_collision.py`
- **İlgili sınıf:** `DynamicActorCollisionResolver`
- **Entegrasyon:** `application/continuous_player_movement.py`

Olumlu bulgular:
- Statik dünya engelleri ile hareketli aktör çarpışması ayrı sorumluluklarda.
- Sürekli hareket/çarpışma çözümleme yaklaşımı mevcut.
- Duvar boyunca kayma ve engel aşmama davranışları için testler bulunuyor.
- Oyuncu-NPC itişinde başarısız hareketin geçici etkilerini geri alma davranışına yönelik test kapsamı var.

**Ölçeklenebilirlik riski:** Dinamik çözümleyici, hareket çözümünde NPC gövde yarıçaplarını tekrar tarıyor ve mekânsal indeks üzerinden aday sorguluyor. Mekânsal indeks doğru yönde bir tasarım olsa da aday sorgusundan önceki tam taramanın maliyeti aktör sayısı arttıkça ölçülmelidir.

**Öneri:** NPC gövde verilerinin hangi sıklıkta değiştiğini belirleyip değişmeyen veriyi tekrar hazırlamamak; çarpışma adaylarını mekânsal indeks üzerinden sınırlamak. Ancak gerçek profiler sonucu olmadan bu alanın en büyük darboğaz olduğu ileri sürülmemelidir.

### 3.6 Fareyle hedefe hareket

**Bulgu MOV-02 — Yüksek önem**

- **Dosya/fonksiyon:** `game_ui/world_rendering/hex_gameplay_view.py`, `click_move_intent()`
- **Kanıt:** Fonksiyon hedef hücreyi ve oyuncu konumunu alıp `runtime.path_to()` çağırıyor. Fonksiyon fizik güncellemesi sırasında tekrar çağrıldığı için aynı hedef ve değişmeyen dünya durumunda yol tekrar sorgulanabiliyor.
- **Oyuncu deneyimi:** Hex merkezlerine yönelme, hücre geçişlerinde küçük yön değişimleri oluşturabilir. Duraksamanın gerçek sebebi ayrıca ölçülmeli.
- **Performans:** Tekrarlı pathfinding olası maliyet; profiler olmadan gerçek FPS etkisi bilinmiyor.
- **Öneri:** Hedef, başlangıç hücresi ve navigasyon/dünya sürümüne bağlı yol önbelleği. Hedef değiştiğinde, yol geçersizleştiğinde veya navigasyon verisi değiştiğinde yeniden hesaplama.
- **Test:** Aynı hedefte yol sorgusu sayısı; hedef değiştirilince eski yolun iptali; yol üzerindeki engel değişince yeniden planlama; erişilemeyen hedef; hedefe varış toleransı.

İncelenen yaklaşım fare koordinatını hex hücresine dönüştürüp sonraki hücre merkezini hareket hedefi olarak kullanıyor. Bu, hücre tabanlı navigasyon için anlaşılır bir yöntemdir. Daha akıcı bir deneyim için hücre geçiş eşiği, köşe yumuşatma (path smoothing), son hedefe yaklaşırken hız azaltma ve hedef değişiminde komut iptali birlikte değerlendirilmelidir.

Klavye ve fare hareketinin aynı fizik tabanını kullanması doğru yöndür: klavye doğrudan hareket yönü niyeti üretirken fare navigasyonu yol üzerindeki bir sonraki yönü üretmeli; ikisi de aynı hız/çarpışma integrasyonundan geçmelidir.

### 3.7 Shift ve Alt hareket modları

Girdi ve hareket yapılandırması birlikte değerlendirildiğinde modlar fizik hızına aktarılıyor; yalnızca UI katmanında kalmıyor.

İncelenen hız çarpanları:
- Normal: 1,0
- Shift/koşma: 1,5
- Alt/gizlilik: 0,5
- Alt ve Shift birlikte: Alt öncelikli

Alt davranışı basılı tutma değil, toggle olarak ele alınıyor. Bu mevcut davranış ve test sözleşmesi korunmalı; değişiklik yapılacaksa ayrıca tasarım kararı alınmalı.

**Eksik:** Mod değişimi hedef hızı anında değiştirebiliyor. İvmelenme sistemi eklendiğinde koşma/gizlilik geçişleri hız vektörüne kademeli yansıtılmalı.

### 3.8 Kamera

- **Dosya/sınıf:** `game_ui/world_rendering/camera.py`, `HexCamera`
- Kamera takip yumuşatması zaman tabanlı üstel yaklaşım kullanıyor.
- İncelenen algoritmada (alpha=1-e^{-8Delta t}) biçiminde delta-time bağımlı yumuşatma bulunuyor.
- İzometrik projeksiyon, harita sınırları ve kenar kaydırma dikkate alınıyor.

Bu yaklaşım farklı render FPS değerlerinde sabit katsayılı Lerp kullanmaktan daha tutarlıdır. Ancak oyuncu interpolasyonu henüz yokken kameranın son fizik konumunu, oyuncu çiziminin de aynı son konumu kullanması render kareleri arasında adım hissi doğurabilir.

**Öneri:** Kamera, render edilecek interpolasyonlu oyuncu konumunu izlemeli; kamera sınırlandırması da aynı render koordinat uzayında uygulanmalı. Kamera smoothing ile fizik interpolasyonu birbirine karıştırılmamalıdır.

---

## 4. Performans denetimi

### 4.1 Harita hücrelerinin her karede sıralanması

**Bulgu PERF-01 — Olası darboğaz**

- **Dosya/fonksiyon:** `game_ui/world_rendering/hex_gameplay_view.py`, `render()`
- **Kanıt:** `map_definition.valid_cells` üzerinde her render çağrısında `sorted(..., key=(r, q))` çalıştırılıyor.
- **Risk:** Harita hücre sayısı büyüdükçe her karede sıralama maliyeti artar.
- **Öneri:** Hücre sırasını harita tanımı değiştiğinde bir kez üretip saklamak.
- **Ölçüm:** Harita boyutları 384, 1.000, 5.000 ve 10.000 hücre iken render hazırlık süresi.

### 4.2 Dünya merkezlerinin tekrar hesaplanması

**Bulgu PERF-02 — Olası darboğaz**

- **Dosya/fonksiyon:** `game_ui/world_rendering/hex_gameplay_view.py`, `render()`
- **Kanıt:** Kamera sınırları için valid hücrelerin axial koordinatları dünya koordinatlarına her render çağrısında dönüştürülerek tuple oluşturuluyor.
- **Risk:** Değişmeyen harita geometrisi için tekrar hesaplama ve geçici koleksiyon oluşturma.
- **Öneri:** Harita geometrisi/cache anahtarıyla ilişkilendirilmiş dünya merkezleri ve sınırları.
- **Ölçüm:** Bu hazırlık adımının render toplam süresindeki payı.

### 4.3 Görünürlük kontrolü

**Bulgu PERF-03 — Olası darboğaz**

- **Dosya/fonksiyon:** `game_ui/world_rendering/hex_gameplay_view.py`, `render()`
- **Kanıt:** Hücreler tam koleksiyon üzerinden dolaşılarak kamera görünürlüğü kontrol ediliyor.
- **Risk:** Ekranda olmayan hücreler çizilmese bile görünürlük kararı için taranıyor.
- **Öneri:** Kamera viewport'unu axial/hex aralığına dönüştürüp yalnızca aday hücreleri sorgulamak; büyük haritalarda chunk/bölge tabanlı render.
- **Ölçüm:** Toplam hücre, görünür hücre ve çizilen hücre sayısı; görünürlük sorgusu süresi.

### 4.4 Terrain çizim maliyeti

**Bulgu PERF-04 — Olası darboğaz**

- **Dosya:** `game_ui/world_rendering/terrain_renderer.py`
- **Kanıt:** Görünür terrain hücrelerinde polygon/outline ve bazı terrain türleri için küçük dekoratif detay çizimleri yapılıyor. Texture ölçekleme tarafında önbellek kullanımı olumlu.
- **Risk:** Değişmeyen zemin detaylarının her karede tekrar çizilmesi.
- **Öneri:** Terrain yüzeylerini önceden oluşturma, statik chunk yüzeyleri ve doğru cache invalidation.
- **Ölçüm:** Hücre başına çizim çağrısı, terrain renderer süresi, cache hit/miss ve yüzey tahsisi.

### 4.5 NPC ve dünya nesnesi taramaları

**Bulgu PERF-05 — Olası darboğaz**

- **Dosya/fonksiyon:** `game_ui/world_rendering/hex_gameplay_view.py`, `_advance_npc_visuals()` ve `render()`
- **Kanıt:** NPC görsel güncellemesi ve render hazırlığı farklı aşamalarda entity koleksiyonlarını dolaşıyor; dünya varlıkları yeniden sorgulanabiliyor.
- **Risk:** NPC ve dünya nesnesi sayısı arttıkça tekrarlı koleksiyon taraması.
- **Öneri:** Simülasyon snapshot'ı üzerinden tek karelik render verisi üretmek; kamera alanına göre NPC/nesne sorgulamak.
- **Ölçüm:** NPC update süresi, entity sorgu sayısı, görünür/işlenen aktör sayısı.

### 4.6 Gereksiz nesne oluşturma

**Bulgu PERF-06 — Kesin kod maliyeti; etkisi ölçülmeli**

- **Dosyalar:** `game_ui/game_window.py` ve `application/continuous_player_movement.py`
- **Kanıt:** `_advance_continuous_player_movement()` içinde `ContinuousPlayerMovementController` yeniden oluşturuluyor; `step()` içinde `DynamicActorCollisionResolver` yeniden oluşturuluyor.
- **Risk:** Tekrarlı nesne başlatma ve bellek tahsisi; gerçek frame-time etkisi henüz ölçülmedi.
- **Öneri:** Controller ve resolver yaşam döngüsünü sahip oldukları bağımlılıklarla birlikte oturum/oyun penceresi seviyesinde değerlendirmek.
- **Ölçüm:** Kare başına nesne tahsisleri, GC etkinliği, update süresi ve profiler örnekleri.

### 4.7 Render istatistiklerinin güncellenmemesi

**Bulgu PERF-07 — Kesin sorun**

- **Dosya/özellik:** `game_ui/world_rendering/hex_gameplay_view.py`, `render_stats`
- **Kanıt:** `render_stats` `_last_render_stats` içeriğinin kopyasını döndürüyor; incelenen uygulamada sözlük başlatılıyor ancak gerçek render sayaçlarıyla güncellenmiyor.
- **Etki:** Render maliyeti ve işlenen nesne sayıları bu arayüzden güvenilir biçimde izlenemiyor.
- **Öneri:** Render sonunda gerçek ölçülen sayaçları yayımlamak; sayaç toplama maliyetini düşük tutmak.
- **Test:** Bilinen hücre/NPC fixture'ında raporlanan sayaçların beklenen değerlerle eşleşmesi.

### 4.8 Gerçek performans ölçüm stratejisi

60 FPS hedefinin kare bütçesi:

[
1000/60 = 16.67 	ext{ ms}
]

Önerilen ölçümler:

| Metrik | Açıklama |
|---|---|
| FPS | Ortalama ve anlık FPS |
| Frame time | Her karenin ms cinsinden süresi |
| p50 / p95 / p99 | Kare süresi dağılımı ve uzun kuyruk |
| Render süresi | Toplam çizim süresi |
| Fizik süresi | Sabit fizik adımlarının toplam maliyeti |
| NPC update süresi | NPC simülasyon/görsel güncellemesi |
| Kamera süresi | Kamera hedefi, smoothing ve sınır hesapları |
| Harita çizim süresi | Terrain ve hücre render maliyeti |
| Hücre sayıları | Toplam, aday, görünür ve çizilen hücre |
| Aktör sayıları | Toplam, aday, görünür ve çizilen NPC/nesne |
| Frame spike | Eşik üstü karelerin sayısı ve sıklığı |
| Yol sorgusu | Kare başına pathfinding çağrısı ve süre |
| Tahsis/GC | Nesne tahsisleri ve garbage collection etkisi |

Önerilen yaklaşım: Önce ölçüm noktalarını düşük ek yükle eklemek; aynı donanımda aynı harita/NPC senaryolarını tekrar çalıştırmak; optimizasyon öncesi ve sonrası p50/p95/p99 kıyaslamak. Tek bir FPS ortalaması yeterli değildir.

**Önemli:** Bu denetimde gerçek profiler çalıştırılmadı. Bu nedenle sistemin 60 FPS hedefini karşıladığı veya belirli bir modülün kullanıcıda gözlenen FPS düşüşünün sebebi olduğu iddia edilmemektedir.

---

## 5. Test ve kalite sonuçları

### 5.1 GitHub Actions

Denetim sırasında görülen son hedef dal CI kayıtlarında:

- Eldoria CI: 5/5 iş başarılı.
- Core quality: 2/2 iş başarılı.
- Windows ve Ubuntu doğrulamaları ile Python 3.11/3.12 kombinasyonları raporlanmış.
- Pygame headless smoke doğrulaması başarılı.
- Release candidate pytest kaydı: 2.435 başarılı, 0 başarısız, 59 uyarı; ayrıca 260 subtest başarılı olarak raporlanmış.

Bu sonuçlar GitHub Actions kayıtlarına aittir; yerel test çalıştırması değildir. CI sonuçları yalnızca incelenen commit/run bağlamında geçerlidir.

Önceki bir başarısız CI kaydında şu iki NPC kaçınma testi başarısız görünmüştür:
- `test_flee_state_moves_npc_away_from_player_and_leaves_idle_npc_untouched`
- `test_avoidance_is_bounded_by_static_map_collision`

Daha sonraki hedef dal doğrulamasında test paketi başarılıdır. Önceki başarısızlık, güncel başarısızlık gibi sunulmamalıdır.

### 5.2 Ruff

Core quality workflow'unda Ruff kontrolü başarılı görünmektedir. Ancak workflow'un açık dosya/kapsam listesi `hex_world_lab` paketinin tamamını kapsamamaktadır.

**Bulgu QA-01 — Orta önem:** Laboratuvar hareket/fizik/kamera/render paketinin bir kısmı Ruff kapsamı dışında kalabilir. Workflow kapsamı genişletilmeli veya paket bazında açıkça doğrulanmalıdır.

### 5.3 Pytest kapsamı

Mevcut testler temel hareket, çapraz normalizasyon, hareket modları, çarpışma, NPC itişi, sabit zaman adımı ve kamera davranışları için iyi bir başlangıç sunuyor.

Eksik veya sınırlı alanlar:

| Test alanı | Değerlendirme |
|---|---|
| WASD/yön tuşları ve çapraz hız | İyi |
| Shift/Alt davranışı | İyi |
| Statik çarpışma ve kayma | İyi |
| Oyuncu-NPC itişi | İyi |
| Sabit zaman adımı temel davranışı | İyi |
| Kamera takip/sınırları | İyi |
| İvmelenme ve yumuşak frenleme | Mevcut sözleşmede yok |
| Farklı render FPS'lerinde eşdeğer fizik | Eksik |
| Oyuncu render interpolasyonu | Eksik |
| Fare hedefi/pathfinding çağrı sayısı | Eksik |
| Büyük harita render benchmark'ı | Eksik |
| NPC sayısı arttıkça performans | Sınırlı |
| Frame spike regresyon ölçümü | Eksik |

Yeni hareket modeli eklendiğinde anlık durma/yön değişimini bekleyen testler yeni davranış sözleşmesine göre güncellenmelidir; eski testlerin başarısı yeni hareket hissini doğrulamaz.

---

## 6. Sorun kayıtları

Önem dereceleri, oyuncu deneyimine ve mimari riske göre verilmiştir; performans etkisi ölçülmemiş bulgularda bu açıkça belirtilmiştir.

| ID | Önem | Sınıf | İlgili yer | Kısa açıklama |
|---|---|---|---|---|
| MOV-01 | Yüksek | Kesin kod bulgusu | `core/domain/movement/integrator.py::MovementIntegrator.step` | İvmelenme/frenleme yok |
| MOV-02 | Yüksek | Kesin kod bulgusu | `hex_gameplay_view.py::click_move_intent` | Her çağrıda yol sorgusu |
| MOV-03 | Yüksek | Kesin kod bulgusu | `gameplay_step_clock.py::FixedStepAccumulator.advance` | Catch-up adım sınırı yok |
| MOV-04 | Orta | Kesin kod bulgusu | `hex_gameplay_view.py::_sync_continuous_visual` | Oyuncu interpolasyonu yok |
| MOV-05 | Orta | Kesin kod maliyeti | `game_window.py::_advance_continuous_player_movement`; `continuous_player_movement.py::step` | Controller/resolver tekrar oluşturuluyor |
| PERF-01 | Orta | Olası darboğaz | `hex_gameplay_view.py::render` | Her kare hücre sıralama |
| PERF-02 | Orta | Olası darboğaz | `hex_gameplay_view.py::render` | Dünya merkezlerini yeniden hesaplama |
| PERF-03 | Orta | Olası darboğaz | `hex_gameplay_view.py::render` | Tam hücre koleksiyonu görünürlük taraması |
| PERF-04 | Orta | Olası darboğaz | `terrain_renderer.py` | Statik terrain detaylarının tekrar çizimi |
| PERF-05 | Orta | Olası darboğaz | `hex_gameplay_view.py` NPC update/render | Tekrarlı entity taramaları |
| PERF-06 | Orta | Ölçüm gerekli | Hareket ve çarpışma nesne yaşam döngüsü | Tahsis maliyeti |
| PERF-07 | Orta | Kesin sorun | `hex_gameplay_view.py::render_stats` | Gerçek sayaçlar yayımlanmıyor |
| QA-01 | Orta | Kesin kapsam eksikliği | `.github/workflows/core-quality.yml` | Ruff kapsamı hex_world_lab'i tam içermiyor |
| QA-02 | Orta | Test kapsamı eksikliği | `tests/` hareket testleri | FPS, interpolasyon, path query ve benchmark testleri eksik |
| ARCH-01 | Orta | Mimari risk | `core/domain/movement/` ve `hex_world_lab/movement/` | Paralel hareket sözleşmeleri |

### Her bulgu için önerilen doğrulama

- **MOV-01:** Birim testinde hız-zaman eğrisi, fren mesafesi, ters yöne geçiş ve mod değişimi.
- **MOV-02:** Aynı hedefte path query sayacı; hedef/engel değişiminde cache invalidation.
- **MOV-03:** Yapay uzun frame senaryolarında maksimum adım sayısı ve zaman kaybı politikası.
- **MOV-04:** 30/60/120/144 FPS render örneklemesinde fizik sonucu ve görsel konum karşılaştırması.
- **MOV-05/PERF-06:** Profiler ve tahsis sayacıyla controller/resolver oluşturma sıklığı.
- **PERF-01/02/03:** Farklı harita boyutlarında render hazırlık süresi ve aday/görünür hücre sayaçları.
- **PERF-04:** Terrain cache hit/miss ve çizim süresi.
- **PERF-05:** 10/50/100/250 NPC ile entity sorgusu ve NPC update süresi.
- **PERF-07:** Kontrollü fixture'da render sayaçlarının doğruluğu.
- **QA-01:** CI loglarında hedef paketlerin Ruff tarafından tarandığının doğrulanması.
- **QA-02:** Yeni regresyon testlerinin pytest ve Windows/Linux CI'da çalıştırılması.
- **ARCH-01:** Tek hareket davranış sözleşmesi ve ortak test matrisi.

---

## 7. Güçlü yönler ve korunacak kararlar

1. Hareket domain mantığının Pygame UI katmanından ayrılması.
2. Sabit zaman adımlı fizik yaklaşımı.
3. Hareket niyeti ile hareket fiziğinin ayrılması.
4. Çapraz hareket normalizasyonu.
5. Normal/koşma/gizlilik modlarının açık hız profilleri.
6. Statik dünya çarpışması ve dinamik aktör çarpışmasının farklı sorumluluklarda olması.
7. Sürekli çarpışma çözümü, duvar boyunca kayma ve NPC itişi için testlerin bulunması.
8. Kamera smoothing algoritmasının delta-time bağımlı olması.
9. Texture ölçekleme gibi bazı render işlemlerinde önbellek yaklaşımının bulunması.
10. Test ve CI altyapısının Windows/Linux ve birden fazla Python sürümünü kapsaması.
11. `hex_world_lab` tarafındaki snapshot, simülasyon koordinatörü ve mekânsal sorgu tasarımlarının gelecekteki ortak altyapı için incelenmeye değer olması.

Gelecekte NPC'lerin engellerden kaçınması, oyuncu/diğer aktörlerle çarpışınca itilmesi ve yoldaşların takip/bekleme komutları alması planlanıyor. Bu gereksinimler mevcut denetimde uygulanmamıştır. Mevcut ayrıştırılmış hareket niyeti, fizik integrasyonu, çarpışma ve mekânsal indeks kavramları bu hedefler için iyi bir başlangıçtır. Ancak aktör başına hareket politikası ile ortak fizik/çarpışma çözümünün açık sözleşmesi ileride netleştirilmelidir.

---

## 8. Teknik iyileştirme yol haritası

Aşamalar bağımlılıklarına göre düzenlenmiştir. Hiçbiri bu raporun yazılması sırasında uygulanmamıştır.

### Aşama 1 — Ölçüm ve teşhis altyapısı

**Amaç:** Optimizasyon kararlarını gerçek frame-time verisine dayandırmak.

İşler:
- Kare başına frame time ölçümü.
- Ortalama, p50, p95, p99 ve minimum/uzun kare istatistikleri.
- Render, fizik, NPC, kamera ve terrain sürelerini ayrı ölçme.
- Toplam/görünür/çizilen hücre ve aktör sayaçları.
- Pathfinding çağrı sayısı ve süreleri.
- Render stats arayüzünün gerçek verilerle doldurulması.
- Ölçüm ek yükünün düşük tutulması ve debug/benchmark modunda açılıp kapatılabilmesi.

**Çıkış kapısı:** Küçük/orta/büyük harita ve farklı NPC sayılarında tekrar edilebilir baseline raporu.

### Aşama 2 — Hareket fiziği ve akıcılık

**Amaç:** Fizik sözleşmesini kararlı tutarak daha rafine oyuncu kontrolü sağlamak.

İşler:
- Hız vektörünü koruyan ivmelenme ve frenleme.
- Yön değişiminde kontrollü dönüş.
- Normal/koşma/gizlilik modlarının hedef hıza etkisi.
- Sınırlı catch-up adımı ve açık fazla-zaman politikası.
- Çarpışma sonrası hız vektörü tutarlılığı.

**Çıkış kapısı:** Hareket eğrileri, çarpışma regresyonları ve farklı frame bölünmelerinde deterministik fizik testleri.

### Aşama 3 — Klavye ve fare hareketini bütünleştirme

**Amaç:** Farklı giriş yöntemlerinin aynı hareket/fizik altyapısını kullanması.

İşler:
- Klavye hareketinin doğrudan yön niyeti üretmesi.
- Fare navigasyonunun yol üzerindeki yön niyetini üretmesi.
- Yol önbelleği ve doğru geçersizleştirme.
- Hex geçiş eşikleri ve path smoothing.
- Hedefe yaklaşırken yavaşlama.
- Yeni hedef verildiğinde önceki komutun iptali.

**Çıkış kapısı:** Klavye ve fare ile aynı çarpışma kuralları; hedef değişimi ve yol invalidation testleri.

### Aşama 4 — Kamera ve görsel interpolasyon

**Amaç:** Fizik 60 Hz kalırken render frekansında akıcı görsel hareket.

İşler:
- Önceki/sonraki fizik snapshot'ı.
- Render alpha ile oyuncu interpolasyonu.
- Kamera takibinin interpolasyonlu görsel konumla tutarlı çalışması.
- NPC ve oyuncu görsel zamanlamasının ortaklaştırılması.
- Harita sınırlarında interpolasyon davranışının doğrulanması.

**Çıkış kapısı:** 30/60/120/144 FPS'de görsel süreklilik ve aynı fizik sonucu.

### Aşama 5 — Harita ve render performansı

**Amaç:** Harita büyüdükçe maliyetin kontrol edilebilir kalması.

İşler:
- Hücre sıralamasını ve dünya geometrisini önbelleğe alma.
- Harita değişiminde cache invalidation.
- Kamera viewport'una göre aday hücre sorgusu.
- Terrain chunk/surface cache.
- NPC ve nesneler için görünürlük sorgusu.
- Entity snapshot tekrar kullanımının değerlendirilmesi.
- Derinlik sıralamasının yalnızca gerekli olduğunda yenilenmesi.

**Çıkış kapısı:** Büyük harita benchmark'ında p95/p99 ve çizilen/işlenen nesne sayılarının hedefleri karşılaması.

### Aşama 6 — Test kapsamı ve CI güvenilirliği

**Amaç:** Yeni davranışların her değişiklikte korunması.

İşler:
- İvmelenme/frenleme/yön değişimi testleri.
- FPS bağımsızlığı testleri.
- Fare path cache ve hedef iptali testleri.
- Interpolasyon testleri.
- Büyük harita/NPC benchmark veya performans regresyon senaryoları.
- Ruff kapsamına `hex_world_lab` ve ilgili hareket/render paketlerinin alınması.
- Windows/Linux CI'da tüm kontrollerin çalıştırılması.
- Benchmark testlerinin donanım gürültüsüne dayanıklı eşiklerle ayrıştırılması.

**Çıkış kapısı:** Tüm testler ve kalite kontrolleri CI'da başarılı; benchmark sonuçları önceki baseline ile karşılaştırılmış.

---

## 9. Kabul kriterleri

Aşağıdaki değerler önerilen hedeflerdir; mevcut sistemin bunları sağladığı anlamına gelmez.

| Kriter | Önerilen kabul |
|---|---|
| Fizik adımı | 60 Hz |
| Render hedefi | 60 FPS temel hedef |
| 60 FPS kare bütçesi | 16,67 ms |
| p95 frame time | 16,67 ms veya altı hedef |
| p99 frame time | 25 ms veya altı hedef |
| Fizik deterministikliği | Aynı simülasyon girdisi/zamanında eşdeğer sonuç |
| Çapraz hareket | Eksen hareketiyle aynı toplam hız |
| Tuş bırakma | Tanımlı frenleme eğrisi |
| Yön değişimi | Hız vektöründe kontrolsüz sıçrama olmaması |
| Çarpışma | Statik engellerden geçmeme; mevcut itiş/kayma davranışının korunması |
| Fare hareketi | Değişmeyen hedef/yol için gereksiz tekrar path query olmaması |
| Hedef değişimi | Eski hareket yolunun iptal edilmesi |
| Kamera | Oyuncuyla görsel zamanlama uyumu; görünür mikro titreşim olmaması |
| Görünürlük | Kamera dışı hücre/aktörlerin pahalı çizim aşamalarına girmemesi |
| CI | Pytest, Ruff ve headless smoke doğrulamasının hedef dalda başarılı olması |

### Benchmark senaryoları

Harita boyutları:
- 384 hücre
- 1.000 hücre
- 5.000 hücre
- 10.000+ hücre

NPC sayıları:
- 10
- 50
- 100
- 250

Render hızları:
- 30 FPS
- 60 FPS
- 120 FPS
- 144 FPS

Her senaryoda aynı donanım, çözünürlük, kamera hareketi, terrain içeriği ve simülasyon davranışı kullanılmalı. Sonuçlar ortalama FPS ile sınırlı kalmamalı; frame-time p95/p99 ve spike sayısı raporlanmalı.

---

## 10. Context7 dokümantasyon doğrulaması

Context7 üzerinden Pygame Community Edition dokümantasyonu sorgulandı. Kullanılan kütüphane kimliği: `/pygame-community/pygame-ce`.

Doğrulanan noktalar:

1. `pygame.time.Clock.tick(framerate)` son çağrıdan beri geçen milisaniyeyi döndürür ve kare hızını sınırlamak için kullanılabilir.
2. `Clock.get_time()` önceki iki tick arasındaki süreyi milisaniye cinsinden verir.
3. `tick_busy_loop()` daha hassas zamanlama sağlayabilir ancak busy loop nedeniyle daha fazla CPU tüketebilir; varsayılan çözüm olarak önerilmez.
4. `pygame.key.get_pressed()` o anda basılı olan tuşların durumunu okumak içindir; sürekli hareket için event queue'daki tek KEYDOWN olayına göre daha uygun bir durum sorgusudur.
5. Event queue düzenli işlenmelidir; aksi halde pencere/işletim sistemi olayları birikebilir ve uygulama yanıt vermiyor gibi algılanabilir.
6. Olay kuyruğu ve anlık input state farklı ihtiyaçlara hizmet eder: sürekli hareket için state, tek seferlik kritik etkileşimler için event yaklaşımı birlikte kullanılabilir.

Kaynaklar:
- Pygame-ce Clock: https://github.com/pygame-community/pygame-ce/blob/main/docs/reST/ref/time.rst
- Pygame-ce Event: https://github.com/pygame-community/pygame-ce/blob/main/docs/reST/ref/event.rst
- Pygame-ce Keyboard/move tutorial: https://github.com/pygame-community/pygame-ce/blob/main/docs/reST/tutorials/en/move-it.rst
- Pygame-ce Surface: https://pyga.me/docs/ref/surface.html

CI kayıtlarında görülen Pygame-ce sürümü 2.5.8'dir. Proje bağımlılık tanımı `pygame-ce>=2.5` biçiminde alt sınır belirlemektedir; bu nedenle yerel ortamlarda tam sürüm eşitliği garanti edilmez. Sürüm sabitleme kararı ayrı değerlendirilmelidir.

---

## 11. Proje sahibinin onayına sunulan kararlar

1. **Hareket karakteri:** Kontrollü ivmelenme ve yumuşak durma; ancak girişe hızlı tepki veren, gecikmeli hissettirmeyen bir model.
2. **Shift/Alt önceliği:** Alt gizlilik açıkken Shift'in koşma etkisi olmaması; mevcut önceliğin korunması.
3. **Fare navigasyonu:** Kesintisiz yol takibi, yumuşak dönüş ve hedefe yaklaşırken yavaşlama.
4. **Zaman mimarisi:** Fizik 60 Hz, render donanımın izin verdiği hızda; sınırlı catch-up ve render interpolasyonu.
5. **Kanonik hareket sözleşmesi:** Aktif `core/domain/movement` ana sözleşme olarak korunsun; `hex_world_lab` bileşenleri ölçülü biçimde değerlendirilsin.
6. **NPC/yoldaş ortak altyapısı:** Ortak fizik ve çarpışma altyapısı; aktör başına ayrı davranış politikası. Bu gelecek kapsamıdır, mevcut denetim uygulamasına dahil değildir.
7. **Performans hedefleri:** 60 FPS ve p95/p99 eşikleri başlangıç kabul hedefi olarak onaylansın; gerçek donanım baseline'ı alındıktan sonra kesinleştirilsin.

---

## 12. Sonuç ve uygulama kararı

Denetim sonucunda Eldoria'nın hareket altyapısının temelden değiştirilmesi gerektiğine dair kanıt bulunmamıştır. En doğru yaklaşım, mevcut domain/fizik/çarpışma ayrımını koruyup eksik hareket hissini ve ölçülebilir performans sorunlarını aşamalı olarak gidermektir.

**Uygulama için önerilen ilk adım Aşama 1 — Ölçüm ve teşhis altyapısıdır.** Gerçek frame-time verisi elde edilmeden terrain cache, chunk sistemi veya geniş kapsamlı render optimizasyonuna başlanmamalıdır.

Bu raporun eklenmesi dışında denetim sırasında uygulama değişikliği yapılmamıştır. Sonraki çalışma, proje sahibinin onayından sonra ve ayrı bir uygulama planı üzerinden yürütülmelidir.
