# Eldoria — Aşama 3 Ayrıntılı Teknik Mimari Planı
## Klavye ve Fare Hareketinin Bütünleştirilmesi

- **Proje:** Eldoria RPG
- **Depo:** `trippes/RPG_KAYNAK_YONETIMI`
- **Hedef dal:** `experiment/map-cleanup`
- **Durum:** Teknik mimari planı — uygulama yapılmadı
- **Genel plan:** `reports/phase-3-keyboard-mouse-movement-integration-plan.md`
- **Dayanak denetim:** `reports/experiment-map-cleanup-hareket-mimarisi-performans-teknik-denetimi.md`
- **Aşama 2 kapanışı:** `reports/phase-2-npc-perception-optimization-closure.md`
- **Aşama 2 kapanış commit'i:** `9806120f2ec2665f027cdffcbb73cc1a4a954154`
- **Tarih:** 21 Kasım 2026

---

## 1. Mimari hedef ve değişmez kurallar

Aşama 3'te iki ayrı kontrol yöntemi aynı oyuncu hareket hattını kullanacaktır:

- Klavye adaptörü, o an basılı yönlerden bir `MovementIntent` üretir.
- Fare navigasyonu, aktif rotanın sıradaki geçerli waypoint'ine doğru bir `MovementIntent` üretir.
- `GameWindow`, sabit fizik adımlarını ve komut önceliğini yönetir.
- `ContinuousPlayerMovementController`, mevcut domain integratörü ve çarpışma çözümünü uygular.
- `HexWorldRuntime`, oyuncunun sürekli konumunu ve hex occupancy durumunu kanonik olarak günceller.

Değişmezler:

1. Girdi adaptörleri dünya konumunu veya occupancy kaydını doğrudan değiştiremez.
2. Klavye ve fare farklı hareket/fizik algoritmaları kullanamaz.
3. Hareket komutu yalnızca niyet üretir; fizik ve collision tek yerde uygulanır.
4. A* yalnızca rota üretir; hedefe yönelme ve gerçek hareket controller sorumluluğundadır.
5. Cache hiçbir koşulda eski rotayı güvenli kabul edip geçersiz hücreye geçiş yaptırmaz.
6. Her fizik adımı güncel oyuncu konumundan yürütülür; rota cursor'ı gerçek runtime hücresiyle eşleştirilir.
7. NPC davranışlarının orkestrasyon sırası, algılama eşikleri ve NPC mantıksal simülasyon sıklığı değiştirilemez.
8. Görsel konum, authoritative runtime konumunun yerine geçemez.

## 2. Mevcut kod akışı ve mimari sorunlar

### 2.1 Klavye

`game_ui/movement_input.py::PygameMovementInput` doğrudan `pygame.key.get_pressed()` sağlayıcısını kullanır. WASD/yön tuşlarından yön vektörü; Shift'ten RUNNING; Alt basış kenarından STEALTH toggle üretir. Pencere odağı kaybında klavye girdisi temizlenir.

Ayrı olarak `game_ui/input.py::InputMapper`, KEYDOWN olaylarından `InputState.actions` üretir. `HexGameplayView.DIRECTIONS` bu eylemleri altı hex yönüne çevirir. Bu iki yolun GameWindow içindeki çağrı sırası ve sorumlulukları 3.1 envanterinde açıkça belgelenmelidir. KEYDOWN tek başına sürekli hareket kaynağı olarak kullanılmamalı; sürekli hareket için basılı tuş durumu kullanılmalıdır.

### 2.2 Fare

`HexGameplayView.handle()` sol tık koordinatını panel, NPC, sahne nesnesi ve dünya hedefi kontrollerinden geçirir. Geçerli harita hücresi ise `_move_goal` ve `_move_map_id` saklanır.

