# Core 2.1 — Resmî Kapanış

## 1. Amaç ve kapsam

Core 2.1, Core 2.0 Architecture Baseline ve Architecture Freeze üzerinde
geliştirilen canonical world/session state, ownership ve restore sözleşmelerini
tamamlar. Bu belge, mevcut kaynak kodu, architecture sözleşmeleri ve kapanış
denetiminde doğrulanan test sonuçları üzerinden Core 2.1 kapsamını resmîleştirir.

Core 2.1.5 ve Core 2.1.6 adları geçmiş uygulama kilometre taşları olarak
bilinmektedir. Mevcut architecture belgelerinde bağımsız resmî faz başlıkları
olarak tanımlanmadıkları için burada ayrı tarihsel architecture fazları olarak
sunulmazlar.

Core 2.1; Core 2.0'ın foundation, domain, application, simulation,
compatibility ve persistence boundary kararlarını değiştirmez. Bu kapanış,
gerçek save/load backend'i veya gameplay implementasyonu anlamına gelmez.

## 2. Tamamlanan mimari sözleşmeler

### Canonical session state

`core/persistence/state.py` içindeki `CanonicalSessionState`, world kayıtlarını,
`EntityRepositoryState` değerini, `WorldMembershipState` değerini,
`active_world_id` değerini ve `simulation_tick` değerini taşır.

İlgili doğrulama:

- `tests/test_persistence/test_contracts.py`
- `tests/test_persistence/test_session_state_records.py`
- `tests/test_application/test_core20_integration.py`

### Runtime-free persistence state

Canonical state runtime object graph değildir. Scheduler, dispatcher, event queue,
runtime consumer kayıtları, world clock ayrıntıları ve compatibility projection
nesneleri canonical persistence state içine alınmaz.

Bu sınır `core/persistence/state.py` ve `core/persistence/restore.py` içinde
uygulanır; `tests/test_persistence/test_contracts.py` ve
`tests/test_persistence/test_restore_contract.py` ile doğrulanır.

### World domain ve runtime separation

`core/domain/world_contract.py` içindeki `WorldDomainState`, runtime-free world
kimliği, adı ve bounds sözleşmesidir. World yönetimi `WorldManager`, runtime
uygulama sınırı ise `WorldRuntimeBoundary` üzerinden ayrıştırılmıştır.

İlgili doğrulama:

- `tests/test_domain/test_world_model.py`
- `tests/test_world/test_world_runtime_separation.py`
- `tests/test_architecture/test_world_model_boundaries.py`

### Entity repository ve world ownership

`core/application/entity_repository.py` entity kayıt ve sorgulama sorumluluğunu
taşır. `core/application/ownership.py` içindeki `WorldMembershipService`,
Entity–World ownership ilişkisinin canonical writer'ıdır. `Entity.world_id` ve
`World._entities` compatibility projection olarak korunur.

İlgili doğrulama:

- `tests/test_application/test_entity_repository.py`
- `tests/test_application/test_repository_invariants.py`
- `tests/test_application/test_ownership.py`
- `tests/test_application/test_entity_world_boundary.py`

### Deterministik simulation ve event akışı

`core/simulation/runtime.py` içindeki `SimulationRuntime.advance_to()` ve
`advance_by()` yalnızca canonical `Tick` değerleriyle ilerler. Scheduler callback
çalıştırmak yerine scheduled work üretir. `CanonicalEventTransport`, event’leri
`(simulation_tick, insertion_sequence)` sırasıyla taşır; dispatcher bunları
belirlenmiş registration ve queue kurallarıyla dağıtır.

İlgili kaynaklar:

- `core/simulation/runtime.py`
- `core/simulation/scheduler.py`
- `core/simulation/transport.py`
- `core/simulation/dispatcher.py`

İlgili doğrulama:

- `tests/test_simulation/test_runtime.py`
- `tests/test_simulation/test_scheduler.py`
- `tests/test_simulation/test_event_transport.py`
- `tests/test_simulation/test_dispatcher_contract.py`
- `tests/test_time/test_canonical_tick.py`

### Restore validation ve preparation

`core/persistence/restore.py` içindeki `RestoreContract.validate()` canonical
state invariant’larını kontrol eder. `RestoreContract.prepare()` doğrulanmış,
immutable `CanonicalRestoreState` üretir. Unknown reference, duplicate identity,
multiple ownership, invalid active world ve geçersiz tick değerleri açık hata
olarak ele alınır.

İlgili doğrulama:

- `tests/test_persistence/test_restore_contract.py`
- `tests/test_persistence/test_contracts.py`

### Atomik restore activation

`core/application/session.py` içindeki `GameSession.activate_restore()` yeni
world, entity, membership ve simulation runtime graph’ını mevcut session’a
uygulamadan önce oluşturur. Validation veya activation başarısız olursa mevcut
çalışan session değiştirilmez.

