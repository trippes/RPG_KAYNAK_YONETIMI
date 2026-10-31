# Core 2.0 Implementation Plan

## Phase 0 — Baseline contracts

- Amaç: Architecture, API, dependency, event, time ve serialization kararlarını sabitlemek.
- Değişen paketler: `docs`, test discovery, metadata, architecture tests.
- Değişmeyenler: tüm 1.x runtime paketleri ve gameplay iskeletleri.
- API etkisi: yok.
- Risk: düşük.
- Test: 1.x regression + architecture tests.

## Phase 1 — Foundation and canonical value objects

- Amaç: ID, errors, immutable Position, Tick ve typed event primitives.
- Değişecek paketler: yeni `core/foundation`, `core/time`, `core/events`.
- Değişmeyecekler: gameplay ve 1.x compatibility modülleri.
- API etkisi: yeni API; façade korunur.
- Risk: orta; value object dönüşümleri dikkat ister.
- Test: unit, deterministic ve contract testleri.

## Phase 2 — Ownership and runtime boundary

- Amaç: `EntityRepository`, `WorldMembershipService` ve `GameSession` ile tek
  canonical ownership kaynağı oluşturmak.
- Değişen paketler: `core/application`, mevcut `Game` façade'si.
- Değişmeyenler: World clock, Scheduler, EventBus/EventQueue, Action ve gameplay.
- API etkisi: 1.x `Game.varlik_ekle/cikar` korunur; operasyonlar adapter üzerinden
  canonical service'e yönlenir.
- Risk: yüksek; Entity.world_id ve World._entities projection olarak tutulur.
- Test: repository, membership, transfer, rollback, GameSession ve regression.

## Phase 3 — Simulation and action/scheduler boundary

- Amaç: Canonical Tick progression, callback-free Scheduler, ActionProcessor ve
  deterministic lifecycle event stream oluşturmak.
- Değişen paketler: `core/simulation`, `GameSession` runtime exposure.
- Değişmeyenler: 1.x `GameClock`, `time_system.Scheduler`, `ActionManager`,
  EventBus/EventQueue, World clock ve gameplay.
- API etkisi: yeni canonical API; mevcut Game/Action/Scheduler API'leri
  compatibility olarak korunur.
- Risk: yüksek; scheduled trigger tick semantiği korunmalıdır.
- Test: same-tick ordering, cancellation, invalid transitions, duration,
  deterministic jump progression ve architecture tests.

## Phase 2 — Ownership and runtime boundary

- Amaç: EntityRepository, World membership ve GameSession ayrımı.
- Değişecek paketler: `core/domain`, `core/application`.
- Değişmeyecekler: gameplay.
- API etkisi: compatibility adapter gerekir.
- Risk: yüksek; üçlü ownership yapısı değişir.
- Test: transaction rollback, multi-world ve invariant testleri.

## Phase 3 — Simulation and action/scheduler boundary

- Amaç: Simulation loop, scheduled event ve action processor.
- Değişecek paketler: `core/simulation`, `core/time`, `core/events`.
- Değişmeyecekler: gameplay implementation.
- API etkisi: action/scheduler contract değişebilir.
- Risk: yüksek; ordering ve determinism korunmalı.
- Test: replay, ordering, cancellation/failure ve clock testleri.

## Phase 4 — Compatibility hardening

- Amaç: 1.x façade, deprecation warning ve migration tooling.
- Değişecek paketler: `core/compatibility/v1`.
- Değişmeyecekler: gameplay.
- API etkisi: warning başlar, removal yapılmaz.
- Risk: orta.
- Test: import compatibility ve API contract testleri.

## Gameplay gate

Gameplay ancak Phase 0–4 tamamlanıp architecture, regression,
determinism ve serialization contract testleri başarılı olduktan sonra
başlayabilir.

## Phase 4 — Canonical Event Transport & Runtime Integration

- `SimulationEvent` identity ve immutable envelope alanları görünür kılınır.
- `CanonicalEventTransport` `(simulation_tick, insertion_sequence)` sırasını
  uygular.
- ActionProcessor ve SimulationRuntime aynı transport'a bağlanır.
- World olayları runtime dispatcher/legacy adapter sınırından geçirilir.
- 1.x EventBus/EventQueue ve Game façade'si kaldırılmaz.
- Persistence, serialization implementation ve gameplay bu fazın dışındadır.

## Phase 5 — Compatibility Hardening & Canonical Contract

- Canonical Event Dispatcher ve minimal consumer contract'ı eklendi.
- Registration, filtering, nested event ve re-entrant dispatch politikaları
  sabitlendi.
- `SimulationEvent.schema_version` default `1` ile explicit hale getirildi.
- Legacy event isimleri canonical type registry alias'larıyla eşlendi.
- Legacy API deprecation matrix'i kod ve dokümana alındı.
- Canonical simulation katmanının legacy event/time modüllerine import'u
  architecture testleriyle yasaklandı.

## Phase 6 — Compatibility Migration Tooling

- Immutable deprecation metadata ve canonical migration registry oluşturuldu.
- AST tabanlı static usage scanner eklendi; test/docs/cache alanları hariçtir.
- Runtime compatibility counter ve birleşik usage report eklendi.
- Kontrollü `DeprecationWarning` yalnızca işaretlenmiş deprecated API'de
  etkinleştirildi.
- Legacy API'ler kaldırılmadı; removal blocker ve hedef fazlar matrix'te
  belgelenmeye devam ediyor.

## Phase 7 — World Runtime Separation & Low-Risk Legacy Reduction

- Runtime-free `WorldDomainState` contract'ı eklendi.
- World clock, local EventQueue ve callback Scheduler ayrıntıları
  `LegacyWorldRuntime` compatibility delegate'ine taşındı.
- `GameSession.world_runtime` application runtime boundary olarak eklendi.
- Ownership service public World writer'ları yerine compatibility projection
  writer'larını kullanıyor.
- Canonical Position ile World spatial query uyumluluğu sağlandı.
- Migration dashboard scanner'ı ownership projection'larını daha doğru
  sınıflandıracak şekilde daraltıldı.

## Phase 8 — Persistence Preparation

- `core.persistence` altında disk I/O içermeyen canonical state contract'ları oluşturuldu.
- ID, Position ve Tick için deterministic round-trip representation tanımlandı.
- EntityRepository record state'i ve WorldMembership mapping state'i internal dict'lerden ayrıştırıldı.
- `CanonicalSessionState` runtime graph'tan ayrıldı.
- Persistence schema version ile event schema version ayrımı test edildi.
- Legacy/runtime exclusion listesi ve malformed schema validation eklendi.

## Phase 9 — Canonical State Restore & Persistence Adapter Boundary

1. Canonical state'i deterministic olarak validate et.
2. Value objects, worlds, entities, repository, membership, active world,
   Tick ve session için immutable restore planı üret.
3. Activation'ı validated plan callback'i ile sınırla; başarısız validation'da
   runtime mutation yapma.
4. `PersistenceAdapter` decode ve schema-version gate'ini teknoloji bağımsız
   bırak.
5. Gerçek save/load, disk I/O, migration transform, replay ve event sourcing'i
   sonraki fazlara bırak.