`HexGameplayView.click_move_intent()`:
1. Aktif runtime ve oyuncu entity'sini doğrular.
2. Oyuncunun map kimliğini hedef map ile karşılaştırır.
3. Physics snapshot ve oyuncu body bilgisini alır.
4. Oyuncunun güncel hücresini ve sürekli konumunu okur.
5. Hedef aynı hücre değilse `runtime.path_to()` çağırır.
6. Yolun ikinci hücresinin merkezine yön vektörü üretir.

Bu fonksiyon, `GameWindow._advance_continuous_player_movement()` içindeki sabit fizik adımı döngüsünde çağrılır. Aynı hedef ve aynı rota için bir frame'de birden çok path query oluşabilir.

### 2.3 Ortak hareket

`GameWindow._advance_continuous_player_movement()` sabit adım sayısını hesaplar; `ContinuousPlayerMovementController` oluşturur ve her adımda controller'a intent verir. Controller `MovementIntegrator`, `HexPhysicsSnapshot.resolve_motion()` ve binding/runtime commit yolunu kullanır.

Mevcut davranışta fare intent'i hareket ediyorsa klavye intent'inin tamamının yerini alır. Fare intent'i varsayılan `MovementMode.NORMAL` ile üretildiği için fare yürüyüşü sırasında Shift/Alt modunun ne olacağı açıkça tasarlanmamıştır. Bu, 3.1'de testle sabitlenecek ve 3.2'de açık politikaya bağlanacaktır.

### 2.4 Pathfinding ve engel verisi

`HexWorldRuntime.path_to()`:
- entity'yi doğrular,
- entity hareket iznini kontrol eder,
- occupancy registry'den diğer aktörlerin bloklu hücrelerini çıkarır,
- `HexPathfinder.find_path()` ile A* çalıştırır,
- metrics etkinse arama süresini kaydeder.

`HexPathfinder` harita maskesi, bloklu hücreler, hareket profili, `MovementRules` ve isteğe bağlı edge validator kullanır. Fare rotasında edge validator `HexPhysicsSnapshot.can_reach_cell()` üzerinden statik fizik geçişini kontrol eder.

`HexPhysicsSnapshot` immutable harita/çarpışma snapshot'ıdır. `HexOccupancyRegistry` ise aktörlerin dinamik hücre doluluğunu tutar; mevcut sürümde açık bir monoton occupancy revision/version alanı bulunmamaktadır. Bu nedenle Aşama 3, var olmayan bir revision API'sini varsayamaz.

## 3. Hedef sorumluluk mimarisi

Önerilen akış:

```text
Pygame event queue + key state
             |
             v
       Input adapters
       /            \
 keyboard intent   mouse command
       \            /
        v          v
      Player Input Arbitration
                 |
       +---------+----------+
       |                    |
  direct intent       active move command
                            |
                            v
                 ClickMoveRouteController
                 - command lifecycle
                 - route + cursor
                 - replan/invalidation
                 - next-edge validation
                            |
                            v
                  waypoint direction intent
       +--------------------+
       |
       v
 GameWindow fixed-step movement loop
       |
       v
 ContinuousPlayerMovementController
       |
       +--> MovementIntegrator
       +--> HexPhysicsSnapshot collision
       +--> ActorHexBindingService
       +--> HexWorldRuntime authoritative position
```

### 3.1 Sorumluluk sahipliği

| Bileşen | Sorumluluk | Yapmaması gereken |
|---|---|---|
| `InputMapper` | Tek seferlik event, tıklama ve UI/world action üretmek | A* veya fizik çalıştırmak |
| `PygameMovementInput` | Basılı klavye durumundan hareket intent'i üretmek | Runtime konumu değiştirmek |
| `HexGameplayView` | Harita tıklamasını hedef komutuna çevirmek; NPC/nesne/kapı etkileşimini ayırmak | Her fizik adımında kendi başına A* çalıştırmak |
| `GameWindow` | Input arbitration, pause/focus politikası ve fixed-step yürütme | Rota algoritması veya collision kuralı taşımak |
| `ClickMoveRouteController` (tasarım rolü) | Aktif fare komutu, rota, cursor, replan ve invalidation | Aktör konumunu doğrudan commit etmek |
| `HexWorldRuntime` | Entity, occupancy ve pathfinding için kanonik veri | UI input önceliği belirlemek |
| `HexPathfinder` | Saf/deterministik rota araması | Aktif kullanıcı komutu saklamak |
| `ContinuousPlayerMovementController` | Her fixed step'te ortak hareket/fizik/commit | Fare hedefi veya UI state saklamak |

