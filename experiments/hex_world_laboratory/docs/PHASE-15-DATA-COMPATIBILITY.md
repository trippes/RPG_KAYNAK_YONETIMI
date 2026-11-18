# Aşama 15.3 — Veri ve Şema Uyumluluğu

Tarih: 19 Kasım 2026. Kapsam: Laboratuvar JSON formatları ile ana oyunun mevcut map/runtime/content kayıtlarının karşılaştırılması.

## 1. Mevcut format envanteri

| Format | Sistem | Sürüm | İçerik | Durum |
|---|---|---:|---|---|
| Lab MAP JSON | Lab world.persistence | 1 | world_id, map_id, layout, cells, terrain/walkability/obstacle | Mevcut sözleşme korunacak |
| Lab Runtime Snapshot | Lab world.persistence | 1 | Base map fingerprint ve sparse cell overrides | MAP JSON'dan ayrı runtime state |
| Lab Content Library | Lab content.persistence | 1 | VisualDocument tabanlı vector definitions | Aşama 14 tamamlandı |
| Lab Map Content | Lab content.persistence | 1 | MAP JSON v1 wrapper + world-space placements | Aşama 14 tamamlandı |
| Main Content Package | Main application.content_loader | 1 | Manifest, package files, maps, world map, presentation pointers | Ayrı paket formatı |
| Main Hex Map | Main application.hex_map_definition | 2 | Map-local axial hücreler, terrain, blocked, feature/landmark/transition | Lab MAP v1 ile aynı şema değil |
| Main Raster Asset Catalog | Main AssetCatalog | 1 | asset_id, PNG path, dimensions, scale, normalized anchor, collision AABB, depth/layer | Mevcut ana oyun kaynağı |
| Main Scene Placement | Main ScenePlacementCatalog | 1 | object_id, asset_id, map_id, q/r, offsets, footprint, collision_box, depth/layer | Map-local axial placement |

## 2. Uyumluluk sonucu

Hiçbir mevcut format diğerinin yerine doğrudan kullanılamaz.

- Lab MAP JSON v1 ile Main Hex Map schema v2 farklı alanlar ve map/domain varsayımları taşır.
- Lab Runtime Snapshot v1, Lab HexMapDefinition ve canonical map serialization fingerprint'i ile anlamlıdır.
- Lab Map Content v1, Lab MAP JSON v1'i map alanında sarar; Main schema v2 map payload'ını desteklediği kanıtlanmamıştır.
- Lab Content Library v1 vector artwork ve explicit collider tanımlar; Main AssetCatalog v1 raster PNG path ve presentation metadata taşır.
- Lab ContentPlacement world-space x/y kullanır; Main SceneObjectPlacement map-local axial q/r ve pixel offsets/footprint taşır.
- Main content package loader legacy combined presentation_assets ve split asset_catalog + map_placements biçimlerini ayrı destekler. Lab JSON v1 bu manifest sözleşmelerine kayıtlı değildir.

## 3. Alan eşleştirme tablosu

| Lab alanı | Main karşılığı | Otomatik dönüşüm? | Dikkat |
|---|---|---|---|
| content_id | asset_id | Hayır | ID namespace ve uniqueness kapsamı |
| instance_id | object_id | Hayır | Stable ID mapping ve duplicate kontrolü |
| VisualDocument.logical_size | PNG width/height | Hayır | Rasterization boyutu, scale ve DPI |
| ground_anchor | AssetDefinition.anchor | Koşullu | Lab doküman koordinatı; Main normalized [0,1] |
| depth_anchor | depth_offset / scene depth | Hayır | Anchor Y ile depth offset aynı kavram değil |
| layers/order | scene layer | Kısmi | Document layer order ile underlay/ground/canopy/overlay eşlemesi |
| CircleCollider | collision_box | Hayır | AABB'ye dönüşüm şekil bilgisini kaybettirir |
| ConvexPolygonCollider | collision_box | Hayır | Polygonu AABB'ye indirgemek fidelity kaybıdır |
| Placement x,y | Main q,r,offset_x,offset_y | Hayır | Layout, origin, map size ve world-unit/pixel scale gerekir |
| category/metadata | category/terrain_types/interaction | Kısmi | Semantik mapping ayrıca tanımlanmalı |

## 4. Geriye dönük uyumluluk ilkeleri

1. Main Content Package v1, Main Hex Map schema v2 ve raster placement kayıtları korunur.
2. Lab MAP JSON v1, runtime snapshot v1, Content Library v1 ve Map Content v1 korunur.
3. A16'da aynı dosyaya iki sistemin yazmasına izin verilmez; tek writer/owner belirlenir.
4. Yeni ortak format gerekiyorsa mevcut schema v1/v2 dosyalarının üstüne yazılmaz; yeni açık schema sürümü ve migration gerekir.
5. Migration öncesi package backup, staged parse/validate, referential integrity ve rollback zorunludur.
6. Bilinmeyen alan/versiyon sessizce atılmaz; strict validation korunur.
7. Mevcut PNG dosyaları ve asset ID'leri migration denemesinde silinmez veya yeniden adlandırılmaz.

## 5. Önerilen A16 yaklaşımı

İlk entegrasyon diliminde migration yerine read-only coexistence adapter tercih edilmelidir:
- Vector VisualDocument, renderer tarafında geçici/cached Surface'e çevrilir.
- Main AssetCatalog raster kaynağı olarak korunur.
- Main ScenePlacementCatalog axial placement sahibi olmaya devam eder.
- Lab MapContentDocument doğrudan Main package içine yazılmaz.
- World-space → axial placement dönüşümü testli ve kayıpsızlık koşulları belgelenmeden devreye alınmaz.

Bu öneri teknik tavsiyedir; A16'da kullanıcı onayı olmadan uygulanmış karar sayılmaz.

## 6. Kanıt kaynakları

Lab: MAP_JSON_SCHEMA_V1.md, RUNTIME_JSON_SCHEMA_V1.md, CONTENT_LIBRARY_JSON_SCHEMA_V1.md, MAP_CONTENT_JSON_SCHEMA_V1.md.
Main: application/hex_map_definition.py, application/content_loader.py, game_ui/assets/asset_definition.py, game_ui/assets/placement_catalog.py.
