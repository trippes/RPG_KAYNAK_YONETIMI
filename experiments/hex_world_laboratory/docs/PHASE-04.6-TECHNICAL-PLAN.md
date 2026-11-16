# Aşama 4.6 — Hareket Kabul Prototipi Teknik Mimari Planı

> **Belge türü:** Onaylı genel planın teknik uygulama sözleşmesi  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Genel plan:** `docs/PHASE-04.6-GENERAL-PLAN.md`  
> **Durum:** TEKNİK PLAN HAZIR — KULLANICI ONAYI BEKLİYOR  
> **Uygulama durumu:** Henüz kod değişikliği yapılmadı.

---

## 1. Teknik amaç ve mevcut durum

Aşama 4.6'nın amacı, 4.1–4.5'te oluşturulmuş hareket ve dünya entegrasyonu bileşenlerini mevcut laboratuvar Pygame uygulama kabuğunda bir araya getirmek ve davranışlarını kabul prototipiyle görünür/doğrulanabilir hâle getirmektir.

Mevcut kod incelemesinde şu gerçekler esas alınmıştır:

- `src/hex_world_lab/app.py` mevcut Pygame pencere döngüsüdür; pencereyi açar, klavye adaptörünü, MovementSystem'i ve DemoTickPump'ı kurar. Şu anda ekranı yalnızca düz renge boyar; dünya veya aktör çizimi yoktur.
- `AppConfig` pencere boyutunu, başlığı, hedef render FPS değerini ve prototip hareket hızını taşır.
- `DemoTickPump` monotonic saatten 60 TPS tick üretir; bir `pump()` çağrısında en fazla 8 tick işler; artan zaman borcunu korur.
- `MovementSystem.step(tick_number, intent)` yalnızca beklenen ardışık tick'i kabul eder ve sabit `1/60` saniyelik hareket adımı uygular.
- `PygameKeyboardAdapter` WASD/ok tuşlarını okur; odak kaybında nötr intent verir.
- `MovementCellTracker.update(WorldPoint)` mevcut `MovementWorldContext` üzerinden axial hücreyi çözer ve önceki hücreyi korur.
- `HexWorld`, `HexMapDefinition`, `HexCellData`, `HexLayout`, `axial_to_world`, `hex_polygon` ve `HexWorldView` gerekli dünya/çizim verisini sağlar.
- Pygame bağımlılığı yalnızca uygulama ve input katmanındadır; movement, geometry ve world çekirdeği Pygame import etmez.

Bu plan, mevcut `app.py` girişini koruyup uygulama sorumluluklarını küçük bir demo orkestratörüne ayırmayı önerir. Yeni bir genel oyun motoru veya ECS oluşturulmayacaktır.

## 2. Sabit mimari kararlar

| Konu | Teknik karar |
|---|---|
| Aktör sayısı | Görsel prototipte tek aktör |
| Harita | Tek, deterministik, belleğe yüklenmiş test haritası |
| Harita geometrisi | Flat-top yönelimli, matematiksel Y yukarı; mevcut HexLayout |
| Harita hücreleri | Axial koordinatlarda sınırlı, deterministik bir hex disk |
| Hex yarıçapı | Prototip yapılandırmasında açıkça belirlenmiş dünya birimi; başlangıç değeri 32.0 |
| Hareket hızı | Mevcut AppConfig sözleşmesi; varsayılan 60 dünya birimi/saniye |
| Tick | Mevcut 60 TPS MovementSystem ve DemoTickPump |
| Tick sınırı | Her kabul edilen tick'te MovementSystem bir kez; ardından tracker bir kez |
| Başlangıç konumu | Haritanın merkez hücresinin axial_to_world merkezi |
| Hücre dışı davranış | Hareket sürer; tracker geometrik axial koordinatı verir, cell_data None olabilir |
| Çizim | Yalnızca Pygame application katmanı; salt okunur |
| Ekran dönüşümü | Prototipe özel basit dünya → pencere dönüşümü; genel kamera sistemi değil |
| Teşhis | State ve TickPumpDiagnostics snapshot'larından türetilir |
| Saat | Yalnızca DemoTickPump monotonic saati |
| Test | Headless unit/integration + gerçek pencerede manuel kontrol |
| Ana oyun | Entegrasyon yok; yalnızca laboratuvar dalı |

