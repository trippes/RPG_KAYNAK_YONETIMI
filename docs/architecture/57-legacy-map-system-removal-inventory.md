# 57 — Legacy Map System Removal Inventory

**Branch:** `experiment/map-cleanup`  
**Purpose:** Remove the pre-laboratory square-map and demo-Hex gameplay systems before integrating the laboratory Hex architecture.  
**Status:** Historical baseline plus completed cleanup record. Sections 2–5 describe the pre-cleanup inventory and are not the current repository state. The current result is recorded in the final section below.

## 1. Target state

The cleanup branch must not retain the old square-map gameplay model or the old seven-map Hex demo content/runtime wiring. The laboratory Hex implementation is the source for the replacement architecture and remains untouched on its archive branch until it is deliberately integrated.

The target is not to preserve the nine square maps as fallback gameplay. They are legacy content and are scheduled for removal with their code dependencies. No square `(x, y)` coordinate is to be converted into an axial coordinate. Existing saves must not be silently reinterpreted as Hex positions.

## 2. Confirmed legacy content inventory

The package currently contains 16 map JSON files:

- Nine schema-v1 square maps: `village`, `forest`, `south_forest`, `west_forest`, `east_forest`, `north_mine`, `south_mine`, `west_mine`, `east_mine`.
- Seven schema-v2 Hex demo maps: `hex_forest_demo`, `hex_clearing_demo`, `hex_northeast_demo`, `hex_northwest_demo`, `hex_west_demo`, `hex_southwest_demo`, `hex_southeast_demo`.

The package also contains:

- `world.json`, a world graph/placement file for the seven demo Hex maps.
- `placements/hex_forest_demo.json` and `placements/hex_clearing_demo.json`, environmental scene placements.
- `presentation_assets.json`, which contains six reusable asset definitions and fourteen map-specific object placements.
- `asset_catalog.json`, the split six-asset catalog.

These map-specific records are not the future NPC/resource/market axial placement model. The six reusable asset definitions are separable from map placements and may be retained only if the new architecture still consumes the same asset contract.

## 3. Confirmed legacy runtime dependencies

### Content loading and startup

- `application/content_loader.py` discovers schema-v1 and schema-v2 map files in one directory and optionally loads the legacy world-map graph and scene placements.
- `application/content_pack.py` loads `package.map_definitions`, validates NPC/resource/market positions against square-map dimensions and landmarks, builds a `WorldMap`, creates `LocalMapDefinition` records, and places the player using a square starting position.
- `content/demo_eldoria/manifest.json` declares `maps`, `world_map`, `asset_catalog`, and `map_placements`.
- `pyproject.toml` explicitly packages `world.json`, map JSON files, and placement JSON files.

### Gameplay and UI

- `world/map_definition.py`, `world/map_loader.py`, `world/local_map.py`, `world/location.py`, and `world/map.py` implement the legacy rectangular-map schema, local dimensions, location graph, and graph traversal.
- `world/map_catalog.py` is a legacy square-map catalog adapter. It is still imported by branch-specific tests/runtime paths and must remain until those consumers are migrated; default-branch code search alone is not sufficient evidence that a file is unused.
- `application/movement.py` plans movement over `WorldMap` location IDs and stores legacy square positions through the compatibility boundary.
- `game_ui/screens/main_screen.py` renders the square tile grid, reads square-map landmarks/features, and owns four-direction movement/interaction behavior.
- `game_ui/screens/map_screen.py` renders the legacy location graph.
- `game_ui/hex_world_view.py` currently loads the seven demo Hex maps as a separate portal/demo surface. This is not yet the laboratory system integrated as the normal gameplay world.

### Gameplay content

- Four NPC records use square `location_id` and `position: [x, y]` fields.
- Twenty-two resource nodes refer to square map IDs and square-map landmark IDs.
- The starter market `village_inn` is attached to `village_id`, NPC `innkeeper_mira`, and square position `[20, 23]`.
- Quest definitions refer to resource-node and NPC IDs. Those domain references should remain stable where possible; only their map placement dependencies should be replaced.

### Persistence and compatibility

- Save restoration currently rebuilds package world maps and local map dimensions, checks saved actor locations against the active square map catalog, and validates saved `(x, y)` bounds.
- Actor persistence still carries legacy location and square position data through a compatibility boundary.
- No implicit square-to-axial migration is permitted. Legacy saves must be preserved and either explicitly supported through a versioned migration or clearly rejected with a recoverable message.

## 4. Explicit preservation boundary

Do not remove generic world simulation/time infrastructure merely because its path contains `world`:

- `core/world/World`, `WorldManager`, world membership, clock, scheduler, and event lifecycle are not the square-map subsystem.
- Generic resource, NPC, quest, economy, inventory, container, and save-domain behavior must remain.
- Hex geometry, axial coordinate value objects, Hex runtime/occupancy/movement contracts, renderer primitives, and their tests are not legacy square-map code.
- The laboratory archive branch is immutable during this cleanup.

## 5. Removal sequence

