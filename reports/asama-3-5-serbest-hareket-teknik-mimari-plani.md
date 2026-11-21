# ELDORIA RPG — AŞAMA 3.5
## Serbest Hareketin İvmelenme, Frenleme ve Hedef Takibi Mimarisi
### Ayrıntılı Teknik Mimari Planı ve Uygulama Sözleşmesi

**Proje:** Eldoria RPG — Kaynak Yönetimi Oyunu  
**Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
**Hedef dal:** `experiment/map-cleanup`  
**Tarih:** 21 Kasım 2026  
**Belge türü:** Uygulama öncesi teknik mimari ve entegrasyon planı  
**Kapsam:** Aşama 3.5 — mevcut axial HexWorldRuntime tabanlı sürekli hareket zincirinin geliştirilmesi

---

# 1. Amaç ve kapsam

Bu belgenin amacı, Eldoria'nın mevcut sürekli oyuncu hareket sistemini kontrollü ivmelenme, yavaşlama, hedefe yaklaşırken frenleme, waypoint dönüş kontrolü ve kalıcı hareket durumu ile tamamlamaktır.

Bu çalışma yeni bir harita sistemi veya ikinci bir fizik motoru oluşturmaz. `experiment/map-cleanup` dalında bulunan axial hex dünya modeli, `HexWorldRuntime`, native fizik çözümü, aktör çarpışması ve mevcut click-to-move rota altyapısı üzerinde ilerler.

Aşama 3.5'in temel hedefi şudur:

> Oyuncu hareketi fizik adımları arasında hız sürekliliğine sahip olmalı; hedefe ve dönüş noktalarına kontrollü yaklaşmalı; çarpışma sonrasında yalnızca gerçekten gerçekleşen hareketi kabul etmeli; dünya runtime'ının konum bütünlüğünü bozmamalıdır.

## 1.1 Kapsam dahilinde

- NORMAL, RUNNING ve STEALTH hareket modları.
- Klavye ile sürekli yön hareketi.
- Fare ile click-to-move rota takibi.
- İvmelenme ve yavaşlama.
- Hedefe kalan mesafeye bağlı frenleme.
- Hedefi aşmayan displacement sınırı.
- Dönüş waypoint'lerine kontrollü yaklaşma.
- State ve velocity sürekliliği.
- Statik ve dinamik collision zincirinin korunması.
- NPC itişi ve başarısız commit durumunda rollback.
- 60 Hz fixed-step ve sınırlı catch-up politikası.
- Hareket/rota performans telemetrisi.
- Birim, entegrasyon, regresyon ve manuel testler.

## 1.2 Kapsam dışında

- HexWorldRuntime'ın yeniden yazılması.
- Axial hex koordinat sisteminin değiştirilmesi.
- Eski kare harita veya legacy demo sistemlerinin geri getirilmesi.
- Yeni pathfinding algoritması geliştirilmesi; mevcut rota algoritması yalnızca gerekli waypoint semantiği kadar güncellenecek.
- NPC'ler için bağımsız genel amaçlı AI navigasyon sistemi.
- Yoldaş komutlarının davranış uygulaması.
- Yeni fizik kütüphanesi veya başka harici bağımlılık eklenmesi.
- Oyuncu hareketinin canonical dünya simülasyon tick'ini doğrudan ilerletmesi.

Bu aşamada tasarım, ileride NPC ve yoldaş hareketinin aynı domain hareket çekirdeğinden yararlanmasına engel olmayacak şekilde yapılmalıdır. Ancak Aşama 3.5'te NPC AI veya yoldaş navigasyonu kapsam genişletmesi yapılmayacaktır.

---

# 2. Mevcut mimarinin doğrulanmış başlangıç noktası

Aşağıdaki dosyalar `experiment/map-cleanup` dalında incelenen mevcut mimarinin temel parçalarıdır.

| Dosya | Mevcut sorumluluk |
|---|---|
| `core/domain/movement/integrator.py` | Saf hareket adımı hesabı |
| `core/domain/movement/state.py` | Immutable hareket durumu |
| `core/domain/movement/intent.py` | Yön ve hareket modu |
| `core/domain/movement/config.py` | Hız ve mod çarpanları |
| `core/domain/movement/mode.py` | NORMAL, RUNNING, STEALTH |
| `core/domain/physics/vector2.py` | Native 2D vektör matematiği |
| `application/continuous_player_movement.py` | Oyuncu hareket adımı, collision ve runtime commit |
| `application/click_move_route.py` | Click-to-move rota ve waypoint takibi |
| `application/hex_physics_bridge.py` | Hex haritadan native fizik snapshot'ı |
| `application/dynamic_actor_collision.py` | Dinamik aktör collision/itiş işlemleri |
| `application/hex_actor_binding.py` | Aktör ve hex runtime bağlantısı |
| `application/hex_world_runtime.py` | Authoritative dünya konumu, occupancy ve spatial index |
| `game_ui/game_window.py` | Fixed-step döngüsü ve gameplay orkestrasyonu |
| `game_ui/world_rendering/hex_gameplay_view.py` | Dünya input'u, click hedefi ve görsel sunum |
| `game_ui/movement_input.py` | Klavye hareket girdisi |
| `application/performance_monitor.py` | Opt-in performans ölçümü |
| `content/demo_eldoria/gameplay_rules.json` | Demo oyun kuralları ve içerik konfigürasyonu |

## 2.1 Mevcut domain hareket davranışı

Mevcut `MovementIntegrator.step(state, intent, delta_seconds)`:

