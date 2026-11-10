# Core Sertleştirme ve Legacy Kullanım Raporu

## Güncel statik envanter

Ölçüm, GitHub Actions Linux doğrulama işi içinde
`python -m core.compatibility.usage .` komutuyla alınmıştır.

- Ölçüm commit'i: `39e69d486fdf31fc5a951816f7febe3d95094c15`
- Python: 3.11
- Test sonucu: 880 test, 0 hata
- Rapor: 13 legacy API başlığı, toplam 63 statik kullanım kaydı
- Runtime sayaçları: rapor adımının temiz süreçte çalışması nedeniyle 0

| Legacy API | Statik kullanım | Canonical karşılık |
|---|---:|---|
| `World._entities` | 17 | `EntityRepository` |
| `core.entity.position.Position` | 14 | `core.domain.spatial.Position` |
| `Entity.world_id` | 6 | `WorldMembershipService` |
| `core.constants event constants` | 8 | `CanonicalEventType` |
| `core.events.EventQueue` | 5 | `CanonicalEventTransport` |
| `core.actions.Action` | 4 | `core.simulation.Action` |
| `time_system.Scheduler` | 3 | `CanonicalScheduler` |
| `core.clock.GameClock` | 2 | `WorldRuntimeBoundary.advance_world` |
| `core.event_bus.EventBus` | 2 | `CanonicalEventDispatcher` |
| `core.event_types.EventType` | 2 | `CanonicalEventType` |
| `Game.dunya_olaylarini_aktar` | 0 | `Game.dunya_olaylarini_canonical_aktar` |
| `core.actions.ActionManager` | 0 | `CanonicalActionAdapter` |
| `time_system.Tick` | 0 | `core.time.Tick` |

Bu sayılar benzersiz dosya veya çağıran sayısı değil, tarayıcının bulduğu
import, construction, inheritance, method ve projection referanslarının
sayısıdır. Scanner; import alias, modül alias ve alias üzerinden construction
ile inheritance biçimlerini kapsar. Dinamik import, reflection ve runtime'da
oluşturulan isimler statik AST taramasının kapsamı dışındadır.

Önceki rapordaki 62/59 değerleri eski scanner davranışına aittir; yeni
tarayıcı daha fazla kullanım biçimini tanıdığı için doğrudan karşılaştırma
yapılmamalıdır.

## Aşama 3'te uygulanan sınırlar

- `time_system.Tick`, canonical `core.time.Tick` sınıfının geriye dönük
  uyumlu export'udur. `core.clock.GameClock` canonical Tick'i doğrudan alır.
- Mutable legacy Entity Position, canonical immutable Position değerini
  saklayan adaptördür. Yeni kod canonical Position kullanmalıdır.
- `WorldRuntimeBoundary`, canonical `SimulationRuntime` zamanını
  authoritative kaynak olarak ilerletir; eski World saatini yalnızca
  compatibility projection olarak eşitler.
- `LegacyWorldRuntime`, eski callback scheduler ve event queue sahipliğini
  izole eder. Eski tüketiciler bulunduğu için bu API'ler silinmemiştir.
- `EntityRepository` ve `WorldMembershipService` canonical sahiplik
  kaynaklarıdır. `Entity.world_id` ve `World._entities` eski public World
  API'sini destekleyen projection alanlarıdır; save/restore kaynağı değildir.
- Architecture testleri canonical domain/time/simulation katmanlarının
  legacy runtime bağımlılıklarını engeller.

## Önceki Core sertleştirme kararları

- Core canonical persistence state'i runtime scheduler, dispatcher, event
  queue ve aktif aksiyonları içermez. Gameplay continuation snapshot'ları
  application katmanında tutulur.
- Application save envelope v0→v1 migrasyonunu yapar. Core persistence
  boundary eski Core kayıtlarını dönüştürmez; mevcut Core şemasını doğrular
  ve gelecek sürümleri reddeder.
- Restore sonrasında dispatcher consumer'ları ve tick listener'ları korunur;
  geçici event kuyruğu ve scheduler işleri yeniden üretilmez.
- Save/load ve runtime replacement akışları candidate graph kurup doğrulama
  tamamlandıktan sonra atomik olarak yayımlar.

## Kalan migration işi

Legacy yüzeyin tamamı kaldırılmış değildir. Sonraki aşamada kaldırma
değerlendirmesi yapılabilmesi için önce dış/legacy tüketicilerin canonical
API'lere taşınması gerekir. Özellikle World callback scheduler, World saat ve
event API'si, mutable Entity Position ve membership projection'ları major
version uyumluluk kararı olmadan kaldırılmamalıdır.

Ayrıntılı aşama kaydı: `docs/architecture/33-stage-3-architecture-debt.md`.
