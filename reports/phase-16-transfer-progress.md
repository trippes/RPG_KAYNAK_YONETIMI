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

## 2026-11-19 — Native continuous movement domain slice

### Existing timing policy verified

- `time_system/tick.py` defines the legacy calendar's `TICKS_PER_SECOND = 60`.
- `game_ui/game_window.py` currently accumulates 60 simulation ticks per elapsed real second, but only while a duration-based activity is running and gameplay is unpaused.
- `hex_world_lab/simulation/movement_system.py` uses a 1/60-second movement step.
- Canonical `SimulationRuntime` itself remains integer-tick-only and has no seconds-per-tick contract. The 60 Hz behavior currently lives in application/legacy policy, not in the canonical clock abstraction.
- No authoritative player world-units-per-second movement speed was found in the inspected native gameplay configuration. No speed value was invented.

### Native implementation added

Created `core/domain/movement/` as an Eldoria-owned, Pygame-independent domain package:

- `MovementMode`: normal, running, stealth identifiers.
- `MovementConfig`: validated speed and mode multipliers; maximum speed is mandatory and has no invented default.
- `MovementIntent`: device-independent direction and mode.
- `MovementState`: immutable continuous world position, velocity, and mode using native Eldoria `WorldPoint` and `Vector2`.
- `MovementIntegrator`: pure seconds-based integration. It owns no clock, tick counter, actor registry, map runtime, or presentation state.
- `tests/test_spatial/test_native_continuous_movement.py`: coverage for normalization, mode multipliers, idle input, zero delta, invalid delta/configuration, and state immutability.

The native implementation was authored against Eldoria's own domain values; no laboratory source was copied. Context7 Python 3.11 documentation was consulted for dataclass validation and finite-number handling.

### Integration boundary retained

This slice deliberately does not register the integrator with `SimulationRuntime` or change `GameWindow._advance_active_time`. The current 60-tick/real-second policy runs only while timed activities are active, whereas continuous player movement must also function during ordinary exploration. Reusing that policy blindly would make movement stop whenever no timed activity is running or would silently change the game's time progression. A canonical fixed-step gameplay driver and its pause/active-world policy must be established before wiring movement into the canonical runtime.

The next slice must source the actual player movement speed from authoritative gameplay/content configuration, define how gameplay fixed steps advance during exploration and pause, and then compose native integration with the already-native continuous collision solver and `HexWorldRuntime` synchronization.

### Validation

- Eldoria CI and Core Quality workflows were triggered by the new branch commits; their final results are pending at the time of this report.
- Core Quality's Ruff file list was expanded to include all new native movement files and the new test module.
- No local Python test execution is claimed in this GitHub-only pass.

### Safety

All changes target `experiment/map-cleanup` only. No changes were made to `main`, `demo_eldoria`, or `experiment/hex-world-laboratory`. The lab release-gate imports and package discovery remain intact.


## 2026-11-19 — Application fixed-step movement clock

The timing boundary was advanced without coupling continuous movement to canonical world time:

- Added `application/gameplay_step_clock.py` with `FixedStepAccumulator`. It converts measured frame elapsed seconds into a count of fixed movement steps (default 1/60 second), carries fractional time between frames, validates numeric inputs, and discards partial accumulated time when gameplay is inactive.
- Added `tests/test_application/test_gameplay_step_clock.py` for partial-frame accumulation, multiple due steps, pause/inactive reset, zero elapsed time, and invalid inputs.
- Extended Core Quality Ruff scope to include the new application clock and its tests.
- Context7 Pygame documentation confirms `Clock.tick()` reports elapsed milliseconds between frames and optionally caps render framerate. It is therefore an elapsed-time measurement source, not itself a simulation tick or movement executor.

### Deliberate boundary

This clock is application-owned movement scheduling infrastructure only. It does not create or advance canonical `core.time.Tick`, does not change the in-world calendar, does not own actors/world state, and does not invoke the movement integrator. The default 60 Hz step preserves the laboratory movement system's existing fixed-step cadence; the scheduler remains independent of whether a duration-based world activity is running.

No movement speed/balance value, save schema, collider size, or gameplay behavior has been added. The next slice can consume the returned step count to orchestrate the native integrator and continuous collision solver through the existing actor registry and `HexWorldRuntime`.

