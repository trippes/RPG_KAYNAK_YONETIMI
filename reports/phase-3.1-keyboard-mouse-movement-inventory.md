# Eldoria — Aşama 3.1 Kaynak Kodu ve Davranış Envanteri

- **Proje:** Eldoria RPG
- **Dal:** `experiment/map-cleanup`
- **Envanter taban commit'i:** `dcd31cbacaec0fdee905891de05ec3212fd4c27b`
- **Tarih:** 21 Kasım 2026
- **Durum:** Kaynak kodu envanteri tamamlandı; uygulama değişikliği yapılmadı.
- **Üst belgeler:** Aşama 2 kapanış raporu, hareket mimarisi/performance denetimi, Aşama 3 genel planı ve Aşama 3 teknik mimarisi.

---

## 1. Kapsam ve doğrulama yöntemi

Envanter, GitHub üzerinde `experiment/map-cleanup` dalının güncel içeriğinden yapıldı. Dosya yolları, dosya içerikleri ve ilgili test modülleri dal referansı açıkça verilerek okundu. Bu rapor, yerel çalışma kopyasının `git status` çıktısını temsil etmez; GitHub bağlantısı kullanıcının bilgisayarındaki commit edilmemiş yerel değişiklikleri göremez.

İncelenen zorunlu kaynaklar:

| Dosya | Doğrulanan sorumluluk |
|---|---|
| `game_ui/movement_input.py` | Basılı tuşlardan sürekli `MovementIntent`, Shift/Alt modları ve focus state |
| `game_ui/input.py` | Pygame olay kuyruğunu `InputState` eylemlerine dönüştürme |
| `game_ui/world_rendering/hex_gameplay_view.py` | Dünya tıklaması, etkileşim ayrımı, click-to-move hedefi ve waypoint yön niyeti |
| `game_ui/game_window.py` | Input sıralaması, klavye/fare önceliği, pause/overlay ve sabit adım yürütme |
| `application/continuous_player_movement.py` | Ortak integrator, statik collision, dinamik aktör çarpışması ve runtime commit |
| `application/gameplay_step_clock.py` | 60 Hz sabit hareket adımı biriktiricisi |
| `application/hex_world_runtime.py` | Kanonik entity/continuous position, occupancy ve path sorgusu |
| `application/hex_pathfinding.py` | Deterministik axial hex A* |
| `application/hex_physics_bridge.py` | Immutable statik fizik snapshot'ı ve hücreler arası geçiş doğrulaması |
| `application/hex_occupancy.py` | Hücre doluluğu, hareket engeli ve atomik occupant güncellemesi |

Ayrıca `core/domain/movement/integrator.py` incelenerek ivmelenme/frenleme desteği doğrulandı.

## 2. Gerçek input ve hareket akışı

### 2.1 Klavye adaptörleri

İki ayrı giriş yolu vardır:

1. `InputMapper.collect(events)`, olay kuyruğundaki KEYDOWN olaylarından `InputState.actions` üretir. Ok tuşları ve Z/X altı yön eylemlerine, diğer tuşlar oyun/UI eylemlerine çevrilir.
2. `PygameMovementInput.read_intent()`, `pygame.key.get_pressed()` benzeri basılı tuş sağlayıcısından WASD/yön tuşları, Shift ve Alt durumunu okuyarak sürekli `MovementIntent` üretir.

Sürekli hareketin ana kaynağı KEYDOWN değildir; basılı tuş durumudur. Bu ayrım Pygame-ce dokümantasyonuyla da uyumludur. Alt, basış kenarında stealth toggle; Shift hold-to-run davranışındadır. Stealth, running moduna önceliklidir. Focus kaybında adapter klavye intent'ini sıfırlar, stealth durumunu kapatır ve Alt'ın yeniden etkinleşmesi için tuşun bırakılmasını bekler.

