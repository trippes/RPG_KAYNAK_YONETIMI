# Architecture Dependency Rules

## Katman sırası

```text
foundation → domain → time/events → application → simulation → gameplay → adapters
```

Ok yönü bağımlılık yönüdür. Alt katman üst katmanı import edemez.

## Kurallar

1. `core` hiçbir gameplay paketi import edemez.
2. `foundation` yalnızca Python standard library ve foundation içi modülleri kullanabilir.
3. `domain` application, simulation, gameplay, UI veya persistence import edemez.
4. `time` domain gameplay kurallarını import edemez.
5. `events` concrete gameplay sınıflarına bağımlı olamaz.
6. `application` domain/time/events kullanabilir; gameplay kuralı taşıyamaz.
7. `simulation` core contract'ları ve port'ları kullanır; UI import edemez.
8. `gameplay` Core public API'sini kullanabilir; Core internal implementation'a bağlanmamalıdır.
9. `adapters` port/contract implement eder; domain nesnelerini doğrudan mutate edemez.
10. Global singleton ve implicit service locator kullanılmaz.
11. Core modülleri arasında import cycle bulunamaz.
12. Event handler, başka bir katmanın concrete sınıfını import ederek orchestration yapamaz.
13. `core.simulation` gameplay, UI, persistence veya wall-clock adapter import edemez.
14. Canonical Scheduler callback ile gameplay kodu çalıştıramaz; `ScheduledWork` üretir.
15. Simulation progression yalnızca `Tick` ile yapılır; `datetime`, `sleep` ve timer kullanılamaz.
16. `core.simulation` legacy `core.events`, `core.event_bus` veya `time_system`
    import edemez. Legacy dönüşümler yalnızca adapter/uygulama sınırında yapılır.

Phase 5'te `LegacyEventAdapter` legacy sınıfı import etmez; Event-shaped veriyi
adapter sınırında kabul eder. Böylece canonical simulation graph'ında legacy
modül kenarı bulunmaz.

## Foundation özel kuralları

`core.foundation` yalnızca standard library veya foundation içi modülleri
import edebilir. Foundation; domain, entity, world, action, simulation,
application ve gameplay katmanlarına bağımlı olamaz.

İlk canonical foundation nesneleri `Identifier` ve uzmanlaşmış ID value
object'leridir. `Position` domain spatial katmanında, `Tick` ise core time
katmanında bulunur.

## Yasaklı Core importları

`character`, `combat`, `economy`, `inventory`, `npc`, `quests`, `resources`,
`pygame`, `save`, `gameplay` ve `adapters` isimleri Core kaynaklarında yasaktır.
## Phase 4 event transport boundary

`core.simulation.transport` yalnızca Foundation/Time ve canonical event
contract'larını kullanır; Gameplay veya legacy event modüllerine bağımlı
değildir. `SimulationRuntime`, `ActionProcessor` ve World dispatcher aynı
`CanonicalEventTransport` örneğini kullanabilir. World-local 1.x olayları
runtime/application sınırındaki `LegacyEventAdapter` üzerinden çevrilir.

Persistence contract'ı backend bağımsızdır; database/file adapter veya gameplay
import edemez.
