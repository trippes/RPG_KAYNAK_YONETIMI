# Core 2.0 — Architecture Freeze

## 1. Phase 10 sonucu

Core 2.0 final integration, stabilization ve architecture freeze sınırıdır.
Yeni gameplay geliştirmez ve Core 2.1 World Model'e başlamaz.

## 2. Canonical architecture

```text
foundation → domain → time/events → application → simulation
           → gameplay/adapters (Core dışı tüketiciler)
```

Foundation ID/Position/Tick; runtime-free domain; application repository,
membership ve session; canonical simulation runtime; persistence state ve
restore boundary Core 2.0 kapsamındadır.

## 3. Dependency rules

- Domain application, simulation, gameplay veya persistence import etmez.
- Canonical simulation legacy event/time modüllerini import etmez.
- Persistence gameplay, legacy runtime veya concrete backend import etmez.
- Core içinde circular dependency yoktur.
- Compatibility canonical core'u kullanabilir; yön tersine çevrilmez.

## 4. Ownership rules

`EntityRepository` entity registry'nin, `WorldMembershipService` ise tek
canonical Entity–World ownership writer'ının authoritative kaynağıdır.
`Entity.world_id` ve `World._entities` compatibility projection'dır. Duplicate
membership, multiple-world ownership ve non-atomic transfer kabul edilmez.

## 5. Time, event and action rules

Canonical simulation zamanı yalnızca non-negative `Tick`'tir; wall-clock,
datetime, sleep ve timer kullanılmaz. Event akışı
`SimulationEvent → CanonicalEventTransport → CanonicalEventDispatcher` olup
ordering `(simulation_tick, insertion_sequence)` ile deterministiktir.
Action lifecycle kontrollü state transition'lara sahiptir. Canonical scheduler
callback çalıştırmaz, `ScheduledWork` üretir; geçmiş Tick ve geriye zaman
ilerlemesi reddedilir.

## 6. Persistence and restore

`CanonicalSessionState` runtime object graph değildir. Restore sırası schema/
version, value objects, worlds, entities, repository, membership, active world,
Tick ve session'dır. Akış `validate → immutable plan → activation boundary`dir;
invalid state activation callback'ine ulaşmaz. Adapter teknoloji bağımsızdır.

Gerçek save/load, disk I/O, database, slot, autosave, compression, encryption,
replay ve event sourcing kapsam dışıdır.

## 7. Compatibility and migration

EventBus, EventQueue, EventType, GameClock, legacy Scheduler, ActionManager,
legacy Action/Position/Tick, `Entity.world_id`, `World._entities` ve
`Game.dunya_olaylarini_aktar()` silinmez. Matrix, deprecation metadata, static
scanner ve runtime counter korunur; compatibility yönü canonical core'a doğru
olabilir, tersi olamaz.

## 8. Validation and freeze criteria

Architecture tests, full tests, usage scanner, compileall, `main.py` smoke test
ve source BOM check başarıyla geçmelidir. Dokümantasyon canonical public API,
dependency, ownership, time, event, action, persistence ve compatibility
contract'larıyla senkron tutulur.

## 9. Deferred scope and Core 2.1 boundary

Gameplay, UI, combat, NPC, quest, resource, inventory, economy, gerçek runtime
restore ve persistence backend'i deferred'dır. Core 2.1 World Model; ID/Position/
Tick, repository ownership, membership authority, event ordering, Tick-only
simulation, callback-free scheduler, persistence adapter ayrımı ve compatibility
yönünü değiştiremez. Değişiklik için yeni architecture phase gerekir.
