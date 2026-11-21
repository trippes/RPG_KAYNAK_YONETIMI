# Eldoria — Aşama 3 Genel Planı
## Klavye ve Fare Hareketinin Bütünleştirilmesi

- **Proje:** Eldoria RPG
- **Depo:** `trippes/RPG_KAYNAK_YONETIMI`
- **Hedef dal:** `experiment/map-cleanup`
- **Aşama:** 3 — Klavye ve fare hareketinin bütünleştirilmesi
- **Durum:** Plan — uygulama yapılmadı
- **Dayanak denetim:** `reports/experiment-map-cleanup-hareket-mimarisi-performans-teknik-denetimi.md`
- **Önceki iş kapanışı:** Aşama 2 NPC algılama/çevre tarama kapanışı, commit `9806120f2ec2665f027cdffcbb73cc1a4a954154`
- **Tarih:** 21 Kasım 2026

---

## 1. Amaç

Klavye ile doğrudan yön hareketi ve fareyle harita üzerinde hedef seçerek yürüme, aynı kanonik oyuncu hareket/fizik/çarpışma hattından çalışmalıdır. Giriş cihazı yalnızca hareket niyeti üretmeli; hız, fizik, çarpışma, konum sahipliği ve dünya hücresi güncellemesi mevcut uygulama/domain katmanlarında kalmalıdır.

Aşama 3'ün ana hedefleri:

1. Klavye ve fare komutlarının tek bir açık öncelik ve iptal sözleşmesine bağlanması.
2. Fare hedefi değişmediği sürece A* yolunun her fizik adımında yeniden hesaplanmasının önlenmesi.
3. Yolun ilerleyişinin, oyuncunun gerçek hücre/konum durumuyla deterministik biçimde izlenmesi.
4. Dinamik doluluk veya statik fizik engeli değiştiğinde geçersiz sonraki adımın kullanılmaması.
5. Hex yolunun hareket niyetine çevrilmesinde gereksiz yön sıçramalarının ve hücre sınırı titreşiminin azaltılması.
6. Klavye ve fare hareketinin aynı hız profili, sabit fizik adımı ve çarpışma çözümünü kullanmasının testlerle kanıtlanması.

Bu belge bir uygulama talimatı/planıdır; kod değişikliği, yeni API veya performans kazanımı gerçekleştiği anlamına gelmez.

## 2. Mevcut durum ve kanıtlanmış bulgular

Denetim ve kaynak incelemesinde doğrulanan ana parçalar:

| Bileşen | Mevcut sorumluluk / durum |
|---|---|
| `game_ui/movement_input.py` | `PygameMovementInput`; WASD/yön tuşları, Shift koşma, Alt gizlilik toggle ve pencere odağı yönetimi |
| `game_ui/input.py` | Olay kuyruğundan fare tıklaması ve klavye eylemlerini `InputState` biçimine çevirme |
| `game_ui/world_rendering/hex_gameplay_view.py` | Altı hex yönü, tıklanan hedef hücre, `click_move_intent()`, görsel hareket ve dünya etkileşimleri |
| `application/continuous_player_movement.py` | `MovementIntent` girdisini ortak integratör, fizik ve runtime commit hattına taşıma |
| `application/gameplay_step_clock.py` | Oyuncu hareketi için 60 Hz sabit adım biriktiricisi |
| `application/hex_world_runtime.py` | Kanonik sürekli konum/hücre sahipliği ve `path_to()` giriş noktası |
| `application/hex_pathfinding.py` | Deterministik axial hex A* araması |
| `application/hex_physics_bridge.py` | Harita statik çarpışma snapshot'ı ve hücreler arası geçiş doğrulaması |
| `application/hex_occupancy.py` | Aktörlerin hücre doluluğu ve hareket engeli kayıtları |

**Önemli kesin bulgu:** `HexGameplayView.click_move_intent()`, hedef hücre aynı kaldığı hâlde her çağrıda `runtime.path_to()` çağırıyor. `GameWindow` bu metodu sabit fizik adımlarının içinde çağırdığı için tek render karesinde birden fazla fizik adımı olduğunda aynı hedef için birden fazla A* sorgusu da oluşabiliyor.

Mevcut `HexPathfinder` axial hex mesafesi kullanan deterministik A* uygulamasıdır. `HexWorldRuntime.path_to()` her çağrıda entity görünümünü, occupancy kaynaklı bloklu hücreleri ve path aramasını hazırlar. Dolayısıyla gereksiz tekrar yalnızca A* maliyeti değildir; runtime doğrulama ve bloklu hücre kümesi üretimi de tekrarlanır.