Hex yarıçapı 32.0 bir prototip başlangıç değeridir; fiziksel/oyun tasarımı açısından nihai ölçek kararı değildir. Hareket hızı mevcut AppConfig varsayılanından gelir ve yeni bir hız sistemi yaratılmaz.

## 3. Uçtan uca çalışma sırası

### 3.1 Başlatma

1. `LabApplication.run()` Pygame'i başlatır ve mevcut AppConfig boyutlarında pencereyi açar.
2. Yeni `MovementDemo` nesnesi deterministik dünya ve harita verisini oluşturur.
3. Dünya kaydına tek MapId kaydedilir; HexMapDefinition yüklenir.
4. `MovementWorldContext` ve `MovementCellTracker` oluşturulur.
5. Aktörün MovementState'i haritanın merkez hücresinin world-space merkezinde başlatılır.
6. Tracker ilk hücre çözümlemesini yapar; bu işlem konumu değiştirmez.
7. PygameKeyboardAdapter ve DemoTickPump oluşturulur.
8. DemoTickPump.start() ile gerçek-zaman başlangıç anı yakalanır.

### 3.2 Her render karesi

1. Pygame olayları okunur; QUIT ve pencere odak olayları ilgili bileşenlere iletilir.
2. `MovementDemo.pump()`, DemoTickPump'ı bir kez çalıştırır.
3. Pump sıfır veya daha fazla (en fazla 8) simülasyon tick'i çağırabilir.
4. Her tick callback'inde klavye durumu o tick için yeniden okunur.
5. `MovementSystem.step(tick_number, intent)` çağrılır.
6. Başarılı hareket adımının yeni `state.position` değeri `MovementCellTracker.update()` metoduna verilir.
7. Render katmanı son MovementState, son MovementCellResolution ve son TickPumpDiagnostics snapshot'ını okur.
8. Hex hücreleri, aktör işaretçisi ve teşhis paneli çizilir.
9. Ekran sunulur; Pygame Clock yalnızca render FPS sınırlaması/ölçümü için kullanılır, hareket delta zamanı sağlamaz.

Bir tick callback'i başarısız olursa DemoTickPump'ın mevcut başarısız tick/time-debt koruma davranışı korunur. MovementSystem kendi state/tick güncellemesini atomik yapar; tracker da başarısız çözümlemede son başarılı sonucunu korur.

### 3.3 Sorumluluk ayrımı

- `MovementDemo`: Dünya, aktör, klavye, pump ve tracker bileşenlerini birleştiren laboratuvar prototip orkestratörü.
- `LabApplication`: Pygame pencere yaşam döngüsü, olay dağıtımı ve render-frame akışı.
- `MovementDemo.render(surface, render_fps)`: Salt okunur çizim.
- MovementSystem/MovementIntegrator: Fiziksel hareket; world veya Pygame bağımlılığı yok.
- MovementCellTracker/MovementWorldContext: Hareketten sonra mekânsal hücre çözümleme; konum mutasyonu yok.

## 4. Dosya bazında uygulama planı

### 4.1 Yeni üretim dosyası

| Dosya | Sorumluluk |
|---|---|
| `src/hex_world_lab/application/movement_demo.py` | Deterministik demo dünyası/haritası, MovementSystem, MovementCellTracker, PygameKeyboardAdapter ve DemoTickPump orkestrasyonu; tick callback'i; salt okunur render ve diagnostics |

Bu dosya uygulama katmanında kalır ve Pygame kullanabilir. Hareket/geometry/world çekirdeğine yeni Pygame bağımlılığı eklenmez.

### 4.2 Güncellenecek üretim dosyaları

| Dosya | Değişiklik |
|---|---|
| `src/hex_world_lab/app.py` | Mevcut pencere döngüsünü koruyarak MovementDemo kurmak; event/pump/render yaşam döngüsünü orkestre etmek; mevcut main() girişini korumak; mevcut movement_system gözlem özelliğini geriye dönük uyumlu tutmak |
| `src/hex_world_lab/config.py` | Yalnız gerekirse prototip harita/hex görünümü için doğrulanmış sabit ayarları eklemek; varsayılan pencere boyutu, target_fps ve movement_speed davranışını bozmayacak şekilde |

Yeni genel konfigürasyon sistemi kurulmaz. Hex yarıçapı, harita disk yarıçapı, çizim renkleri ve panel yerleşimi gibi prototipe özgü sabitler `movement_demo.py` içinde özel sabitler olarak kalabilir; dışarıdan değiştirilmeleri için kullanıcı ihtiyacı oluşursa ayrıca ele alınır.

