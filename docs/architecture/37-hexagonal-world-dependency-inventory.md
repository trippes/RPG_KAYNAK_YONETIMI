# Eldoria — Altıgen Dönüşümü Dosya ve Bağımlılık Envanteri

**Durum:** Aşama 0 kaynak kod incelemesi.  
**İncelenen commit:** `5e77ef0cd70d1bc439ef2eb0bd2d5b86302ef9fc` (`demo_eldoria`)

Sınıflandırma:
- **Doğrudan değişecek:** kare hücre varsayımı altıgen geometriye taşınmalı.
- **Uyarlanacak:** arayüz/serialization koordinat türü veya valid-cell sözleşmesiyle güncellenmeli.
- **Korunacak:** mekânsal anlamı yok veya yalnızca ID/domain kuralı taşıyor.
- **Yalnızca test edilecek:** değişiklik gerekmemesi bekleniyor; regresyon kapsamına alınır.
- **İncelenmesi gerekiyor:** tam çağrı zinciri veya dolaylı referanslar sonraki aşamada yeniden doğrulanmalı.

## 1. Geometri ve dünya

| Dosya | Mevcut görev / somut bağımlılık | Altıgen kararı | Sınıf / risk |
|---|---|---|---|
| `core/domain/spatial/position.py` | Immutable float/int x/y; hypot distance; dict x/y persistence | Genel Position korunur; HexCoord ayrı tip | Korunacak / Orta |
| `core/entity/position.py` | Legacy mutable Entity adapter, canonical Position kullanır | Hex cell API'sine dönüştürülmez | Korunacak / Düşük |
| `world/map_definition.py` | MapSize width/height; tuple x/y; blocked/features/landmarks/transitions | Hex cell mask ve LocalHexPosition içeren yeni definition contract | Doğrudan / Çok yüksek |
| `world/local_map.py` | LocalMapDefinition world/location + width/height | Bounds yardımcı metadata; valid cell mask authoritative | Doğrudan / Yüksek |
| `world/map_loader.py` | JSON map discovery, bounds, reciprocal transitions, WorldMap builder | Hex schema/valid mask/yön validator; package discovery korunur | Doğrudan / Çok yüksek |
| `world/location.py` | Location.position object/tuple | WorldHexPosition ile tiplenir; UI pixel ayrı | Uyarlanacak / Yüksek |
| `world/map.py` | ID graph, symmetric/directed edges, BFS | Graph API korunur; edge yön/konum doğrulaması eklenir | Uyarlanacak / Yüksek |
| `world/movement.py` | Location graph movement view | API semantiği korunur; path result world-level olabilir | Yalnızca test / Düşük |

## 2. Application ve içerik yükleme

| Dosya | Mevcut görev / somut kullanım | Altıgen kararı | Sınıf / risk |
|---|---|---|---|
| `application/movement.py` | set_tile_position x/y bounds; Position(x,y); actor location graph | LocalHexPosition + map valid-cell check | Doğrudan / Çok yüksek |
| `application/world_object_placement.py` | x/y + width/height; dikdörtgen occupied_tiles ve overlap | Hücre kümesi/footprint listesi; hex occupancy | Doğrudan / Çok yüksek |
| `application/actor_system.py` | WorldActor.position: Position; location_id ayrı | Yerel actor cell için yeni typed alan/adapter | Uyarlanacak / Yüksek |
| `application/gameplay_service.py` | register_world_map; local map width/height; tile position API; placement | Yeni tipleri servis API'sine geçir; ekonomi/quest servislerini değiştirme | Uyarlanacak / Çok yüksek |
| `application/content_pack.py` | map/world build; NPC position tuple→Position; NPC/resource/market bounds validation; starting position | İçerik koordinat parser'ları, references ve valid-cell kontrolü | Doğrudan / Çok yüksek |
| `application/content_loader.py` | manifest files + maps directory; map loader import | Package boundary ve JSON-only yükleme korunur | Korunacak/uyarlanacak / Orta |
| `application/session_bundle.py` | movement/world_objects registry composition ve validation | Yeni placement/map registries bağlanır | Uyarlanacak / Orta |
| `application/game_application.py` | candidate restore; actor position bounds; map restore; snapshot composition | Migration ve valid-cell restore kontrolü | Doğrudan / Çok yüksek |