`HexGameplayView.handle()` içindeki altı yönlü `InputState` hareket yolu da korunmuştur. Gerçek GameWindow akışında hareket adapter'ı geçerli bir hareket intent'i ürettiğinde aynı yön eylemleri `InputState` içinden çıkarılır; böylece normal native hareket hattı çift tetiklenmez. View içindeki `_advance_player_physics()` ise native GameWindow döngüsü dışında barındırılan view'lar için fallback fixed-step yoludur.

### 2.2 GameWindow arbitration ve fixed-step

`GameWindow.step()` sırası özetle:

1. Olayları `InputMapper` ile `InputState`'e dönüştürür.
2. Aynı olayları `PygameMovementInput.handle_events()` üzerinden focus adapter'ına verir.
3. Gameplay, pause/dialogue, pencere/overlay ve ekran koşullarını değerlendirir.
4. Uygun durumda basılı tuşlardan hareket intent'i okur.
5. Altı yön eylemlerini sürekli adapter'ın yön intent'iyle çakışmayacak şekilde temizler.
6. Aktif manuel hareket varsa click-to-move iptal edilir.
7. Manuel hareket yoksa ve aktif click hedefi varsa fare hareketi fixed-step yürütmeye alınır.
8. Her iki giriş de `_advance_continuous_player_movement()` aracılığıyla `ContinuousPlayerMovementController.step()` hattına ulaşır.

Dolayısıyla **klavye önceliği GameWindow seviyesinde zaten uygulanmaktadır**: hareket eden klavye intent'i fare komutunu iptal eder. Bununla birlikte bu önceliğin aynı frame'deki tüm olay kombinasyonlarıyla test kapsamı eksiktir.

`FixedStepAccumulator` varsayılan olarak 1/60 saniyelik adım kullanır. Biriken süre kadar tüm adımları döndürür; maksimum catch-up adım sınırı yoktur. Bu davranış testte de açıkça doğrulanmıştır. Aşama 3 genel planı catch-up politikasını kapsam dışı tuttuğundan bu aşamada değiştirilmemelidir.

`GameWindow._advance_continuous_player_movement()`, çağrı başına bir controller oluşturur ve o kareye ait bütün fixed step'leri aynı controller örneğiyle yürütür. Sonraki frame çağrısında controller yeniden oluşturulur. Bu yaşam döngüsü ilerideki rota state'inin controller içine konmaması gerektiğini gösterir; fare komutunun yaşam döngüsü GameWindow/view tarafında ayrı tutulmalıdır.

### 2.3 Ortak fizik ve authoritative konum

`ContinuousPlayerMovementController.step()` sırası:

- Aktör ve spatial entity'yi binding üzerinden doğrular.
- Başlangıç konumunu entity'nin continuous position bilgisinden alır.
- `MovementIntegrator.step()` ile önerilen hareketi hesaplar.
- `HexPhysicsSnapshot.resolve_motion()` ile statik collision uygular.
- `DynamicActorCollisionResolver` ile dinamik aktör temas/itişini çözer.
- Sonucu `HexWorldRuntime.set_continuous_position()` üzerinden commit eder.
- Oyuncu commit'i başarısızsa geçici NPC itişlerini geri alır.

`HexWorldRuntime` continuous position ve occupancy'nin kanonik sahibidir. Entity view, occupancy ve spatial index tutarlılığını doğrular. `set_continuous_position()` hücre sınırı geçişinde map mask, MovementRules ve güncel occupancy kontrollerini tekrar uygular. Bu kontroller cache veya smoothing optimizasyonunda atlanamaz.

## 3. Fare rotasının mevcut davranışı ve kesin darboğaz

`HexGameplayView.handle()` sol tıklamayı sırasıyla NPC, panel sınırı, sahne nesnesi ve harita hücresi bağlamında değerlendirir. Geçerli boş harita hücresinde `_move_goal` ve `_move_map_id` saklanır. NPC ve sahne nesnesi tıklamaları yürüme hedefi oluşturmaz; etkileşim/inceleme sonucuna gider.

