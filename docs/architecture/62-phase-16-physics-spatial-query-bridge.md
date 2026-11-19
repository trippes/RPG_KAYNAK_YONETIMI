# Aşama 16 — Physics ve Spatial Query Bridge

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **STATİK FİZİK PROJEKSİYONU VE HÜCRE HAREKETİ ÖN DENETİMİ TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilim: [Actor Identity ve Movement Ownership Bridge](61-phase-16-actor-identity-movement-ownership-bridge.md)

## 1. Amaç

Laboratuvarın statik çarpışma geometrisi, sürekli çarpışma çözücüsü ve obstacle spatial index bileşenlerini Eldoria'nın canonical `HexMapDefinition` verisiyle kullanmak. Fizik katmanı yalnızca hareket isteğini önceden değerlendirir; actor kimliği, mantıksal konumu ve occupancy sahipliğini devralmaz.

Bu dilim, laboratuvar `EntityRegistry`, `MovementSystem` veya `SimulationTickCoordinator` sınıflarını ana gameplay hareket sahibi yapmaz.

## 2. Sahiplik ve veri akışı

| Sorumluluk | Otorite | Physics bridge davranışı |
|---|---|---|
| Actor kimliği ve gameplay durumu | `WorldActorRegistry` | Değiştirmez |
| Map-local axial konum ve occupancy | `HexWorldRuntime` / `HexOccupancyRegistry` | Yalnızca başarılı doğrulamadan sonra mevcut runtime hareketini çağırır |
| Harita hücre maskesi ve terrain/blocked verisi | Eldoria `HexMapDefinition` | Statik collision snapshot'ına kaynak olur |
| Dünya kapsamı | canonical `core.foundation.WorldId` | Snapshot ve actor binding'de eşleşme zorunlu |
| Statik fizik geometrisi | `HexPhysicsSnapshot` | Haritadan türetilmiş, salt okunur snapshot |
| Çarpışma sorgusu | Hex World physics resolver | Yan etkisiz swept-circle sorgusu |

Akış:

1. Eldoria haritası, açık `WorldId` ve pointy-top `HexLayout` ile physics snapshot'a projekte edilir.
2. Hücre engelleri, yürünemez landmark'lar ve seçilen harita sınırı politikası collision geometry'ye aktarılır.
3. Hareket isteği önce `HexWorldRuntime.validate_move_to` ile logical rules ve occupancy bakımından denetlenir.
4. Ardından fizik snapshot'ı, oyuncu gövdesinin iki hücre merkezi arasındaki hareketini değerlendirir.
5. İki denetim de başarılıysa konum ve occupancy değişikliğini yalnızca mevcut `HexWorldRuntime.move_to` uygular.

## 3. Uygulanan kod

### `application/hex_physics_bridge.py`

Yeni `HexPhysicsSnapshot` ve `build_hex_physics_snapshot`:

- Canonical Eldoria haritasını geçici bir Hex World map aggregate'ine projekte eder.
- Geçici aggregate yalnızca statik collision geometry üretmek için kullanılır; snapshot içinde ikinci map registry veya runtime sahibi tutulmaz.
- Eldoria `WorldId` ve map ID değerlerini snapshot'ta korur.
- Başka world veya map'e ait snapshot'ın gameplay movement'te kullanılmasını engeller.
- `cell.blocked` ve `walkable=False` landmark'larını fiziksel obstacle olarak projekte eder.
- `BoundaryPolicy.BLOCKED` ve `BoundaryPolicy.OPEN` seçeneklerini destekler.
- Harita maskesi dışındaki source/target hücreleri reddeder.
- Circle body ile center-to-center cell-step swept collision sorgusu yapar.
- Obstacle sorgularında özel `ObstacleSpatialIndex` kullanır.
- Body kapalıysa çarpışma engellerini devre dışı bırakır; actor konumu veya occupancy yine değiştirilmez.

### `application/hex_actor_binding.py`

