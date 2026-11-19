# Aşama 16 — Physics ve Static Spatial Bridge

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **STATIC COLLISION PROJECTION VE CELL-STEP PHYSICS VALIDATION TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki dilim: [Actor Identity ve Movement Ownership Bridge](61-phase-16-actor-identity-movement-ownership-bridge.md)

## 1. Amaç

Laboratuvarın fizik motorunu Eldoria'nın mevcut axial map sözleşmesine bağlamak; bunu yaparken:
- Core `HexMapDefinition` tek içerik kaynağı olarak kalmalı,
- `HexWorldRuntime` mantıksal cell position ve dynamic occupancy sahibi olmaya devam etmeli,
- fizik çözümü hareket state'i veya tick state'i saklamamalı,
- dinamik actor'lar statik obstacle listesine kopyalanmamalı.

## 2. Uygulanan mimari

### Canonical map → ephemeral collision projection

Yeni modül: `application/hex_physics_bridge.py`

`build_hex_physics_snapshot`:
1. Eldoria `HexMapDefinition` değerini okur.
2. LocalHexPosition hücrelerini Aşama 16 geometry bridge üzerinden laboratuvar axial bazına dönüştürür.
3. Core map'in `blocked` hücrelerini fizik obstacle'ı olarak üretir.
4. `walkable=False` landmark hücrelerini fizik obstacle'ı olarak üretir.
5. `HexMapFeature` değerlerine fiziksel anlam atamaz; feature türleri için henüz collision-footprint sözleşmesi yoktur.
6. Yalnızca collision snapshot üretmek için geçici bir lab `HexWorld` oluşturur.
7. `HexMapCollisionGeometry` ve `ObstacleSpatialIndex` üretir.
8. Geçici lab world/registry nesnelerini saklamaz; yalnızca immutable geometry snapshot ve statik obstacle index döndürür.

Bu geçici projection ikinci bir map/content owner değildir. Ana map definition, Eldoria'nın core map definition'ıdır.

### Cell-step physics validation

`HexPhysicsSnapshot.resolve_cell_step` iki hücre merkezi arasındaki hareketi laboratuvarın swept-circle collision resolver'ı ile saf biçimde değerlendirir. `can_reach_cell` yalnızca hedef merkeze tam ulaşılabiliyorsa true döndürür.

`ActorHexBindingService.move_to_with_physics` şu sırayı uygular:
1. Actor kimliği ve world scope doğrulanır.
2. `HexWorldRuntime.validate_move_to` side-effect-free ön kontrolü yapar.
3. Static physics, source cell merkezinden target cell merkezine tam geçişi doğrular.
4. Fizik engeli varsa `PHYSICAL_COLLISION` döner ve hiçbir konum/occupancy değişmez.
5. Fizik geçişi temizse hareketi yalnızca `HexWorldRuntime.move_to` commit eder.

### Runtime preflight

`HexWorldRuntime.validate_move_to` eklendi. Hareket kurallarını ve dynamic occupancy'yi değiştirmeden doğrular. `move_to` aynı doğrulamayı kullanır ve yalnızca başarı durumunda occupancy değiştirir.

`MovementFailureReason.PHYSICAL_COLLISION` yeni, ayrı bir başarısızlık sebebidir; terrain/map block ve dynamic occupied cell durumlarıyla karıştırılmaz.

## 3. Sahiplik sınırları

| Katman | Otorite |
|---|---|
| Base map, valid-cell mask, blocked flag, landmark | Eldoria `HexMapDefinition` |
| Actor ID ve gameplay state | `WorldActorRegistry` |
| Logical cell position ve dynamic occupancy | `HexWorldRuntime` |
| Static collision geometry snapshot | `HexPhysicsSnapshot` (türetilmiş, yeniden üretilebilir) |
| Static obstacle broadphase | Laboratuvar `ObstacleSpatialIndex` |
| Dynamic actor occupancy kontrolü | `HexOccupancyRegistry` |

Laboratuvar `EntitySpatialIndex`, `EntityRegistry` ve `EntityWorldCoordinator` bu dilimde kullanılmadı. Dinamik actor'ları ikinci bir registry'ye kopyalamak yerine mevcut occupancy kontrolü korundu.

Laboratuvar `MovementSystem`, `CollisionAwareMovementSystem` ve `SimulationTickCoordinator` da kullanılmadı. Bu aşamada fizik çözümü saf bir hareket doğrulamasıdır; continuous WorldPoint movement state veya ikinci tick owner oluşturmaz.

## 4. Test kapsamı

Yeni dosya: `tests/test_application/test_hex_physics_bridge.py`

Test edilen davranışlar:
1. Core blocked cells → static collision obstacles.
2. Walkable olmayan landmarks → static collision obstacles.
3. Collision obstacle source-cell world/map kimliklerinin korunması.
4. OPEN boundary policy'nin perimeter wall üretmemesi.
5. Map ID uyuşmazlığının reddedilmesi.
6. Engel olmayan iki komşu hücre merkezi arasında tam fiziksel geçiş.
7. Hücre geçiş yolundaki statik obstacle'ın swept-circle hareketini durdurması.
8. Fizik başarısızlığında actor cell/occupancy'nin değişmemesi.
9. Fizik başarılı olduğunda commit'in mevcut HexWorldRuntime üzerinden yapılması.
10. Farklı map'e ait physics snapshot'ın hareket öncesinde reddedilmesi.

## 5. Doğrulama

- `PHYSICAL_COLLISION` domain sonucu: `6ac4a7e767e6769eee14f6c901d2c519f3dba074`
- Side-effect-free runtime preflight: `eb4a7649eedd00ab48a634688299f301ee2380a5`
- Static physics projection: `2cf7b09a327e167a5a5bc1684c38d8c0ef3e5e4d`, `1a9848c25c406e5462c6c146b6447750a7eeb7d7`
- Actor physics commit bridge: `4b72566cba5ce2b535a54ecd3acafa5cb9d79577`
- Physics tests / doğrulanan HEAD: `93c37fca395659dca1b67d593208834e70e64979`
- GitHub Actions: [#44513116544](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44513116544)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platform: 2.168 test, 235 subtest başarılı; 59 pygame deprecation uyarısı.
- Ruff, legacy cleanup boundary, compileall, wheel/izole kurulum ve release verification başarılı.

## 6. Sonraki dilim

**Aşama 16 — Dynamic Spatial Query Bridge.**

Laboratuvarın `EntitySpatialIndex` sistemi ikinci `EntityRegistry` olmadan doğrudan kullanılamaz. Sonraki dilimde Eldoria `WorldActorRegistry` + `HexWorldRuntime` verilerinden salt-okunur actor spatial projection üretme veya mevcut `HexOccupancyRegistry` üzerinde gerekli sorguları genişletme seçenekleri karşılaştırılacak.

Hedef; interaction radius, yakındaki actor sorguları ve ileride NPC/companion algısı için tek actor identity ve tek logical position sahibiyle çalışmaktır. Bu karar verilmeden lab EntityRegistry ana oyuna eklenmeyecek.