## 3. Persistence

| Dosya | Mevcut alan | Altıgen etkisi | Sınıf / risk |
|---|---|---|---|
| `application/actor_persistence.py` | ActorRecord.position Position; x/y dict | map_id bağlamlı axial record ve migration | Doğrudan / Çok yüksek |
| `application/extended_persistence.py` | SocialSnapshot NPC position x/y | NPC local cell typed serialization | Doğrudan / Yüksek |
| `application/container_persistence.py` | placement x/y/width/height | Occupied hex cells ve dönüşüm | Doğrudan / Çok yüksek |
| `application/migrations.py` | save v0→v1→v2; legacy NPC position backfill | Yeni envelope migration; içerik manifestine dayalı koordinat eşlemesi | Doğrudan / Çok yüksek |
| `application/save_document.py` | rpg-game-save schema v2 | Yeni schema boundary ve nested snapshot uyumu | Uyarlanacak / Çok yüksek |
| `application/lock_persistence.py` | Lock/entity ilişkisi; konum yok | Konum eklenmedikçe değişmez | Korunacak / Düşük |
| `application/production_persistence.py` | facility/job/recipe state | Konum yok; yalnızca dış referans test edilir | Yalnızca test / Düşük |
| `resources/persistence.py` | inventory/resource quantity/job state | Resource node ID korunur; cell ownership başka katmanda | Yalnızca test / Orta |
| `character/persistence.py` | Character stats/equipment | Harita koordinatı yok | Korunacak / Düşük |
| `quests/persistence.py` | quest identity/progress | Map/cell hedefi varsa hedef referansı ayrıca incelenir | İncelenmesi gerekiyor / Orta |

## 4. Pygame ve sunum

| Dosya | Mevcut görev / somut bağımlılık | Altıgen kararı | Sınıf / risk |
|---|---|---|---|
| `game_ui/screens/main_screen.py` | TILE_SIZE=16; x/y tile; dört-neighbor BFS; kare mouse division; boundary dx/dy | Altıgen renderer, cube-rounded pointer pick, 6-neighbor path | Doğrudan / Çok yüksek |
| `game_ui/renderer.py` | Renderer chrome, map drawing entry point ve UI primitives | UI chrome korunur; world map geometry adapter | Uyarlanacak / Orta |
| `game_ui/screens/map_screen.py` | Location.position ile dünya konumlarını çizme/seçme | WorldHexPosition → pixel; hit test hex polygon | Uyarlanacak / Yüksek |
| `game_ui/camera.py` | x/y world_to_screen offset | Pixel camera pan + zoom transform; domain koordinatı bilmez | Uyarlanacak / Orta |
| `game_ui/input.py` | keyboard + mouse events; left/right/up/down | Input eventleri kalır; yön tuşu altıgen seçimi tasarlanır | Uyarlanacak / Orta |
| `game_ui/scaled_renderer.py` | DPI scale wrapper | UI DPI ölçeği korunur; hex world zoom ile karıştırılmaz | Korunacak / Düşük |
| `game_ui/screens/main_screen.py` | NPC, landmark, container placement hit test ve draw | Bütün selection/occupancy aynı hex conversion servisini kullanmalı | Doğrudan / Çok yüksek |

## 5. İçerik dosyaları