`click_move_intent()` her çağrıda:

1. Runtime ve oyuncu entity'sini doğrular.
2. Hedef map ile oyuncu map'ini karşılaştırır.
3. Physics snapshot ve player body varlığını kontrol eder.
4. Güncel continuous konumu okur.
5. Oyuncu hedef hücrede değilse `runtime.path_to()` çağırır.
6. A* yolunun ikinci hücresinin merkezine yön intent'i üretir.
7. Hedef hücreye gelindiğinde hedef merkezine ilerler ve 0.5 dünya birimi toleransında komutu temizler.

**Kesin performans bulgusu:** Aynı aktif hedef için her `click_move_intent()` çağrısında yeni `runtime.path_to()` çağrılır. Metot fixed-step döngüsünde çağrıldığı için aynı render karesinde birden fazla fixed step varsa aynı hedef için tekrarlı path sorguları oluşur. Tekrarlanan maliyet yalnızca A* değildir: `HexWorldRuntime.path_to()` her çağrıda entity doğrulaması yapar ve occupancy registry'den bloklu hücre kümesini yeniden üretir.

View'da `_path_query_count` ve `_path_query_ms` alanları vardır; runtime tarafında da opsiyonel `runtime_path_queries` ve pathfinder süre metriği bulunur. Ancak view'ın `render_stats` property'si yalnızca `_last_render_stats` döndürür; bu path query alanları mevcut haliyle kullanıcıya/benchmark raporuna bağlı bir click-route telemetry sözleşmesi değildir.

Şu an kalıcı rota dizisi, cursor, waypoint listesi, route status, replan nedeni veya route invalidation sayacı bulunmamaktadır. View yalnızca hedef hücre/map kimliğini saklar. Bu nedenle Aşama 3.3'te eklenecek rota yaşam döngüsü mevcut kodda varmış gibi kabul edilmemelidir.

## 4. Input ve komut davranış matrisi — mevcut kod

| Durum | Mevcut doğrulanmış davranış |
|---|---|
| Basılı WASD/yön tuşu | `PygameMovementInput` sürekli intent üretir |
| Manuel klavye + aktif fare hedefi | GameWindow manuel hareketi seçer ve click-to-move komutunu iptal eder |
| Yeni geçerli boş harita sol tıkı | Aktif hedefi yeni hücre/map ile değiştirir |
| Sol tık NPC | Eski hedefi temizler, NPC seçimi/diyalog sonucu üretir |
| Sol tık sahne nesnesi | Eski hedefi temizler, inceleme sonucu üretir |
| Sağ tık | Önce click-to-move hedefini temizler; NPC/nesne/kapı bağlam menüsü akışına geçer |
| Panel dışı sol tık | Yeni rota üretmez; mevcut hedef açıkça temizlenmediği için devam eder |
| Geçersiz harita hücresi sol tıkı | Yeni hedef atanmaz; mevcut hedef korunur |
| Harita geçişi | Altı yönlü manuel geçişte hedef manuel hareket dalında temizlenir; rota eski map ile eşleşmezse click intent temizlenir |
| Focus kaybı | Klavye intent'i sıfırlanır; aktif click-to-move devam edebilir |
| Pause menüsü | Fizik yürütme erken döner; click hedefi korunur ve devamda sürer |
| Dialogue/overlay açık | Oyuncu hareketi aktif değildir; fixed-step accumulator inactive çağrısıyla sıfırlanır; hedef state'i view'da kalır |
| Save/load | Rota state'i persist edilmez; mevcut view hedefinin load sonrasında aynı map/goal ile kalıp kalmadığı için açık regresyon testi yoktur |
| Aynı hedefe yeniden tıklama | Yeni click olayı hedefi yeniden atar; ayrı bir komut kimliği veya dedup politikası yoktur |
| Shift/Alt fare hareketi | `click_move_intent()` varsayılan `MovementMode.NORMAL` üretir; mevcut klavye modunu fare rotasına aktarmıyor |
| Dinamik sonraki hücre işgali | Her çağrıda yeniden A* occupancy'yi taze okur; ayrıca runtime commit hücre geçişinde occupancy'yi tekrar doğrular |
| Statik engel | Path A* edge validator `HexPhysicsSnapshot.can_reach_cell()` kullanır; gerçek hareket collision resolver'dan geçer |

