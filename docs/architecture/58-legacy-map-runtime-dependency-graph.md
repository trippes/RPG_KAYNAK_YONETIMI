# Legacy Map Runtime Dependency Graph

**Branch:** `experiment/map-cleanup`  
**Audit base:** `2aac5035d58a8dc15ec90f04e3b6959d6f353791`  
**Status:** Historical dependency baseline followed by the completed cleanup state in section 8. Sections 2–7 describe the pre-cleanup architecture and must not be read as current dependencies.

## 1. Cleanup objective

The cleanup branch must remove the previous square-map gameplay system and the previous seven-map Hex demo/portal system. The laboratory Hex architecture is an archive and must remain untouched. Only after the legacy map runtime and its content wiring have been removed will the laboratory architecture be integrated.

The eventual square-map Easter egg is a separate, deliberately authored exception. It must not keep the old square-map network, old square movement, or old square-map runtime alive. Its `(x, y)` coordinates remain a separate coordinate domain; no square-to-axial conversion is permitted.

## 2. Two different legacy map paths

### 2.1 Square-map path — currently authoritative gameplay

The current opening session is still created from the nine schema-v1 square maps.

Dependency chain:

1. `content/demo_eldoria/manifest.json` points to `maps/`.
2. `application/content_loader.py` calls `world.map_catalog.load_map_catalog()` to load square definitions, while also loading schema-v2 Hex definitions.
3. `application/content_pack.py` validates NPC, resource, market, trade-partner, and starting-position references against the square map definitions.
4. `application/content_pack.py::_register_opening_content` builds a legacy `WorldMap`, registers `LocalMapDefinition` objects, and places the player on the map declaring `starting_position`.
5. `application/movement.py` registers and traverses the legacy `WorldMap` graph and updates the actor's legacy spatial state.
6. `game_ui/screens/main_screen.py` renders the square tile map, resolves NPC/resource positions, moves the player on square tiles, and follows square-map transitions.
7. `game_ui/screens/map_screen.py` displays the legacy location graph.
8. Save/restore and actor compatibility code still expose legacy `location_id` and `(x, y)` state.

Nine current square map files:

- `village.json`
- `forest.json`
- `south_forest.json`
- `west_forest.json`
- `east_forest.json`
- `north_mine.json`
- `south_mine.json`
- `west_mine.json`
- `east_mine.json`

These files are not safe to delete while the current opening-content builder and gameplay screens still depend on them.

### 2.2 Hex demo path — separate H-key development portal

The seven schema-v2 Hex maps are not yet the authoritative gameplay world. They are loaded by `application/content_loader.py` and presented through `game_ui/hex_world_view.py`, which is entered/exited through the H-key bridge in the main screen.

The demo Hex content consists of:

- `hex_forest_demo.json`
- `hex_clearing_demo.json`
- `hex_northeast_demo.json`
- `hex_northwest_demo.json`
- `hex_west_demo.json`
- `hex_southwest_demo.json`
- `hex_southeast_demo.json`
- `world.json`, which arranges those seven map IDs.
- Two scene-placement files under `placements/`.
- A split `asset_catalog.json` and a legacy combined `presentation_assets.json`.

This is demo content and temporary UI wiring, not the laboratory architecture itself. The seven demo maps, their world arrangement, their map-specific placements, and the H-key portal must not be mistaken for the lab branch's canonical Hex implementation.

The generic Hex geometry, runtime, occupancy, movement, camera, terrain, and rendering components must be reviewed individually. They are not to be deleted merely because the demo portal currently uses them; many are intended foundations for the later lab integration.

## 3. Gameplay content dependencies that must be resolved before square-map deletion

The map dependency is not limited to map JSON files.

| Content | Current spatial dependency | Stable gameplay identity to preserve |
|---|---|---|
| 4 NPC records | All use `village_id` and square `[x, y]` positions | NPC IDs, roles, dialogue IDs, faction links |
| 22 resource nodes | Use square forest/mine map IDs and square landmark IDs | Resource node IDs, resource types, quantities, regeneration/gathering rules |
| Starter market | `village_id`, `innkeeper_mira`, square `[20, 23]` | Market, merchant, inventory, product and NPC IDs |
| Quests | Refer to NPC and resource IDs, not directly to map coordinates | Quest IDs, objective IDs, target IDs, rewards |
| Player start | One square map's `starting_position` | Player/hero identity and character data |