İlgili doğrulama:

- `tests/test_application/test_session.py`
- `tests/test_application/test_restore_activation.py`

### Architecture ve import boundaries

Core katmanları gameplay, concrete persistence backend’i ve yasaklanan legacy
bağımlılıklarına bağlanmaz. Domain, persistence ve canonical simulation
sınırları architecture testleriyle korunur.

İlgili doğrulama:

- `tests/test_architecture/test_core_boundaries.py`
- `tests/test_architecture/test_world_model_boundaries.py`

### Compatibility ve migration tooling sınırı

`core/compatibility` altında legacy API metadata’sı, migration registry, static
usage scanner, runtime usage counter ve kontrollü deprecation davranışı bulunur.
Legacy API’ler bu kapanışta kaldırılmaz.

İlgili doğrulama:

- `core/compatibility/deprecation.py`
- `core/compatibility/migration.py`
- `core/compatibility/usage.py`
- `tests/test_compatibility/test_migration_tooling.py`

## 3. Exit criteria

Core 2.1 kapanış kriterleri aşağıdaki şekilde karşılanmıştır:

1. Kapanış denetiminde tam test paketi 458 başarılı, 0 başarısız ve 0 atlanan
   test sonucu vermiştir. Bu sayı Core 2.1 kapanışının tarihsel ölçümüdür;
   güncel proje test sonucu değildir.
2. `python main.py` başlangıç smoke testi başarılı olmuştur.
3. Canonical state ile runtime object graph ayrımı korunmuştur.
4. Entity repository, world membership ve world runtime sınırları korunmuştur.
5. Tick, scheduler, event transport ve dispatcher davranışları deterministik
   sözleşmelerle sınırlandırılmıştır.
6. Restore validation, preparation ve activation akışı uygulanmıştır.
7. Geçersiz restore girişiminde mevcut çalışan session’ın korunması testlerle
   doğrulanmıştır.
8. Architecture Freeze import ve bağımlılık sınırlarında ihlal tespit
   edilmemiştir.
9. Gerçek dosya/database persistence backend’inin Core 2.1 kapsamında olmadığı
   açıkça korunmuştur.

Yukarıdaki test sayıları kapanış denetiminin tarihsel sonuçlarıdır. Bu belgeyi
oluşturma işlemi sırasında testler yeniden çalıştırılmamıştır.

Güncel doğrulama için bu belge tek doğruluk kaynağı değildir. Core 14–17
uygulamalarından sonra tam test paketi `python -m unittest discover -s tests
-t . -p "test_*.py"` komutuyla 672 başarılı, 0 başarısız sonuç vermektedir.
Güncel kapsam ve faz durumu `docs/architecture/30-master-roadmap.md` içinde
tutulur.

## 4. Kapsam dışı işler

Aşağıdaki işler Core 2.1 kapanış engeli değildir ve bu belgeyle başlatılmaz:

- gerçek dosya veya database save/load backend’i;
- save slot ve autosave;
- gerçek schema migration transform’ları;
- gameplay-specific entity factory ve gameplay persistence;
- resource, inventory, economy ve diğer gameplay sistemleri;
- UI veya pygame entegrasyonu;
- replay ve event sourcing;
- legacy API’lerin tamamen kaldırılması.

Bu işler sonraki fazlarda ayrıca değerlendirilebilir. Bu belge sonraki fazların
kapsamını kesinleştirmez ve herhangi bir Persistence veya Gameplay geliştirmesi
başlatmaz.

## 5. Mimari koruma ilkeleri

Core 2.0 Architecture Freeze geçerliliğini korur. Bu kapanış belgesi:

- yeni bir architecture redesign getirmez;
- public API değişikliği tanımlamaz;
- concrete persistence backend’i eklemez;
- gameplay bağımlılığı eklemez;
- canonical ownership, Tick, event ordering veya restore sınırlarını değiştirmez.

İleride Persistence veya Gameplay ihtiyaçları Core API’lerinde genişleme
gerektirebilir. Böyle bir ihtiyaç mevcut mimarinin kanıtlanmış hatası olarak
değil, ayrı bir fazda değerlendirilecek bir tasarım kararı olarak ele alınmalıdır.

## 6. Kapanış kararı

Core 2.1, bu belgede tanımlanan mevcut mimari kapsam açısından **tamamlandı**.

Bu karar gerçek persistence backend’inin tamamlandığı anlamına gelmez. Core 2.1
canonical state, runtime separation, ownership, deterministic simulation,
restore boundary, architecture rules ve compatibility sınırlarını tamamlar;
gerçek save/load ve gameplay özellikleri sonraki fazların konusudur.
