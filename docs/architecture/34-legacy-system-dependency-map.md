# Legacy Sistemler — Bağımlılık Haritası ve Geçiş Planı

Bu belge `fix/phase-1-critical-stability` dalındaki kaynak kodu ve mevcut mimari
kayıtları temel alır. Amaç eski API'leri kaldırmak değil; sahipliklerini,
tüketicilerini ve güvenli geçiş koşullarını görünür kılmaktır.

## 1. Karar özeti

- Bu çalışma kapsamında hiçbir legacy sınıf, modül veya public import kaldırılmaz.
- `core.time.Tick` tek canonical Tick sınıfıdır. `time_system.Tick` ve
  `time_system.tick.Tick` aynı sınıfı yeniden export eder; ikinci bir Tick
  implementasyonu bulunmaz.
- `core.domain.spatial.Position` immutable canonical değer nesnesidir.
  `core.entity.position.Position` ise Entity'nin eski mutable API'sini
  koruyan, canonical Position değerini içeride kullanan adaptördür.
- Eski EventBus/EventQueue/EventManager ve callback Scheduler farklı
  sorumluluklar taşır. Bunlar canonical transport/dispatcher/scheduler ile
  davranış eşdeğerliği kanıtlanmadan birleştirilmemeli veya silinmemelidir.
- Deprecated uyarısı yalnızca metadata'da açıkça `deprecated=True` olan
  API'lere verilir. `compatibility`, `alias` ve `projection` statüleri
  desteklenen geçiş yüzeyleridir; sırf eski oldukları için DeprecationWarning
  üretmemelidir.

## 2. Tick sınıflarının gerçek durumu

| Import yolu | Gerçek rol | Karar |
|---|---|---|
| `core.time.Tick` | Immutable, sıralanabilir, non-negative canonical simulation-time value object | Tek otorite |
| `time_system.tick.Tick` | `core.time.Tick` import/re-export | Legacy import yolu korunur |
| `time_system.Tick` | `time_system.tick.Tick` üzerinden public re-export | Legacy public import korunur |

`time_system/tick.py` içindeki diğer içerikler (GameTime, takvim sabitleri ve
`random_start_tick`) ayrı bir sorumluluktur; Tick'in tekilleştirilmesi bu
modülün tamamının kaldırılabileceği anlamına gelmez.

`core.clock.GameClock` Tick'i doğrudan `core.time` paketinden alır. Buna
karşılık eski takvim, callback scheduler ve zaman sabitleri `time_system`
yüzeyinde yaşamaya devam eder.

## 3. Position sınıflarının görev ayrımı

### Canonical: `core.domain.spatial.position.Position`

- Immutable (`frozen=True`) ve karşılaştırılabilir koordinat value object.
- Sonlu sayısal koordinatları doğrular; `translated()`, `distance_to()`,
  `to_dict()` ve persistence dönüşümlerini sağlar.
- World sınırı, çarpışma, hareket izni veya gameplay politikası uygulamaz.
- Yeni domain, simulation, actor, movement ve persistence kodunun tercih
  etmesi gereken tiptir.

### Compatibility adapter: `core.entity.position.Position`

- Eski Entity API'sinin mutable `x/y`, `move()`, `set_position()`,
  `copy()`, `distance_to()` ve `get_position()` davranışını korur.
- Koordinatları kendi mutable primitive alanlarında değil, içeride canonical
  immutable Position nesnesi tutarak saklar.
- `to_canonical()` ile canonical değeri açıkça verir.
- Üretim kodunda doğrudan import edilen başlıca sahipler
  `core.entity.entity.Entity` ve `core.application.session` içindeki eski
  Entity/session uyumluluk akışıdır. Entity'nin public mutable davranışı
  kaldırılmadan bu adaptör silinemez.

**Geçiş kuralı:** Yeni kod canonical Position kullanır. Eski Entity
sözleşmesinin kaldırılması ayrı bir major-version kararıdır; adaptörün
canonical nesne saklaması tek başına kaldırma gerekçesi değildir.

## 4. Legacy event sistemleri