Focus kaybında click komutunun devam etmesi, mevcut kod davranışıdır; teknik mimaride açık ürün kararı olarak ele alınması gereken bir nokta olmaya devam eder. Shift/Alt davranışında ise mevcut kod normal mod kullanır; mimarinin “komut anındaki modu koru” önerisi henüz uygulanmış değildir.

## 5. İlgili test envanteri

### Mevcut doğrudan test dosyaları

| Test dosyası | Kapsam |
|---|---|
| `tests/test_game_ui/test_movement_input.py` | WASD/ok tuşları, Shift hold, Alt toggle, stealth önceliği, focus kaybı |
| `tests/test_game_ui/test_hex_gameplay_view.py` | Altı yön eylemleri, mouse hedef seçimi, click intent, NPC/nesne etkileşimi, manuel fixed-step, görsel/runtime konum ayrımı |
| `tests/test_game_ui/test_game_window_rendering.py` | Click intent'in shared fixed-step controller'a gönderilmesi, NPC fixed-step ve merkezi simülasyon girişi |
| `tests/test_application/test_continuous_player_movement.py` | Authoritative continuous position, occupancy, statik collision, dinamik NPC itişi, rollback ve duvar boyunca kayma |
| `tests/test_application/test_gameplay_step_clock.py` | 60 Hz, fractional accumulator, büyük frame'de tüm adımların dönmesi, inactive reset |
| `tests/test_application/test_hex_world_runtime.py` | A*, blocked/occupied cells, runtime konum/occupancy ve map transition davranışları |
| `tests/test_application/test_hex_physics_bridge.py` | Statik engel, hücre geçişi, snapshot map/world kimliği, klavye/fare fizik konfigürasyonu |
| `tests/test_application/test_hex_actor_binding.py` | Binding ile runtime/physics sahipliği ve commit entegrasyonu |

Ayrı bir `test_hex_pathfinding.py` veya `test_hex_occupancy.py` modülü bulunmadı; A* ve occupancy davranışlarının doğrudan testleri ağırlıklı olarak `test_hex_world_runtime.py` içinde yer alıyor.

### Testlerle doğrulanan davranışlar

- Klavye yön intent'leri ve Shift/Alt modu.
- Focus kaybında klavye intent'inin sıfırlanması.
- Fare tıklamasının geçerli axial hedef seçmesi.
- NPC tıklamasının diyalog üretmesi ve yürüme hedefi oluşturmaması.
- Sağ tık NPC/boş hücre bağlam menüsü davranışı.
- Click intent'in shared fixed-step controller'a iletilmesi.
- Klavye hareketinin fixed-step continuous physics kullanması.
- Statik collision ve dinamik aktör itişinin runtime commit hattından geçmesi.
- Runtime occupancy ve spatial index tutarlılığı.
- Sabit adımın 60 Hz olması ve büyük elapsed time için bütün adımların döndürülmesi.

### Eksik karakterizasyon/regresyon kapsamı

Aşağıdaki senaryoları doğrudan ve deterministik olarak kanıtlayan test bulunmuyor:

