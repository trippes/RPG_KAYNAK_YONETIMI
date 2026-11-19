# Aşama 16 — Actor Identity ve Movement Ownership Bridge

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **ACTOR/SPATIAL BINDING VE GAMEPLAY SERVICE BAĞLANTISI TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilim: [Geometry ve World Identity Bridge](60-phase-16-geometry-world-identity-bridge.md)

## 1. Amaç

Eldoria'nın mevcut actor kimliğini, laboratuvarın EntityId sözleşmesiyle tekil biçimde eşlemek ve mevcut hex runtime hareketini ana GameplayService üzerinden erişilebilir kılmak. Bu dilim ikinci bir actor registry veya ikinci bir mantıksal konum otoritesi oluşturmaz.

## 2. Sahiplik kararı

| Sorumluluk | Tek otorite | Not |
|---|---|---|
| Actor kimliği ve gameplay bağlantıları | `WorldActorRegistry` | actor_id, world_id, role, character/inventory/activity |
| Hex map-local mantıksal konum ve occupancy | `HexWorldRuntime` / `HexOccupancyRegistry` | EntityPosition occupancy kaydından okunur |
| Hareket profili ve hex hareket izni | `HexWorldRuntime` | MovementProfile ve movement-enabled durumu |
| Dünya kapsamı | `core.foundation.WorldId` + world-scoped HexWorldRuntime | Actor binding sırasında eşleşme zorunlu |
| Gameplay API | `GameplayService` | SessionBundle'dan aktif world/runtime çözülür |

`WorldActor.actor_id` ve `HexWorldRuntime.entity_id` aynı kararlı string kimliği kullanır. Laboratuvar `EntityId` yalnızca sınırda bu değeri sarmalar; yeni bir ID üretmez ve registry oluşturmaz.

Actor `active` durumu ile hex runtime `movement_enabled` durumu aynı şey değildir:
- Actor inactive ise gameplay hareket isteği reddedilir.
- Actor aktif olsa bile hex movement ayrı olarak devre dışı bırakılabilir.
- Bu iki bayrak otomatik olarak birbirine kopyalanmaz.

## 3. Uygulanan değişiklikler

### `application/hex_world_runtime.py`

- Runtime'a isteğe bağlı canonical `WorldId` bağlama alanı eklendi.
- `world_id` salt okunur property olarak sunuluyor.
- `remove_entity` eklendi. Önce entity/occupancy tutarlılığını doğrular; ardından occupancy, entity state ve patrol index kaydını birlikte temizler.

Mevcut bağımsız runtime testleri için world_id parametresi opsiyonel kalır. Ancak actor binding servisi yalnızca açıkça world-scoped oluşturulmuş runtime'ı kabul eder.

### `application/hex_actor_binding.py`

Yeni `ActorHexBindingService`:
- Actor'ın `WorldActorRegistry` içinde bulunmasını zorunlu tutar.
- Actor'ın world_id değerini binding'in world_id değeriyle karşılaştırır.
- Runtime'ın aynı canonical WorldId ile oluşturulmuş olmasını zorunlu tutar.
- Actor ID'yi değiştirmeden aynı kimlikle HexWorldRuntime'a spatial kayıt yapar.
- Actor inactive ise hareketi reddeder.
- Runtime movement-enabled bayrağını actor active bayrağından bağımsız yönetir.
- Spatial kaydı kaldırırken actor kimliğini ve gameplay bağlantılarını silmez.

### `application/gameplay_service.py`

Yeni `hex_actor_binding` property:
- Aktif Core world'ü çözer.
- SessionBundle içindeki mevcut HexWorldRuntime'ı alır.
- Runtime yoksa, world scope yoksa veya farklı world'e bağlıysa kontrollü hata üretir.
- Her çağrıda mevcut SessionBundle bileşenlerine bağlanan servis görünümü üretir; yeni state owner oluşturmaz.

## 4. Bilinçli olarak entegre edilmeyen laboratuvar bileşenleri

Laboratuvarın `EntityRegistry` / `EntityWorldCoordinator` sınıfları ikinci bir entity store ve transform sahibi olacağından ana oyun akışına bağlanmadı.