| Bileşen | Sorumluluk | Mevcut bağlantılar | Canonical yön |
|---|---|---|---|
| `core.events.Event` | 1.x olay zarfı; `tur/veri/zaman` taşır, zaman alanı wall-clock metadata'sıdır | EventQueue, EventBus, EventManager ve legacy World event akışı | `SimulationEvent` |
| `core.events.EventQueue` | FIFO legacy olay kuyruğu | EventManager; LegacyWorldRuntime; legacy adapter/regression testleri | `CanonicalEventTransport` |
| `core.event_bus.EventBus` | EventHandler aboneliklerini yönetir ve EventQueue içeriğini handler'lara dağıtır | EventManager üzerinden Game ve GameApplication; legacy testler | `CanonicalEventDispatcher` |
| `core.event_manager.EventManager` | Event oluşturma, kuyruğa alma, bus üzerinden yayınlama/işletme facade'ı | `core.game.Game`, `application.game_application.GameApplication`, testler | Canonical transport + dispatcher; uygulama event üretim sınırı |
| `core.simulation.transport.LegacyEventAdapter` | Legacy Event'i canonical SimulationEvent'e dönüştürür | WorldRuntimeBoundary'in World event aktarımı | Geçiş adaptörü; kaldırma hedefi değil |

Önemli ayrım: EventBus bir subscriber/handler modeli sunar; canonical
EventTransport ise deterministik olay taşıma kuyruğudur. Canonical
EventDispatcher consumer kayıtlarını yönetir. Bu nedenle EventBus ile
EventTransport bire bir aynı sınıfın iki adı değildir. Handler davranışları,
consumer filtreleri, kayıt sırası, yeniden giriş, hata halinde event'in
korunması ve aynı tick sıralaması ayrı ayrı karşılaştırılmalıdır.

### Event sistemi bağımlılık grafiği

```text
Game ───────────────────────┐
                            ├─> EventManager ──> EventBus ──> EventHandler
GameApplication ────────────┘        │
                                     └──────────> EventQueue

World ──> LegacyWorldRuntime ──> EventQueue
  │              │
  │              ├──────────────> GameClock ──> callback Scheduler
  │              └──────────────> legacy event üretimi
  │
  └─ WorldRuntimeBoundary ──> LegacyEventAdapter ──> CanonicalEventTransport
                                                        │
                                                        └─> CanonicalEventDispatcher
```

`core.event_manager.EventManager` başlangıçta migration matrix dışında
kalmıştı. A aşamasında ayrı compatibility kimliği, AST scanner kaydı ve
runtime constructor sayacı eklendi. Bu kayıt EventManager'ı deprecated yapmaz;
Game ve GameApplication canonical-backed adapter kullanır; public EventBus handler API'si compatibility statüsünde tutulur.

## 5. ActionManager ve Scheduler

### `core.actions.ActionManager`

- Mutable 1.x Action nesnelerini oluşturur, başlatır, günceller ve tamamlar.
- Güncel Game/GameApplication uygulama yolu doğrudan ActionManager kurmaz;
  `CanonicalActionAdapter`, canonical `ActionProcessor` üzerine 1.x şekilli
  bir facade sağlar.
- Eski ActionManager public import'u ve doğrudan davranış testleri korunur.
- Önce dış/legacy tüketicilerin adapter veya canonical ActionProcessor'a
  taşındığı doğrulanmalıdır.

### `time_system.Scheduler`

- Callback tabanlıdır; `GameClock` ilerlediğinde zamanı gelen callback'leri
  çalıştırır.
- `LegacyWorldRuntime` tarafından oluşturulan LegacyCallbackSchedulerAdapter ile GameClock'a bağlanır.
- `WorldRuntimeBoundary.advance_world()`, canonical SimulationRuntime
  tick'ini ilerletip World saatine projection yapar; `world.advance(0)`
  çağrısı aynı tick'teki legacy callback işlerini işler.
- Bu callback semantiği canonical `core.simulation.CanonicalScheduler` ile
  aynı değildir. Canonical scheduler callback çalıştırmaz; deterministik
  `ScheduledWork` kayıtları üretir ve `pop_ready()` ile tüketiciye verir.

**Geçiş kuralı:** Callback'lerin sahibi ve yan etkileri envantere alınmadan
legacy Scheduler, GameClock veya World.advance zinciri devreden çıkarılmaz.

## 6. Tüketici envanteri ve doğrulanmış kapsam

- `Game` ve `GameApplication`: EventManager üzerinden legacy olay kuyruğu
  yüzeyini tutar; action işlemlerinde CanonicalActionAdapter kullanır.
