# Aşama 16 — NPC ve Resource Node Spatial Binding

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **NPC VE RESOURCE NODE SPATIAL ADAPTER'LARI TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilimler:
- [Geometry ve World Identity Bridge](60-phase-16-geometry-world-identity-bridge.md)
- [Actor Identity ve Movement Ownership Bridge](61-phase-16-actor-identity-movement-ownership-bridge.md)
- [Physics ve Spatial Query Bridge](62-phase-16-physics-spatial-query-bridge.md)

## 1. Amaç

NPC ve kaynak düğümlerini açık axial yerleşim verisi üzerinden ana HexWorldRuntime'a bağlamak. Bu dilim yeni NPC, kaynak, harita, landmark veya koordinat üretmez. Yalnızca daha sonra içerik tarafından sağlanacak `EntityPosition(map_id, LocalHexPosition(q,r))` değerlerini mevcut runtime sahiplik modeline kaydeden uygulama adaptörlerini sağlar.

## 2. NPC spatial binding

Yeni `application/npc_hex_binding.py` / `NPCSpatialBindingService`:

- NPC sosyal ve davranış kaydı `SocialRuntime.npcs` / `NPCRegistry` içinde kalır.
- Genel dünya aktör kimliği `WorldActorRegistry` içinde kalır.
- NPC kimliği ile actor kimliği aynı kararlı ID string'ini kullanır; yeni bir actor/entity ID üretilmez.
- Map-local konum ve occupancy yalnızca `HexWorldRuntime` tarafından tutulur.
- NPC'nin spatial kaydı yapılmadan önce aynı ID'ye sahip bir world actor kaydının bulunması zorunludur. Adapter gizlice actor oluşturmaz; böylece başarısız spatial registration sonrasında yarım kimlik kaydı bırakılmaz.
- NPC'nin kendi `active` durumu ve genel actor'ın `active` durumu ayrı hareket izin kapılarıdır. Hex runtime movement-enabled bayrağı da bunlardan ayrıdır.
- Doğrudan hücre hareketi ve önceki Physics Bridge üzerinden physics-aware hareket sunulur.
- Spatial kayıt kaldırıldığında NPC ve actor domain kayıtları korunur.

`GameplayService.npc_hex_binding`, aktif SessionBundle, SocialRuntime ve aktif world-scoped actor binding üzerinden çözülür; yeni state owner oluşturmaz.

## 3. Resource node spatial binding

Yeni `application/resource_node_hex_binding.py` / `ResourceNodeHexBindingService`:

- Kaynak düğümünün kimliği, world scope'u, miktarı, kapasitesi ve yenilenmesi `WorldResourceNodeManager` / `WorldResourceNode` içinde kalır.
- Resource node ID, HexWorldRuntime spatial entity ID olarak aynen kullanılır.
- Her kaynak düğümü sabit `object` spatial kaydı ve `MovementProfile(can_move=False)` ile temsil edilir.
- Gameplay resource node kaydı varsayılan olarak actor hareketini veya occupancy'yi engellemez. Ağaç/kaya gibi fiziksel engeller, kaynak miktarından bağımsız olarak physics collision geometry içinde tanımlanır.
- Adapter, node'un world_id değerini aktif runtime dünyasıyla karşılaştırır.
- Map maskesi dışındaki konumlar runtime tarafından reddedilir.
- Spatial kayıt kaldırıldığında kaynak miktarı ve son işlenmiş simulation tick'i değişmez.

`GameplayService.resource_node_hex_binding`, aktif world ve mevcut SessionBundle runtime'ı üzerinden çözülür.

## 4. Sahiplik matrisi

| Veri / davranış | Tek otorite |
|---|---|
| NPC sosyal kimliği, faction ve davranış durumu | `NPCRegistry` / `SocialRuntime` |
| Genel actor kimliği, world scope ve actor active durumu | `WorldActorRegistry` |
| Resource node kimliği, world scope, quantity ve regeneration | `WorldResourceNodeManager` |
| NPC ve resource node map-local konumu | `HexWorldRuntime` / `HexOccupancyRegistry` |
| NPC hareket izni | NPC active + actor active + runtime movement-enabled |
| Statik fiziksel engeller | `HexPhysicsSnapshot` |