### 4.3 Test dosyaları

| Dosya | Test kapsamı |
|---|---|
| `tests/unit/test_movement_demo_world.py` | Demo dünyasının tek kayıtlı/yüklü haritası, deterministik hücre kümesi, layout ve başlangıç hücresi |
| `tests/integration/test_movement_demo_flow.py` | Klavye → tick → MovementSystem → tracker zinciri; hareketten sonra hücre güncellemesi; kesirli konumun korunması |
| `tests/integration/test_movement_demo_render.py` | Headless Pygame Surface üzerinde çizim; render'ın state/tick/tracker değerlerini değiştirmemesi; hücre/aktör/diagnostics çizim yaşam döngüsü |
| `tests/integration/test_movement_demo_fps.py` | Aynı tick başına input dizisiyle 30/60/120 render kareleme hızında aynı tick sayısı ve aynı son MovementState/hücre sonucu |
| `tests/integration/test_movement_demo_lifecycle.py` | LabApplication açılış/kapanış, QUIT, max_frames ve mevcut lifecycle regresyonu |
| `tests/performance/test_movement_demo_benchmark.py` | 1/10/100/1000 actor update + cell resolve benchmark fonksiyonunun çalışması ve ölçüm çıktısı biçimi; süre eşik garantisi yok |

Test klasörlerinin mevcut düzeni tekrar kontrol edilir. `tests/performance/` yoksa oluşturulur. Test adları mevcut testlerle çakışırsa var olan test dosyası gelişigüzel değiştirilmez; isimler teknik uygulama öncesi gerçek dosya ağacına göre uyarlanır.

### 4.4 Benchmark aracı ve dokümantasyon

| Dosya | Sorumluluk |
|---|---|
| `benchmarks/benchmark_movement_demo.py` | 1/10/100/1000 aktör için tekrarlanabilir update + cell resolution ölçümü; ortalama, P95 ve aktör başına süre çıktısı |
| `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md` | Gerçek Pygame penceresinde kullanıcı tarafından uygulanacak kısa görsel kabul listesi |

Benchmark yeni üçüncü taraf bağımlılık gerektirmez; standart `time.perf_counter` kullanır. Benchmark ölçümü test başarısı için sabit milisaniye eşiğine bağlanmaz.

## 5. Deterministik test haritası ve world kurulumu

Demo world factory tek bir açık harita oluşturur:

- `WorldId("movement-demo-world")`
- `MapId("movement-demo-map")`
- Map name: `"Movement Demo Map"`
- `HexOrientation.FLAT_TOP`
- `HexLayout.radius = 32.0`
- `HexLayout.origin = WorldPoint(0.0, 0.0)`
- Hücreler axial merkezli, yarıçapı 4 olan tam hex disk: `max(abs(q), abs(r), abs(q + r)) <= 4`.
- Her hücre deterministik `HexCellData("grass", True, False)` taşır.
- Başlangıç aktörü axial `(0, 0)` hücre merkezindedir.
- Tek harita kayıt edilir ve bir kez yüklenir; auto-load/unload yoktur.

Bu küme 61 hücreden oluşur. Testler hücre sayısını, kimlikleri, kayıt/yükleme durumunu ve başlangıç çözümünü doğrular. Harita üretimi rastgele sayı kullanmaz.

## 6. Görsel gösterim ve koordinat dönüşümü

### 6.1 Dönüşüm

Geometri çekirdeği matematiksel Y yukarı koordinat kullanır. Pygame ekranında Y aşağı olduğundan yalnızca application katmanında dönüşüm yapılır:

- Ekran merkezi mevcut pencere boyutlarından hesaplanır.
- Dünya origin'i ekran merkezine karşılık gelir.
- Ekran X = merkezX + dünyaX.
- Ekran Y = merkezY - dünyaY.
- Bu prototipte zoom/pan/camera transform yoktur.
- Dünya koordinatları çizim öncesi Pygame'in kabul ettiği tam piksel koordinatlarına yuvarlanır; bu yuvarlama yalnız çizim içindir, MovementState.position üzerinde yapılmaz.

### 6.2 Hex çizimi