Mevcut klavye ve fare kontrolleri `HexGameplayView` ve `GameWindow` arasında paylaşılmıştır. Klavye/fare önceliği, komut iptali ve hedef yaşam döngüsü tek bir açık sözleşme olarak henüz belgelenmemiştir.

## 3. Kapsam

### Dahil

- Mevcut klavye ve fare giriş akışının envanteri.
- Tek hareket niyeti birleştirme/öncelik politikası.
- Fare hareket komutunun başlatılması, sürdürülmesi, iptali ve tamamlanması.
- Oyuncu için aktif yolun yeniden kullanılması.
- Yol imlecinin gerçek oyuncu hücresiyle eşleştirilmesi.
- Dinamik doluluk ve statik fizik geçişlerinin güvenli doğrulanması.
- Hex yolunda yön/waypoint yumuşatma için güvenli sınırlar.
- Hedefe yaklaşma davranışının mevcut hareket fiziği sözleşmesiyle entegrasyonunun tasarlanması.
- Path query, cache hit/miss, replan ve iptal sayaçları.
- Pytest, Ruff, headless smoke ve GitHub Actions doğrulaması.
- Önce/sonra karşılaştırmalı, tekrarlanabilir oyuncu click-to-move benchmark'ı.

### Hariç

- NPC kaçınma sisteminin `_escape_path()` aday arama algoritmasını optimize etmek.
- NPC devriye/kaçınma/yoldaş registry taramalarını değiştirmek.
- Yeni bir paralel spatial index kurmak.
- NPC algılama periyodunu veya davranış eşiklerini değiştirmek.
- Sabit zaman adımı/catch-up politikasını yeniden tasarlamak.
- Genel ivmelenme/frenleme fiziğini bu aşamada yeniden yazmak.
- Oyuncu/NPC ortak hareket politikası veya yoldaş AI tasarlamak.
- Kamera interpolasyonu ve büyük harita render optimizasyonları.

**Aşama 2'den devralınan ayrım:** Kapanış raporundaki 66–74 ms p95 pathfinder bulgusu NPC aktif kaçınma profilinden gelmektedir. Bu, oyuncunun fare hedefi için tekrarlanan `path_to()` çağrısından ayrı bir iş yüküdür. Aşama 3 oyuncu click-to-move yol tekrarını ele alır; NPC kaçınma pathfinding optimizasyonu ayrı kapsam ve benchmark gerektirir.

## 4. Uygulama alt aşamaları

### 3.1 — Kaynak envanteri ve davranış sözleşmesi

- GameWindow input okuma sırası, InputMapper, PygameMovementInput ve HexGameplayView ilişkisini uçtan uca çıkar.
- Aynı frame'de klavye, sol tık, sağ tık, NPC/nesne etkileşimi ve harita geçişi geldiğinde mevcut davranışı testlerle kaydet.
- Aktif oyuncu, runtime, map, physics snapshot ve collider yaşam döngüsünü doğrula.
- Mevcut testleri ve eksik senaryoları listele.
- Klavye hareketi, fare hedefi ve etkileşim tıklamalarının birbirini nasıl etkilediğini açıkça tanımla.

**Çıkış kapısı:** Mevcut davranış matrisi ve değiştirilmeyecek sözleşmeler yazılı ve testlerle doğrulanmış olmalı.

### 3.2 — Birleşik hareket niyeti ve komut önceliği

- Klavye niyeti ve fare rota niyeti aynı `MovementIntent`/oyuncu hareket controller hattına verilmeli.
- Hareket komutu önceliği tek yerde belirlenmeli.
- Önerilen politika: aktif klavye yön girdisi fare komutunu derhal iptal eder; yeni geçerli sol tık hedefi mevcut fare komutunu değiştirir; sağ tık bağlam menüsü/etkileşim hareket komutunu iptal eder; pencere odağı kaybı klavye girdisini temizler ve fare komutunun devam edip etmeyeceği oyun politikası olarak açıkça belirlenir.
- NPC/nesne/kapı/harita dışı tıklamalar yanlışlıkla yürüyüş hedefi üretmemeli.
- Shift/Alt modları klavye hareketindeki mevcut anlamını korumalı; fare hareketinde hangi modun geçerli olduğu ayrıca tanımlanmalı. Varsayılan öneri mevcut oyuncu hareket modunu korumaktır; fare komutu kendi başına koşma/gizlilik modu açmamalıdır.

**Çıkış kapısı:** Her input kombinasyonu tek, deterministik bir hareket/etkileşim sonucuna sahip olmalı.

### 3.3 — Click-to-move rota önbelleği ve yaşam döngüsü