Yeni bir controller sınıfı zorunlu değildir. Envanter sonucunda mevcut application sınırları yeterliyse küçük bir bileşen veya mevcut bir sınıfın dar sorumluluğu tercih edilebilir. Ancak A* sorgusunun `HexGameplayView.click_move_intent()` içindeki her çağrıda yapılması son mimaride sürdürülmemelidir.

## 4. Hareket komutu sözleşmesi

### 4.1 Komut durumları

Fare hareketi için aşağıdaki kavramsal durumlar tanımlanmalıdır:

- **Idle:** Aktif fare hedefi yok.
- **Planning:** Yeni hedef için rota aranıyor.
- **Following:** Rota mevcut ve sıradaki waypoint'e yönelinmiş.
- **Replanning:** Beklenen sonraki adım artık güvenli değil veya oyuncu rotadan saptı.
- **Arrived:** Hedef hücre/konum toleransı karşılandı; komut temizlenir.
- **Blocked/Failed:** Ulaşılabilir rota yok veya güvenli biçimde devam edilemiyor; komut temizlenir ve gerekirse UI bildirimi üretilir.
- **Cancelled:** Manuel hareket, etkileşim, yeni komut, map/runtime değişimi veya pause/load/reset politikasıyla komut iptal edildi.

Bunlar UI ekranı veya genel oyun state'i değildir; yalnızca click-to-move komut yaşam döngüsüdür.

### 4.2 Komut verisi

Önerilen asgari komut bağlamı:

| Alan | Amaç |
|---|---|
| `actor_id` | Komutun hangi oyuncuya ait olduğunu belirlemek |
| `runtime_identity` | Eski oyun oturumundan rota kullanılmasını önlemek |
| `map_id` | Harita geçişinde komutu geçersizleştirmek |
| `goal_cell` | Kullanıcının seçtiği nihai hedef |
| `route_cells` | A* sonucu olan immutable hücre dizisi |
| `route_cursor` | Beklenen mevcut/sonraki waypoint konumu |
| `physics_snapshot_identity` | Rota üretiminde kullanılan statik collision bağlamını tanımak |
| `status` | Komut durumunu belirlemek |
| `replan_reason` | Ölçüm ve teşhis için son replan nedeni |

Bu alanlar önerilen veri sözleşmesidir; gerçek isim ve yerleşim 3.1 kod envanterinden sonra seçilmelidir. Mutable entity nesneleri veya eski `HexMovableEntity` referansları rota cache'inde saklanmamalıdır.

### 4.3 Input arbitration — öncelik tablosu

Önerilen politika:

| Aynı frame/step içindeki girdi | Sonuç |
|---|---|
| Aktif klavye yönü + aktif fare rotası | Klavye kazanır; fare komutu iptal edilir |
| Yeni geçerli harita sol tıkı | Eski fare komutu iptal edilir; yeni hedef planlanır |
| Sol tık NPC | Diyalog/seçim; yürüme hedefi oluşturulmaz |
| Sol tık sahne nesnesi | İncele/etkileşim; yürüme hedefi oluşturulmaz |
| Sağ tık bağlam menüsü | Mevcut fare hareketi iptal edilir |
| Sağ tık dünya hedefi/kapı/structure | Mevcut etkileşim sözleşmesi uygulanır; otomatik yürüyüş eklenmez |
| Harita dışı/panel dışı sol tık | Yeni rota oluşturulmaz; mevcut rota için iptal politikası açıkça belirlenir |
| Pencere odağı kaybı | Klavye intent'i sıfırlanır; fare komutunun devamı tek bir ürün politikasıyla belirlenir |
| Pause/dialogue/save-load | Oyuncu movement clock resetlenir; aktif rota pause/resume veya cancel kararıyla tutarlı ele alınır |
| Map transition | Fare komutu iptal edilir; yeni map üzerinde eski rota kullanılamaz |