- `EventManager`: EventBus ve EventQueue varsayılanlarını oluşturur; event
  oluşturma/kuyruklama/işletme facade'ıdır.
- `LegacyWorldRuntime`: GameClock, EventQueue ve canonical-backed callback
  scheduler adapter'ının birlikte yaşadığı compatibility sahibidir.
- `WorldRuntimeBoundary`: canonical tick'i authoritative kaynak kabul eder;
  World clock projection'ını eşitler ve legacy callback zincirini aynı tick'te
  işler. Legacy World event'lerini LegacyEventAdapter ile canonical
  transport'a aktarır.
- `Entity`: legacy mutable Position adaptörünün public sahibi olmaya devam
  eder.
- Canonical domain/time/simulation katmanlarının legacy runtime modüllerine
  bağımlı olmaması architecture testleriyle sınırlandırılmıştır.
- `ActionManager` üretim uygulama yolunda doğrudan kullanılmaz; testler ve
  public 1.x API yüzeyi nedeniyle tutulur.

Bu envanter statik import ve kod incelemesiyle doğrulanmıştır. Dinamik import,
reflection, plugin/harici istemci ve çalışma anında üretilen bağımlılıklar
statik taramanın kapsamı dışındadır. Dış kullanıcı bulunmadığı sonucu
çıkarılmamalıdır.

## 7. Deprecated API uyarı politikası

Mevcut ortak mekanizma `core.compatibility.deprecation` içindedir:

- `LEGACY_API_MATRIX` her kayıt için durum, canonical karşılık, sürüm,
  migration notu ve blocker bilgisini taşır.
- `@deprecated_api("...")` fonksiyon/metot çağrısında ortak
  `warn_deprecated()` yolunu kullanır.
- `warn_deprecated()` yalnızca `deprecated=True` kayıtlar için
  `DeprecationWarning` üretir ve runtime kullanım sayacını artırır.
- `compatibility`, `alias` ve `projection` statüsündeki API'ler şu an
  desteklenen geçiş yüzeyleridir; otomatik warning almamaları bilinçlidir.
- Bu dalda açıkça deprecated işaretlenmiş API
  `Game.dunya_olaylarini_aktar` sınırıdır. Canonical karşılığı
  `dunya_olaylarini_canonical_aktar`dır. İç forwarding bu uyarıyı tekrar
  üretmemek için wrapper'ın `__wrapped__` fonksiyonunu kullanır.

Yeni bir API deprecated ilan edilmeden önce canonical karşılığı, migration
talimatı, deprecated sürümü ve kaldırma fazı belirlenmelidir. Sınıf
constructor'larına dağınık `warnings.warn` çağrıları eklenmemeli; tüm
uyarılar ortak decorator/helper üzerinden geçmelidir. Warning'ler
`DeprecationWarning` kategorisinde kalmalı; testlerde
`warnings.catch_warnings` ile açıkça yakalanmalıdır.

## 8. Güvenli geçiş planı

### Aşama A — Envanteri kapat (silme yok)

1. CI üzerinde `python -m core.compatibility.usage .` çıktısını güncel
   branch head için üret ve commit SHA ile sakla.
2. EventManager'ı compatibility matrix/statik tarayıcıda ayrı kimlik olarak
   izleme gereksinimini değerlendir.
3. Her legacy kullanım için dosya, satır, kullanım türü (import, construction,
   inheritance, method, runtime) ve sahibi kaydet.
4. Harici public API kullanıcıları ve plugin/extension noktaları için ayrıca
   kanıt topla.

**Çıkış ölçütü:** Bilinen üretim içi ve test tüketicileri listelenmiş; dinamik
ve harici kullanım belirsizliği açıkça kayıtlı olmalı.

### Aşama B — Davranış sözleşmelerini sabitle

1. Tick için import identity, karşılaştırma, aritmetik ve persistence testleri.
2. Position için mutable Entity API'si ile immutable canonical değer
   davranışını ayıran testler.
3. Event sistemi için FIFO, handler sırası, filtreleme, event ekleme,
   re-entrancy ve handler exception semantiği.
4. Scheduler için aynı tick sıralaması, cancel, callback yan etkileri,
   callback'in callback eklemesi ve World.advance(0) davranışı.
5. ActionManager adapter'ı için Action ID, lifecycle, hata ve sonuç
   eşleştirmesi.

