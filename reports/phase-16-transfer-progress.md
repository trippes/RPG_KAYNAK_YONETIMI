# Aşama 16 — Teknik Aktarım Uygulama İlerleme Kaydı

**Tarih:** 2026-11-19  
**Çalışma dalı:** `experiment/map-cleanup`  
**Mimari referans:** `reports/phase-16-continuous-world-integration-contract.md`

Bu kayıt, laboratuvar kabiliyetlerinin Eldoria mimarisinde yerel olarak uygulanması sırasında tamamlanan ilk dikey dilimi ve henüz aktarılmayan sorumlulukları ayırır.

## Tamamlanan ilk aktarım dilimi

1. **Yerel sürekli koordinat modeli:** `core.domain.spatial.WorldPoint` ve map-scoped `ContinuousEntityPosition` eklendi. Kanonik eksen +X sağa, +Y aşağı; değerler sonlu ve immutable.
2. **Geometri:** mevcut pointy-top axial dönüşümler korunarak sürekli dünya noktası dönüşümü, fractional axial çözümü, deterministik cube rounding ve önceki hücreyi yalnızca eşit mesafe sınırında koruma eklendi.
3. **Kamera/screen sınırı:** `WorldTransform` sürekli world point ↔ screen dönüşümünü destekliyor.
4. **Runtime sahipliği:** yeni runtime oluşturulmadı. Mevcut `HexWorldRuntime` sürekli konumu tutuyor; hücre pozisyonu/occupancy bu konumla tutarlı türetilmiş görünüm olarak doğrulanıyor. Eski cell-based çağrılar hücre merkezine yerleşerek geriye uyumluluğu koruyor.
5. **Spatial broadphase temeli:** native `AABB` ve map-scoped `UniformGridIndex` eklendi. Mevcut actor ID anahtarı kullanılıyor; index kimlik veya pozisyon otoritesi değil.
6. **Runtime index bağlantısı:** aktör kaydı, hareket, map transfer ve kaldırma sırasında sürekli konum indeksleniyor/güncelleniyor. Runtime sorgusu stabil ID sırasıyla aday döndürüyor.
7. **Persistence:** `HexWorldSnapshot` v2 sürekli x/y kaydediyor. v1 cell-only kayıtlar açıkça hücre merkezine migrate ediliyor; kayıtta olmayan hız/ara hareket uydurulmuyor. Dış `GameSaveDocument` sürümü değiştirilmedi.
8. **Interaction katmanı:** NPC tıklama hedeflemesi `HexGameplayView` hücre taramasından application `HexInteractionService`'e taşındı. Ekran noktası önce world point'e çevriliyor, adaylar spatial index ile bulunuyor; sol tık diyalog ve sağ tık boş menü kabuğu davranışı korunuyor.
9. **Render:** NPC ve oyuncu render konumları mevcutsa runtime'ın sürekli konumunu kullanıyor; render interpolasyonu authoritative runtime state'i değiştirmiyor.
10. **Kimlik bağımlılığı:** `hex_actor_binding.py` içindeki lab EntityId wrap/unwrap kaldırıldı. `WorldActorRegistry` actor ID'si doğrudan kullanılıyor.

## Eklenen/yenilenen test kapsamı

- WorldPoint ve continuous position doğrulaması.
- Y-down axial/world round-trip ve sınır tie-break.
- WorldTransform continuous screen/world round-trip.
- Uniform grid map scope, AABB exact filtering, update/remove ve deterministik sorgu.
- Runtime continuous position, türetilmiş occupancy, index tutarlılığı, başarısız güncelleme atomikliği.
- Hex-world snapshot v2 round-trip ve v1 cell-only migration.
- Application NPC hedef sorgusu ve aynı hücrede stabil ID tie-break.
- Actor identity wrapper kaldırıldı; mevcut actor registry sahiplik testleri korundu.

**Test durumu:** Bu çalışma oturumunda Python test paketi çalıştırılamadı. GitHub commit status sorgusu da raporlanmış bir CI check döndürmedi. Testler eklendi; başarılı oldukları iddia edilmiyor. Yerel doğrulama zorunludur.

## Henüz aktarılmayan / tamamlanmamış kabiliyetler