1. Aynı hedef için aynı frame'de 2–8 fixed step çalıştığında path query sayısı.
2. Aynı hedefin ardışık `click_move_intent()` çağrılarında tekrar A* yapıldığının sayısal karakterizasyonu.
3. Klavye intent'i ile aktif fare hedefinin aynı GameWindow frame'inde birlikte bulunduğu arbitration.
4. Focus kaybında fare komutunun devam etmesi.
5. Shift/Alt modunun fare intent'ine aktarılıp aktarılmaması.
6. Pause/resume ve load/runtime replacement sonrasında eski komut state'i.
7. Dinamik occupancy değiştiğinde rota üzerindeki bir sonraki hücrenin güvenli biçimde yeniden değerlendirilmesi.
8. Oyuncu rotadan saptığında cursor/replan davranışı.
9. Rota smoothing açık/kapalı collision eşdeğerliği.
10. 1/10/100 hücrelik oyuncu click-to-move benchmark'ı.

Bu eksikler Aşama 3'ün sonraki uygulama alt aşamalarında test edilmelidir. Envanter sırasında kaynak kodu veya test dosyaları değiştirilmedi.

## 6. Fizik, rota güvenliği ve kapsam sınırları

- `MovementIntegrator.step()` hızı her adımda intent yönü ve mod çarpanından doğrudan üretir; önceki velocity'yi hedef hıza doğru kademeli yaklaştıran acceleration/braking modeli yoktur.
- `MovementState.velocity` mevcut olsa da bu, tek başına ivmelenme/frenleme desteği anlamına gelmez.
- `HexPhysicsSnapshot` immutable'dır ve statik engel geçişini doğrulayabilir.
- `HexOccupancyRegistry` içinde açık monoton revision/version alanı yoktur. Genel cache invalidation için var olmayan bir API varsayılmamalıdır.
- `HexWorldRuntime.path_to()` occupancy bloklu hücrelerini her sorguda üretir.
- `HexWorldRuntime.set_continuous_position()` hücre değişiminde occupancy kontrolü yapar; bu güvenlik kapısı korunmalıdır.
- `ContinuousPlayerMovementController` statik collision ve `DynamicActorCollisionResolver` çağrısını korur. NPC push rollback davranışı test edilmiştir.
- Aşama 2 NPC algılama/kaçınma/yoldaş orkestrasyonu bu aşamanın kapsamı dışındadır. NPC `_escape_path()` arama maliyeti oyuncu click-to-move path sorgularıyla aynı benchmark olarak ele alınamaz.
- Fixed-step 60 Hz sözleşmesi korunur. Catch-up sınırı tasarımı bu aşamanın kapsamı dışındadır.
- Aggressive smoothing için swept collision/supercover kanıtı mevcut envanterde gösterilmemiştir; ilk sürümde yalnızca güvenliği kanıtlanabilen kollinear waypoint azaltımı değerlendirilebilir.

## 7. Belge uyumu ve teknik karar sırası

Okunan belgeler:

1. `reports/phase-2-npc-perception-optimization-closure.md`
2. `reports/experiment-map-cleanup-hareket-mimarisi-performans-teknik-denetimi.md`
3. `reports/phase-3-keyboard-mouse-movement-integration-plan.md`
4. `reports/phase-3-keyboard-mouse-movement-integration-technical-architecture.md`

Çelişki tespit edilmedi. Uygulama sırasında yorum çatışması olursa aşağıdaki kapsam sırası uygulanacaktır:

1. Aşama 3 teknik mimarisi: Aşama 3'ün uygulama sözleşmesi.
2. Aşama 3 genel planı: alt aşama kapsamı ve kabul kriterleri.
3. Hareket teknik denetimi: mevcut durumun ve önceki mimari risklerin kanıtı.
4. Aşama 2 kapanış raporu: NPC optimizasyonlarının tamamlanmış kapsamı ve Aşama 3'e devredilmeyecek NPC pathfinding ayrımı.

Bu sıralama, Aşama 2'nin NPC orkestrasyon sırasını ve optimizasyonlarını değiştirme yetkisi vermez. Aşama 3 teknik belgeleri yalnızca oyuncu input/click-to-move kapsamını yönetir.

## 8. Mevcut GitHub Actions durumu

Envanter taban commit'i `dcd31cbacaec0fdee905891de05ec3212fd4c27b` için GitHub Actions kayıtları incelendi:

