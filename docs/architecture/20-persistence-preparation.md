# Phase 8 — Persistence Preparation

## 1. Purpose

Bu faz save/load veya disk formatı uygulamaz. Gelecekteki persistence adapter'ı
için canonical state sınırını tanımlar.

## 2. Persistence boundary

```text
Canonical domain/application state
              ↓
       core.persistence contracts
              ↓
       future save/load adapter
```

`PersistenceDocument` schema identifier `rpg-core` ve schema version `1` taşır.

## 3. Canonical state

Canonical inventory: `EntityId`, `WorldId`, `ActionId`, `EventId`, `Position`,
`Tick`, `WorldDomainState`, entity records, membership records, active World ID
ve simulation tick.

## 4. Runtime state

GameSession implementation graph'ı, WorldManager dictionary'si, scheduler,
dispatcher, consumer registration, EventBus, EventQueue, clock ve callback'ler
runtime state'tir.

## 5. Value-object serialization

ID'ler deterministic primitive string; Position `{x, y}`; Tick non-negative
integer olarak temsil edilir. Her biri type-safe round-trip contract'ına sahiptir.

## 6. Entity persistence boundary

EntityRepository internal dict'i yerine sorted `CanonicalEntityRecord` listesi
kullanılır. Record EntityId, type, canonical state ve canonical Position taşır.

## 7. World persistence boundary

World yalnızca `WorldDomainState` olarak temsil edilir: WorldId, name ve bounds.
Clock, scheduler, local queue ve `_entities` dahil edilmez.

## 8. Membership persistence

`WorldMembershipState`, sorted `entity_id → world_id` kayıtlarından oluşur.
Restore sırasında membership tekrar WorldMembershipService üzerinden kurulabilir.

## 9. GameSession boundary

`CanonicalSessionState` World metadata, entity records, membership records,
active World ID ve simulation tick taşır. Session'ın runtime object graph'ı
serialize edilmez.

## 10. Schema versioning

Persistence `schema_version` ile `SimulationEvent.schema_version` farklıdır.
Unknown future fields tolere edilir; missing required fields ve unsupported
schema version açık validation hatasıdır.

## 11. Determinism

Entity records EntityId'ye, memberships `(entity_id, world_id)` sırasına,
World records WorldId'ye göre sıralanır. Aynı canonical state aynı representation
üretir.

## 12. Compatibility exclusion

`Entity.world_id`, `World._entities`, legacy EventBus/EventQueue, GameClock,
time_system.Scheduler, ActionManager, legacy Position/Tick, callbacks ve
transient runtime objects persistence state değildir.

## 13. Future save/load architecture

İleride bir adapter `CanonicalSessionState` ve `PersistenceDocument` üzerinden
çalışabilir. Migration/version transform katmanı schema version'a göre seçilir.

## 14. Explicit non-goals

Bu fazda dosya I/O, JSON standardı, save/load API, database, slot, autosave,
compression, encryption veya gameplay persistence implement edilmez.

## 15. Phase 9 continuation

Bu contract `CanonicalSessionState` için restore validation, immutable plan,
adapter decode sınırı ve schema-version gate'i ekler. Gerçek persistence
backend'i veya runtime activation implementation'ı hâlâ kapsam dışıdır.