- Delta süresini doğrular.
- Hareket moduna göre azami hızı seçer.
- Hareket varsa normalize edilmiş yön ile sabit hızdan displacement üretir.
- Hareket yoksa velocity değerini sıfırlar.
- Önceki state velocity değerini ivmelenme hesabında kullanmaz.

Dolayısıyla mevcut integrator sabit hızlıdır. State içinde velocity alanının bulunması, tek başına ivmelenme veya frenleme olduğu anlamına gelmez.

## 2.2 Mevcut controller yaşam döngüsü sorunu

İncelenen mevcut zincirde:

- Controller step başında yeni `MovementState(start)` oluşturur.
- Collision sonrasında gerçekleşen displacement üzerinden velocity hesaplanır.
- Bu velocity sonraki fizik adımına kalıcı şekilde taşınmaz.
- `GameWindow` hareket ilerletme akışında controller'ı render karesi başına yeniden oluşturur.

Bu nedenle ilk çözülmesi gereken konu hareket algoritmasına ivme eklemek değil, hareket state'inin doğru yaşam döngüsünü kurmaktır.

## 2.3 Mevcut click-to-move davranışı

- `ClickMoveRouteController` hedef ve rota durumunu saklar.
- `ARRIVAL_TOLERANCE = 0.5` hedefe varış kontrolünde kullanılır.
- Rota smoothing, güvenli swept collision kontrolüyle düz hat üzerindeki bazı collinear waypoint'leri birleştirebilir.
- Dönüş waypoint'leri smoothing ile atlanmaz.
- Rota cursor ilerlemesinde oyuncunun mevcut hücresi önemli rol oynar.

Hücreye geçiş ile waypoint dünya koordinatına fiziksel olarak varış aynı olay değildir. Frenleme ve dönüş davranışında bu fark açıkça ele alınmalıdır.

## 2.4 Mevcut collision ve runtime sırası

Korunacak hareket zinciri:

1. Hareket önerisi.
2. Statik swept collision çözümü.
3. Dinamik aktör collision ve NPC itişi.
4. Oyuncu konumunun `HexWorldRuntime` üzerinden commit edilmesi.
5. Kabul edilen konum ve gerçek velocity state'inin güncellenmesi.

Runtime konum, occupancy ve spatial index'i birlikte yönetir. `set_continuous_position` güncellemesi bu bütünlüğün parçasıdır. Runtime commit atlanamaz.

NPC itişinin geçici uygulanması ve oyuncu commit'i başarısız olduğunda rollback edilmesi mevcut davranıştır; yeni sistem bu garantiyi korumalıdır.

## 2.5 Fixed-step ve telemetri başlangıç durumu

- Fixed-step accumulator 1/60 saniyelik adımlar kullanır.
- Pause sırasında birikmiş zamanın temizlenmesi mevcut davranıştır.
- Uzun render gecikmesinde üretilebilecek alt adım sayısına açık üst sınır bulunmadığı tespit edilmiştir.
- `ClickMoveRouteController` kendi rota metriklerini üretir.
- `HexGameplayView` içindeki bazı path-query sayaçlarının artırıldığı bir nokta kaynak taramasında bulunamamıştır; gerçek ölçüm hattı uygulama sırasında tekrar izlenmelidir.

---

# 3. Mimari ilkeler ve değiştirilemez kurallar

1. `MovementIntegrator` saf domain hesaplama katmanı olarak kalır.
2. Domain hareket kodu Pygame, Clock, render, input cihazı, route controller veya `HexWorldRuntime` bağımlılığı almaz.
3. Dünya konumunun tek yetkili sahibi `HexWorldRuntime` olmaya devam eder.
4. Hareket state'i yalnızca runtime tarafından kabul edilmiş konumla eşitlenir.
5. Collision sırası: statik collision → dinamik aktör collision → runtime commit.
6. Click-to-move hedef mesafesi `MovementIntent.direction.length` üzerinden türetilmez.
7. Klavye ve click-to-move aynı hareket domain çekirdeğini kullanabilir; hedef metadata'sı açık ve opsiyoneldir.
8. Hedefe snap, teleport veya doğrudan konum eşitlemesi yapılmaz.
9. Collision çözümlemesinin uyguladığı gerçek displacement, bir sonraki state velocity hesabının temelidir.
10. Rota yönetimi ile fizik entegrasyonu birbirinin sorumluluğunu üstlenmez.
11. Mevcut axial hex dünya modeli ve occupancy/spatial index sözleşmesi korunur.
12. Yeni harici dependency eklenmez.
13. Çalışma yalnızca `experiment/map-cleanup` dalında yapılır. Başka dala geçilmez, yeni dal oluşturulmaz.
14. Kullanıcı değişiklikleri incelenmeden dosya silinmez, üzerine yazılmaz veya geri alınmaz.

---

# 4. Hedef mimari ve veri akışı

## 4.1 Katmanlar

**Input katmanı**
- Klavye tuş durumunu ve hareket modunu üretir.
- Click-to-move hedefi için UI olayını route controller'a iletir.
- Fiziksel konum veya velocity hesaplamaz.

**Rota katmanı**
- Rota, hedef ve sıradaki anlamlı waypoint'i belirler.
- Hedef/waypoint dünya koordinatını uygulama katmanına sunar.
- Hız, ivme veya collision çözmez.

**Domain hareket katmanı**
- Mevcut state, intent, config, opsiyonel hedef ve delta time girdilerinden hareket önerisi üretir.
- Saf matematik ve doğrulama yapar.
- Runtime'a yazmaz.

**Fizik/çarpışma katmanı**
- Önerilen displacement'ı statik ve dinamik engellere göre çözer.
- Gerçekte uygulanabilen displacement'ı döndürür.
- Dünya konumunu kendisi commit etmez.