| Workflow | Run ID | Sonuç |
|---|---:|---|
| Core quality | `44879653192` | Başarılı |
| Eldoria CI | `44879653203` | Başarılı |

Core quality içindeki Linux `verify` ve Windows `verify-windows` işleri başarılı. Eldoria CI içindeki Pygame headless smoke ile Windows/Linux, Python 3.11/3.12 test matrisindeki dört iş başarılı.

Bu sonuçlar envanter taban commit'inin CI sonuçlarıdır; bu rapor commit'inden sonra oluşacak yeni değişikliklerin test edildiği anlamına gelmez. Yerel pytest/Ruff komutu bu GitHub oturumundan çalıştırılmadı.

## 9. Aşama 3.1 çıkış değerlendirmesi

| Kriter | Durum | Kanıt |
|---|---|---|
| Zorunlu kaynak dosyalarının gerçek yolları | Tamamlandı | 10 zorunlu dosya ve ek integrator incelendi |
| Input akışının uçtan uca çıkarılması | Tamamlandı | InputMapper → GameWindow → View → fixed-step controller |
| Runtime/physics/occupancy sahipliği | Tamamlandı | Runtime ve controller kodu incelendi |
| Mevcut davranış matrisi | Tamamlandı | Bölüm 4 |
| Mevcut test kapsamı ve boşluklar | Tamamlandı | Bölüm 5 |
| Teknik belge uyumu | Tamamlandı | Bölüm 7 |
| Kaynak kodu değişikliği yapılmadan envanter | Tamamlandı | Bu commit öncesinde kod/test değişikliği yok |
| Birleşik input edge-case karakterizasyonu | Sonraki uygulama adımlarına devredildi | Eksik test listesi bölüm 5 |

**Aşama 3.1 kararı:** Kaynak kodu ve davranış envanteri tamamlandı. Bu alt aşamada uygulama koduna dokunulmadı. Mevcut testler temel davranışları kanıtlıyor; birleşik input ve rota yaşam döngüsü edge-case'leri henüz kanıtlamıyor. Bu eksikler 3.2 ve 3.3 uygulama değişikliklerinden önce hedefli regresyon testleriyle kapatılmalıdır.

## 10. Aşama 3.2 için devredilen karar noktaları

1. Klavye manuel intent'i fare rotasını iptal eder; mevcut GameWindow davranışı korunmalıdır.
2. Fare hareketinin Shift/Alt modu mevcut kodda NORMAL'dir. Teknik mimarinin önerdiği mod politikası, ürün davranışına dönüştürülmeden önce test ve karar kaydıyla sabitlenmelidir.
3. Focus kaybında klavye durur, fare rotası mevcut kodda devam eder. Bu davranış korunacaksa açıkça test edilmelidir.
4. Panel dışı tıklama mevcut fare hedefini temizlemez. Yeni komut üretmemesi ile aktif komutu iptal etmesi ayrı kararlardır.
5. Pause/resume fare hedefini korur; save/load ve runtime replacement için route state invalidation testi eklenmelidir.
6. Aynı hedefe tekrar tıklama mevcut kodda özel dedup davranışına sahip değildir; rota cache politikası tanımlanmalıdır.
7. Dinamik occupancy her path sorgusunda tazelenir. Rota cache'e geçildiğinde bir sonraki edge, güncel occupancy ve statik physics snapshot ile yeniden doğrulanmalıdır.
8. Yaklaşma yavaşlaması mevcut integrator ile uygulanamaz; bu bağımlılık Aşama 3.5'te ertelenmiş olarak raporlanmalıdır.

**Sonuç:** Aşama 3.1 envanter teslimatı tamamlandı. Aşama 3.2'ye geçiş için teknik engel yoktur; sonraki uygulama alt aşamasında önce kararları hedefli testlerle sabitleyip sonra kod değişikliğine başlanmalıdır.