- Haritanın 61 hücresinin her biri için `hex_polygon(coord, layout)` veya eşdeğer mevcut geometri API'si kullanılır.
- Hücreler Pygame polygon çizim çağrılarıyla gösterilir.
- Aktörün tracker tarafından seçilmiş hücresi farklı bir kenar/vurgu ile işaretlenir.
- Görsel katman `HexWorldView` veya immutable map definition'dan okur; runtime verisini değiştirmez.
- Çizim için ikinci bir hex koordinat matematiği yazılmaz.

### 6.3 Aktör

- Aktör basit daire/işaretçi ile çizilir.
- Konumu doğrudan son `MovementState.position` üzerinden alınır.
- Hücre merkezinden bağımsız hareket görünür.
- Harita hücreleri dışında kalan koordinatlarda aktör konumu değiştirilmeden çizim dönüşümüne verilir; pencere dışına çıkması hareketin durdurulması anlamına gelmez.

### 6.4 Teşhis paneli

Panel şu değerleri salt okunur gösterir:

- WorldId / MapId.
- WorldPoint x/y (yeterli ondalık hassasiyet).
- Velocity x/y ve `math.hypot(vx, vy)`.
- Axial q/r; çözüm yoksa `—`.
- Cell data mevcut/yok.
- Son tamamlanan tick: `total_ticks - 1`; henüz tick yoksa `—`.
- Render FPS (Pygame Clock snapshot).
- Son karede işlenen tick sayısı.
- Bekleyen tam tick sayısı ve toplam time debt.

Tick numarası için MovementSystem ve TickPump'ın mevcut sayaçları karşılaştırılır; bağımsız sayaç oluşturulmaz. Panel metinleri yalnızca mevcut snapshot'lardan biçimlendirilir.

## 7. FPS eşdeğerliği ve deterministik doğrulama

FPS testi gerçek duvar saatine veya uyku çağrısına dayanmayacaktır. Fake monotonic clock ile aynı toplam süreyi farklı render aralıklarına böler:

- 30 FPS: her render adımı 1/30 saniye.
- 60 FPS: her render adımı 1/60 saniye.
- 120 FPS: her render adımı 1/120 saniye.

Her senaryoda aynı başlangıç state'i, aynı map ve aynı simülasyon tick numaralarına ait MovementIntent dizisi kullanılır. Test, toplam 60 tick (1 simülasyon saniyesi) tamamlanınca:

- `MovementSystem.next_tick_number` değerini,
- son WorldPoint ve velocity değerlerini,
- son axial coord ve CellAddress'i,
- TickPump toplam tick ve time debt değerlerini

karşılaştırır. Floating-point karşılaştırmaları mevcut test tolerans yaklaşımıyla yapılır.

Girdi örüntüsü tick numarasına göre sabitlenir (ör. belirli tick aralıklarında doğu, kuzeydoğu ve nötr). Böylece render karelerinde tuş değişim zamanlaması kaynaklı belirsizlik, simülasyon determinism testine karışmaz. Gerçek klavye örnekleme davranışı ayrıca mevcut keyboard integration testleri ve manuel kontrolle doğrulanır.

## 8. Headless Pygame ve yaşam döngüsü

- Test modülleri SDL video/audio dummy ortamını Pygame import edilmeden önce ayarlar; mevcut `test_app_lifecycle.py` yaklaşımıyla tutarlı kalır.
- Render testi gerçek pencere açmadan `pygame.Surface` kullanır.
- `LabApplication.run(max_frames=1)` mevcut otomatik kapanış testini korur.
- QUIT olayı demo tick veya render çağrısını devam ettirmemelidir.
- Pygame `finally` bloğunda her koşulda kapatılır.
- Birden fazla uygulama çalıştırma veya global Pygame state'ini yeniden tasarlama bu aşamanın kapsamı değildir.

## 9. Performans benchmark sözleşmesi

Benchmark aynı yüklü test haritasını ve aynı layout'u paylaşan bağımsız actor state'leri oluşturur. Her actor için ayrı MovementSystem ve MovementCellTracker bulunur. Her benchmark tick'inde:

1. Actor'ın önceden belirlenmiş intent'iyle MovementSystem bir adım ilerler.
2. Yeni WorldPoint, o actor'ın tracker'ına verilir.
3. Ölçüm tüm actor güncellemelerini kapsar.

Senaryolar:
- 1 aktör
- 10 aktör
- 100 aktör
- 1.000 aktör

