# Core Runtime Contracts

## Game façade

`Game` 1.x compatibility façade'sidir. 2.x canonical karşılığı
`core.application.GameSession`/application runtime'dır. Façade yalnızca command routing,
lifecycle, registry ve processor orchestration yapar; combat, economy,
character veya resource kuralı taşımaz.

`Game.varlik_ekle()` ve `Game.varlik_cikar()` geçiş döneminde korunur; canonical
ownership işlemleri `GameSession → WorldMembershipService` üzerinden yürür.

## Entity–World ownership

Entity tek bir World'e bağlanabilir. `EntityRepository` yalnızca Entity
object'lerini kaydeder; World membership kararı vermez. Bağlama/ayırma işlemi
application katmanındaki `WorldMembershipService` üzerinden yapılır. Entity,
World projection ve membership registry atomik olarak güncellenir. 1.x
doğrudan metotları compatibility döneminde korunur.

## Event queues

World-local queue, World içinde üretilen olayların staging alanıdır. Global
queue, session dışına sunulan canonical event akışıdır. Runtime dispatcher
world-local olayları sıralı biçimde global queue'ya aktarır; gameplay doğrudan
queue iç yapısına erişmez.

Phase 4'te global akış `CanonicalEventTransport` ile temsil edilir. Runtime,
ActionProcessor ve world dispatcher aynı transport'a enqueue eder; consumer
`peek/dequeue/drain` ile kontrollü erişir. Transport event üretmez ve handler
çalıştırmaz.

Persistence için `GameSession` doğrudan serialize edilmez. Gelecekte
`CanonicalSessionState` üzerinden World metadata, entity records, membership
records, active World ID ve simulation tick ayrı state olarak üretilecektir.
Dispatcher, consumer registration, scheduler implementation ve legacy queue'lar
runtime state olarak dışarıda kalır.

World runtime boundary application katmanındadır: `GameSession.world_runtime`
World compatibility projection'larını canonical SimulationRuntime transport ve
scheduler'a bağlar. World domain facade'ı canonical scheduler, global event
transport veya simulation clock sahibi değildir.

## Event payload and time

Event payload typed ve versioned olmalıdır. 1.x `dict` payload compatibility
formatıdır. Canonical event zamanı `simulation_tick` değeridir. `created_at`
varsa yalnızca gözlem metadata'sıdır ve simulation ordering için kullanılamaz.

## Scheduler and actions

Canonical Scheduler zaman geldiğinde callback yerine typed `ScheduledWork`
üretir. `SimulationRuntime` ve `ActionProcessor` bu kaydı yürütür. Action
lifecycle eventleri:

```text
ActionCreated → ActionStarted → ActionCompleted
                           ├→ ActionCancelled
                           └→ ActionFailed
```

Canonical runtime erişimi `GameSession.simulation` üzerindendir. Mevcut
`GameClock` ve callback tabanlı Scheduler 1.x compatibility yolunda kalır.

## Bounds and Position

`core.domain.spatial.Position` immutable, hashable ve karşılaştırılabilir bir
value object'tir. Yalnızca koordinat biçimini doğrular; World bounds ve
collision policy Position'ın sorumluluğu değildir. Doğrudan mutable koordinat
değişimi canonical API değildir. Movement command, World bounds ve collision
policy kontrolünden sonra yeni Position üretir ve PositionChanged event'i
yayınlar.

`core.time.Tick` immutable, non-negative ve karşılaştırılabilir simulation time
value object'idir. `core.foundation` üst katmanlara bağımlı değildir.

## GameState

GameState session/runtime lifecycle bilgisidir. World clock, Entity state ve
gameplay state'i GameState içine gömülmez.

## Resource boundary

RPG Resource Core domain'i değildir. Core yalnızca generic quantity/unit,
identity ve event contract'ı sağlayabilir; gathering, production, depletion ve
economy kuralları gameplay/simulation katmanında kalır.

## Phase 9 restore sınırı

Restore, `CanonicalSessionState` üzerinden validate → prepare → activate olarak
ayrılır. `GameSession` doğrudan deserialize edilmez; activation yalnızca
validated restore planını alır.
