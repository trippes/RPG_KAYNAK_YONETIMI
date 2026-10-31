# Serialization Contract

Bu belge implementation değildir; save/load adapter'larının uyması gereken
contract'tır.

## Envelope

Her snapshot aşağıdaki üst alanları taşır:

```json
{
  "schema": "rpg-core",
  "schema_version": 1,
  "core_version": "2.0",
  "snapshot_id": "...",
  "simulation_tick": 0,
  "state": {}
}
```

## Kurallar

1. `schema` sabit kimliktir.
2. `schema_version` integer ve migration anahtarıdır.
3. `core_version` bilgilendirici sürümdür; migration kararı schema version ile verilir.
4. `simulation_tick` zorunludur; wall-clock timestamp zorunlu değildir.
5. Snapshot deterministik sıralanabilir olmalıdır.
6. Runtime callback, function, open file veya UI object serialize edilmez.
7. Entity ve World referansları ID ile tutulur.
8. Enum değerleri stabil string contract olarak yazılır.
9. Bilinmeyen alanlar forward-compatible okuyucular tarafından tolere edilir.
10. Eksik zorunlu alanlar açık bir schema validation hatası üretir.

## Core state kapsamı

Core snapshot'ı yalnızca şu altyapı state'lerini kapsar:

- Game/session state
- World registry ve active world ID
- World metadata
- Entity identity, state ve position
- Clock tick
- Pending actions
- Scheduler kayıtları, yalnızca serializable command verisiyle

Gameplay state'i ayrı namespace altında versioned extension olarak eklenir.

## Phase 8 canonical boundary

Persistence state yalnızca canonical domain/application state'tir. Canonical
ID'ler primitive string, `Position` koordinat object'i ve `Tick` non-negative
integer olarak temsil edilir. `WorldDomainState`, entity records ve membership
mapping ayrı state bölümleridir; repository'nin internal dict'i persistence
formatına sızmaz.

Persistence `schema_version`, `SimulationEvent.schema_version` ile farklıdır.
İlk persistence schema version `1` ve schema identifier `rpg-core`'dur.
Bilinmeyen gelecek alanlar tolere edilir; eksik zorunlu alanlar veya desteklenmeyen
version açık schema hatası üretir.

`Entity.world_id`, `World._entities`, EventBus/EventQueue, GameClock,
time_system.Scheduler, ActionManager, legacy Position/Tick, callback'ler ve
transient runtime nesneleri canonical persistence state değildir.

## Phase 9 — Canonical State Restore & Persistence Adapter Boundary

- `CanonicalSessionState` için validate → prepare → activate ayrımı tanımlandı.
- `RestoreContract` deterministic, atomic restore planı üretir; invalid state
  activation callback'ine ulaşmaz.
- `PersistenceAdapter` technology-agnostic decode sınırı ve yalnızca version
  gate'i yapan migration boundary eklendi.
- Runtime graph, event replay, event sourcing ve gerçek save/load bu fazın
  dışındadır.