Raporlanacak değerler:
- Tek batch update için ortalama süre.
- Batch update için P95 süre.
- Aktör başına ortalama süre.
- Tick başına toplam süre.
- Python sürümü, platform, işletim sistemi, işlemci bilgisi erişilebiliyorsa CPU tanımı ve commit SHA.

Benchmark default tekrar sayısı teknik uygulamada belirlenecek; ölçüm süresini makul tutacak, ısınma turu ayrı uygulanacaktır. Sabit performans eşiği veya FPS iddiası yoktur. Benchmark testinin CI'da çalışması fonksiyonelliği ve rapor formatını doğrular; farklı CI makinelerindeki süreler doğrudan karşılaştırılmaz.

## 10. Hata ve sınır davranışları

- Harita context'i oluşturulurken map kayıtlı değilse mevcut `UnknownMapError` davranışı korunur.
- Harita unload edilmişse mevcut `MapNotLoadedError` davranışı korunur.
- Aktör harita hücreleri dışına ilerlerse MovementSystem çalışmaya devam eder.
- Tracker axial koordinatı hesaplar; ilgili cell data yoksa `None` döndürür.
- Tracker başarısız çözümlemede önceki başarılı resolution değerini korur.
- Hücre sınırı eşitliğinde önceki hücre tie-break davranışı değişmez.
- Render başarısızlığı veya yüzey çizim işlemi MovementState'i değiştiremez.
- Tick callback hatasında DemoTickPump'ın mevcut tick/time debt koruma sözleşmesi değiştirilmeyecektir.

## 11. Test matrisi ve kabul kanıtları

| Alan | Test/kanıt | Kabul ölçütü |
|---|---|---|
| Demo world | Unit | Tek world/map, 61 deterministik hücre, map loaded |
| Başlangıç | Unit | Actor axial (0,0) merkezinde; tracker doğru cell |
| Input | Integration | WASD/ok ve focus-loss sözleşmesi korunur |
| Tick | Integration | Her tick'te tek MovementSystem.step ve ardından tracker update |
| Konum | Integration | Kesirli WorldPoint korunur; snap yok |
| Hücre | Integration | Sınır tie-break, hücre geçişi ve cell_data=None davranışı |
| FPS | Integration | 30/60/120 render bölünmesinde aynı 60 tick sonucu |
| Render | Headless | Hex/actor/panel çizilir; simülasyon state'i değişmez |
| Lifecycle | Headless | Açılış, QUIT, max_frames ve pygame.quit |
| Mimari | Regression | Movement/geometry/world modüllerine Pygame import'u eklenmez |
| Benchmark | Performance | 1/10/100/1000 senaryosu ölçülür; ortalama/P95 raporlanır |
| Regression | Full suite | Tüm laboratuvar testleri ve mevcut Stage 2/3/4 testleri geçer |
| CI | GitHub Actions | Laboratuvar CI + Core Quality Linux/Windows başarılı |
| Manual | Checklist | Gerçek pencerede kullanıcı kontrolü; yapılmadıysa açıkça ertelenir |

Mevcut test toplamı için sabit sayı yazılmaz; uygulama öncesi HEAD ve test ağacı yeniden doğrulanır, gerçek pytest sonucu kapanış raporuna işlenir.

## 12. Kapsam dışı

Bu teknik uygulama aşağıdakileri yapmayacaktır:

- Çarpışma, collider, duvar, obstacle veya is_walkable hareket engeli.
- Pathfinding, NPC, çoklu actor gameplay veya ECS.
- Genel kamera, zoom, pan, takip sistemi.
- Nihai sprite, animasyon, y-sort, HUD veya görsel sanat sistemi.
- Çoklu harita geçişi, auto-load/unload, offline progression.
- Hareket state persistence.
- Main veya demo_eldoria entegrasyonu.
- Godot/başka motor geçişi.
- Ağ/multiplayer.
- Yeni üçüncü taraf bağımlılık.
- Ölçüm öncesi optimizasyon veya 60 FPS garantisi.

## 13. Riskler ve önlemler