**Runtime katmanı**
- Commit işlemiyle authoritative konum, occupancy ve spatial index'i tutarlı günceller.
- Başarılı veya başarısız commit sonucunu bildirir.

**Orkestrasyon katmanı**
- `GameWindow` sabit zaman adımlarını ve input/route/controller bağlantısını yönetir.
- Hareket controller'ının oturum boyunca korunmasını sağlar.
- Render katmanına algoritmik sorumluluk yüklemez.

## 4.2 Veri akışı

```text
Keyboard Input ───────┐
                      ├──> MovementIntent ─────────┐
Click Route ─> Target ┘                            │
                                                   v
Persistent MovementState ─────────────────> MovementIntegrator
MovementConfig ────────────────────────────>        │
Fixed delta time ──────────────────────────>        v
                                             Proposed Movement
                                                   │
                                                   v
                                           Static Collision
                                                   │
                                                   v
                                         Dynamic Actor Collision
                                                   │
                                                   v
                                            Runtime Commit
                                                   │
                                      ┌────────────┴───────────┐
                                      v                        v
                                Commit success            Commit failure
                                      │                        │
                                      v                        v
                           Accepted position/state      Rollback/reconcile
                                      │
                                      v
                              Next fixed-step update
```

## 4.3 Önerilen domain arayüzü

Mevcut çağrıların geriye uyumluluğu gözetilerek hedef bilgisi intent'e zorunlu alan olarak eklenmemelidir.

Önerilen şekil:

```python
result = MovementIntegrator.step(
    state,
    intent,
    delta_seconds,
    target=movement_target,  # optional
)
```

Bu imza bir tasarım hedefidir; uygulamadan önce mevcut integrator dönüş tipi ve çağrı noktalarıyla uyumlu hale getirilmelidir. Mevcut positional çağrılar bozulmamalı; yeni argüman keyword-only ve opsiyonel olmalıdır.

---

# 5. Domain veri sözleşmeleri

## 5.1 MovementIntent

Mevcut `MovementIntent` temel girdi sözleşmesi olarak korunur.

| Alan | Tür | Anlam |
|---|---|---|
| `direction` | `Vector2` | İstenen hareket yönü |
| `mode` | `MovementMode` | NORMAL, RUNNING veya STEALTH |
| `is_moving` | `bool` | Yön vektörünün sıfırdan farklı olması |

Kurallar:
- Yön vektörü normalize edilerek kullanılır.
- Diyagonal girişin hızı eksenel girişten fazla olamaz.
- Sıfır yön, oyuncunun hareket isteği olmadığını ifade eder; mevcut velocity'nin aynı adımda zorla sıfırlanması anlamına gelmez. Yavaşlama davranışı integrator tarafından hesaplanır.
- Klavye yön vektörünün büyüklüğü hedef mesafesi olarak yorumlanmaz.

## 5.2 MovementTarget

Yeni bir immutable value object önerilir:

**Dosya:** `core/domain/movement/target.py`

| Alan | Tür | Kural |
|---|---|---|
| `position` | `WorldPoint` | Sonlu dünya koordinatı |
| `arrival_tolerance` | `float` | Sonlu ve negatif olmayan mesafe |

Sorumluluk:
- Hedefin fiziksel dünya koordinatını tanımlar.
- Hedefe varış toleransını tanımlar.
- Kendi başına rota, actor veya runtime referansı taşımaz.

Hedef mesafesi her fizik adımında güncel kabul edilmiş konumdan hesaplanır. Önceki adımdan kalmış mesafe değeri kullanılmaz.

Click-to-move rotasında frenleme hedefi, her zaman nihai hedef olmak zorunda değildir. Dönüş içeren rotalarda sıradaki anlamlı dönüş waypoint'i frenleme hedefi olabilir. Collinear smoothing ile birleştirilen ara waypoint'ler gereksiz fren hedefi haline getirilmemelidir.

## 5.3 MovementState

Mevcut immutable state korunur; gerekmedikçe alan sayısı artırılmaz.

| Alan | Tür | Anlam |
|---|---|---|
| `position` | `WorldPoint` | Son kabul edilmiş konum |
| `velocity` | `Vector2` | Son kabul edilmiş gerçek hız |
| `mode` | `MovementMode` | Son kabul edilmiş hareket modu |

State'in önerilen konumu değil, runtime tarafından kabul edilen konumu temsil etmesi zorunludur.

## 5.4 MovementConfig

**Dosya:** `core/domain/movement/config.py`

Mevcut parametreler korunur:
- `max_speed`
- `running_speed_multiplier`
- `stealth_speed_multiplier`

Eklenecek parametreler:
- `acceleration`: istenen yöne doğru hız değişiminin üst sınırı.
- `deceleration`: hareket girdisi kesildiğinde hız azaltma oranı.
- `braking_deceleration`: hedefe yaklaşırken hız azaltma oranı.

Kurallar:
- Bütün sayısal değerler finite ve non-negative olmalıdır.
- `bool`, sayısal değer olarak kabul edilmemelidir.
- Mevcut config kurucularının positional kullanımını kırmamak için yeni alanlar geriye uyumlu varsayılanlarla eklenmelidir.
- Mod hız çarpanları mevcut anlamını korumalıdır.
- İvme parametrelerinin mod çarpanlarıyla nasıl ölçekleneceği tek yerde tanımlanmalı; controller ve integrator ayrı yorumlar üretmemelidir.

Başlangıç tuning değerleri (test fixture ve ilk oyun içi ayar için öneri; kesin denge kararı değildir):

| Parametre | Başlangıç değeri |
|---|---:|
| Running multiplier | 1.5 |
| Stealth multiplier | 0.5 |
| Acceleration | 180 world units/s² |
| Deceleration | 240 world units/s² |
| Braking deceleration | 360 world units/s² |