Klavye önceliği frame bazında değil, hareket simülasyonuna giren gerçek intent bazında değerlendirilmelidir. Yalnızca KEYDOWN event'i ile sürekli basılı klavye durumu birbirine karıştırılmamalıdır.

### 4.4 Hareket modu

- Klavye modu mevcut sözleşmeyi korur: Alt gizlilik, Shift koşma, gizlilik koşmaya önceliklidir.
- Fare hareketinin modu açıkça tanımlanmalıdır. Önerilen varsayılan, komutun verildiği anda geçerli oyuncu hareket modunu kullanmaktır; fare rotası kendiliğinden koşma veya gizlilik açmaz.
- Kullanıcı fare rotası sürerken Shift/Alt'a basarsa yeni mod bir sonraki fixed step'te uygulanır.
- Rota controller yalnızca yön/waypoint intent'i üretmeli; hız çarpanı ve mode policy tek input arbitration katmanında çözülmelidir.

## 5. Rota cache ve invalidation mimarisi

### 5.1 Cache kapsamı

Genel amaçlı path cache değil, **tek oyuncunun tek aktif click-to-move komutuna ait rota state'i** kullanılmalıdır.

Aynı hedef ve aynı rota bağlamı için her physics step'te `runtime.path_to()` çağrılmamalıdır. Rota ilk hedefte veya gerekli replan anında üretilir; sonraki fixed step'lerde cursor ve sıradaki waypoint kullanılır.

### 5.2 Neden yalnızca hedef hücre anahtarı yeterli değil?

Aynı hedef için rota aşağıdaki koşullarda değişebilir:
- Oyuncu başka map'e geçer veya runtime yeniden oluşturulur.
- Oyuncu beklenen rotadan farklı bir hücreye geçer.
- Statik harita/collision snapshot değişir.
- Diğer aktörlerin occupancy durumu, rotanın sıradaki hücresini bloke eder.
- Oyuncu hareket profili veya collider/body bağlamı değişir.
- Yükleme/restore sonrasında aynı actor id farklı konuma veya dünyaya bağlanır.

Mevcut `HexPhysicsSnapshot` immutable'dır; snapshot kimliği değişimi güvenli invalidation işaretidir. Buna karşılık occupancy registry'nin açık revision sayacı yoktur. Aşama 3, bütün rotayı her occupancy değişiminde iptal etmek zorunda değildir; bu, oyuncunun her hücre geçişinde kendi occupancy kaydını değiştirmesi nedeniyle cache'i etkisiz kılabilir.

### 5.3 Önerilen güvenli strateji

1. Rota üretiminde `runtime.path_to(actor_id, goal, edge_validator=...)` kullanılır.
2. Rota immutable hücre dizisi olarak saklanır; entity referansı saklanmaz.
3. Her fixed step başında oyuncunun güncel `entity.position.cell` ve map kimliği okunur.
4. Güncel hücre beklenen route cursor ile eşleşiyorsa sıradaki hücre belirlenir.
5. Cursor uyuşmazsa oyuncu kalan rota üzerinde beklenen bir hücrede mi diye kontrol edilir; değilse replan yapılır.
6. Bir sonraki hücreye geçmeden hemen önce:
   - map valid-cell mask kontrolü,
   - map static blocked kontrolü,
   - `runtime.occupancy.can_enter(..., excluding=actor_id)`,
   - `physics_snapshot.can_reach_cell(current, next, body)`
   uygulanır.
