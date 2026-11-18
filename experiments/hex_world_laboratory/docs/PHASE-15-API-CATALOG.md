# Aşama 15.3 — Doğrulanmış API ve Modül Kataloğu

Denetim tarihi: 19 Kasım 2026. Bu katalog gerçek export ve kaynak kullanımına göre doğrulanan API adaylarını listeler; her sınıfı public API ilan etmez.

## 1. Laboratuvar — Pygame bağımsız çekirdek

| Paket | Doğrulanan API adayları | Sorumluluk | Bağımlılık sınırı |
|---|---|---|---|
| geometry | AxialCoord, CubeCoord, WorldPoint, HexLayout, HexOrientation, dönüşüm/komşuluk fonksiyonları | Hücre matematiği ve sürekli dünya koordinatı | Saf Python; Pygame yok |
| world | WorldId, MapId, CellAddress, HexMapDefinition, MapRegistry, HexWorldRuntime, HexWorldView | Dünya/harita kimliği, immutable map tanımı ve runtime | Geometry/domain |
| movement | MovementIntent, MovementState, MovementConfig, vector/integrator | Sürekli WorldPoint hareketi | Geometry; presentation yok |
| physics | body/shape/contact/solver, continuous collision, broadphase/narrowphase | Hareket kısıtları ve çarpışma | Geometry, spatial adapter |
| spatial | UniformGrid, Quadtree, bounds/entry/protocol | AABB aday sorgusu | Genel veri yapıları |
| entities | EntityId, EntityKind, EntityRecord, EntityRegistry, EntityTransform, EntitySpatialIndex | PLAYER/NPC/RESOURCE kayıtları | World, physics/spatial |
| simulation | SimulationTickCoordinator, CollisionAwareMovementSystem, MovementCellTracker | Deterministik tick sırası ve state eşitleme | Pygame/wall-clock yok |
| rendering.snapshot | WorldRenderSnapshot ve immutable visual records | Render-pass için salt okunur veri | Pygame yok |
| content | VisualDocument, ContentDefinition, ContentLibrary, ContentPlacement, MapContentDocument | Vektör içerik modeli ve yerleşim | Pygame yok |
| content.persistence | Library/map-content JSON v1 codec ve file storage | Strict JSON persistence | Domain; Pygame yok |

## 2. Laboratuvar — Pygame adaptörleri

| Paket | Sorumluluk | Sınır |
|---|---|---|
| input | Pygame klavye/input örnekleme | Event/display thread koşullarına bağlı |
| camera | Kamera state ve world/screen transform | Simülasyon state'ine yazmaz |
| rendering.procedural | Canvas/Surface, palette, geometry drawing, profile builders, bounded cache | Pygame Surface üretir |
| rendering.content_adapters | ContentDefinition/Placement → environment scene ve physics shape | Domain modelini runtime sunum tiplerine dönüştürür |
| rendering.pygame_world_renderer | Snapshot + camera ile çizim | Render-only |
| app.py, __main__.py | Laboratuvar demo uygulaması/launcher | Ana oyuna taşınmaz |

Pygame bağımsız paketler ana oyunun çekirdek/domain katmanına aday olabilir. Surface, event veya display kullanan modüller domain'e alınamaz; A16'da adaptör ve test gerekir.

## 3. Ana oyun — mevcut hex/domain sözleşmeleri

| Modül | Rol | Sahip olduğu veri |
|---|---|---|
| core.domain.spatial.HexCoord | Axial geometri adresi | Topolojik q/r |
| LocalHexPosition | Map-local axial hücre | Hücre q/r |
| WorldHexPosition | Dünya haritasındaki axial map konumu | World-level q/r |
| EntityPosition | map_id + LocalHexPosition | Hex runtime içindeki mantıksal entity konumu |
| MovementRequest/Result/Profile | Hücre adımlı hareket kuralları | Hareket isteği/sonucu |
| application.HexWorldRuntime | Entity movement, occupancy ve pathfinding | Ana oyunun hex entity lifecycle/state'i |
| PresentationContentService | UI bağımsız package/asset/placement facade | Paket yükleme, validation, save |
| PresentationContentStore | staged validation, atomic write, backup/rollback | Mevcut raster içerik kayıtları |
| AssetCatalog | Raster asset metadata ve güvenli path | PNG path, scale, anchor, collision, depth |
| ScenePlacementCatalog | Map-scoped scene placement | map_id, axial q/r, offsets, footprint, collision, layer |
| WorldTransform | axial/world-pixel/screen dönüşümü | Presentation transform |
| DepthSorter | q/r veya numeric depth sıralaması | Render ordering |
| HexCamera | Takip/edge-scroll camera state | Sunum kamerası |

Main Position(x,y) genel sürekli 2D değer tipidir; EntityPosition hex runtime için map-local discrete hücre adresidir. Bunlar birbirinin yerine kullanılamaz.

## 4. API istikrar sınıfları

- Aday public/domain API: geometry value objects, world definitions, content domain models, persistence codec.
- Adaptör API: simulation coordinator callback sınırı, physics/spatial adapters, renderer snapshot adapter, content-to-environment adapter.
- Uygulama içi/özel: demo app, test fixture, diagnostics overlay, profile factory iç ayrıntıları, cache key ve renderer internals.
- Entegrasyon sözleşmesi olmayanlar: launcher, demo scene, phase benchmark scripts.

## 5. A16 API kapıları

1. Alınacak her paket için import bağımlılık grafiği ve Pygame import taraması.
2. Public API listesi gerçek __all__, dış import kullanımı ve testlerle sabitlenmeli.
3. Main API kaldırılmadan önce adapter parity testleri yazılmalı.
4. Lab API doğrudan Main public API'sine taşınmamalı; namespace ve packaging kararı önce çözülmeli.
5. Serialization API'leri mevcut schema dosyalarını değiştirmeden ayrı format olarak kalmalı.

## 6. Kaynaklar

Lab: geometry/__init__.py, world/__init__.py, simulation/__init__.py, simulation/tick_coordinator.py, rendering/snapshot.py, content/definition.py, content/persistence/codec.py.
Main: core/domain/spatial/__init__.py, core/domain/spatial/movement.py, application/hex_world_runtime.py, application/presentation_content_service.py, application/presentation_content_store.py, game_ui/assets/asset_definition.py, game_ui/assets/placement_catalog.py.