The current seven-map Hex demo does not contain equivalent gameplay placements:

- No Hex village/start-area content is authored.
- No NPC has an axial gameplay placement.
- The 22 resource nodes do not have axial placements.
- The demo Hex landmark `demo_ore_vein` does not match the existing resource-node IDs.
- The two Hex placement files contain environmental scene objects, not NPC/resource/market gameplay placements.

Therefore, deleting the square maps before deciding how gameplay placements are represented would either break content validation or silently discard gameplay content. No automatic conversion from square coordinates to axial coordinates is allowed.

## 4. Files and consumers requiring coordinated migration

| Area | Current files / consumers | Required cleanup outcome |
|---|---|---|
| Package loader | `application/content_loader.py`, `world/map_catalog.py` | Stop requiring the legacy square catalog; keep generic package loading and later Hex content loading |
| Opening content | `application/content_pack.py` | Remove square-map validation/building and establish the new world-content registration boundary |
| Movement | `application/movement.py` | Remove legacy graph/path traversal from active gameplay after all consumers migrate |
| Gameplay UI | `game_ui/screens/main_screen.py`, `game_ui/screens/map_screen.py` | Remove square grid, square transitions, and legacy world-map screen |
| Actor/save compatibility | actor spatial compatibility API and save/restore validators | Remove square spatial authority only after explicit save-version policy is in place |
| Hex demo portal | `game_ui/hex_world_view.py` and H-key entry/exit | Remove demo-specific portal and hard-coded demo map IDs; preserve reusable Hex components |
| Demo data | `content/demo_eldoria/maps/`, `world.json`, `placements/`, manifest fields | Remove old square and demo Hex map data only after code and tests no longer require them |
| Package build | `pyproject.toml` | Remove package-data declarations for deleted map/world/placement files |
| Release verification | `scripts/verify_release.py` | Replace hard-coded 9-square/7-Hex demo assertions with the new content contract |
| Tests | content-loader, demo-map, mixed-map, Hex portal and save tests | Replace demo-specific fixtures; retain generic Hex geometry/runtime and domain regression coverage |

## 5. Branch-specific verification evidence

The recursive Git tree for this audit was retrieved from the current cleanup-branch commit and was not truncated. Source inspection was performed against `experiment/map-cleanup`, not the repository default branch.

A previous attempted deletion of `world/map_catalog.py` demonstrated that branch-specific tests and runtime paths still import it. The module was restored exactly. The restore commit and the subsequent documentation commit both passed the GitHub Actions Core Quality workflow on Linux and Windows. Consequently, `world/map_catalog.py` remains in place until its real consumers have been migrated.

## 6. Safe implementation order

1. **Freeze the target content contract.** Define how the player start, NPCs, resource nodes, markets, containers and environmental placements are represented in the future Hex content model. Preserve stable domain IDs. Do not invent coordinates and do not convert square coordinates.
2. **Separate content identity from spatial placement.** Ensure NPC, resource, quest, market and inventory domain records can exist independently of legacy square map IDs and `(x, y)` positions.
3. **Migrate gameplay registration and validation.** Replace square-map assumptions in `application/content_pack.py` and the relevant service boundary. Add tests for missing/invalid axial placements and stable cross-domain references.
4. **Migrate active gameplay UI and movement.** Remove square-grid movement, square map transitions and the legacy world-map screen only after the replacement runtime boundary is ready.
5. **Define save compatibility explicitly.** Version or reject old square-map saves with a clear message. Never infer axial coordinates from old `(x, y)` data.
6. **Remove the temporary Hex demo path.** Remove the seven demo map IDs, demo world arrangement, map-specific placements, H-key portal and demo-only tests. Keep reusable Hex runtime/rendering components needed for later integration.
7. **Delete legacy data and packaging references.** Remove the nine square maps, the seven old demo Hex maps, obsolete world/placement files and their `pyproject.toml` entries once no code/test refers to them.
8. **Remove legacy modules last.** Delete `world/map_catalog.py`, square map loaders/models, `WorldMap` graph movement and remaining actor/save compatibility only after branch-specific reference scans and CI prove there are no consumers.
9. **Run the complete technical gate.** Pytest, Ruff, compileall, wheel build/isolated install, release smoke, and Linux/Windows GitHub Actions. Visual testing is not part of this cleanup gate.

