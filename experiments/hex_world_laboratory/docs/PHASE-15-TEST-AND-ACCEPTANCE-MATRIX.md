# Aşama 15.7 — Entegrasyon Test ve Kabul Matrisi

Tarih: 19 Kasım 2026. Bu matris A16 için test gereksinimlerini tanımlar; A15 sırasında yeni testlerin çalıştırıldığı anlamına gelmez.

## 1. Test katmanları ve kabul kanıtı

| Alan | Otomatik test | Regresyon / entegrasyon | Manuel/görsel kabul |
|---|---|---|---|
| Geometry | Axial↔WorldPoint roundtrip; flat/pointy; negative/large coords; boundary tie-break; tolerance | Main HexCoord/LocalHexPosition parity ve map/world ID mapping | Hücre merkezleri, kenar seçimi ve kamera hizası |
| Map/world | Missing cell, map scope, map transition, immutable definitions | Lab map adapter vs Main schema v2 fixtures | Harita sınırları, map değişiminde entity konumu |
| Movement | Fixed tick, velocity, collision, wall slide, high-speed sweep, deterministic retry | Main movement rules/occupancy parity; no duplicate actor state | Karakter hareketi, engel ve köşe davranışı |
| Physics | Narrowphase truth, broadphase no false negatives, shape transforms | Existing Main collision/blocked cell regression | Collider overlay, sprite anchor ve collision alignment |
| Spatial/entity | UniformGrid vs brute-force; lifecycle add/update/remove; stale/duplicate checks | Registry/occupancy consistency, map unload/reload | Player/NPC/resource selection and target range |
| Simulation | Tick order, retry checkpoint, one input sample, render purity | Main scheduler/action/tick ownership; no double update | Frame pacing, time progression, no duplicated movement |
| Camera/render | World-screen roundtrip, snapshot immutability, culling, stable sort | Main WorldTransform/depth sorter and renderer adapter | Zoom/pan/follow, Y-sort, anchor, map bounds |
| Content model | JSON v1 roundtrip, unknown field/version rejection, duplicate IDs, refs | Main asset catalog/placement adapter and ID mapping | Vector profile appearance and layer order |
| Collider/content | Explicit circle/polygon collider tests; no visual-derived collider | Conversion fidelity; no silent polygon→AABB downgrade | Tree trunk/canopy, rock footprint, anchor alignment |
| Persistence | Create/replace modes, invalid input no-write, backup/rollback | Main PresentationContentStore + legacy/split package fixtures | Existing content package and saves open unchanged |
| Packaging | clean install, wheel/sdist file listing, import smoke, dependency resolution | Python 3.11/3.12, Windows/Linux, chosen pygame distribution | Start/quit, asset availability, no missing module |
| Performance | Tick, render, spatial query, memory benchmark | Same workload/environment baseline comparison | Target hardware frame pacing and responsiveness |
| Licensing | Dependency metadata, NOTICE, asset provenance manifest check | Distribution bundle audit | Manual release/legal sign-off |

## 2. Required CI matrix

Minimum A16 release-candidate matrix:
- OS: Windows and Ubuntu Linux.
- Python: 3.11 and 3.12 (extend if project support policy changes).
- Pygame distribution: only the explicitly selected distribution in each environment.
- Install modes: editable source install and built wheel install.
- Headless: SDL dummy display/audio smoke where applicable.
- Test commands: Lab pytest, Main unittest, Ruff lint/format, packaging smoke, asset/resource resolution.

Lab and Main tests must remain separately invocable until shared package boundaries are proven. A single combined test count must not conceal which project or platform failed.

## 3. Performance baseline protocol

Compare only when hardware/runner, Python version, dependency distribution, entity count, workload and warm/cold cache state are held constant.

Record:
- simulation tick mean and p95 batch latency;
- render snapshot mean and p95;
- spatial query vs brute-force;
- index build/update cost;
- Surface cold generation/cache hit;
- peak Python heap and process memory separately;
- frame-time p50/p95 on user target hardware.

Historical A11/A13/A14 benchmark figures are observational references, not release thresholds. A16 must create a fresh pre-integration baseline and compare each slice against it.

## 4. Data/persistence regression fixtures

Required fixtures:
- Existing Main content package manifest v1.
- Legacy combined presentation_assets.json.
- Split asset_catalog.json + map_placements directory.
- Main Hex Map schema v2 examples.
- Lab MAP JSON v1 and runtime snapshot v1.
- Lab Content Library v1 and Map Content v1.
- Missing PNG, invalid PNG, unsafe path, unknown asset/content ID.
- Existing save files and package backups.

Acceptance: Every supported legacy fixture remains readable; unsupported/unknown schema fails explicitly; invalid staged update changes no live file; rollback restores original bytes.

## 5. Visual acceptance checklist for A16

- Axial cell center and world transform remain aligned at zoom 0.5x/1x/2x.
- Camera follow, pan, edge bounds and viewport resize behave consistently.
- Sprite ground anchor and depth sorting do not jitter.
- Tree trunk/canopy visual and collider responsibilities remain separate.
- Rock collider matches footprint; visual bounds do not become collider implicitly.
- Vector profiles rasterize consistently across Windows/Linux.
- Existing Main world assets and placements render as before.
- Missing/corrupt asset fallback remains deterministic.
- Existing save/content package opens without migration.
- No unexpected flicker, stale render snapshot, duplicate movement or frame hitch.

## 6. A15 evidence status

- Aşama 14 kapanış raporu historical reference: Lab 881/881, Ruff pass, Core Quality Linux 2,344 and Windows success.
- These historical results are not a new A15 execution result.
- A15 final HEAD CI must be rechecked before readiness closure.
- User desktop acceptance is still required for any A16 visual/runtime changes.