Bu değerler gerçek oyun hissi testinden sonra ayarlanabilir. Birim: world units ve saniye.

---

# 6. MovementIntegrator algoritması

## 6.1 Girdi ve çıktı

Girdiler:
- Son kabul edilmiş `MovementState`.
- Güncel `MovementIntent`.
- Pozitif veya sıfır finite `delta_seconds`.
- Opsiyonel `MovementTarget`.
- `MovementConfig`.

Çıktı:
- Domain tarafından önerilen yeni state veya eşdeğer movement proposal.
- Önerilen displacement.
- Hedefe varış/limit bilgisi gerekiyorsa açık sonuç metadata'sı.

Integrator runtime commit sonucu hakkında karar vermez.

## 6.2 Hız hedefi

Modun izin verdiği azami hız:

```text
mode_max_speed = config.max_speed * mode_multiplier
```

Hareket yönü normalize edilir. İstenen hız vektörü bu yön ve mod azami hızından oluşturulur.

## 6.3 İvmelenme ve yavaşlama

Hız değişimi delta time ile sınırlanmalıdır. Bir adımda hızın sınırsız sıçramasına izin verilmez.

Hareket girdisi mevcutsa:
- İstenen velocity hesaplanır.
- Mevcut velocity ile istenen velocity arasındaki fark değerlendirilir.
- Hız değişimi `acceleration * delta_seconds` sınırını aşmaz.

Hareket girdisi yoksa:
- Velocity sıfıra anında eşitlenmez.
- Hız `deceleration * delta_seconds` sınırında azaltılır.
- Hız sıfıra yeterince yaklaştığında sayısal artık temizlenir.

Yön değişiminde mevcut velocity'nin yeni yöne bir anda döndürülmesine izin verilmez. Vektörel hız değişimi ivme sınırıyla kontrol edilir. Bu, ani yön değişiminde fiziksel olarak tutarlı bir yavaşlama/dönüş sağlar.

## 6.4 Hedefe frenleme

Hedefe kalan mesafe `d`, frenleme ivmesi `a) olmak üzere teorik frenleme hızı:

```text
braking_speed = sqrt(2 * a * d)
allowed_speed = min(mode_max_speed, braking_speed)
```

Bu değer hız hedefini sınırlamak için kullanılır; tek başına displacement garantisi değildir.

Hedefin gerisinde kalmayı garanti eden ikinci kontrol:
- Önerilen displacement büyüklüğü kalan mesafe ile karşılaştırılır.
- Displacement hedefi aşacaksa güvenli sınıra düşürülür.
- Hedef toleransı içinde varış kabul edilir.
- Hedefe snap yapılmaz; konum mevcut fizik çözümü ve runtime commit yolundan geçer.

Sayısal tolerans:
- `arrival_tolerance` ile displacement epsilon'u uyumlu olmalıdır.
- Sıfır veya çok küçük hedef mesafelerinde sıfıra bölme ve yön kararsızlığı önlenmelidir.

## 6.5 Hedef değişimi

Yeni hedef geldiğinde:
- Önceki hedefe ait kalan mesafe ve frenleme hesabı yeniden kullanılmaz.
- Mevcut kabul edilmiş velocity korunur.
- Yeni hedefe göre yön ve frenleme hedefi hesaplanır.
- Eski hedefe yönelik yapay snap veya velocity sıfırlaması yapılmaz.

## 6.6 Delta time ve deterministik davranış

- Domain hesapları verilen delta time ile çalışır.
- Negatif, NaN veya sonsuz delta time reddedilir.
- Sıfır delta time hareket konumunu değiştirmez.
- Aynı başlangıç state'i, intent, config ve delta time aynı domain sonucunu üretmelidir.
- Clock veya frame ölçümü integrator içine eklenmez.

---

# 7. Hareket state'inin yaşam döngüsü

## 7.1 Sahiplik

Hareket state'i oyun oturumu/oyuncu hareket controller'ı kapsamında kalıcı olmalıdır.

`GameWindow` her render karesinde yeni controller oluşturmamalıdır. Controller veya eşdeğer session-scoped state sahibi, gameplay oturumu boyunca yaşamalıdır.

## 7.2 Başlangıç ve eşitleme

Controller ilk oluşturulduğunda:
- Actor'ın authoritative runtime konumu okunur.
- Başlangıç velocity'si sıfır kabul edilir.
- Movement mode varsayılanı mevcut oyun kuralıyla eşitlenir.
- İlgili runtime, map ve physics snapshot kimliği izlenir.

Harita/actor/runtime değişiminde:
- Eski state yeni haritaya taşınmaz.
- Yeni authoritative konumdan state yeniden kurulur.
- Eski click route iptal edilir veya yeniden planlanır.

## 7.3 Başarılı commit

Başarılı runtime commit sonrasında:
- State position runtime'ın kabul ettiği konumla eşitlenir.
- Velocity, collision sonrasında gerçekten uygulanan displacement / delta time üzerinden hesaplanır.
- Mode güncel input ile tutarlı hale getirilir.

## 7.4 Başarısız commit

Başarısız commit durumunda:
- Authoritative oyuncu konumu değişmemiş olmalıdır.
- Geçici NPC itişleri mevcut rollback sözleşmesine göre geri alınır.
- Bir sonraki adıma başarısız proposal velocity'si taşınmaz.
- Güvenli varsayılan olarak velocity sıfırlanır veya yalnızca doğrulanmış gerçekleşmiş displacement'tan yeniden türetilir.
- Occupancy ve spatial index tutarlılığı test edilir.

## 7.5 Pause/resume

- Pause sırasında hareket accumulator'ı temizlenir.
- Pause süresince oyuncu hareketi ilerlemez.
- Resume ilk adımında geçmiş gerçek zaman birikmiş delta gibi uygulanmaz.
- Input focus kaybı mevcut input temizleme davranışını korur.

---

# 8. Click-to-move ve waypoint mimarisi

## 8.1 Sorumluluk ayrımı

`ClickMoveRouteController`:
- Rota oluşturur ve geçerliliğini izler.
- Sıradaki hedef/waypoint'i seçer.
- Rota sapması veya blocked edge durumunda replan yapar.
- Smoothing için mevcut swept collision kontrollerini korur.
- Hedef tamamlandığında route durumunu kapatır.

`MovementIntegrator`:
- Kendisine verilen hedefe göre frenleme ve displacement hesaplar.
- Route cursor veya path query yönetmez.

`ContinuousPlayerMovementController`:
- Route controller'ın sunduğu hedefi domain integrator'a aktarır.
- Collision ve commit zincirini yönetir.

## 8.2 Waypoint ilerlemesi

Hücre değişimi tek başına waypoint varışı kabul edilmemelidir.

Waypoint ilerlemesi için:
- Waypoint'in dünya koordinatı belirlenir.
- Oyuncunun kabul edilmiş fiziksel konumu ile waypoint arasındaki mesafe hesaplanır.
- Varış toleransı kontrol edilir.
- Yalnızca anlamlı waypoint'e ulaşıldığında cursor ilerletilir.

Collinear ve güvenli biçimde birleştirilmiş ara waypoint'ler ayrı fren noktası olmamalıdır.

Dönüş waypoint'leri:
- Smoothing ile atlanmamalıdır.
- Dönüşten önce frenleme hedefi olarak kullanılmalıdır.
- Waypoint'e varıştan sonra yeni segment yönü etkinleştirilmelidir.
- Dönüşte ani yön sıçraması ve hücre değişimine bağlı erken rota kırılması engellenmelidir.

## 8.3 Nihai hedefe varış

- Nihai hedefin `WorldPoint` koordinatı kullanılır.
- Hedef mesafesi her adımda güncellenir.
- `ARRIVAL_TOLERANCE` değeri mevcut 0.5 davranışıyla uyumlu tutulur; değişiklik yapılacaksa test ve gerekçe eklenir.
- Varışta route tamamlanır, hedef metadata'sı temizlenir ve kalan velocity güvenli şekilde sıfıra indirilir.
- Oyuncu konumu hedef merkezine zorla eşitlenmez.

## 8.4 Klavye önceliği ve hedef iptali

Mevcut manuel klavye hareketinin click-to-move hedefini iptal etme davranışı korunur.

- Klavye girdisi başladığında aktif click route temizlenir.
- Klavye girdisi kesildiğinde eski click hedefi kendiliğinden yeniden etkinleşmez.
- Yeni fare hedefi eski hedefin yerini açıkça alır.
- Hedef yokken click-to-move frenleme kısıtı uygulanmaz.

---

# 9. Collision, NPC itişi ve runtime commit sözleşmesi

## 9.1 Değiştirilmeyecek işlem sırası

```text
Movement proposal
      |
      v