7. Sonraki adım geçersizse eski rota kullanılmaz. Bir defa replan denenir; replan başarısızsa komut Blocked/Failed olarak sonlandırılır. Aynı fizik step içinde sınırsız replan döngüsü yasaktır.
8. Oyuncu hücre değiştirdiğinde cursor ilerletilir; yalnızca oyuncu hareket ettiği için tüm rota yeniden hesaplanmaz.
9. Her yeni komut, runtime/map/physics bağlamı değişimi ve açık iptal olayında eski rota temizlenir.

Bu strateji, occupancy version alanı eklenmeden de sonraki adımı güvenli biçimde kontrol edebilir. Daha sonra profiling, uzak gelecekteki rota blokajlarını erken tespit etmenin önemli olduğunu gösterirse occupancy revision API'si ayrı bir tasarım/uygulama kararı olarak ele alınabilir.

### 5.4 Invalidation nedenleri

Açıkça ölçülmesi gereken nedenler:

- `new_goal`
- `manual_keyboard_override`
- `right_click_interaction`
- `map_changed`
- `runtime_replaced`
- `physics_snapshot_changed`
- `actor_unavailable`
- `route_deviation`
- `next_edge_blocked`
- `replan_failed`
- `arrived`
- `pause_or_load_reset`

Invalidation sayacı yalnızca cache temizlendiğinde artırılmalı; replan sayacı yalnızca gerçekten yeni path search başlatıldığında artırılmalıdır.

## 6. Waypoint yönü, eşik ve smoothing

### 6.1 Hücre geçişi

Mevcut davranış sıradaki hücrenin merkezine doğru bir vektör üretir. Oyuncunun continuous konumu ile hedef merkez arasındaki mesafe çok küçük olduğunda komut temizlenir. Sabit `0.5` dünya birimi toleransı mevcut kodda vardır; bu değerin hex boyutu, hız ve physics step ile ilişkisi test edilmelidir.

Yeni tolerans:
- Tek bir yerde tanımlanmalı.
- Dünya koordinat biriminde açıkça belgelenmeli.
- Farklı render FPS'lerinde değil, fixed-step runtime konumunda değerlendirilmelidir.
- Hedef hücreye varış ile nihai hedef merkezine varışı birbirinden ayırmalıdır.

### 6.2 Konservatif smoothing

İlk sürümde güvenli yaklaşım:
- Aynı doğrultuda ardışık hex edge'lerini tek bir daha uzak waypoint yönüne indirgemek.
- Dönüş köşelerini otomatik kesmemek.
- A* rota hücrelerinin sırasını ve geçilebilirlik kanıtını korumak.
- Her adımda normal collision resolver'ı kullanmaya devam etmek.

Daha agresif köşe yumuşatma ancak aşağıdakiler birlikte kanıtlanırsa değerlendirilebilir:
1. Segmentin geçtiği tüm hex hücreleri için supercover/line traversal geçerli-cell ve blocked-cell kontrolü.
2. Oyuncu collider'ının tüm segment boyunca swept collision doğrulaması.
3. Dinamik occupancy için geçiş öncesi kontrol.
4. Aynı başlangıç/hedefte smoothing açık ve kapalı sonuçlarının engel güvenliği bakımından eşdeğerliği.

Spline/Bezier rotaları veya collision bypass bu aşamanın hedefi değildir.

## 7. Hedefe yaklaşma ve hareket fiziği bağımlılığı

Mevcut `MovementIntegrator.step()` her adımda hızı intent yönünden doğrudan üretir; `MovementState.velocity` geçmiş hız için kullanılsa da mevcut integratör ivmelenme/frenleme uygulamaz.

Bu nedenle yalnızca rota controller içinde mesafeye göre intent yönünü küçültmek yeterli değildir: integratör yönü normalize ettiği için vektörün büyüklüğü hız azaltımı sağlamaz.

Gerçek yaklaşma yavaşlaması, hareket fiziği yol haritasındaki ivmelenme/frenleme modeliyle birlikte uygulanmalıdır. Bu bağımlılık tamamlanmadıysa Aşama 3:
- hedefe varış toleransını,
- son waypoint yaklaşma mesafesini,
- komutun tamamlanma koşulunu
tanımlar; ancak kademeli hız düşüşünü uygulamış gibi raporlamaz.