Laboratuvarın `MovementSystem` ve `CollisionAwareMovementSystem` sınıfları sürekli `WorldPoint` konumu saklar. Bunları doğrudan `HexWorldRuntime` ile eş zamanlı kullanmak aynı actor için iki bağımsız konum otoritesi oluşturabilir. Eldoria'nın mevcut sözleşmesinde map-local `EntityPosition` ve occupancy otoritesi `HexWorldRuntime` olduğundan bu sistemler henüz gameplay movement owner olarak kullanılmıyor.

Benzer şekilde laboratuvar `SimulationTickCoordinator` kendi tick sıra numarasını yönetir; Eldoria'da canonical tick sahibi Core simulation'dır. İkinci bir tick owner eklenmedi.

Bu bileşenlerin daha sonra kullanılması gerekirse:
- Sürekli konumun authoritative mi yoksa yalnızca görsel interpolasyon mu olacağı,
- Occupancy'nin authoritative state mi yoksa türetilmiş indeks mi olacağı,
- Core simulation tick'inin laboratuvar hareket adımını nasıl çağıracağı

ayrı bir teknik sözleşmeyle belirlenmelidir. Şimdilik mevcut hex-cell hareket modeli korunmuştur.

## 5. Test kapsamı

Yeni testler:
- `tests/test_application/test_hex_actor_binding.py`
- `tests/test_application/test_gameplay_service_hex_actor_binding.py`

Doğrulanan davranışlar:
1. Actor ID ↔ lab EntityId birebir round-trip.
2. Aynı actor ID ile spatial kayıt; ikinci kimlik/registry üretmeme.
3. Başka world'e ait actor'ın reddi.
4. Başka world'e bağlı runtime'ın reddi.
5. WorldId taşımayan runtime'ın actor binding için reddi.
6. Actor inactive iken hareketin reddi.
7. Actor active ile movement-enabled bayraklarının bağımsızlığı.
8. Occupancy çakışmasında hareketin atomik başarısız olması.
9. Spatial kayıt kaldırıldığında actor kimliğinin ve gameplay bağlantılarının korunması.
10. Bilinmeyen actor'ın kaydedilememesi veya hareket ettirilememesi.
11. GameplayService'in aktif world/runtime üzerinden binding servisini çözmesi.
12. Runtime henüz oluşturulmamışsa veya başka world'e aitse kontrollü hata.

## 6. Doğrulama

- Runtime world scope ve remove_entity: `52372cb358f049b1c0b2335e76ed0c059f920cd9`
- Actor binding: `5dd7bb3a96fc054a5e591b125b8bd802e80530db`
- World-scoped runtime kontrolü: `b1da9d672728b56dc151b7c5c1dad193be43761e`, `edca5c4e398e6794f827e5edf72c546bc2ae13b1`, `67541dc6cca7453ca0d7cab56c3f82572391d778`
- GameplayService bağlantısı: `69fff84b8ffccd427501ea245bc5f69924b2d906`, `9ab922124af9bf748273666c96cf333af38b6714`
- GitHub Actions: [#44512190752](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44512190752)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platform: 2.160 test, 235 subtest başarılı; 59 pygame deprecation uyarısı.
- Ruff, legacy cleanup boundary, compileall, wheel/izole kurulum ve release verification başarılı.

## 7. Sonraki dilim

**Aşama 16 — Physics ve Spatial Query Bridge.**

Önce laboratuvarın statik collision geometry ve pure collision resolver bileşenlerinin Eldoria `HexMapDefinition` ve `HexWorldRuntime` ile nasıl kullanılacağı belirlenecek. Bu aşamada `EntityRegistry` veya `MovementSystem` sahipliği alınmayacak; physics yalnızca mevcut hex hareket isteğinin geçerliliğini değerlendiren bir servis olarak ele alınacak. Dynamic actor occupancy kontrolü yine `HexWorldRuntime` tarafından yapılacak.

Bu rapor, ana oyunun harita/actor içeriklerinin veya renderer'ın tamamen entegre edildiği anlamına gelmez.
