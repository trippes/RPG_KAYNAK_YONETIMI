# Core 2.0 Canonical Scheduler

## Model

Canonical scheduler callback çalıştırmaz:

```text
CanonicalScheduler
    → ScheduledWork
    → SimulationRuntime
    → ActionProcessor / consumer
```

`ScheduledWork` şu alanları taşır:

- `trigger_tick: Tick`
- `sequence: int`
- `work_id: str`
- `work_type: str`
- immutable payload mapping

## Ordering

İşler `(trigger_tick, sequence)` sırasıyla çıkarılır. Aynı tick içindeki
işlerde insertion sequence deterministik ordering sağlar.

## Cancellation

Cancellation work item ID üzerinden yapılır. İptal edilen iş `pop_ready()`
sonucuna girmez. İkinci cancellation isteği `False` döndürür.

## Invalid scheduling

Mevcut scheduler tick'inden küçük bir tick'e scheduling `ValueError` üretir.
Simulation progression geriye gidemez.

## Compatibility

Mevcut callback tabanlı `time_system.Scheduler` bu fazda değiştirilmemiştir.
Gameplay callback zinciri canonical scheduler'a bağlanamaz.

Freeze contract: schedule aynı Tick'te insertion sequence ile deterministiktir,
geçmiş Tick reddedilir, simulation zamanı geriye gidemez ve cancellation
callback çalıştırmaz.
