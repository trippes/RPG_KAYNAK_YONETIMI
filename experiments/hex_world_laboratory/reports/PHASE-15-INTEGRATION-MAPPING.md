# Aşama 15.4 — Laboratuvar / demo_eldoria Entegrasyon Eşleştirmesi

Denetim tarihi: 19 Kasım 2026. demo_eldoria kaynakları salt okunur incelendi. Hiçbir ana oyun dosyası değiştirilmedi.

## 1. Dosya ve sorumluluk eşleştirmesi

| Lab bileşeni | Main karşılığı | Önerilen sınıflandırma | Gerekçe / A16 işi |
|---|---|---|---|
| geometry/* | core/domain/spatial/hex_coord.py, hex_geometry.py, local_hex_position.py | ADAPTÖRLE KULLAN | Aynı axial kavramlar mevcut; layout/radius/origin ve dönüşüm API'leri aynı değildir. Parity testleri ve tek geometry authority gerekir. |
| world/* | application/hex_map_definition.py, hex_world_runtime.py, world_map_definition.py | ANA OYUNDA MEVCUT/KORU + ADAPTÖR | Main schema v2 ve map registry mevcut. Lab map v1/runtime modelini doğrudan kopyalamak paralel dünya otoritesi üretir. |
| movement/* | application/hex_movement_rules.py, hex_occupancy.py, hex_pathfinding.py, core/domain/spatial/movement.py | ADAPTÖRLE KULLAN / YENİDEN TASARIM | Main hücre adımlı movement; Lab continuous WorldPoint + collision-aware step. İkisi eşdeğer değil. Tek authoritative player movement modeli kararlaştırılmalı. |
| physics/* | core/domain/spatial/*, application/hex_occupancy.py ve mevcut actor movement | ADAPTÖRLE KULLAN | Main occupancy hücre tabanlıdır; Lab continuous collision geometry ayrı. A16 ilk dilimde fizik davranışı doğrudan değiştirilmemeli. |
| spatial/* | application/hex_occupancy.py, core/entity/* | ANA OYUNDA MEVCUT/KORU + KOŞULLU ADAPTÖR | Main occupancy logical cell/blocking; Lab UniformGrid AABB broadphase. Farklı sorumluluklar. Dynamic query workload kanıtlanırsa index adaptörü eklenebilir. |
| entities/* | core/entity/*, application/actor_system.py, application/hex_world_runtime.py | ADAPTÖRLE KULLAN | Main actor/entity lifecycle ve Lab EntityRegistry ayrı modeller. İki registry aynı actor için paralel authoritative kayıt tutmamalı. |
| companions/* / interaction/* | Main social/NPC/gameplay service ve UI interaction | KAPSAM DIŞI (A15) | A15 yalnızca mevcut sözleşme eşleştirmesi; yeni companion/AI davranışı veya gameplay değişikliği yok. |
| simulation/* | core/simulation/*, application/gameplay_service.py, game_application.py | ADAPTÖRLE KULLAN | Main simulation runtime/action dispatcher zaten var. Lab tick coordinator'ı ikinci tick owner olarak doğrudan eklenemez. |
| camera/* | game_ui/camera.py, game_ui/world_rendering/camera.py, world_transform.py | ANA OYUNDA MEVCUT/KORU + ADAPTÖR | Main WorldTransform axial/world-pixel/screen; Lab camera transform continuous WorldPoint. Viewport/scale contract gerekir. |
| rendering/* | game_ui/renderer.py, game_ui/world_rendering/*, AssetManager | ANA OYUNDA MEVCUT/KORU + ADAPTÖR | Main renderer, sprite/scene objects ve depth sorter mevcut. Lab snapshot renderer doğrudan replacement değil. |
| environment/* | game_ui/assets/*, world_rendering/scene_object.py | ADAPTÖRLE KULLAN | Lab WorldPoint anchor/scene modelini Main q/r + pixel offsets/footprint/layers'a dönüştürmek gerekir. |
| content/* | game_ui/assets/asset_definition.py, placement_catalog.py, application/content_loader.py | ADAPTÖRLE KULLAN / COEXIST | Raster AssetCatalog ve axial ScenePlacementCatalog korunmalı; vector VisualDocument için ayrı asset provider/renderer adapter. |
| content persistence | application/presentation_content_service.py, presentation_content_store.py | ANA OYUNDA MEVCUT/KORU | Main staged validation, atomic writes, backup/rollback mevcut. Lab storage kodu Main package üzerine yazılmamalı. |
| lab app.py / __main__.py | main.py, application/game_application.py, game_ui/starter.py | KAPSAM DIŞI | Lab launcher ve test scene ana oyun giriş noktasına taşınmaz. |

## 2. Content pipeline özel eşleştirmesi

Main:
- AssetCatalog: raster PNG path, dimensions, scale, normalized anchor, collision AABB, depth/layer metadata.
- ScenePlacementCatalog: map_id + axial q/r, pixel offsets, footprint, collision box, depth, layer.
- PresentationContentService: UI bağımsız load/validate/list/save facade.
- PresentationContentStore: staged package validation, atomic replacement, backup/rollback ve explicit legacy migration.
- AssetManager / SceneObjectRenderer: Pygame image cache ve sprite presentation.

Lab:
- VisualDocument: Pygame bağımsız vector primitives/layers/palette/ground-depth anchor.
- ContentDefinition/Library: reusable vector definition ve explicit collider.
- ContentPlacement/MapContentDocument: map-local world-space x/y placement.
- JSON v1 strict codec ve Pygame Surface adapter.

Öneri: Main package ve mevcut PNG kayıtları korunur. Vector ContentLibrary ilk etapta ayrı read-only kaynaktan okunup Pygame Surface asset provider'a bağlanabilir. Main placement katalogları axial yerleşim otoritesi olarak kalır. Bu yalnızca A16 için öneridir; bu aşamada kod yazılmamıştır.

## 3. Koordinat dönüşüm riskleri

- Lab WorldPoint matematiksel world coordinates: X sağa, Y yukarı.
- Main WorldTransform world-pixel presentation: pixel geometry ve camera/zoom.
- Main SceneObjectPlacement q/r map-local hücre + world-pixel offset.
- Main WorldHexPosition dünya topolojisinde map konumudur; Lab WorldId/MapId ile otomatik eşdeğer değildir.
- Lab ContentPlacement x/y doğrudan Main q/r'ye atanamaz.
- Lab circle/polygon collider, Main collision AABB'ye indirgenirse şekil doğruluğu kaybolur; bu dönüşüm varsayılan kabul edilemez.

## 4. Dosya kararı ve güvenlik

- Main core/domain, application, game_ui ve content dosyaları A15 boyunca değiştirilmez.
- Eski Main runtime, AssetCatalog, ScenePlacementCatalog ve safe store kaldırılmaz.
- Her A16 dilimi önce adapter/parity testleri ile başlar; eski yol yeni yol kabul edilmeden devreden çıkarılmaz.
- Aynı entity veya content record için iki authoritative writer kurulmaz.
- Schema migration ayrı onay ve backup/rollback gerektirir.

## 5. İncelenen ana dosya aileleri

application/hex_map_definition.py, hex_world_runtime.py, hex_movement_rules.py, hex_occupancy.py, hex_pathfinding.py, content_loader.py, presentation_content_service.py, presentation_content_store.py, core/domain/spatial/*, core/entity/*, core/simulation/*, game_ui/world_transform.py, game_ui/world_rendering/camera.py, depth_sorter.py, scene_object.py, game_ui/assets/asset_definition.py, placement_catalog.py, asset_manager.py.

**Sonuç:** Laboratuvarın değeri Main'in mevcut altyapısını silmek değil; sürekli hareket/fizik, entity broadphase, immutable render snapshot ve vector content gibi kabiliyetleri kontrollü adaptörlerle kazandırma potansiyelidir.