CI validation for this new slice is pending the newly triggered workflow runs.


## 2026-11-19 — Native continuous player movement orchestration (next slice)

Added the first application-layer composition of the Eldoria-native movement and collision contracts:

- `HexPhysicsSnapshot.resolve_motion(...)` now resolves arbitrary continuous circle-body displacement against its own map-scoped static obstacle index. This keeps broadphase ownership inside the existing immutable physics snapshot.
- `application/continuous_player_movement.py` adds `ContinuousPlayerMovementController`. It validates the existing actor binding and map/world scope, reads the current continuous position from `HexWorldRuntime`, integrates one caller-supplied intent/delta, resolves static collision, then commits the final position through `HexWorldRuntime.set_continuous_position(...)`.
- The controller does not create an actor registry, world runtime, clock, input device, or persistence store. `WorldActorRegistry` remains the identity owner and `HexWorldRuntime` remains the continuous position/occupancy owner.
- Failed actor eligibility, collision resolution, or occupancy/map validation does not overwrite the canonical position. Successful cell-boundary crossings update the existing occupancy and spatial index through the runtime API.
- `tests/test_application/test_continuous_player_movement.py` covers continuous position updates, cell/occupancy synchronization, static obstacle response, occupied destination rejection, inactive actors, idle intent, and map-scope validation.
- Core Quality Ruff scope now includes the new controller and tests.

### Important integration boundary

This is an application orchestration component, not yet the live `GameWindow` movement path. The current game input adapter is event-edge based and does not yet provide the laboratory's held-key snapshot semantics, Alt stealth toggle, Shift run hold, or focus-loss reset. In addition, no authoritative production player `max_speed` setting has been identified in Eldoria's existing content/configuration. Test fixtures using a speed value are test-only and are not a gameplay balance decision.

Therefore do not wire an invented speed or infer one from a unit-test fixture. The next slice must migrate the device-independent keyboard intent adapter into Eldoria's input boundary, source or explicitly define the production movement configuration, and only then connect the fixed-step accumulator to this controller in the persistent gameplay loop. Preserve click-to-move, map transitions, dialogue selection, and pause behavior while doing so.

### Validation

CI was triggered by these commits; passing status is not claimed until the corresponding GitHub Actions runs complete. No local test execution is claimed in this GitHub-only implementation pass.

### Safety

All changes target `experiment/map-cleanup`. No changes were made to `main`, `demo_eldoria`, or `experiment/hex-world-laboratory`. The laboratory package, tests, release-gate imports, and package discovery remain intact.


### CI feedback and correction

The first full-suite CI run exposed one incorrect test expectation: map compatibility is validated when a controller processes an actor step, because the actor/map binding is not selected until an actor ID is supplied. The test was corrected to assert rejection at `step(...)` rather than at controller construction. This was a test-contract correction; no runtime behavior was weakened. The corrected commit has triggered fresh CI, and its result remains pending.


## 2026-11-19 — Native keyboard input, actor movement profiles, and live fixed-step wiring

The approved movement-input and content-configuration design has been implemented on the integration branch.

### Keyboard adapter

- Added `game_ui/movement_input.py`, an Eldoria-owned Pygame adapter that emits native `MovementIntent`, `MovementMode`, and `Vector2` values. It does not import or depend on `hex_world_lab`.
- WASD and arrow keys provide held movement; Shift is hold-to-run; Alt toggles stealth on a press edge. Focus loss clears direction and mode state, and focus regain requires Alt to be released before a fresh stealth toggle.
- Direction vectors follow Eldoria's canonical world frame: +X right and +Y down. This intentionally differs from the lab adapter's mathematical +Y-up convention.
- Added focused adapter tests for direction combinations, mode priority, Alt edge behavior, and focus loss/regain.

### Actor-specific movement configuration

