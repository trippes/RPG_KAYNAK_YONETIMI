# Core 2.0 Time Model

## İki ayrı zaman

### Simulation time

- Canonical API'de `core.time.Tick` ve event'lerde `simulation_tick` ile temsil edilir.
- World state, Action, Scheduler ve Event ordering yalnızca bunu kullanır.
- Monotonic ve deterministic olmalıdır.
- Save/load ve replay için serialize edilir.

### Wall-clock time

- `datetime.now()` gibi sistem zamanıdır.
- Sadece logging, telemetry veya IO metadata'sıdır.
- Simulation state veya event ordering için kullanılamaz.
- Replay ve restore sırasında gerekli değildir.

## Clock contract

Canonical clock/progression sınırı `SimulationRuntime.advance_to()` ve
`advance_by()` metodlarıdır. İlerletme işlemi yalnızca `Tick` kabul eder; clock
doğrudan gameplay çağırmaz. Scheduler zamanı geldiğinde hazır kayıtları çıkarır.

## Determinism

Aynı başlangıç snapshot'ı, aynı input command listesi ve aynı random seed ile
aynı simulation event akışı üretilmelidir. Wall-clock farklılıkları sonucu
değiştiremez.

## 1.x migration

`Event.zaman` ve doğrudan `int` time API'leri compatibility katmanında tutulur.
Canonical 2.x event'leri `simulation_tick` taşır. Mevcut `time_system.Tick`,
1.x compatibility API'sidir; bu fazda değiştirilmemiştir.

Persistence'ta yalnızca canonical simulation tick saklanabilir. `datetime.now()`,
`time.time()`, sleep, GameClock iç state'i ve wall-clock ölçümleri persistence
state değildir.

FAZ 7'de World içindeki clock `LegacyWorldRuntime` delegate'ine taşınmıştır.
Bu, 1.x `World.advance()` ve clock API'lerini koruyan compatibility projection'dır.
Yeni 2.x kodu `GameSession.simulation`/`WorldRuntimeBoundary` üzerinden
`core.time.Tick` kullanır; World domain contract'ı zamanı mutate etmez.

## Phase 9 persistence

Restore yalnızca non-negative simulation `Tick` kabul eder. Wall-clock,
`GameClock`, scheduler timing ve callback zamanı canonical restore state'e
girmez.