1. Laboratuvar movement intent, mode, state ve integrator davranışlarının ana oyunun canonical simulation tick'ine bağlanması.
2. Gerçek movement speed/config değerlerinin doğrulanması; mevcut Eldoria'da onaylı world-unit/s değeri bulunmadan değer atanmayacak.
3. Native physics body/shape, static hex collision geometry, broadphase/narrowphase, continuous sweep ve solver aktarımı.
4. Player radius 8 dışında NPC/prop collider ölçülerinin belirlenmesi; henüz onay yok.
5. Dinamik çarpışma indeksinin gerçek collider bounds ile beslenmesi. Şu anki runtime grid actor merkez noktalarını interaction/konum adayı olarak indeksler; fiziksel gövde broadphase'i değildir.
6. Etkileşim profile/range/tag/priority sözleşmesinin tam aktarımı. Mevcut click davranışı korunmuştur; yeni etkileşim davranışı eklenmemiştir.
7. `hex_world_geometry_bridge.py`, `hex_physics_bridge.py` ve kalan tüm lab import tüketicilerinin native Eldoria karşılıklarıyla değiştirilmesi.
8. `pyproject.toml` içindeki `hex_world_lab*` package discovery'nin kaldırılması. Bu adım tüm runtime ve test import'ları sıfırlanana kadar yapılmayacak.

## Koruma notları

- `experiment/map-cleanup` dışında dal değiştirilmedi.
- `main`, `demo_eldoria` veya laboratuvar dalına yazılmadı.
- Laboratuvar kaynak dosyaları ana oyuna kopyalanmadı.
- Yeni oyun içeriği veya oynanış özelliği eklenmedi.
- Save migration açık ve sürümlüdür; dış save schema v3 korunmuştur.

**Sonuç:** İlk yerel dikey dilim uygulandı; teknik aktarım tamamlanmış değildir. Sıradaki ana iş, native fizik ve sabit tick movement pipeline'ıdır. Lab paketini kaldırma aşamasına henüz gelinmemiştir.


## 2026-11-19 — Native physics foundation (first slice)

After inspecting the laboratory physics package and Eldoria's existing spatial contracts, an Eldoria-owned physics domain package was introduced:

- `core/domain/physics/vector2.py`: finite immutable vector using Eldoria's y-down (+X right, +Y down) convention.
- `core/domain/physics/shapes.py`: validated circle and strictly-convex polygon collider values.
- `core/domain/physics/body.py`: immutable physics body definition and ground-anchor transform.
- `core/domain/physics/obstacle.py`: map-scoped static obstacle value and world-shape projection.
- `core/domain/physics/__init__.py`: public exports.
- `tests/test_spatial/test_native_physics_primitives.py`: primitive, validation, transform and obstacle tests.

These are newly authored Eldoria-native contracts; no laboratory source file was copied. They are not yet wired into `hex_physics_bridge.py`, actor binding, map geometry generation, or movement. The existing bridge still uses laboratory types and must remain until the native collision pipeline is complete.

### Simulation timing finding

The canonical Eldoria simulation clock is `core.simulation.SimulationRuntime`, which advances by integer `Tick` values and notifies registered tick listeners. The laboratory movement integrator accepts a seconds-based delta but does not own a clock. Pygame `Clock.tick()` supplies elapsed frame milliseconds and is a render-loop timing measurement, not a canonical simulation tick definition. Therefore no tick frequency or movement speed has been assumed and no Pygame frame delta has been wired directly into authoritative movement.

### Current status after this slice

- Native collider/body primitives: authored; tests added but not executed.
- Native map collision geometry: not yet implemented.
- Native narrowphase/continuous sweep/kinematic solver: not yet implemented.
- Runtime movement integration: not yet implemented.
- Lab imports: still present; no dependency cleanup attempted.
- CI/test result: not verified in this session.


## 2026-11-19 — Native map collision geometry (second slice)

Added an Eldoria-native map collision projection without constructing a laboratory world:

- `core/domain/physics/hex_map_geometry.py`: immutable `BoundaryPolicy`, `HexBoundaryEdge`, and `HexMapCollisionGeometry` contracts. Boundary edges can be represented as thin static polygon obstacles.
- `core/domain/physics/obstacle_index.py`: static obstacle AABB calculation and a map-scoped `StaticObstacleIndex` backed by Eldoria's `UniformGridIndex`.
- `application/hex_map_physics.py`: application-layer factory that reads the canonical `HexMapDefinition` directly and creates native obstacles for blocked cells, non-walkable landmarks, supplied static obstacles, and exposed perimeter edges.
- `tests/test_spatial/test_native_hex_map_geometry.py`: tests for blocked cells, non-walkable/walkable landmarks, blocked/open boundaries, deterministic broadphase lookup, and invalid hex size.

