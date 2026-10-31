# Core 2.0 Simulation Runtime

## Canonical flow

```text
SimulationRuntime.advance_to(Tick)
        ↓
CanonicalScheduler.advance_to(Tick)
        ↓
ScheduledWork ordered by (trigger_tick, sequence)
        ↓
ActionProcessor
        ↓
SimulationEvent lifecycle stream
```

Runtime target tick'e ileri sıçrayabilir. Action transition zamanı runtime'ın
hedef tick'i değil, ilgili `ScheduledWork.trigger_tick` değeridir. Bu kural
aynı başlangıç state'i ve aynı scheduled work sırası için deterministic sonuç
sağlar.

`SimulationRuntime` gerçek zaman, sleep, timer veya wall-clock kullanmaz.

Runtime'ın `event_transport` alanı ActionProcessor tarafından üretilen tüm
canonical lifecycle event'lerinin ortak kuyruğudur. `advance_to()` eventleri
uyumluluk için tuple olarak döndürmeye devam eder; aynı eventler transport'ta
consumer erişimi için tutulur. World-local legacy olayları
`dispatch_world_events()` ile World tick'i kullanılarak aynı transport'a
aktarılır.

## Scope

Bu runtime gameplay simulation yapmaz. Yalnızca Core action lifecycle ve
scheduled work işleme altyapısını sağlar.

## Compatibility

Mevcut `Game.zamani_ilerlet()`, `GameClock`, `time_system.Scheduler` ve
`core.actions.ActionManager` 1.x compatibility yollarıdır. Canonical runtime
`Game.session.simulation` üzerinden erişilir.

Phase 10'da `SimulationRuntime`, `CanonicalScheduler`, `ActionProcessor`,
`CanonicalEventTransport` ve dispatcher birlikte frozen application boundary'dir.