Aşama 3 sırasında hareket fiziği sözleşmesi değiştirilmek zorunda kalırsa bu ayrı bir kapsam değişikliği olarak durdurulup değerlendirilmelidir.

## 8. Hata ve edge-case politikası

| Durum | Beklenen davranış |
|---|---|
| `runtime.path_to()` None/boş/kısa yol döndürür | Komut Failed; hareket intent'i sıfır |
| Hedef geçersiz/blocked | Komut reddedilir; oyuncu yerinde kalır |
| Oyuncu map değiştirir | Komut iptal edilir |
| Runtime/entity kaybolur | Komut iptal edilir; exception oyun döngüsüne taşınmaz |
| Physics snapshot yok veya map uyuşmaz | Hareket durur; komut güvenli biçimde iptal edilir |
| Rota sıradaki hücresi dolu | Bir replan; başarısızsa Blocked |
| Oyuncu collision nedeniyle ilerleyemez | Sabit adım başına sınırsız replan yok; belirli sayıda başarısız ilerleme sonrası replan/iptal politikası test edilir |
| Aynı hedef tekrar tıklanır | Aynı aktif komut korunur veya bilinçli refresh edilir; gereksiz yeni A* yapılmaz |
| Yeni hedef tıklanır | Eski komut tek seferde iptal, yeni komut planlanır |
| Manuel klavye girdisi başlar | Fare komutu iptal edilir ve klavye intent'i aynı fixed-step controller'a geçer |
| Pause/resume | Movement clock resetlenir; rota state'i seçilen ürün politikasına göre güvenli biçimde korunur veya iptal edilir |
| Save/load | Eski runtime referanslı rota state'i taşınmaz; yeni runtime'da yeniden planlanır |

## 9. Telemetri ve benchmark

### 9.1 Sayaçlar

Asgari sayaçlar:
- `player_click_path_queries`
- `player_click_route_cache_hits`
- `player_click_route_cache_misses`
- `player_click_route_replans`
- `player_click_route_invalidations`
- `player_click_route_blocked_steps`
- `player_click_route_waypoints_total`
- `player_click_route_arrivals`
- `player_click_route_failures`

Zaman ölçümleri:
- path planning p50/p95/p99,
- komut başlatma süresi,
- hedefe ulaşma süresi,
- replan süresi.

Metrics nesnesi kapalıyken `perf_counter` çağrısı ve liste örneklemesi yapılmamalı; mevcut NPC metrics yaklaşımındaki opsiyonel maliyet ilkesi korunmalıdır.

### 9.2 Benchmark senaryoları

| Senaryo | Durum | Beklenen kanıt |
|---|---|---|
| P1 | Aynı hedef, 1 fixed step/frame | Tek planlama; devam eden step'lerde cache hit |
| P2 | Aynı hedef, frame başına 2–8 fixed step | Step sayısı artsa da gereksiz path query artmaz |
| P3 | Hedef değişimi | Eski rota iptal; yeni hedef için tek plan |
| P4 | Aynı hedefe tekrar tıklama | Belirlenen politika; plansız tekrar araması yok |
| P5 | Sıradaki hücre dinamik olarak işgal edilir | Eski rota kullanılmaz; replan/Blocked |
| P6 | Oyuncu rotadan saptırılır | Cursor mismatch tespit edilir; replan |
| P7 | Dar geçit ve statik engel köşesi | A* ve collision güvenliği korunur |
| P8 | Geçersiz/erişilemeyen hedef | Kontrollü Failed; sonsuz replan yok |
| P9 | Manuel yön girdisi | Fare komutu iptal; klavye aynı controller'dan yürür |
| P10 | Map/runtime/physics snapshot değişimi | Eski rota kullanılmaz |
| P11 | Shift/Alt ile fare hareketi | Açıkça belirlenmiş mode policy uygulanır |
| P12 | NPC/nesne/sağ tık etkileşimi | Etkileşim ve yürüyüş hedefi karışmaz |