- `move_to_with_physics`: logical/occupancy ön denetiminden sonra physics denetimi yapar; yalnızca iki denetim başarılıysa runtime hareketini commit eder.
- `move_with_physics`: yön tabanlı bir hücre adımını aynı ön denetim ve commit yoluna bağlar.
- Fizik çarpışması `MovementFailureReason.PHYSICAL_COLLISION` ile raporlanır.
- Physics reddinde actor, occupancy ve logical position kayıtları değişmeden kalır.

## 4. Bilinçli sınırlar

- İlk entegrasyon yalnızca circle collider ile center-to-center altıgen hücre hareketini kapsar. Polygon actor body ve serbest sürekli actor konumu bu dilimin kapsamında değildir.
- BodyDefinition çağıran gameplay katmanından sağlanır. Henüz actor metadata'sına ikinci bir body registry eklenmemiştir.
- Bu snapshot statik obstacle verisini temsil eder. Dinamik actor çarpışmaları ve doluluk çakışmaları için tek otorite `HexWorldRuntime` olmaya devam eder.
- Physics resolver hareketi değerlendirir; render/interpolasyon konumu veya simulation tick'i yönetmez.
- Harita/layout yeniden üretildiğinde statik snapshot yeniden oluşturulmalıdır; bu dilim canlı map-edit invalidation sistemi eklemez.
- Eski kare harita, save verisi veya koordinatları bu köprüye aktarılmaz.

## 5. Test kapsamı

`tests/test_application/test_hex_physics_bridge.py` aşağıdakileri doğrular:

1. Engelli hücre ve yürünemez landmark projeksiyonu.
2. Açık/kapalı map boundary politikası.
3. Harita maskesi dışındaki source/target sorgularının reddi.
4. Açık bir hücre geçişinin fiziksel olarak erişilebilir olması.
5. Statik obstacle'ın hücre geçişini engellemesi.
6. Physics çarpışmasında actor ve occupancy konumunun değişmemesi.
7. Başarılı hareketin mevcut HexWorldRuntime occupancy kaydı üzerinden commit edilmesi.
8. Yanlış map snapshot'ının reddi.
9. Yanlış world snapshot'ının reddi.
10. Yön tabanlı hareketin aynı fizik denetiminden geçmesi.
11. Snapshot geometry ile map kimliği uyuşmazlığının reddi.

## 6. CI doğrulaması

- Nihai commit: `7151457b61b4525503c56dc24684950de8d537df`
- GitHub Actions: [#44514155780](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44514155780)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.170 test + 235 subtest başarılı**.
- Her iki platformda release-candidate verification başarılı.
- Ruff ve legacy cleanup boundary kontrolleri başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir ve bu dilimde değiştirilmemiştir.

Ara doğrulama notu: İlk ara commit'te snapshot constructor imzası değişirken doğrudan constructor kullanan bir test güncellenmemişti. İlk CI bu tek testi yakaladı; test yeni world-scoped imzaya uyarlandı. Nihai commit için yukarıdaki Linux/Windows run tamamen başarılıdır.

## 7. Sonraki teknik kapı

Physics bridge artık hücre hareketi için güvenli bir ön denetim sunuyor; fakat bu henüz tüm oyun varlıklarının ana Hex gameplay'e taşındığı anlamına gelmez.

Sıradaki iş, NPC ve diğer gameplay varlıklarının axial yerleşim sözleşmesini mevcut domain sahipliğine göre incelemek ve bir placement/registration adaptörü tasarlamaktır. Kullanıcı tarafından yeni axial koordinatlar verilmeden NPC, kaynak, pazar veya konteyner konumu oluşturulmayacaktır. NPC AI, otomatik takip, pathfinding veya yeni tick owner bu aşamada eklenmeyecektir.

Ana oyun içerik paketi, save/load, renderer ve legacy map cleanup entegrasyonu ayrı kabul kapıları olarak kalır.