- Aynı hedef için her fizik adımında A* çalıştırılması kaldırılmalı.
- Aktif rota; runtime/world kimliği, map kimliği, oyuncu kimliği, hedef hücre ve kullanılan fizik snapshot/harita bağlamıyla ilişkilendirilmeli.
- Rota, bir cursor/waypoint index ile takip edilmeli.
- Oyuncu beklenen rota hücresine ilerlediğinde cursor ilerletilmeli; hareket başka hücreye saparsa rota yeniden değerlendirilmelidir.
- Her sonraki hücre geçişi, o anki dinamik occupancy ve mevcut fizik snapshot üzerinden doğrulanmalıdır.
- Bir sonraki adım artık uygun değilse eski rota körlemesine yürütülmemeli; kontrollü replan yapılmalı veya komut güvenli biçimde sonlandırılmalıdır.
- Yeni hedef, manuel hareket, map değişimi, runtime değişimi, oyuncu/runtime binding kaybı, pause/load/reset ve geçersiz hedef durumlarında rota iptal edilmelidir.
- Hedefe ulaşma, yol bulunamaması ve komut iptali ayrı terminal durumlar olmalıdır.
- Cache yalnızca aynı aktif komutun rotasını tekrar kullanmak içindir; NPC'ler veya başka aktörler arasında genel path cache değildir.

**Çıkış kapısı:** Aynı hedefte gereksiz tekrar path query yok; hedef/konum/engel değişiminde güvenli invalidation var.

### 3.4 — Hex waypoint takibi ve güvenli path smoothing

- Yolun bir sonraki hücre merkezi mevcut continuous movement controller'a yön niyeti olarak aktarılmalı.
- Hex hücre sınırında hedefin bir sonraki hücreye geçmesiyle oluşan yön titreşimi ölçülmeli.
- Smoothing yalnızca yolun statik çarpışma güvenliğini koruyorsa uygulanmalı.
- Birden fazla waypoint'i tek doğrusal segmentle birleştirme ancak aradaki hareket gövdesinin swept collision testi ve hücre geçiş doğrulaması başarılıysa yapılmalı.
- Smoothing, engel/occupancy kontrollerini atlayamaz; A* yolunu veya collision resolver'ı devre dışı bırakamaz.
- İlk uygulama en küçük kapsamlı olmalı: gereksiz ara waypoint azaltımı ve hedef yönünün kararlı seçimi. Büyük ölçekli spline/curved path sistemi bu aşamada önerilmez.

**Çıkış kapısı:** Yol kısaltma açık/kapalı durumlarında hedefe ulaşma ve çarpışma sonuçları eşdeğer; engel köşelerinden kesme yok.

### 3.5 — Hedefe yaklaşma ve durma entegrasyonu

- Hedefe yaklaşırken yavaşlama, denetim raporunda önerilmiş olmakla birlikte mevcut `MovementIntegrator` her adımda hızı doğrudan atamaktadır; ivmelenme/frenleme modeli mevcut değildir.
- Bu nedenle gerçek kademeli yavaşlama, hareket fiziği yol haritasındaki ivmelenme/frenleme sözleşmesi tamamlanmadan sahte bir görsel hız azaltımı olarak uygulanmamalıdır.
- Aşama 3 mimarisi hedefe varış toleransı, son waypoint ve durma koşulunu tanımlamalı; kademeli yaklaşma entegrasyonunu ilgili hareket fiziği bağımlılığına bağlamalıdır.
- Bu bağımlılık tamamlanmadıysa alt aşama 3.5 açıkça bloke/ertelenmiş olarak raporlanmalı; aşama tamamlandı gibi gösterilmemelidir.

**Çıkış kapısı:** Hedefte aşırı geçme, salınım veya hücre çevresinde bitmeyen komut yok; yavaşlama davranışı yalnızca desteklenen fizik sözleşmesiyle uygulanmış.

### 3.6 — Ölçüm, regresyon ve CI

- Path query toplamı, aynı komut içindeki cache hit/miss, replan, invalidation nedeni, rota uzunluğu ve hedefe varış süresi ölçülmeli.
- Sayaçlar varsayılan oyun döngüsünde düşük maliyetli olmalı; ayrıntılı zamanlama debug/benchmark ile sınırlandırılmalı.
- 1, 10 ve 100 hücrelik rota; kısa/uzun hedef; dar geçit; engel köşesi; dinamik işgal; yeni hedef; manuel iptal; map/runtime değişimi senaryoları benchmark/test matrisine alınmalı.
- Pytest davranış ve eşdeğerlik testleri; Ruff hedef paket kontrolü; headless Pygame smoke; Windows/Linux GitHub Actions çalıştırılmalı.
- Donanım bağımlı FPS eşikleri birim testine konmamalı. Performans karşılaştırması aynı runner/ortam ve aynı senaryo ile yapılmalı.