Architecture correction during implementation: map-definition projection belongs in the application layer because `HexMapDefinition` is owned by `application`. The physics domain package now contains only physics/spatial contracts and does not import application types. No second world/runtime or lab-world conversion is used by the new builder.

### Current limits

- The native map geometry is authored but not yet consumed by `application/hex_physics_bridge.py`; the existing bridge and its lab imports remain in place.
- The native obstacle index currently covers static obstacle bounds only. Dynamic actor collider AABBs are not yet registered.
- Circle-vs-polygon narrowphase, swept collision, contact resolution, and sliding response are not implemented yet.
- The newly added tests have not been executed in this session; no passing CI result is claimed.


## 2026-11-19 — Native narrowphase and kinematic resolution (third slice)

Added the first Eldoria-owned collision decision and response layer:

- `core/domain/physics/contacts.py`: immutable contact and contact-manifold values. Contact normals are normalized and point from the obstacle toward the moving shape.
- `core/domain/physics/narrowphase.py`: circle-circle, circle-convex-polygon, and convex-polygon-convex-polygon overlap/contact calculations using Eldoria `WorldPoint` and `Vector2`.
- `core/domain/physics/kinematic_solver.py`: deterministic discrete kinematic resolution, bounded depenetration, stable obstacle ordering, conservative swept-AABB candidate selection, and tangential wall sliding.
- `tests/test_spatial/test_native_collision_solver.py`: narrowphase and kinematic tests, including indexed/unindexed candidate equivalence.
- Exported the native contracts from `core.domain.physics`.

The implementation intentionally retains the laboratory solver's current discrete-move limitation: this slice does not prevent tunneling when a single displacement crosses a thin obstacle and ends beyond it. It is not continuous collision detection. Swept AABB is used only to gather possible obstacles; final overlap decisions are made by narrowphase.

Context7's Pygame documentation was checked. `pygame.Rect` collision tests are pixel-rectangle overlap operations with right/bottom edge exclusion; they are not suitable as the authoritative arbitrary-convex continuous physics layer. No Pygame dependency was added to the domain package.

No gameplay movement, simulation tick, collider sizes, save schema, or existing bridge imports were changed. The new solver is not wired into `HexPhysicsSnapshot` or `HexWorldRuntime` yet. Tests are added but their CI result must be checked before claiming they pass.


### Validation result for the native collision slice

Validation completed successfully on commit `293b40104cffd4631df7e68274a6b2053ec4124e`:

- Eldoria CI: all four Python 3.11/3.12 Linux/Windows matrix jobs passed; Pygame headless smoke test passed.
- Core quality: Linux and Windows verification passed. Ruff now explicitly includes the new native physics/application/test files; the legacy map cleanup boundary check and release-candidate verification passed.
- The first CI attempt exposed a pre-existing workflow dependency gap: Eldoria CI installed the runtime package but not `requirements-test.txt`, while laboratory tests import pytest. The workflow now installs the test requirements before unittest discovery.
- The first explicit Ruff pass exposed one missing/unused import pair in the native physics files; both were corrected, and the subsequent Core quality run passed.

This confirms CI validation for the current native map geometry, contact generation, and discrete kinematic solver code. It does not validate continuous collision detection, runtime/gameplay wiring, or local interactive gameplay.


## 2026-11-19 — Native continuous circle collision (fourth slice)

Added the Eldoria-native swept-circle collision layer:

- `core/domain/physics/continuous_solver.py`: circle-vs-convex-polygon edge/vertex time-of-impact tests, circle-vs-circle sweeps, earliest-hit selection, collision skin, pre-move depenetration, and wall-slide projection after impact.
- `tests/test_spatial/test_native_continuous_collision.py`: thin-wall tunneling prevention, polygon edge impact, tangential sliding, moving-away behavior, circle obstacles, and indexed/unindexed result equivalence.
- Exported `SweepHit`, `ContinuousCollisionResolution`, `sweep_circle_polygon`, and `resolve_continuous_motion`.
- Extended Core quality Ruff scope to include the native continuous solver and its tests.