Benchmark 1/10/100 hücrelik yolları ve farklı sabit-step sayısını kapsamalı. Önce/sonra aynı branch runner, Python sürümü ve fixture ile çalıştırılmalıdır. Ölçüm raporu query sayısı, p50/p95/p99 ve rota uzunluğunu içermelidir.

## 10. Test mimarisi

### 10.1 Birim testleri

- Route controller state geçişleri.
- Aynı hedefte route reuse.
- Cursor ilerletme ve sapma tespiti.
- Next-edge occupancy/static collision validation.
- Replan tek-sefer sınırı.
- Her invalidation nedeni.
- Arrived/Failed/Blocked/Cancelled ayrımı.
- Mode arbitration ve keyboard override.

### 10.2 Entegrasyon testleri

Mevcut doğrulanmış test dosyaları:
- `tests/test_game_ui/test_hex_gameplay_view.py`
- `tests/test_game_ui/test_movement_input.py`

Bunların yanı sıra repository'deki gerçek `GameWindow`, `ContinuousPlayerMovementController`, `HexWorldRuntime` ve `HexPathfinder` test modülleri 3.1 envanterinde bulunmalı; test dosya adları doğrulanmadan yeni yol varsayılmamalıdır.

Entegrasyon testleri:
- Klavye ve fare intent'inin aynı controller'a gittiğini doğrulamalı.
- Her iki girişte de statik collision ve dynamic actor push davranışının aynı olduğunu doğrulamalı.
- InputMapper event ve PygameMovementInput key-state ayrımını korumalı.
- UI etkileşimlerinin click-to-move hedefi üretmediğini doğrulamalı.
- Pause/load/map transition sonrasında eski rota state'inin sızmadığını doğrulamalı.

### 10.3 Davranış eşdeğerliği

- Cache açık/kapalı aynı değişmeyen dünyada aynı rota hücrelerini ve nihai hedefi üretmeli.
- Aynı input dizisi aynı fixed-step sayısında aynı authoritative konumu üretmeli.
- Smoothing açık/kapalı geçerli hücre ve collision güvenliğini korumalı.
- Path cache, NPC hareketini veya NPC simulation order'ı etkilememeli.

## 11. Kalite ve CI doğrulaması

Her alt aşama sonunda küçük hedefli testler çalıştırılmalı; aşama kapanışında:

1. İlgili pytest paketleri ve tüm proje pytest suite.
2. Ruff: değişen dosyalar ve hareket/navigation/UI paketlerinin tamamı.
3. Pygame headless smoke.
4. Eldoria CI Windows/Linux ve desteklenen Python matrisleri.
5. Core Quality workflow.
6. Benchmark workflow/artefact sonuçları.

Ruff kapsamı denetim raporunda belirtilen `hex_world_lab` kapsam eksikliğini otomatik olarak Aşama 3'e dahil etmek zorunda değildir; fakat Aşama 3'te değiştirilen hareket/navigation paketlerinin gerçekten tarandığı workflow komutuyla doğrulanmalıdır. Daha geniş Ruff kapsam genişletmesi ayrı değişiklikse gerekçesi ve regresyon riski belirtilmelidir.

CI'da donanım bağımlı kesin FPS değerleri fail kriteri yapılmamalı. Deterministik sayaçlar (path query sayısı, cache hit, replan) otomatik kabul kriteri olabilir.

## 12. Uygulama sırası ve karar kapıları