**Çıkış kapısı:** Davranış regresyonu yok, path query azalması sayaçlarla kanıtlı, tüm CI kontrolleri başarılı ve sonuç raporu hazırlanmış.

## 5. Kabul kriterleri

| Alan | Kabul ölçütü |
|---|---|
| Tek hareket hattı | Klavye ve fare aynı controller, integrator, collision ve runtime commit hattından geçer |
| Input önceliği | Eşzamanlı klavye/fare/etkileşim girdilerinin sonucu açık ve deterministiktir |
| Rota cache | Aynı aktif hedefte aynı rota için her fizik adımında A* çağrılmaz |
| Rota ilerlemesi | Cursor oyuncunun gerçek hücre/konum değişimiyle tutarlı ilerler |
| Invalidation | Hedef, map, runtime, oyuncu konumu sapması veya geçiş güvenliği değişince eski rota güvenli biçimde bırakılır |
| Güvenlik | Statik engel ve dinamik occupancy kuralları korunur |
| Determinizm | Aynı başlangıç durumu ve input dizisi aynı rota/sonuç üretir |
| Smoothing | Engel kesme, geçersiz hücre geçişi veya collision bypass oluşmaz |
| Hedefe varış | Tekrarlanabilir varış toleransı ve terminal komut durumu vardır |
| Ölçüm | Path query, cache, replan ve invalidation metrikleri raporlanır |
| Test | İlgili pytest paketleri ve yeni regresyonlar başarılı |
| Kalite | Ruff ve Pygame headless smoke başarılı |
| CI | Hedef dalda Windows/Linux GitHub Actions başarılı |
| Rapor | Önce/sonra karşılaştırması, kalan sınırlamalar ve sonraki işler kayıtlı |

## 6. Riskler ve koruma ilkeleri

1. **Eski rota kullanımı:** Dinamik occupancy değiştiğinde sonraki hücreyi geçmeden önce doğrula; geçersizse replan.
2. **Yanlış cache anahtarı:** Runtime/map/physics bağlamı değişimini açıkça ele al; yalnızca hedef hücreyi anahtar kabul etme.
3. **Oyuncu kendi hareketi nedeniyle cache invalidation:** Her hücre geçişinde bütün rotayı otomatik iptal etme; rota cursor'ı kullan ve yalnızca bir sonraki adımı güncel durumla doğrula.
4. **Smoothing ile duvar kesme:** Geometrik kısaltmayı swept-body collision ve hücre geçiş doğrulaması olmadan yapma.
5. **Klavye/fare yarışması:** Önceliği `GameWindow` ve `HexGameplayView` arasında dağınık if bloklarıyla değil, tek bir komut sözleşmesiyle yönet.
6. **Aşama kapsamının büyümesi:** NPC kaçınma A* maliyeti ve registry optimizasyonunu bu oyuncu kontrol aşamasına karıştırma.
7. **Fizik bağımlılığı:** Gerçek hedef yavaşlamasını henüz bulunmayan ivmelenme/frenleme modelini taklit ederek uygulama.

## 7. Teslimatlar

1. Aşama 3.1 mevcut durum ve input davranış envanteri.
2. Klavye/fare komut önceliği ve iptal sözleşmesi.
3. Click-to-move rota cache/waypoint takip bileşeni veya mevcut view içine en küçük uyumlu çözüm.
4. Rota invalidation ve dinamik sonraki-adım doğrulaması.
5. Güvenli path smoothing kararı ve testleri.
6. Path query/cache/replan metrikleri ve benchmark.
7. Pytest/Ruff/headless smoke/GitHub Actions doğrulaması.
8. Aşama 3 teknik sonuç ve kapanış raporu.

## 8. Teknik karar özeti

Aşama 3'ün önceliği yeni bir navigasyon framework'ü kurmak değil, mevcut `HexPathfinder`, `HexWorldRuntime`, `HexPhysicsSnapshot` ve `ContinuousPlayerMovementController` bileşenlerini açık bir click-to-move komut yaşam döngüsüyle birleştirmektir.

Klavye doğrudan yön niyeti, fare ise geçerli rota üzerindeki bir sonraki yön niyeti üretir. Her ikisi aynı hareket fiziğinden geçer. Rota yeniden kullanımı davranış güvenliğini zedelememeli; her gerçek hücre geçişi öncesinde güncel çarpışma/doluluk şartları korunmalıdır.

**Bu belge yalnızca genel uygulama planıdır. Kaynak kodu, testler, oyun davranışı veya CI yapılandırması değiştirilmemiştir.**