NPC veya resource node domain modellerine ikinci bir axial position alanı eklenmedi. Placement adaptörleri açık konum parametresi alır; aynı konumu domain modeline kopyalamaz.

## 5. Test kapsamı

### NPC

- NPC kaydı ve world actor kimliği aynı ID ile spatial runtime'a bağlanır.
- Actor kaydı yoksa spatial registration reddedilir; otomatik actor yaratılmaz.
- Bilinmeyen NPC reddedilir.
- Inactive NPC spatial registration veya hareket yapamaz.
- NPC hareketi mevcut HexWorldRuntime ve occupancy kaydını kullanır.
- Spatial unregister NPC ve actor domain kayıtlarını silmez.
- Aktif world ile runtime world uyuşmazsa binding reddedilir.

### Resource node

- Resource node sabit, hareket etmeyen ve non-blocking spatial object olarak kaydedilir.
- Aynı hücrede actor occupancy'si resource node nedeniyle engellenmez.
- Bilinmeyen node ve başka world'e ait node reddedilir.
- Map maskesi dışındaki konum reddedilir ve yarım spatial kayıt oluşmaz.
- Spatial unregister node identity, quantity ve regeneration tick'ini korur.
- Runtime yoksa veya başka world'e bağlıysa GameplayService kontrollü hata verir.

### Physics snapshot

- Snapshot immutable davranışı ayrıca test edilir.
- Actor physics movement testleri başarısız harekette occupancy/position değişmediğini doğrular.

## 6. Bilinçli olarak kapsam dışında kalanlar

- NPC/resource için yeni içerik veya axial koordinat belirlemek.
- NPC patrol, autonomous AI, follow/wait companion commands, flee policy veya tick scheduling.
- Kaynak toplama etkileşim mesafesi/menzil kuralı. Mevcut gameplay gathering kuralları bu adapter tarafından değiştirilmez.
- Resource node görsel asset/placement kataloğu.
- Market, container, quest, dialogue ve save/load konum entegrasyonu.
- Ana oyun renderer ve UI'nin HexWorldRuntime'a geçirilmesi.
- Eski kare harita veya kare save verisinin dönüştürülmesi.

NPC actor kaydı ile NPC sosyal kaydı içerik yükleme/registration composition katmanında aynı ID üzerinden birlikte kurulmalıdır. Resource node placement ise ileride ayrı bir axial gameplay placement kataloğundan sağlanmalıdır. Bu rapor hiçbir yerleşim koordinatı tanımlamaz.

## 7. Doğrulama

- Nihai doğrulanan kod commit'i: `d2fa24f137285a45c3ec7462fd9856829637149c`
- GitHub Actions: [#44515432773](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44515432773)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.186 test + 235 subtest başarılı**.
- Her iki platformda release-candidate verification başarılı.
- Linux Ruff: yeni geometry, actor, physics, NPC ve resource-node bridge dosyaları ile ilgili test dosyaları dahil başarılı.
- Legacy map cleanup boundary kontrolü başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 8. Sonraki teknik kapı

Sıradaki iş, **market ve container spatial ownership** denetimidir. Özellikle market konumunun NPC placement ile nasıl ilişkileneceği ve container'ın dünya üzerinde bulunması ile bir actor inventory'sinde/başka container içinde tutulması arasındaki ayrım incelenecektir. Bir container yalnızca açıkça world-placed ise HexWorldRuntime'a kaydedilmelidir; elde taşınan veya iç içe bulunan container'a ikinci bir dünya konumu atanmayacaktır.

Bundan sonra axial gameplay placement katalog şeması, NPC/resource/market/container referans doğrulaması ve içerik paketine bağlanması ayrı bir kapı olarak ele alınacaktır. Kullanıcı tarafından onaylanmamış hiçbir axial koordinat yazılmayacaktır.