- Extended `load_gameplay_rules` with an optional `movement.actors` section and added `load_movement_configs`, returning an immutable mapping from existing stable actor IDs to native `MovementConfig` values.
- Each profile requires a finite, strictly positive `max_speed` in world units per second. Optional running/stealth multipliers retain the laboratory's established 1.5 and 0.5 values unless the package explicitly overrides them.
- Profiles are keyed by the actual actor ID (the player is currently `hero`; NPCs use their existing NPC/actor IDs). Missing profiles are not assigned a default speed.
- Added tests for multiple actor profiles, immutable lookup, absent profiles, invalid speeds, and unsupported fields.
- The protected `content/demo_eldoria/gameplay_rules.json` was not changed. It currently contains no movement profiles, so it does not yet supply a production player speed or NPC speeds.

### Live gameplay-loop composition

- `GameWindow` now owns the native keyboard adapter and `FixedStepAccumulator`. It samples held input during normal gameplay and consumes the accumulator's fixed-duration steps through `ContinuousPlayerMovementController`.
- Movement is inactive during pause, dialogue, open gameplay windows, non-gameplay screens, or lost keyboard focus; the accumulator discards partial elapsed time while inactive. This clock remains separate from canonical world-time ticks and does not change the calendar.
- Configured direct keyboard movement takes priority over click-to-move and cancels the pending click destination. Existing click-to-move remains available when no direct keyboard direction is held. Arrow keys remain UI navigation inputs outside active configured world movement.
- The controller is rebuilt against the current map-scoped binding/snapshot when a movement batch is consumed, so the existing map-transition ownership remains authoritative.

### Activation boundary and verification

- The live loop is wired, but the protected active demo package has no `hero` movement profile. Consequently the default demo does not start continuous keyboard movement yet; no arbitrary speed was inserted. Once an authorized content package supplies a real `hero.max_speed`, the player path becomes active. NPC profiles can be authored independently, while NPC autonomous movement remains a separate future orchestration task.
- Context7 Pygame documentation was used to verify held-key snapshots and `Clock.tick()` elapsed-time semantics.
- Ruff scope now includes the new adapter and its tests plus the actor-profile tests. Final CI verification passed on commit `52ec419f575fcdb308e95796d5357d783334e983`: Eldoria CI run `44581524784` succeeded on Python 3.11/3.12, Linux/Windows, including the Pygame headless smoke test; Core Quality run `44581524798` succeeded on Linux and Windows, including Ruff and release-candidate verification.
- CI initially exposed compatibility gaps in test-created `GameWindow` instances and a focus-regain test expectation. The adapter test and lazy inert runtime initialization were corrected; the successful runs above validate the corrected code.
- All changes remain on `experiment/map-cleanup`. No changes were made to `main`, `content/demo_eldoria`, or `experiment/hex-world-laboratory`.


## 2026-11-19 — Isolated mechanics test content package

Added `content/movement_test/` as a separate, deliberately non-visual test package. It is selected through the existing explicit `--content-package` launch argument; neither `content/active_package.json` nor the protected `content/demo_eldoria/` package is changed.

### Test content

- One 61-cell axial arena with a defined start cell and a small cluster of blocked water/stone cells for continuous collision and wall-sliding checks.
- A player movement profile and two NPC movement profiles. The 64 world-units/second base speed and 1.5/0.5 mode multipliers are test-only values, not final balance.
- One opening-phase NPC with a minimal dialogue and one gameplay-phase NPC used as a blocking spatial actor.
- Two non-blocking resource nodes placed through the package's gameplay-placement catalog.
- No art assets, presentation catalog, or visual effects are included; the package intentionally exercises the existing fallback/minimal world presentation.

### Launch and validation

Run from the repository root:

```powershell
python main.py --play --content-package content/movement_test
```

Added `tests/test_application/test_movement_test_package.py` to verify package loading, movement-profile parsing, NPC/resource registration, and spatial placements. Added that test to the Core Quality Ruff target list.

### Explicit remaining boundary

The package makes player movement, static map collision, NPC presence/occupancy, dialogue, resource placement, and save/load available for manual in-game verification. NPC movement profiles are loaded as content, but autonomous NPC movement orchestration is not yet implemented; do not interpret profile presence as autonomous movement. The test package has not yet been confirmed by a completed CI run or by the user's in-game test.

All files added in this slice are under `content/movement_test/`, the dedicated test module, the Core Quality workflow's Ruff target list, and this report. No changes were made to `main`, `content/demo_eldoria/`, `content/active_package.json`, or `experiment/hex-world-laboratory`.
