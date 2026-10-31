# Core Sertleştirme Raporu

## Ölçüm

`python -m core.compatibility.usage .` ile yapılan statik tarama, test ve dokümantasyon klasörleri hariç 13 legacy başlıkta başlangıçta 62 kullanım tespit etmişti. Geçiş sonrası toplam statik kullanım 59'a indi; uygulama doğrudan `ActionManager` kullanmıyor ve bu başlığın statik kullanım sayısı **0** oldu. Runtime sayaçları temiz başlangıçta sıfırdır; deprecation ile işaretlenmiş çağrılar çalıştığında sayaç artar.

Başlıca yoğunluklar:

- `World._entities`: 17
- `core.entity.position.Position`: 9
- `core.constants event constants`: 8
- `Entity.world_id`: 6
- `core.events.EventQueue`: 5
- `core.actions.ActionManager`: 4

Güncel ölçümde `core.actions.ActionManager`: **0**.

Bu sonuç, eski API'lerin uygulama davranışından tamamen çıkarılmadığını; ancak canonical runtime'ın sahiplik, zaman, action ve event akışının yeni giriş noktası olduğunu gösterir.

## Uygulanan sınır

- Yeni simulation testleri yalnızca `GameSession` ve `SimulationRuntime` üzerinden çalışır.
- World olayları için uygulama katmanındaki legacy aktarım metodu deprecation ölçümüne bağlandı; yeni yol `dunya_olaylarini_canonical_aktar` olarak kalır.
- Canonical event akışını kaydetmek ve aynı akışla karşılaştırmak için `SimulationReplay` eklendi.
- Restore sonrası simulation tick'in korunması migration/restore testine bağlandı.
- `ActionManager` için `CanonicalActionAdapter` eklendi; Game ve GameApplication bu adapter üzerinden canonical `ActionProcessor`a bağlandı.
- World tick ilerletmesi `WorldRuntimeBoundary.advance_world` içine alındı; `SimulationRuntime` authoritative tick olarak kullanılıyor.

## Sonraki daraltma

Legacy `ActionManager` ve 1.x world-clock API'si yalnızca dış 1.x çağıranlar için compatibility katmanında tutuluyor. Uygulama içi çağrılar canonical adapter sınırının arkasında; sonraki temizlik yalnızca dış kullanıcıların migration sürecine bağlı.

## Core kapanış kararı

- Core canonical persistence state'i runtime scheduler, dispatcher, event queue
  ve aktif aksiyonları içermez. Gameplay continuation snapshot'ları application
  katmanında tutulur.
- Application save envelope v0→v1 migrasyonunu yapar. Core persistence boundary
  eski Core kayıtlarını dönüştürmez; mevcut Core şemasını doğrular ve gelecek
  sürümleri reddeder.
- Restore sonrasında dispatcher consumer'ları ve tick listener'ları korunur;
  geçici event kuyruğu ve scheduler işleri yeniden üretilmez.
- Core kapanış doğrulaması unittest, compileall, main smoke ve architecture
  boundary testlerinin birlikte başarılı olmasına bağlıdır.
