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