The continuous solver is intentionally limited to a moving circle against static circle/polygon obstacles, matching the existing lab capability. It does not yet handle moving-vs-moving actor collisions, polygon actor sweeps, rotation during motion, or simulation tick integration. It is not wired into gameplay movement yet.

### Validation

- Eldoria CI passed on Python 3.11 and 3.12, Linux and Windows; Pygame headless smoke test passed.
- Core quality passed on Linux and Windows, including Ruff, legacy map cleanup boundary checks, and release-candidate verification.
- The new native continuous-collision tests are included in the successful 1,405-test unittest matrix.
- Context7 Pygame documentation was used to confirm that Pygame rectangle overlap is not the authoritative continuous collision mechanism; the new solver remains Pygame-independent.


## 2026-11-19 — Native bridge and actor-binding integration (fifth slice)

The native collision stack is now connected to the existing Eldoria application contracts without copying laboratory implementation files:

- `application/hex_physics_bridge.py` now builds and consumes `HexMapCollisionGeometry`, `StaticObstacleIndex`, native `PhysicsBodyDefinition`, and `resolve_continuous_motion`. Its snapshot is immutable and validates world/map scope. Center-to-center movement preflight checks the canonical map mask and reports whether the full requested displacement is physically reachable.
- `application/hex_map_physics.py` projects Eldoria's existing `HexMapDefinition` into native obstacles for blocked cells, non-walkable landmarks, caller-supplied static obstacles, and exposed finite-map perimeter edges. `BoundaryPolicy.OPEN` deliberately omits perimeter walls.
- `application/hex_actor_binding.py` and `application/npc_hex_binding.py` now use native `PhysicsBodyDefinition` contracts rather than the lab body-definition type. `application/gameplay_service.py` creates the player's body with native `CircleShape` / `PhysicsBodyDefinition` values. The already-existing player radius 8 approval remains the only actor collider-size decision; no NPC or prop radius was inferred.
- `application/hex_world_geometry_bridge.py` has been rewritten as Eldoria-native axial/local/world adapters using `HexCoord`, `LocalHexPosition`, `WorldHexPosition`, and `WorldPoint`. It no longer imports or adapts laboratory coordinate types.
- The bridge tests now cover map/world scope, origin handling, blocked-cell and landmark geometry, open/blocked map boundaries, static obstacle blocking, native body contracts, and safe commit behavior through the existing actor/hex runtime. Coordinate adapter tests cover round trips, all six directions, canonical y-down projection, and deterministic boundary tie-break.

### Final CI check for this slice

On branch head `d86865e56fd6ce3d8a78a2ba2a992533543b2585`:

- Eldoria CI run `44558298584`: all five jobs succeeded (Python 3.11/3.12 Linux and Windows plus Pygame headless smoke).
- Core Quality run `44558298827`: both Linux and Windows jobs succeeded, including Ruff, legacy map cleanup boundary checks, and release-candidate verification.

### Remaining audit boundary — do not remove lab discovery yet

The directly relevant application bridge and binding files were inspected on this branch. The player and NPC physics body bindings in those files are native; the container and resource-node hex binding modules contain no lab/body-definition references. The native geometry factory and static obstacle index were also reviewed, and their targeted boundary/query tests are present in the passing CI suite.

**A complete repository-wide scan of every production module and test import has not yet been completed.** Therefore this report does not claim that all laboratory imports have been eliminated. `pyproject.toml` still includes `hex_world_lab*` package discovery intentionally. Do not remove that entry, lab package files, or any test package until a complete branch-specific import/consumer scan establishes that every production consumer has migrated and the remaining test-only dependencies are understood.

### Explicitly not connected in this slice

The continuous solver remains a physics preflight capability, not the authoritative per-frame player/NPC movement integrator. It has not been connected to `SimulationRuntime` because the canonical tick-to-seconds and movement-speed contract still requires a separate decision. The existing `HexWorldRuntime` remains the sole discrete world/occupancy owner. No new actor registry, world runtime, save schema migration, gameplay feature, or unapproved collider size was introduced.


## 2026-11-19 — Complete branch-specific Python dependency scan

A branch-head scan was completed against `experiment/map-cleanup` at commit `4583bbeb1c1006609a32bd81251d8e04c99d7a23`. The recursive Git tree contained 641 Python files: 257 production files outside the laboratory package, 123 laboratory source files, and 261 test files (179 outside the laboratory test suite and 82 under `tests/test_hex_world_lab/`).