**Çıkış ölçütü:** Her eski davranış için canonical eşdeğer veya bilinçli
uyumsuzluk kararı testle belgelenmiş olmalı.

### Aşama C — Tüketicileri kademeli taşı

1. Yeni kodda yalnızca canonical Tick/Position/SimulationEvent/
   CanonicalEventTransport/CanonicalEventDispatcher/CanonicalScheduler/
   ActionProcessor kullan.
2. Eski tüketicileri tek tek adapter veya canonical API'ye taşı.
3. Her taşıma sonrasında static usage raporunu ve runtime counter'larını
   karşılaştır.
4. Legacy API'nin kalan kullanıcılarını ve blocker'larını güncelle.

**Çıkış ölçütü:** Uygulama içi kullanım sıfırlanmış olsa bile public API ve
harici istemci uyumluluğu ayrıca doğrulanmış olmalı.

### Aşama D — Deprecation ve major-version kararı

1. Ancak tüketici göçü tamamlandıktan sonra ilgili matrix kaydını
   `compatibility` durumundan `deprecated` durumuna geçir.
2. Canonical replacement ve sürüm notlarını yayımla; ortak warning
   mekanizmasını API giriş noktasına uygula.
3. Warning'leri CI'da kontrollü biçimde doğrula; ilk aşamada warning'i
   error'a çevirerek mevcut tüketicileri aniden kırma.
4. Kaldırma için en az bir duyurulmuş deprecation dönemi, sıfır bilinen
   production/runtime kullanımı, güncel regression testleri ve major-version
   onayı şartı koy.
5. Ancak bu şartlar sağlanırsa ayrı bir değişiklikte silme yap.


### Aşama E — Kontrollü emeklilik kapısı

1. A-D çıkış ölçütleri tamamlanmadan hiçbir legacy API, import yolu veya
   callback davranışı kaldırılmaz.
2. Kaldırma öncesi son sürümde static kullanımın sıfır olduğu, runtime
   sayaçlarında üretim kullanımının bulunmadığı ve harici tüketici/plugin
   sahiplerinin yazılı olarak doğrulandığı kanıtlanır.
3. Kayıt/persistence, aynı-tick sıralaması, hata/yeniden-deneme ve eski save
   uyumluluğu regresyonları geçmeden emeklilik onaylanmaz.
4. Her API ayrı değişiklik ve ayrı major-version kararıyla emekli edilir;
   EventManager, EventBus, EventQueue ve Scheduler tek paket halinde silinmez.
5. Herhangi bir koşul belirsizse sonuç **KEEP** olur: API korunur, blocker
   kaydedilir ve ölçüm sürdürülür.

**E aşamasının sonucu:** Public EventManager/EventBus/EventQueue ve Scheduler
API'leri adapter'larla korunur; mutable Entity Position da dışa açıktır.
Harici istemci kapsamı statik taramayla kanıtlanamaz. Bu nedenle emeklilik
koşulları sağlanmamıştır ve hiçbir legacy sistem kaldırma onayı alamaz.

## 9. A-E uygulama kaydı

- **A — Envanter:** EventManager ayrı compatibility kimliği olarak matrix ve
  AST scanner kapsamına eklendi. Constructor runtime kullanım sayacıyla
  izleniyor. Testler matrix kaydını, statik import görünürlüğünü ve runtime
  sayaçlarını kapsıyor. Scanner dinamik/reflection ve harici tüketicileri
  kanıtlayamaz; CI çıktısının bu branch head için ayrıca doğrulanması gerekir.
- **B — Davranış sözleşmesi:** EventManager FIFO kuyruk/handler dispatch
  regresyonuna ek olarak EventBus abonelik snapshot'ı, dispatch sırasında
  subscribe/unsubscribe, re-entrant publish ve handler exception/queue
  devamlılığı testleri eklendi. Legacy Scheduler için FIFO, callback içinden iptal,
  callback ekleme, exception sonrası tekrar çalıştırmama ve iptal idempotency
  testleri eklendi. Scheduler, callback öncesi olayı kuyruktan çıkarır; hata
  halinde henüz çalışmamış hazır olayları sonraki çağrıya bırakır. Canonical
  ActionProcessor ile 1.x Action görünümü arasındaki ID, start/completion ve
  failure eşleştirmesi testlerle sabitlendi. Tick/Position mevcut testleri
  korunuyor. Bu kayıt testlerin CI'da çalıştığı anlamına gelmez; sonuç commit
  SHA'sına bağlı Actions doğrulamasıyla ayrıca teyit edilmelidir.