1. **Dependency boundary:** isolate square-map location/position assumptions in startup, gameplay services, UI, content validation, and save restore.
2. **Old demo-content removal:** remove all nine square maps, all seven demo Hex maps, `world.json`, and all map-specific scene placements/references. Retain only reusable non-map assets where the new system still needs them.
3. **Legacy runtime removal:** remove the square map schema/loader/catalog, local-map dimension model, legacy location-graph movement, square renderer and map screen, and obsolete compatibility code after all consumers are migrated.
4. **Gameplay placement contract:** replace NPC/resource/market/container placement assumptions with the laboratory Hex content model; preserve stable domain IDs and quest links.
5. **Persistence contract:** make Hex runtime spatial state authoritative and define explicit legacy-save behavior. Never reinterpret square coordinates as axial coordinates.
6. **Laboratory integration:** bring the approved laboratory implementation into this branch without merging or modifying the archive branch.
7. **Verification:** Pytest, Ruff, compile/package verification, and Linux/Windows GitHub Actions. No visual/manual test is required for this cleanup.

Each slice must have targeted regression tests. The cleanup branch must not be merged into `demo_eldoria` until the user explicitly approves.

## 6. Acceptance conditions

- No schema-v1 square map JSON or square-map runtime remains in normal gameplay.
- No seven-map Hex demo catalog or portal-only demo wiring remains.
- NPC/resource/market/gameplay placement is owned by the integrated Hex model, not by square `location_id`/`(x, y)` records.
- Hex runtime position and occupancy are authoritative; no duplicate live square position is used.
- Save behavior is explicit and tested; no silent coordinate conversion.
- Core world simulation, gameplay domain systems, and the laboratory Hex architecture remain intact.
- Pytest, Ruff, wheel/package verification, and Linux/Windows CI pass.

## 7. Kullanıcı kararı eki — demo gameplay içerikleri taşınmayacak

2026-11-19 tarihinde kullanıcı, mevcut NPC ve kaynak düğümü içeriklerinin yeni haritaya taşınması yerine tamamen kaldırılmasını ve yeni Hex sistem entegrasyonundan sonra sıfırdan oluşturulmasını kararlaştırdı.

Bu nedenle:
- Dört mevcut NPC kaydı ve yirmi iki mevcut resource-node kaydı kaldırılacak; axial konuma dönüştürülmeyecek ve ID/konum eşlemesi korunmaya çalışılmayacak.
- Bu NPC/resource kayıtlarına bağlı eski quest tanımları, NPC diyalog içerikleri, NPC'ye bağlı starter market ve eski demo yerleşimleri de kaldırılacak.
- Bu kayıtları yükleyen/harita üzerinde doğrulayan demo content loader ve starter-content bağlantıları temizlenecek.
- NPC, resource node, gathering, dialogue, quest, market/economy, inventory ve save sistemlerinin genel domain/runtime kodu korunacak. Yalnızca eski demo içerik kayıtları silinecek.
- Yeni NPC, kaynak, quest, diyalog ve pazar kayıtları yeni Hex mimarisi entegre edildikten sonra yeni dünya tasarımına göre sıfırdan yazılacak.

### Bağlayıcı sıra

Önce eski kare harita ve eski yedi haritalı Hex demo/portal sistemi ile bunlara bağlı demo gameplay içerikleri kaldırılır. Bu temizlik tamamlanıp otomatik teknik doğrulamadan geçtikten sonra laboratuvar Hex mimarisi entegre edilir. Önceki sürümlerdeki “NPC/resource ID'lerini koruyarak axial yerleşime taşı” yönündeki ifadeler bu kullanıcı kararıyla geçersizdir. Hiçbir kare koordinat axial koordinata dönüştürülmez.

## Gerçekleşen kaldırma sonucu — 2026-11-19

Bu bölüm önceki envanterdeki hedeflerin gerçek branch durumuyla güncellenmiş halidir.

**Kaldırıldı:**
- Dokuz schema-v1 kare harita JSON'u ve eski kare map catalog/schema/loader.
- Yedi eski demo Hex map JSON'u ve eski demo world arrangement data.
- Eski kare WorldMap graph, MovementManager, square local-map model ve world-object placement registry.
- Eski Hex demo view/portal ve square map screen/HUD graph renderer.
- Dört NPC, 22 resource node, eski quest örnekleri, NPC dialogue, NPC-bound starter market ve eski scene placement kayıtları.
- Actor, NPC ve resource runtime'ındaki kare konum sahipliği.
- Eski kare konumlarıyla çalışan test/fixture ve package bağımlılıkları.

**Korundu:**
- NPC identity/behavior/social runtime, resource node regeneration/gathering, quest/dialogue, economy/market, inventory, container contents/nesting, save/load altyapısı.
- Hex map/world definition, HexWorldRuntime, occupancy, movement rules, pathfinding ve session runtime owner temelleri. Bunlar eski demo portalı değildir; sonraki entegrasyonun hedefidir.
- Reusable asset catalog ve genel presentation/scene-placement loader sözleşmeleri; demo placement kayıtları boşaltılmıştır.

**Save/load kararı:** Eski actor/NPC/resource kare spatial kayıtları ve container placement listeleri decoder seviyesinde tespit edilir ve yükleme reddedilir. Koordinat dönüşümü veya sessiz relocation yoktur.

**Teknik kabul:** HEAD 3790463394b1f47c81655169554e30202de66724; run [#44492476381](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44492476381) Linux/Windows başarılı; 1.341 test + 235 subtest; Ruff, compileall, wheel build, isolated install ve release verification başarılı.
