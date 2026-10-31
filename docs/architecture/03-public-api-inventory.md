# Core 1.x Public API Inventory

Bu liste mevcut kaynak ve test kullanımına göre hazırlanmıştır. 2.0'da
canonical isimler İngilizce olacak; aşağıdaki 1.x yolları compatibility
façade ile geçiş döneminde korunacaktır.

## Entry point

| Import | Public symbols |
|---|---|
| `core.game` | `Game` |
| `main` | `oyun_olustur`, `main` |

## Entity

| Import | Public symbols |
|---|---|
| `core.entity` | `Entity`, `EntityState`, `EntityType`, `EntityIDGenerator`, `Position`, `EntityManager` |
| `core.entity.entity` | `Entity` |
| `core.entity.entity_state` | `EntityState` |
| `core.entity.entity_type` | `EntityType` |
| `core.entity.entity_id` | `EntityIDGenerator` |
| `core.entity.position` | `Position` |
| `core.entity.entity_manager` | `EntityManager` |

## World and time

| Import | Public symbols |
|---|---|
| `core.world` | `World`, `WorldIDGenerator`, `WorldManager` |
| `core.clock` | `GameClock` |
| `time_system` | `Tick`, `GameTime`, `Calendar`, `Scheduler`, `ScheduledEvent`, time constants |

## Events

| Import | Public symbols |
|---|---|
| `core.events` | `Event`, `EventQueue` |
| `core.event_bus` | `EventBus` |
| `core.event_handler` | `EventHandler` |
| `core.event_manager` | `EventManager` |
| `core.event_types` | `EventType` |

## Canonical Core 2.0

| Import | Public symbols |
|---|---|
| `core.simulation` | `SimulationEvent`, `CanonicalEventTransport`, `CanonicalEventDispatcher`, `EventConsumer`, `CanonicalEventType`, `canonical_event_type` |
| `core.compatibility` | `LEGACY_API_MATRIX`, `CompatibilityEntry` |

Canonical API'ler legacy EventBus/EventQueue'yu import etmez. Legacy API'ler
geçiş süresince korunur ve migration matrix ile izlenir.

FAZ 6 migration tooling public surface'i: `core.compatibility.get_mapping`,
`get_all_mappings`, `is_legacy`, `canonical_for`, `status_for`,
`scan_static_usage` ve `usage_report` fonksiyonlarıdır. Registry read-only
metadata döndürür; internal mutable dictionary dışarı açılmaz.

## Actions

| Import | Public symbols |
|---|---|
| `core.actions` | `Action`, `ActionDurumu`, `ActionManager` |

## Utility APIs

| Import | Public symbols |
|---|---|
| `core.math.numbers` | `sayi_mi`, `tam_sayi_mi`, sign/zero helpers, `mutlak_deger` |
| `core.math.operations` | `topla`, `cikar`, `carp`, `bol`, `mod`, `minimum`, `maksimum` |
| `core.math.ratios` | percentage, ratio, bonus and penalty functions |
| `core.math.rounding` | rounding functions |
| `core.random` | seed, random number, probability and selection functions |
| `core.dice` | dice and dice-expression functions |

## Stability classification

- Stable for compatibility: `Game`, Entity/World/Action/Event exported symbols.
- Transitional: direct imports from implementation modules and Turkish method names.
- Candidate for 2.x redesign: queue internals, scheduler callback contract,
  mutable registries, `Event.veri`, `Event.zaman` and `Action.sahip` typing.

Core 2.0 application public surface'i `EntityRepository`,
`WorldMembershipService`, `GameSession` ve `WorldRuntimeBoundary`'dir.
Persistence surface'i canonical state records, `RestoreContract`,
`CanonicalRestoreState`, `PersistenceAdapter`, migration ve activation
boundary'leridir. Internal dictionaries, runtime graph ve legacy projections
canonical public source değildir.