| Yol | Mevcut görev | Dönüşüm |
|---|---|---|
| `content/demo_eldoria/manifest.json` | maps klasörü otomatik keşfi | Yapı korunur; gerekirse map schema version metadata eklenir |
| `content/demo_eldoria/maps/*.json` (9 dosya) | 32×32 kare map, bounds, x/y features/landmarks/exits | Dokuzunun tamamı axial valid-cell mask'e kontrollü çevrilir |
| `content/demo_eldoria/npcs.json` | 4 NPC; location_id + position [x,y] | map_id referansı ve axial cell |
| `content/demo_eldoria/resources.json` | 22 resource node; landmark/location ID bağları | ID'ler korunur; hücre map landmark'ında taşınır |
| `content/demo_eldoria/starter_content.json` | başlangıç world config, NPC/map alias ID, market position | Başlangıç world koordinatları ve market hücreleri incelenir |
| `content/demo_eldoria/quests.json` | quest giver/objective IDs | ID referansları korunur; location/cell varsa ayrı incelenir |
| `content/demo_eldoria/characters.json` | race/class definitions | Korunur |
| `content/demo_eldoria/gameplay_rules.json` | inventory/economy/consumable rules | Korunur |

## 6. Test envanteri ve kabul kapsamı

Mevcut tree'de doğrudan ilgili test dosyaları:
- `tests/test_world/test_map_definition.py`
- `tests/test_world/test_map_loader_transitions.py`
- `tests/test_world/test_demo_local_map_content.py`
- `tests/test_world/test_world.py`
- `tests/test_application/test_movement.py`
- `tests/test_application/test_world_object_placement.py`
- `tests/test_application/test_content_pack.py`
- `tests/test_application/test_content_loader.py`
- `tests/test_application/test_independent_map_content_package.py`
- `tests/test_application/test_actor_system.py`
- `tests/test_application/test_unified_save_document.py`
- `tests/test_game_ui/test_main_screen.py`
- `tests/test_game_ui/test_main_screen_map_data.py`
- `tests/test_game_ui/test_main_screen_map_transitions.py`
- `tests/test_persistence/test_restore_contract.py`, `test_contracts.py`, `test_session_state_records.py`

NPC, resource, container, quest, combat, economy ve inventory testleri değişmeden kalması beklenen alanlarda regresyon güvencesi sağlar.

## 7. Korunacak sınırlar

Aşağıdakiler mekânsal dönüşümün kapsamı değildir: `economy/`, `inventory/resources/`, recipe/production chain, canonical `core.time.Tick`, scheduler/event transport, quest kimlikleri ve graph ilerleme modeli, dialogue content, combat kuralları ve genel `Position` sınıfı. Bu modüller yalnızca bir cell API'sine doğrudan bağımlı oldukları kanıtlanırsa dar adapter alır; sırf aynı uygulama içinde oldukları için yeniden yazılmaz.

## 8. Risk ve doğrulama notu

En yüksek riskler: eski 4 yönlü BFS'nin 6 komşuya geçişinde yeni kısayollar; kare footprint'in axial occupancy'ye çevrilmesi; geçiş hücresi eşlemesinin deterministik olmaması; NPC/actor/container kayıtlarının farklı snapshot'larda bulunması; world_position piksel tuple'larının axial koordinat sanılması.

Bu Aşama 0 çalışmasında GitHub üzerinden dosya ağacı ve kaynak dosyalar incelendi. Uzak GitHub bağlantısı tek başına yerel Python testlerini çalıştırmaz; bu nedenle test suite'i bu aşama raporunda çalıştırılmış/başarılı olarak gösterilmemelidir.


## 9. İkincil modüller ve kapsam sınırı

Kod taramasında aşağıdaki paketler de incelendi. Bunlar ana dönüşümün yanında ele alınmalı; konum tutmayan modüller gereksiz yere yeniden yazılmamalıdır.

