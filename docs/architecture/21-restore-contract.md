# Phase 9 — Canonical State Restore & Persistence Adapter Boundary

## 1. Purpose

FAZ 9, canonical persistence state'in validate edilmesi ve gelecekte runtime'a
aktarılacağı sınırları tanımlar.

**REAL SAVE/LOAD IS NOT IMPLEMENTED IN CORE 2.0 PHASE 9.**

## 2. Serialization vs Restore

Serialization representation üretir; restore canonical state'i doğrular ve
`CanonicalRestoreState` planı üretir. Restore doğrudan disk, JSON veya database
bilmez.

## 3. Validation boundary

`RestoreContract.validate()` yalnızca hata listesini döndürür.
`RestoreContract.prepare()` validation başarılıysa immutable restore planı
üretir. Hatalı state runtime'a uygulanmaz.

## 4. Canonical restore state

Restore girdisi `CanonicalSessionState`'tir: World records, entity records,
membership records, active World ID ve simulation Tick.

## 5. Restore dependency order

1. Schema/version validation
2. Primitive/value-object validation
3. World identity/state
4. Entity identity/state
5. EntityRepository records
6. WorldMembership records
7. Active World ID
8. Simulation Tick
9. Canonical session state
10. Runtime activation

## 6. World restore

World yalnızca `WorldDomainState` olarak restore edilir. Scheduler, clock,
EventQueue, dispatcher, callbacks ve repository oluşturulmaz.

## 7. Entity restore

Entity restore boundary `CanonicalEntityRecord` ve `EntityRepositoryState`'tir.
Duplicate EntityId reddedilir. Unknown/gameplay-specific entity type'ları bu
fazda activation açısından DEFERRED'dır; gameplay entity factory uygulanmaz.

## 8. Membership restore

Ownership `entity_id → world_id` mapping'i ile kurulur. `Entity.world_id` ve
`World._entities` restore source değildir. Unknown reference, duplicate mapping
ve multiple World ownership validation hatasıdır.

## 9. Session restore

GameSession doğrudan deserialize edilmez. `CanonicalSessionState` gelecekte
GameSession construction boundary'sine verilecek canonical girdidir.

## 10. Simulation Tick restore

Yalnızca non-negative integer `core.time.Tick` restore edilebilir. Wall-clock,
datetime, sleep ve monotonic time restore edilmez.

## 11. Atomic restore contract

Akış `prepare → construct → activate` şeklindedir. Activation yalnızca plan
başarıyla hazırlandıktan sonra çağrılır. Invalid restore için
`INVALID STATE → VALIDATION ERROR → NO ACTIVE RUNTIME MUTATION` garantisi
vardır. Gerçek transaction/rollback implementation'ı yoktur.

## 12. Runtime activation boundary

`RuntimeActivationBoundary.activate(plan, activator)` teknoloji-bağımsız bir
callback sınırıdır. Persistence katmanı runtime object graph veya gameplay
nesnesi oluşturmaz.

## 13. Persistence adapter boundary

`PersistenceAdapter` yalnızca external representation → `CanonicalSessionState`
contract'ını tanımlar. File system, JSON, SQLite, network veya binary backend
bilmez.

## 14. Schema migration boundary

`PersistenceMigrationBoundary` stored schema version'ı current version ile
karşılaştırır. v1 → v2 dönüşümleri bu fazda uygulanmaz; unsupported version açık
hata üretir. Persistence schema version, event schema version'dan ayrıdır.

## 15. Compatibility exclusion

EventBus, EventQueue, GameClock, legacy Scheduler, ActionManager,
`Entity.world_id`, `World._entities`, legacy Position/Tick ve dispatcher
consumer state'i canonical restore source değildir.

## 16. Determinism

Entity, World ve membership kayıtları canonical sıralama ile tutulur. Aynı state
aynı restore planını ve aynı logical runtime state'i üretir.

## 17. Error handling

Eksik required field, incompatible type, invalid value, duplicate identity,
unknown reference ve unsupported schema version sessizce yutulmaz; açık
validation error üretilir.

## 18. Explicit non-goals

Save/load, file I/O, JSON storage, database, slots, autosave, compression,
encryption, event replay, event sourcing, gameplay persistence ve legacy API
removal bu fazın dışındadır.

## 19. Future save/load architecture

```text
External storage
      ↓
Future persistence adapter
      ↓
CanonicalSessionState
      ↓
RestoreContract.prepare()
      ↓
RuntimeActivationBoundary
```