Static swept collision resolution
      |
      v
Dynamic actor collision / NPC push
      |
      v
HexWorldRuntime commit
      |
      v
Accepted MovementState
```

## 9.2 Velocity'nin gerçek hareketten hesaplanması

Önerilen displacement collision çözümünden sonra değişebilir:
- Tam uygulanabilir.
- Duvar boyunca kaydırılabilir.
- Kısmen engellenebilir.
- Tamamen engellenebilir.

Bu nedenle bir sonraki velocity, integrator'ın ilk önerdiği velocity olarak kabul edilmemelidir.

```text
actual_velocity = actual_committed_displacement / delta_seconds
```

Sıfır delta time için bölme yapılmaz. Runtime commit başarısızsa başarısız öneri displacement'ı gerçek hareket kabul edilmez.

## 9.3 NPC push ve rollback

- NPC push mevcut geçici güncelleme yaklaşımını korur.
- Oyuncu commit başarısız olursa NPC eski authoritative konumuna döndürülür.
- Rollback sonrasında NPC occupancy ve spatial index doğrulanır.
- Oyuncu ve NPC aynı adımda tutarsız pozisyonlarda bırakılamaz.

## 9.4 Runtime doğrulamaları

Her entegrasyon testinde:
- Runtime entity position.
- Continuous position.
- Occupancy kaydı.
- Spatial index sorgusu.

birbirleriyle tutarlı olmalıdır.

---

# 10. Fixed-step ve zaman yönetimi

## 10.1 Zaman standardı

- Fixed step: `1 / 60` saniye.
- Render frame süresi ile fizik adımı birbirinden ayrıdır.
- Hareket domain'i yalnızca fixed delta time alır.

## 10.2 Catch-up sınırı

Uzun render gecikmesinde sınırsız sayıda fizik adımı tek karede çalıştırılmamalıdır.

İlk uygulama hedefi:
- `max_substeps = 8`.
- 60 Hz için bir karede en fazla yaklaşık 133.3 ms simülasyon işi.
- Limit aşımında accumulator politikası açıkça tanımlanmalı; aşırı gecikme sessizce sonsuz catch-up döngüsüne dönüşmemelidir.

Politika seçimi:
- Gerçek zamanlı oyuncu kontrolü açısından bir karede aşırı simülasyon çalıştırmamak önceliklidir.
- Atılan/ertelenen süre telemetride gözlemlenebilir olmalıdır.
- Pause/resume accumulator sıfırlama davranışı korunmalıdır.
- Fixed-step testleri accumulator'ın gerçekte hangi süreyi tuttuğunu/attığını açıkça doğrulamalıdır.

## 10.3 Zaman testleri

- 60 Hz sabit karelerde beklenen hareket.
- Değişken render delta sürelerinde eşdeğer fixed-step sonucu.
- 100–250 ms frame stall.
- Çok büyük frame stall.
- Pause ve resume.
- Sıfır delta ve geçersiz delta.
- Maksimum substep sınırı.

---

# 11. Performans ve gözlemlenebilirlik

## 11.1 Ölçüm hedefleri

Mevcut `PerformanceMonitor` opt-in davranışı korunur. Yeni ölçümler en az şu alanları kapsamalıdır:

- Movement integrator süresi.
- Static collision çözüm süresi.
- Dynamic actor collision süresi.
- Runtime commit süresi.
- Click path planning süresi.
- Route update süresi.
- Path query sayısı.
- Route cache hit/miss.
- Replan ve invalidation sayısı.
- Blocked step sayısı.
- Arrival ve failure sayısı.
- Fixed-step substep sayısı ve limit aşımı sayısı.

## 11.2 Ölçüm kuralları

- Ölçüm kapalıyken yüksek maliyetli profiling yapılmaz.
- Sayaçlar gerçek olaylarda artırılır; yalnızca render öncesi sıfırlanan fakat hiç güncellenmeyen sayaçlar bırakılmaz.
- Var olan route metrics snapshot tek doğruluk kaynağı olarak kullanılmalı; aynı metrik farklı katmanlarda farklı anlamlarla hesaplanmamalıdır.
- p50/p95/p99 gibi mevcut rolling-window istatistikleriyle uyum korunur.

## 11.3 Performans kabulü

Önce mevcut baseline ölçülür. Sonra aynı harita, aktör sayısı, rota ve donanım koşulunda karşılaştırma yapılır.

Aşama 3.5:
- Normal 60 Hz senaryosunda gereksiz catch-up üretmemeli.
- Hareket state'i için render-frame başına controller yaratmamalı.
- Telemetri kapalıyken belirgin ek maliyet getirmemeli.
- Route metrics ile performans monitor arasında ölçülebilir veri akışı sağlamalı.

Donanım ve test ortamı belirtilmeden mutlak FPS garantisi verilmez.

---

# 12. Dosya bazında değişiklik planı

Aşağıdaki liste beklenen değişiklik alanıdır. Her dosyada uygulamadan önce hedef daldaki güncel içerik ve çağrı noktaları tekrar doğrulanmalıdır.

| Dosya | Beklenen işlem | Öncelik |
|---|---|---|
| `core/domain/movement/config.py` | Acceleration/deceleration/braking config alanları ve doğrulama | P0 |
| `core/domain/movement/target.py` | Yeni immutable MovementTarget value object | P0 |
| `core/domain/movement/state.py` | Kabul edilmiş state semantiğini netleştirme; gerekmedikçe alan eklememe | P0 |
| `core/domain/movement/integrator.py` | İvme, frenleme, hedef displacement cap | P0 |
| `core/domain/movement/intent.py` | Mevcut intent anlamını koruma; gerekirse dokümantasyon | P1 |
| `core/domain/movement/__init__.py` | Yeni public domain tipinin export edilmesi | P1 |
| `application/continuous_player_movement.py` | Kalıcı state, collision sonrası velocity ve commit reconciliation | P0 |
| `game_ui/game_window.py` | Session-scoped controller ve fixed-step orkestrasyonu | P0 |
| `application/click_move_route.py` | WorldPoint waypoint/goal sunumu ve ilerleme semantiği | P0 |
| `game_ui/world_rendering/hex_gameplay_view.py` | Hedefin controller'a taşınması; input/route sınırlarının korunması | P1 |
| `application/fixed_step_accumulator.py` | Maksimum substep ve gecikme politikası | P1 |
| `application/performance_monitor.py` | Hareket/rota ölçümlerinin kaydı | P2 |
| `content/demo_eldoria/gameplay_rules.json` | Gerekliyse demo movement profile tanımlama | P1 |

İnceleme sırasında aşağıdaki dosyalar değişiklik hedefi değil, korunacak entegrasyon sınırıdır:
- `application/hex_world_runtime.py`
- `application/hex_physics_bridge.py`
- `application/dynamic_actor_collision.py`
- `application/hex_actor_binding.py`

Bu dosyalarda değişiklik zorunlu hale gelirse kapsam ve gerekçe ayrıca raporlanmalı; mevcut runtime/physics sözleşmesi korunmalıdır.

## 12.1 Demo movement profile

İncelenen `content/demo_eldoria/gameplay_rules.json` içinde movement profile bulunmadığı ve `GameWindow` tarafında config eşleşmesi yoksa hareketin etkinleşmediği görülmüştür.

Bu durum algoritma eksikliğinden ayrıdır. Aşama 3.5 manuel oyun testinde kullanılacak demo içeriğinde oyuncu actor'ı için açık ve doğrulanmış movement profile bulunmalıdır. Mevcut content schema buna izin vermiyorsa önce loader ve schema sözleşmesi incelenmeli; rastgele JSON alanı eklenmemelidir.

---

# 13. Test mimarisi ve kabul kriterleri

## 13.1 Domain birim testleri

**Config**
- Negatif, bool, NaN ve sonsuz değer reddi.
- Sıfır ivme/yavaşlama davranışı.
- Mevcut config kurucu uyumluluğu.

**Integrator**
- NORMAL/RUNNING/STEALTH azami hızları.
- Yatay/dikey/diyagonal normalizasyon.
- İvmelenme sınırı.
- Input kesilince yavaşlama.
- Yön değişiminde hız vektörü geçişi.
- Hedefe frenleme formülü.
- Hedefi aşmayan displacement.
- Sıfır delta.
- Geçersiz delta.
- Hedefin tolerance içinde olması.
- Uzak hedefte azami hıza çıkma.

**MovementTarget**
- Geçerli WorldPoint.
- Negatif olmayan tolerance.
- Geçersiz sayısal değerler.

## 13.2 Controller entegrasyon testleri

- State velocity bir step'ten diğerine taşınır.
- Controller aynı oturum boyunca korunur.
- Runtime/actor/map değişiminde state yeniden kurulur.
- Static collision sonrası gerçek velocity kullanılır.
- Wall slide sonrası velocity gerçekleşen hareketi yansıtır.
- Tam bloklanmada velocity güvenli biçimde sıfırlanır.
- Dynamic NPC push sonrası occupancy tutarlıdır.
- Player commit failure NPC push rollback yapar.
- Commit failure proposal velocity sonraki step'e sızmaz.

## 13.3 Click-to-move testleri

- Uzak hedefe yaklaşma.
- Yakın hedefte yüksek hızdan frenleme.
- Hedef değiştirme.
- Hedef iptali ve manuel klavye override.
- Düz hat smoothing.
- Collision nedeniyle smoothing fallback.
- Dönüş waypoint'inin atlanmaması.
- Hücre değişiminin tek başına waypoint arrival sayılmaması.
- Dönüş öncesi frenleme.
- Nihai hedefte snap olmadan arrival.
- Blocked edge ve replan davranışının korunması.

## 13.4 Zaman ve performans testleri

- 60 Hz fixed-step.
- Variable render delta.
- Pause/resume.
- Frame stall ve max-substep.
- Telemetri kapalı/açık davranışı.
- Route metrics doğruluğu.
- Uzun süreli hareket ve rota güncellemesi.

## 13.5 Regresyon testleri

Aşağıdakiler mevcut davranışları bozmamalıdır:
- Actor map doğrulaması.
- Runtime commit güvenliği.
- Occupancy ve spatial index tutarlılığı.
- Statik collision çözümü.
- NPC itişi ve rollback.
- Rota cache ve replan.
- Input focus kaybı.
- Harita geçişleri.
- Movement mode davranışları.

## 13.6 Aşama tamamlanma kapısı

Aşama 3.5 ancak aşağıdakilerin tamamı sağlandığında kapatılır:

- [ ] Domain birim testleri geçer.
- [ ] Controller entegrasyon testleri geçer.
- [ ] Click-to-move ve waypoint testleri geçer.
- [ ] Fixed-step testleri geçer.
- [ ] Runtime occupancy/spatial index invariant testleri geçer.
- [ ] NPC push rollback regresyonu geçer.
- [ ] İlgili mevcut proje test paketi geçer.
- [ ] Manuel oyun testi tamamlanır.
- [ ] Performans baseline ve yeni ölçümler raporlanır.
- [ ] Dokümantasyon ve değişiklik listesi güncellenir.
- [ ] Çalışma dalı `experiment/map-cleanup` olarak kalır.

Testi çalıştırılmamış özellik tamamlandı olarak işaretlenemez.

---

# 14. Uygulama paketleri ve bağımlılık sırası

## Paket 0 — Başlangıç doğrulaması

- Dal ve çalışma ağacı durumu kontrol edilir.
- Hedef branch'in güncel kaynakları okunur.
- İlgili test dosyaları ve çağrı noktaları bulunur.
- Demo movement config durumu doğrulanır.
- Mevcut test ve performans baseline alınır.

**Çıkış kapısı:** Değişiklik öncesi kaynak ve test envanteri tamamlanmış olmalı.

## Paket 1 — Domain hareket sözleşmesi

- Config genişletilir.
- MovementTarget eklenir.
- Integrator yeni algoritmayla güncellenir.
- Geriye uyumluluk test edilir.
- Domain testleri tamamlanır.

**Çıkış kapısı:** Uygulama katmanı olmadan domain testleri geçmeli.

## Paket 2 — Persistent controller ve runtime entegrasyonu

- Controller state yaşam döngüsü düzeltilir.
- GameWindow controller'ı oturum kapsamına taşır.
- Gerçek displacement velocity'ye dönüştürülür.
- Commit success/failure davranışları doğrulanır.

**Çıkış kapısı:** Controller ve runtime entegrasyon testleri geçmeli.

## Paket 3 — Click-to-move ve waypoint

- Route controller açık hedef/waypoint bilgisi sunar.
- Hedef metadata'sı integrator'a aktarılır.
- Frenleme ve displacement cap etkinleşir.
- Dönüş waypoint ilerlemesi düzeltilir.
- Manuel input override korunur.

**Çıkış kapısı:** Hedefe yaklaşma, dönüş ve hedef değiştirme testleri geçmeli.

## Paket 4 — Fixed-step ve telemetri

- Max-substep politikası uygulanır.
- Pause/resume doğrulanır.
- Route metrics performans monitor'a bağlanır.
- Ölçüm maliyeti kontrol edilir.

**Çıkış kapısı:** Zaman ve performans testleri geçmeli.

## Paket 5 — Regresyon ve kapanış

- İlgili tam test paketi çalıştırılır.
- Manuel oyun testi tamamlanır.
- Bilinen sınırlamalar kaydedilir.
- Mimari ve uygulama dokümanları güncellenir.
- Aşama 3.5 kapanış raporu hazırlanır.

---

# 15. Ekip iş bölümü ve entegrasyon protokolü

**Uzman A — Domain hareket**
- Bölüm 5 ve 6.
- Config, Target, Integrator.
- Domain testleri.
- Uygulama katmanından bağımsızlık.

**Uzman B — Controller ve runtime entegrasyonu**
- Bölüm 7 ve 9.
- Persistent state.
- GameWindow yaşam döngüsü.
- Commit ve rollback güvenliği.

**Uzman C — Click-to-move ve waypoint**
- Bölüm 8.
- Route target metadata.
- Waypoint arrival ve dönüş frenlemesi.
- Smoothing regresyonu.

**Uzman D — QA, zaman ve performans**
- Bölüm 10, 11 ve 13.
- Fixed-step sınırı.
- Telemetri.
- Test ve kapanış raporu.

## 15.1 Ekip koordinasyonu

- A'nın domain API'si kesinleşmeden B ve C kendi başlarına farklı hedef/state sözleşmesi oluşturamaz.
- B ve C aynı dosyada çakışan değişiklik yapacaksa önce tek entegrasyon sahibi üzerinden uzlaşır.
- D, testleri sonradan yazan pasif rol değildir; paketlerin çıkış kapılarını doğrular.
- Her paket test sonucu ve değişen dosya listesiyle teslim edilir.
- Başarısız test gizlenmez veya atlanmaz; sebep raporlanır.

## 15.2 Git çalışma kuralları

- Tek çalışma dalı: `experiment/map-cleanup`.
- Branch değiştirmek yasaktır.
- Yeni branch oluşturmak yasaktır.
- Başka dala cherry-pick, merge veya push yapılmaz.
- Mevcut kullanıcı değişiklikleri korunur.
- Her commit yalnızca doğrulanmış paket değişikliklerini içermelidir.
- Test edilmemiş kod tamamlandı olarak sunulmaz.

---

# 16. Riskler ve azaltma yöntemleri

| Risk | Etki | Önlem |
|---|---|---|
| Controller'ın her karede yeniden kurulması | Velocity kaybı | Session-scoped state ve lifecycle testi |
| Intent vektöründen hedef mesafesi çıkarılması | Klavye/click semantiği karışır | Ayrı MovementTarget |
| Hücre geçişinin waypoint arrival sayılması | Dönüşlerde erken yön değiştirme | WorldPoint mesafesiyle waypoint arrival |
| Yalnızca frenleme hızına güvenilmesi | Hedefi aşma riski | Ek displacement cap |
| Collision sonrası teorik velocity saklanması | Duvar/NPC sonrası hatalı hız | Gerçek displacement/dt |
| Runtime commit atlanması | World state tutarsızlığı | Runtime invariant testleri |
| NPC push rollback kaybı | Actor konum tutarsızlığı | Mevcut rollback entegrasyon testi |
| Sınırsız catch-up | Frame-time patlaması | Max-substep ve gecikme telemetrisi |
| Demo movement profile eksikliği | Manuel testte hareket çalışmaması | Content schema doğrulaması |
| Telemetri sayaçlarının güncellenmemesi | Yanlış performans raporu | Gerçek olay noktalarında sayaç testi |

---

# 17. Context7 ve teknik referanslar

Uygulama sırasında kullanılan temel kütüphane davranışları:

- Pygame-ce Clock: `Clock.tick()` geçen süreyi milisaniye cinsinden verir; saniyeye dönüştürme uygulama katmanında yapılır.  
  https://github.com/pygame-community/pygame-ce/blob/main/docs/reST/ref/time.rst
- Pygame Rect koordinatları tamsayı tabanlıdır; hassas authoritative fizik konumu için native float tabanlı `Vector2` ve `WorldPoint` kullanılmalıdır.  
  https://github.com/pygame-community/pygame-ce/blob/main/docs/reST/ref/rect.rst
- Python `math` modülü `hypot`, `sqrt` ve `isfinite` gibi gereken matematik ve doğrulama fonksiyonlarını sağlar.  
  https://docs.python.org/3/library/math.html

Mevcut `pyproject.toml` Python `>=3.11` ve `pygame-ce>=2.5` gereksinimlerini tanımlar. Bu aşama için yeni harici paket gerekmemektedir.

---

# 18. Nihai mimari karar

Aşama 3.5 sonunda hedeflenen hareket mimarisi:

1. Input, hareket isteğini ve opsiyonel hedefi üretir.
2. Route controller, rota ve sıradaki anlamlı waypoint'i belirler.
3. Persistent movement controller, son kabul edilmiş state'i kullanır.
4. Saf MovementIntegrator, ivmelenme/frenleme ve displacement önerisi üretir.
5. Static ve dynamic collision, gerçek uygulanabilir hareketi belirler.
6. HexWorldRuntime konumu, occupancy ve spatial index'i atomik iş akışı içinde günceller.
7. Controller yalnızca commit edilmiş konum ve gerçek displacement üzerinden sonraki state'i kurar.
8. Fixed-step döngüsü kontrollü sayıda adım çalıştırır.
9. PerformanceMonitor gerçek hareket ve rota ölçümlerini toplar.

**Sonuç:** Eldoria'nın sürekli hareket altyapısı hedefe kontrollü yaklaşan, fiziksel çarpışma sonrasında tutarlı kalan, runtime bütünlüğünü koruyan ve gelecekte başka aktör türleri tarafından yeniden kullanılabilecek bir domain hareket çekirdeğine sahip olur.

Bu belge Aşama 3.5 uygulamasının teknik referansıdır. Uygulama sırasında kaynak kodla çelişen bir durum görülürse kodu belgeye zorlamak yerine, teknik gerekçesi ve test etkisiyle belge revize edilmelidir.