| Dosya/paket | Gerçek kullanım | Karar |
|---|---|---|
| `npc/npc.py` | NPC `location_id` ve `core.domain.spatial.Position` taşır | Position'ın NPC yerel hücresi olarak kullanıldığı için uyarlanacak |
| `npc/behavior.py` | NPC davranış/karar mantığı | Hücre komşuluğu veya konum sorgusu kullandığı doğrulanırsa uyarlanacak; aksi halde korunacak |
| `npc/faction.py`, `npc/relationship.py`, `npc/reputation.py` | Fraksiyon, ilişki ve itibar kimlik/değerleri | Korunacak |
| `resources/node.py` | Resource node world_id/location_id taşır; hücre koordinatı tutmaz | Korunacak; landmark/map referansı doğrulaması test edilecek |
| `resources/gathering.py` | Node registry world_id üzerinden filtreler | Korunacak; location/cell sorgusu eklenirse dar uyarlama |
| `resources/definition.py`, `resource.py`, `inventory.py`, `jobs.py`, `production.py`, `recipe.py`, `transfer.py` | Kaynak tanımı, stok, iş ve üretim | Korunacak; kaynak kimlikleri ve toplama akışı regresyon testinde |
| `economy/market.py`, `merchant.py` | Market/merchant location_id ve NPC bağı | Location ID korunur; market konumunda ayrıca cell bulunuyorsa content adapter incelenir |
| `economy/currency.py`, `economy/ledger.py`, `economy/exchange.py`, `economy/trade.py`, `economy/prices.py`, `economy/persistence.py` | Para, hesap, fiyat ve ticaret | Korunacak |
| `quests/quest.py`, `objective.py`, `reward.py`, `graph.py`, `condition.py`, `dialogue.py` | Quest/objective target_id ve dialogue graph | Kimlikler korunur; objective türü ileride cell hedefi alırsa ayrıca tasarlanır |
| `game_ui/renderer.py` | `world_map()` location.position'ı panel içi piksel noktası olarak çizer | WorldHexPosition→pixel adaptörü; genel UI çizim API'si korunur |
| `game_ui/screens/container_screen.py`, `inventory_screen.py`, `character_screen.py`, `production_screen.py`, `quest_log_screen.py`, `dialogue_screen.py`, `combat_screen.py` | UI panelleri; quest log rect position'ları ekran koordinatıdır | Oyun harita hücresi kullandığı kanıtlanmadıkça korunur; UI hitbox position'ları hex değildir |
| `game_ui/screens/character_creation.py`, `main_menu.py`, `opening_screen.py`, `save_slots_screen.py`, `market_screen.py`, `trade_screen.py`, `currency_exchange_screen.py` | Menü/karakter/pazar/saklama UI | Korunacak; harita entegrasyonu regresyonu |
| `core/entity/entity.py`, `entity_state.py`, `entity_manager.py`, `entity_type.py`, `entity_id.py` | Genel entity kimliği/durum/sahiplik | Korunacak; genel Position ayrı tutulur |
| `core/persistence/*`, `core/application/persistence.py`, `core/compatibility/migration.py` | Core persistence contracts ve compatibility | Core schema'yı mekânsal app migration'a zorlamadan koru; sınır testleri |
| `character/persistence.py`, `economy/persistence.py`, `quests/persistence.py`, `resources/persistence.py` | Alt domain snapshot'ları | Sadece konum alanı varsa uyarlanır; aksi halde korunur/test edilir |

### Test kapsamının genişletilmesi

İlgili regresyon klasörleri ayrıca:
- `tests/test_npc/` ve `tests/test_social/` mevcutsa NPC position/location akışları,
- `tests/test_resources/` resource node, gathering, production ve resource persistence,
- `tests/test_economy/` market location/trade ve economy persistence,
- `tests/test_quests/` objective identity/graph/persistence,
- `tests/test_character/` character actor links,
- `tests/test_containers/` placement/custody/nesting,
- `tests/test_combat/` combat state,
- `tests/test_entity/` ve `tests/test_foundation/` Position compatibility

altıgen uygulama aşamalarında çalıştırılmalıdır. Klasör veya test adı mevcut snapshot'ta bulunmuyorsa test grubu mevcutmuş gibi varsayılmamalı; gerçek tree yeniden kontrol edilmelidir.