| Risk | Etki | Önlem |
|---|---|---|
| app.py içine tüm demo kodunun yığılması | Bakım zorluğu | Orkestrasyonu application/movement_demo.py içine ayırmak |
| Demo sınıfının yeni motor soyutlamasına dönüşmesi | Gereksiz karmaşıklık | Tek aktör/tek harita; yalnız gerekli API |
| Render'ın simülasyon state'ini değiştirmesi | Determinism bozulması | Salt okunur render; render öncesi/sonrası state testi |
| Ekran Y ekseninin yanlış çevrilmesi | Haritanın ters görünmesi | Matematiksel Y-up → ekran Y-down dönüşümünü tek yerde tutmak |
| İkinci hex matematiği yazılması | Geometri tutarsızlığı | Mevcut hex_polygon/axial_to_world API'lerini kullanmak |
| 1000 aktör benchmark'ının CI süresini büyütmesi | CI yavaşlaması | Benchmark testinde düşük tekrar; ayrıntılı ölçümü ayrı komut |
| FPS testinde gerçek saat dalgalanması | Kararsız test | Fake clock ve sabit tick-input dizisi |
| Pygame import'unun çekirdeğe sızması | Headless/bağımsızlık kaybı | Var olan mimari import testleri ve yeni regression |
| Görsel kontrolün yerel erişim gerektirmesi | Kabul kanıtı eksikliği | Manuel checklist'i ayrı ve açık kayıt |

## 14. Uygulama sırası ve commit sınırları

Teknik plan onaylandıktan sonra önerilen uygulama sırası:

1. **4.6.1 — Demo world factory ve başlangıç state'i:** yeni MovementDemo iskeleti, deterministic world, başlangıç tracker; unit testler.
2. **4.6.2 — Tick/input orkestrasyonu:** keyboard, pump, movement, tracker zinciri; integration testler.
3. **4.6.3 — Hex ve aktör çizimi:** render dönüşümü ve hex grid; headless surface testleri.
4. **4.6.4 — Diagnostics ve app bağlantısı:** panel, app.py delegasyonu, lifecycle regression.
5. **4.6.5 — FPS/determinism kabulü:** fake-clock 30/60/120 testleri, mimari ve full regression.
6. **4.6.6 — Benchmark ve manuel checklist:** ölçüm aracı, sonuçlar, checklist.
7. **4.6.7 — Kapanış raporu:** CI ve gerçek test kanıtları, açık takip maddeleri, GitHub post-write verification.

Her uygulama paketi hedefli testlerden sonra küçük ve anlaşılır commit ile kaydedilir. Bir paketin tamamlanması sonraki pakete otomatik onay vermez; aşama protokolüne göre kullanıcıya sonuç sunulur ve gerekiyorsa onay istenir.

## 15. Git ve korunan dallar

- Bütün değişiklikler yalnızca `experiment/hex-world-laboratory` dalında yapılır.
- Yazma öncesi branch HEAD ve değiştirilecek dosyaların blob SHA değerleri tekrar doğrulanır.
- Yazma sonrası commit, dosya içeriği ve branch HEAD GitHub üzerinden yeniden okunur.
- `main` ve `demo_eldoria` dallarına yazma, merge, cherry-pick, rebase, reset veya silme yapılmaz.
- Aşama 4.6 tamamlanınca Aşama 4 genel kapanış raporu hazırlanır; Aşama 5 otomatik başlamaz.

## 16. Onay kapısı

Bu teknik plan aşağıdaki uygulama sınırlarını kesinleştirir:

1. Var olan `app.py` korunur; Pygame yaşam döngüsü MovementDemo orkestrasyonuna delege edilir.
2. Demo world tek, deterministik, 61 hücreli flat-top haritadır.
3. Hareket ve tracker sırası her tick'te MovementSystem ardından MovementCellTracker şeklindedir.
4. Görsel çizim mevcut geometri API'lerini kullanır ve state'i değiştirmez.
5. Teşhis paneli mevcut state/diagnostics snapshot'larından veri alır; ikinci tick/time kaynağı oluşturmaz.
6. FPS testi fake clock ve aynı tick-input dizisiyle yapılır.
7. Benchmark 1/10/100/1000 actor için ortalama ve P95 raporlar; sabit performans garantisi yoktur.
8. Mevcut hareket/world/geometry sözleşmeleri değiştirilmez; yeni bağımlılık eklenmez.
9. Yerel manuel görsel kontrol yapılamazsa CI ile eşdeğer kabul edilmez; takip maddesi olarak raporlanır.
10. Kod uygulaması yalnızca kullanıcı bu teknik planı açıkça onayladıktan sonra başlar.

**Mevcut durum: TEKNİK MİMARİ PLAN SUNULDU — KULLANICI ONAYI BEKLENİYOR.**