### Findings

- All 257 production Python files outside `hex_world_lab/` were inspected. No production application/domain/UI module imports `hex_world_lab` or its implementation types. The remaining direct production-side coupling is isolated to `scripts/verify_release.py`: its wheel smoke check imports the lab version, `EntityWorldCoordinator`, `PygameWorldRenderer`, `SimulationTickCoordinator`, and `MovementSystem`; its compileall target also includes `hex_world_lab`.
- All 179 Python tests outside `tests/test_hex_world_lab/` were inspected. No test outside that dedicated legacy suite imports the lab package. Hits for `EntityId` and `BodyDefinition` in the scan were reviewed as false positives or native Eldoria contracts (e.g. `core.foundation.EntityId` and `core.domain.physics.PhysicsBodyDefinition`), not lab dependencies.
- The 123 files under `hex_world_lab/` and 82 files under `tests/test_hex_world_lab/` remain the isolated reference implementation and its dedicated test suite. They are not yet removable because several lab capabilities (including camera, movement, companion, interaction, content/environment presentation, and procedural rendering systems) have not all been transferred and validated natively.
- `pyproject.toml` still explicitly includes `hex_world_lab*` in setuptools package discovery. This is currently required by the release wheel check above.
- `.github/workflows/eldoria-ci.yml`, `.github/workflows/core-quality.yml`, `requirements.txt`, `requirements-test.txt`, and `requirements-release.txt` contain no direct `hex_world_lab` package reference.

### Decision

The application/domain/UI import migration is complete for the scanned production surface, but the laboratory package is **not yet removable**. Keep `hex_world_lab*` in package discovery, keep the lab source and its dedicated tests, and keep the release gate intact until its expected lab capabilities are replaced by native Eldoria equivalents and the release gate is updated to verify those native contracts. No source or packaging files were changed as part of this audit.

## 2026-11-19 — Next-slice decision: simulation timing contract

The release gate and movement timing boundary were re-inspected before selecting the next transfer slice.

### Verified repository facts

- `scripts/verify_release.py` still imports the laboratory package in its isolated wheel smoke test (`__version__`, `EntityWorldCoordinator`, `PygameWorldRenderer`, `SimulationTickCoordinator`, and `MovementSystem`) and includes `hex_world_lab` in its compileall targets. This is an intentional remaining release-gate dependency, not a production gameplay import.
- Eldoria's canonical `core.time.Tick` is a non-negative integer value. It defines ordering and arithmetic, but no seconds-per-tick conversion or tick frequency.
- `core.simulation.SimulationRuntime` advances by integer ticks and notifies listeners with the resulting `Tick`. It does not provide elapsed seconds.
- The laboratory `MovementIntegrator` accepts `delta_time` in seconds, and `MovementConfig.max_speed` is expressed in world units per second. Its coordinator owns neither wall-clock time nor presentation.
- Pygame frame timing is therefore not a valid substitute for a canonical simulation-time conversion.

### Decision

Do not connect the continuous movement integrator to `SimulationRuntime` yet. Do not infer a tick frequency, movement speed, or movement mode tuning from frame rate or defaults. The movement transfer remains the next major vertical slice, but its integration contract must first define the canonical tick duration and source the actual movement configuration without inventing values.

The safe implementation order is:
1. Keep the already-native continuous physics and bridge code as-is.
2. Establish an explicit, game-owned simulation-time conversion contract (tick frequency / seconds per tick) and identify the authoritative player movement configuration.
3. Implement an Eldoria-native movement state/integrator using that contract, then register it as a listener on the existing `SimulationRuntime`; preserve `HexWorldRuntime` as the sole world/occupancy owner and synchronize continuous position through its existing APIs.
4. Add deterministic tests for tick-to-displacement, pause/no-op input, mode multipliers, collision response, cell/occupancy synchronization, and save/load continuity.
5. Only after all remaining lab consumers and the release gate have native replacements should `scripts/verify_release.py` and `pyproject.toml` stop referencing the lab package.

### Guardrails retained

No source implementation, package discovery, release gate, save schema, or gameplay behavior was changed in this decision pass. `main`, `demo_eldoria`, and `experiment/hex-world-laboratory` remain untouched. All further work stays on `experiment/map-cleanup`.
