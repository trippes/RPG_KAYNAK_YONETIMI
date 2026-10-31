# Phase 7 — World Runtime Separation

## World canonical contract

`World.domain_state` runtime-free `WorldDomainState` döndürür: canonical
`WorldId`, metadata ve bounds. World domain facade'ı global repository,
canonical scheduler, canonical event transport veya simulation time sahibi
değildir.

## Compatibility delegate

Mevcut 1.x clock, local EventQueue ve callback Scheduler
`core.world.legacy_runtime.LegacyWorldRuntime` içinde tutulur. Public World
metotları (`advance`, `schedule_event`, `emit_event`, `add_entity` vb.) silinmez.
Bu delegate yalnızca compatibility davranışını izole eder.

## Application boundary

`GameSession.world_runtime` canonical SimulationRuntime, CanonicalScheduler ve
CanonicalEventTransport'a erişilen application sınırıdır. World eventleri
`WorldRuntimeBoundary.dispatch_world_events()` üzerinden canonical transport'a
aktarılır.

## Ownership and Position

`WorldMembershipService` EntityRepository'nin authoritative kaynağı olmaya
devam eder ve World projection'ını private compatibility writer'larıyla
günceller. `Entity.world_id` ve `World._entities` kaldırılmamıştır.

Canonical Position World spatial query'lerinde kabul edilir; Position bounds
bilmez. Bounds validation World/domain contract'ında kalır.

## Remaining blockers

1.x World clock/scheduler/event queue ve mutable Entity/Position API'leri public
callers ve regression contract'ları nedeniyle sonraki fazlara bırakılmıştır.
Bu faz destructive migration yapmaz.

## Persistence sınırı

World persistence'a yalnızca `WorldDomainState` olarak girer. LegacyWorldRuntime,
clock, local queue, callback scheduler ve entity projection'ları state dışında
kalır. Membership ayrıca WorldMembershipService üzerinden kaydedilebilir.

## Phase 9 activation

`WorldDomainState` restore planına girer; restore sırasında World runtime
yardımcıları, scheduler, clock, queue, dispatcher veya callback oluşturulmaz.
Runtime activation ayrı bir application boundary'dir.