1. 3.1 envanter: gerçek GameWindow input akışı, testler ve state yaşam döngüsü.
2. Komut önceliği ve mode policy kararı.
3. Cache/route controller tasarımı: sahiplik, key, cursor, invalidation.
4. Cache kapalı/açık eşdeğerlik testleri.
5. Rota reuse uygulaması ve path query sayaçları.
6. Dinamik sonraki-adım doğrulaması ve replan.
7. Konservatif waypoint smoothing.
8. Hedefe varış/terminal durumlar.
9. İvmelenme/frenleme bağımlılığı karşılandıysa yaklaşma yavaşlaması; değilse açık erteleme.
10. Benchmark, tüm regresyon testleri, Ruff ve GitHub Actions.
11. Aşama 3 teknik sonuç ve kapanış raporu.

Her davranış değişikliği önce test sözleşmesiyle açıklanmalıdır. Güvenli rota invalidation veya input önceliği konusunda mevcut testlerin gösterdiği davranış ile önerilen politika çelişirse sessizce değiştirmek yerine karar kaydı tutulmalıdır.

## 13. Açık kararlar ve varsayımlar

Aşağıdaki konular uygulama öncesi 3.1 envanterinde kesinleştirilmelidir:

1. Pencere odağı kaybında fare rotası devam etmeli mi, yoksa tamamen iptal mi edilmeli?
2. Fare rotası sırasında Shift/Alt mod değişimi anında mı uygulanmalı?
3. Aynı hedefe tekrar tıklama aktif rotayı korumalı mı, yoksa açık refresh mi sayılmalı?
4. Pause/resume aktif rotayı korumalı mı? Save/load sonrasında rota kesinlikle yeniden kurulmalı.
5. Oyuncu collision nedeniyle aynı waypoint'e birkaç fixed step boyunca ilerleyemezse kaç başarısız adımdan sonra replan/iptal yapılmalı?
6. Agresif köşe smoothing ilk teslimata alınmalı mı? Varsayılan öneri yalnızca düz/kollinear waypoint birleştirmedir.
7. Gerçek hedefe yaklaşma yavaşlaması için hareket fiziği aşamasının ivmelenme/frenleme sözleşmesi tamamlanmış mı?

Bu kararlar için varsayılan öneriler bu belgede verilmiştir; kaynak kod ve mevcut testler doğrulanmadan sabit API veya sınıf adı dayatılmamıştır.

## 14. Aşama 2 ile ilişki ve kapsam sınırı

Aşama 2 kapanışında aktif NPC kaçınma benchmark'ında pathfinder arama süresi p95'i 66–74 ms düzeyinde raporlanmıştır. Kaynak incelemesinde `NPCAvoidanceSystem._escape_path()`, çevredeki aday hücreleri sıralayıp uygun yol bulana kadar birden fazla `runtime.path_to()` çağrısı yapabilmektedir.

Bu NPC kaçış rota araması, oyuncunun `HexGameplayView.click_move_intent()` içinde tekrarlanan hedef yolu sorgusundan farklı bir tüketicidir. Aşama 3'te NPC `_escape_path()` algoritmasını değiştirmek; NPC davranış sırası, kaçış hedefi seçimi ve performans benchmark kapsamını genişletecektir. Bu nedenle kapsam dışıdır ve ayrı bir NPC pathfinding optimizasyon aşamasına devredilir.

## 15. Nihai mimari karar

Aşama 3 için önerilen çözüm, mevcut A* ve fizik altyapısının yerine yeni bir navigasyon sistemi koymak değildir. Tek aktif oyuncu fare komutunun rota yaşam döngüsünü açıkça yönetmek; klavye ve fareyi ortak fixed-step controller'a bağlamak; her sonraki adımı güncel occupancy ve statik collision ile doğrulamaktır.

En küçük güvenli çözüm tercih edilmelidir. Rota cache'i komut kapsamlı olmalı, cursor authoritative runtime hücresiyle ilerlemeli, replan sınırlı ve ölçülebilir olmalı, smoothing ise collision güvenliğini kanıtlamadan köşe kesmemelidir.

**Bu belge ayrıntılı teknik mimari planıdır. Kaynak kodu, testler, oyun davranışı, bağımlılıklar veya CI yapılandırması üzerinde uygulama değişikliği yapılmamıştır.**