## 7. Non-goals and preservation rules

- Do not modify `experiment/hex-world-laboratory`.
- Do not integrate the lab system into the main game during legacy removal.
- Do not preserve the nine-map square network as normal gameplay.
- Do not build a square multi-map editor or square procedural map generator.
- Do not convert square coordinates to axial coordinates.
- Do not delete generic world simulation, NPC, resource, quest, economy, inventory, clock or scheduler systems as collateral cleanup.
- Do not remove reusable Hex runtime/rendering foundations solely because the temporary demo portal is being removed.
- The eventual single square Easter egg is a later, isolated design task and must not retain the old square gameplay architecture.

## 8. Kullanıcı kararı eki — NPC/resource ve bağlı demo içeriği sıfırlanacak

Kullanıcı, mevcut dört NPC kaydının ve yirmi iki kaynak düğümü kaydının yeni Hex sisteme taşınmamasını; eski içerik olarak silinmesini ve yeni Hex mimarisi entegre edildikten sonra sıfırdan oluşturulmasını kararlaştırdı.

Bu kararın içerik kapsamı:
- Eski dört NPC tanımı ve kare konumları.
- Eski yirmi iki kaynak düğümü tanımı ve kare map/landmark referansları.
- Bu kayıtlara bağlı eski quest örnekleri, NPC diyalog tanımları ve NPC'ye bağlı starter market.
- Bunları kullanan demo başlangıç içeriği, content validation ve test fixture'ları.

Bu karar genel oyun mekaniklerini silmez. NPC ve resource domain modelleri, kaynak toplama servisleri, diyalog/quest altyapısı, market/economy, inventory, persistence ve bunların genel testleri korunacaktır. Eski demo verileri kaldırılır; yeni içerik yeni Hex dünya tasarımına göre daha sonra sıfırdan hazırlanır.

Bu ek, önceki “NPC/resource kimliklerini koruyarak axial yerleşime taşı” yaklaşımını geçersiz kılar. Ayrıca uygulama sırası kesin olarak: legacy square + legacy Hex demo ve bağlı demo içeriklerini temizle → otomatik teknik kabul → laboratuvar Hex mimarisini entegre et → yeni gameplay içeriklerini sıfırdan yaz. Tek kare easter egg daha sonraki bağımsız tasarım kararıdır; eski kare map altyapısının korunmasını gerektirmez.

## Cleanup sonrası bağımlılık durumu — 2026-11-19

Önceki dependency graph, planlanan geçişi tarif ediyordu. Gerçek cleanup sonucu:

**Kaldırılan kare/legacy düğümler:**
- Square map catalog/schema/loader ve dokuz kare map verisi.
- WorldMap location graph ve MovementManager.
- LocalMapDefinition, WorldObjectPlacementRegistry ve kare tile placement API'leri.
- Actor legacy spatial store ve ActorView location/position projection.
- NPC location_id/square Position alanları.
- ResourceNode location_id alanı.
- Kare map HUD/world-map renderer ve eski Hex demo portal/view.

**Bağımsız tutulan domain düğümleri:**
- NPC registry/behavior/social services.
- Resource node regeneration, gathering ve inventory transfer.
- Quest/dialogue, market/economy, container definitions/content/nesting.
- Persistence decoder ve save/load boundary.

**Gelecek Hex entegrasyon düğümleri (korunuyor, henüz ana gameplay akışına bağlanmadı):**
- HexMapDefinition, WorldMapDefinition, HexWorldRuntime.
- Occupancy, movement rules, pathfinding ve session-scoped runtime ownership.
- Reusable asset/presentation loader sözleşmeleri.

**Save rejection boundary:** ActorSnapshot eski actor spatial alanlarını, SocialSnapshot eski NPC spatial alanlarını, GameplaySnapshot eski resource-node location alanını, ContainerSnapshot eski placement listesini tanır. GameApplication bu verileri kare→axial dönüştürmeden reddeder.

Cleanup HEAD 3790463394b1f47c81655169554e30202de66724; run [#44492476381](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44492476381) Linux/Windows başarılı; 1.341 test + 235 subtest, Ruff, compileall, wheel ve isolated install başarılı.
