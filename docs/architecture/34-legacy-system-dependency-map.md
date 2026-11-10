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

`core.event_manager.EventManager` mevcut migration matrix içinde ayrı bir
satır olarak kayıtlı değildir. Bu bir envanter/ölçüm boşluğudur; EventManager
kaldırılmalı anlamına gelmez. Sonraki tooling iyileştirmesinde kendi
compatibility kimliğiyle izlenmesi değerlendirilmelidir.

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
- `LegacyWorldRuntime` tarafından oluşturulur ve GameClock'a bağlanır.
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
- `LegacyWorldRuntime`: GameClock, EventQueue ve callback Scheduler'ın
  birlikte yaşadığı compatibility sahibidir.
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

## 9. Şimdiki karar

Bu değişiklik bir envanter ve geçiş planıdır. Hiçbir legacy sistem silinmez,
davranışı değiştirilmez veya topluca deprecated ilan edilmez. Özellikle
callback Scheduler, EventManager/EventBus/EventQueue ve mutable Entity
Position çalışan compatibility davranışlarıdır; yalnızca yaşları nedeniyle
kaldırılmaları mimari açıdan güvenli değildir.
