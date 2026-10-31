# Phase 6 — Compatibility Migration Tooling

## Deprecation policy

Her legacy kayıt immutable metadata taşır: legacy name, canonical replacement,
status, introduced/deprecated version, planned removal phase, migration notes
ve blocker. `deprecated=True` kayıtlar çağrı sırasında kontrollü
`DeprecationWarning` üretir; warning mesajı migration hedefini içerir.

## Migration registry

`core.compatibility.migration.DEFAULT_REGISTRY` sıralı, read-only registry'dir.
`get_mapping`, `get_all_mappings`, `is_legacy`, `canonical_for` ve `status_for`
kontrollü sorgu API'leridir. Internal dictionary doğrudan dışarı verilmez.

## Usage reporting

`scan_static_usage(root)` AST tabanlıdır ve import, construction, inheritance ve
method call kullanım noktalarını raporlar. `tests`, `docs`, `.git` ve
`__pycache__` taranmaz. `record_usage()` runtime compatibility çağrılarını
ayrı bir counter'da tutar. `usage_report(root)` iki ölçümü canonical replacement
ile birlikte döndürür; static ve runtime kavramları birleştirilmez.

## Removal blockers

EventBus/EventQueue, GameClock, Scheduler, ActionManager, old Position/Tick ve
ownership projection'ları 1.x public callers ve mevcut regression contract'ları
nedeniyle korunur. Bu faz yalnızca ölçüm ve migration boundary sağlar; removal
ve destructive ownership/time migration sonraki fazlara bırakılmıştır.

## Phase 7 dashboard

Static scanner artık `Entity.world_id` kullanımını Entity bağlamıyla,
`World._entities` kullanımını yalnızca World projection dosyasıyla eşler.
Repository içindeki canonical `_entities` storage alanları legacy kullanım
olarak sayılmaz. Böylece rapor migration kararları için daha anlamlıdır.

Persistence hazırlığında compatibility projection'ları ayrıca exclusion olarak
işaretlenir. Migration dashboard'ında görünmeleri, save schema'ya dahil
edilecekleri anlamına gelmez.

## Phase 9 restore exclusion

Restore yalnızca canonical record ve membership state kullanır. Legacy
projection'lar, runtime event consumer/dispatcher state'i ve replay history
compatibility yüzeyi olarak kalır; restore kaynağı değildir.
