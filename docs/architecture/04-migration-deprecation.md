# 1.x → 2.x Migration and Deprecation Policy

## Compatibility façade

`core.compatibility.v1` 1.x import yollarını canonical 2.0 API'ye bağlayan
geçici katmandır. 1.x modülleri davranış korunabildiği sürece doğrudan
silinmez veya sessizce yeniden yorumlanmaz.

## Sürüm politikası

- 2.0: Yeni canonical API ve compatibility façade.
- 2.1+: Yeni API'ye geçiş yardımcıları ve warning mesajları.
- Major sürüm öncesi: kaldırılacak API listesi yayınlanır.
- Removal yalnızca major sürümde yapılır.
- Bir API en az bir minor sürüm boyunca deprecation warning taşır.

## Warning kuralları

`DeprecationWarning` yalnızca deprecated çağrı gerçekten kullanıldığında
üretilir. Import sırasında bütün kullanıcıları gürültüye boğan warning'ler
kullanılmaz. Warning mesajı yeni API yolunu ve removal hedefini belirtir.

## Breaking change adayları

- Event payload sözlüğünden typed payload'a geçiş
- `int` zaman değerlerinden `Tick` contract'ına geçiş
- Entity–World ownership işleminin tek otoriteye alınması
- `Game` içindeki registry ve processor alanlarının ayrıştırılması
- Scheduler callback'lerinin typed command/event'e dönüşmesi

## Phase 5 deprecation matrix

| Legacy API | Canonical replacement | Durum | Removal blocker | Hedef |
|---|---|---|---|---|
| `core.events.EventQueue` | `CanonicalEventTransport` | compatibility | 1.x callers | Phase 7+ |
| `core.event_bus.EventBus` | `CanonicalEventDispatcher` | compatibility | handler API users | Phase 7+ |
| `EventType` / `core.constants` event isimleri | `CanonicalEventType` + aliases | alias | public imports | Phase 6+ |
| `Game.dunya_olaylarini_aktar()` | `dunya_olaylarini_canonical_aktar()` | deprecated boundary | legacy queue consumers | Phase 6+ |
| `GameClock` / `time_system.Scheduler` | `Tick` / `CanonicalScheduler` | compatibility | 1.x clock/callback users | Phase 7+ |
| `ActionManager` | `ActionProcessor` | compatibility | 1.x action callers | Phase 7+ |
| `Entity.world_id` / `World._entities` | ownership service/repository | projection | existing ownership tests | Phase 7+ |
| old `Position` / `time_system.Tick` | canonical value objects | compatibility | old imports | Phase 6+ |

`deprecated` burada removal anlamına gelmez. Public davranış bu fazda
değiştirilmez; warning ve kaldırma ayrı bir major migration kararına bağlıdır.

## Warning policy

`DeprecationWarning` yalnızca metadata'da `deprecated=True` olan API'lerde
çağrı sırasında üretilir. FAZ 6'da bu API `Game.dunya_olaylarini_aktar()`'dır.
Warning mesajı canonical replacement'ı içerir. Python'ın warning filtreleri
aynı çağrı noktası için spam'i kontrol eder; compatibility API'leri sessizce
kaldırılmaz.

## Usage reporting

`core.compatibility.usage` static AST scan ve runtime counter'ı ayrı tutar.
Scanner `tests`, `docs`, `.git` ve `__pycache__` alanlarını dışarıda bırakır.
Rapor her legacy API için static kullanım sayısı, runtime kullanım sayısı ve
canonical replacement döndürür.

Phase 10'da legacy API'ler silinmez. Compatibility matrix, deterministic
migration registry ve static/runtime usage dashboard korunur; yeni canonical
kod legacy katmana bağımlı olamaz.