- **C — Tüketici göçü:** Uygulama içi event üretim ve kuyruk tüketim
  yolları CanonicalEventManagerAdapter üzerine taşındı. Game ve
  GameApplication artık doğrudan EventManager kurmuyor; canonical
  CanonicalEventTransport kuyruk sahibidir. Legacy Event, EventQueue
  görünümü ve EventBus handler yüzeyi adapter sınırında korunur. Bu sayede
  FIFO, aynı Event nesnesi kimliği, re-entrant publish ve handler exception
  sonrasında kalan kuyruğun korunması sürdürülür.
- **C — Scheduler göçü:** World'ün callback API'si
  LegacyCallbackSchedulerAdapter üzerinden CanonicalScheduler typed-work
  kayıtlarına taşındı. Callable nesneleri canonical work payload'ına konmaz;
  adapter'ın callback registry'sinde tutulur. Tek tek tüketim sayesinde
  callback içinden iptal, aynı çağrıda yeni işin ertelenmesi ve exception
  sonrası kalan işlerin korunması sağlanır. World public schedule_event,
  cancel, pending count ve clock API'leri korunur; clock reset canonical
  scheduler zaman çizelgesini de sıfırlar.
- **C — Action ve World event sınırı:** Game ve GameApplication'ın action
  yüzeyi zaten CanonicalActionAdapter üzerinden ActionProcessor kullanır.
  GameApplication World event'lerini WorldRuntimeBoundary üzerinden
  canonical transport'a yönlendirir. Core Game'in açıkça deprecated legacy
  forwarding metodu public uyumluluk için tutulur; yeni canonical aktarım
  metodu mevcuttur.
- **C çıkış kararı:** Uygulama içindeki Game/GameApplication EventManager
  kuyruk sahipliği ve World callback scheduler tüketicileri canonical
  implementasyonlara taşınmıştır. Public 1.x yüzeyleri adapter olarak
  korunmuştur; dış istemci/reflection/plugin kullanımı statik taramayla
  kanıtlanamayacağı için silme veya toplu deprecation yapılmamıştır.
- **D — Deprecation:** Tek kontrollü deprecation sınırı
  `Game.dunya_olaylarini_aktar` olarak tutulur; aynı metadata kimliği
  `GameApplication` içindeki 1.x forwarding façade'ına da uygulanır.
  Warning mesajı deprecated sürümünü, canonical replacement'ı ve en erken
  removal fazını bildirir; kaldırmanın ayrı major-version kararı ve harici
  tüketici kontrolü gerektirdiğini açıkça söyler. Testler iki façade'da da
  tek warning üretildiğini ve runtime sayacının arttığını doğrular.
  EventManager/EventBus/EventQueue/Scheduler, mutable Position ve projection
  API'leri dış kullanıcı kapsamı bilinmediği için compatibility/alias/projection
  durumunda kalır; toplu deprecation yapılmaz.
- **E — Emeklilik kapısı:** Sonuç KEEP / kaldırma yok. Public API ve
  harici tüketici kapsamı için yazılı doğrulama bulunmadığından hiçbir legacy
  API silinmeye uygun değil.

GitHub Actions, bu değişikliklerin her commit'inde otomatik test çalıştırır.
Bu oturumda yerel Python komutu çalıştırıldığı iddia edilmemektedir; sonuçlar
ilgili commit SHA'larına bağlı GitHub Actions kayıtlarından doğrulanır.

## 10. Şimdiki karar

Aşama C'nin uygulama içi tüketici göçü canonical-backed adapter'larla
tamamlandı. Aşama D'de yalnızca önceden tanımlanmış World-event forwarding
sınırı kontrollü deprecation altında tutulur; Game ve GameApplication
façadeleri aynı warning kimliğini kullanır. Warning mesajı replacement,
deprecated sürümü ve removal kapısını belirtir. Diğer public 1.x API'leri
harici tüketici kapsamı kanıtlanamadığı için korunur. Aşama E'nin kaldırma
kapısı kapalıdır: hiçbir legacy API bu değişiklikte silinmez.
