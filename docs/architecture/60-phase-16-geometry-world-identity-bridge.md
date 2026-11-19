# Aşama 16 — Geometry ve World Identity Bridge

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **ADAPTER VE OTOMATİK SÖZLEŞME TESTLERİ TAMAMLANDI; LINUX/WINDOWS CI BAŞARILI**  
Önceki kapı: [Aşama 0 hazırlık ve package/runtime spike](59-phase-16-stage-0-integration-readiness.md)

## 1. Amaç ve sınır

Laboratuvarın geometri ve kimlik değerlerini Eldoria'nın mevcut axial runtime sözleşmesine açık, geri çevrilebilir ve test edilmiş bir sınır üzerinden bağlamak.

Bu dilim:
- Axial koordinat tipleri arasındaki dönüşümü,
- Local map hücresi ile world-map yerleşimi ayrımını,
- Eldoria ve laboratuvar world/map ID sarmalayıcılarını,
- Pointy-top geometri ve kamera koordinat çerçevesi uyumunu

sağlar.

Bu dilim actor registry, hareket, occupancy, physics, simulation, renderer sahipliği, content registry veya save/load davranışını değiştirmez.

## 2. Kaynak-hedef sözleşme farkları

### Eldoria (hedef runtime)

- `HexCoord(q,r)`: geometri/topoloji koordinatı.
- `LocalHexPosition(q,r)`: tek harita içindeki hücre.
- `WorldHexPosition(q,r)`: dünya haritasında harita yerleşimi.
- `EntityPosition(map_id, cell)`: hareketli entity'nin map-local mantıksal konumu.
- `core.foundation.WorldId`: canonical dünya kimliği.
- `application.HexMapDefinition`: pointy-top axial haritanın mevcut içerik sözleşmesi.
- `application.HexWorldRuntime`: entity konumu ve occupancy için mevcut otorite.

### Hex World laboratuvarı

- `AxialCoord(q,r)`: kapsam bilgisi taşımayan geometri koordinatı.
- `WorldPoint(x,y)`: matematiksel dünya düzlemi; y yukarı yönlü.
- `HexLayout`: pointy-top/flat-top, radius ve origin bilgisi.
- `WorldId`, `MapId`, `CellAddress`: laboratuvara ait ayrı immutable kimlik tipleri.
- `WorldScreenTransform`: world y-up koordinatını ekran y-down koordinatına çevirir.

Bu tipler yapısal olarak benzer görünse de aynı Python tipi veya aynı sorumluluk değildir. Doğrudan birbirlerinin yerine kullanılmaları yasaktır.

## 3. Koordinat dönüşüm kararı

Eldoria'nın pointy-top axial koordinatları ve mevcut ekran-world dönüşümü y-down; laboratuvarın matematiksel world koordinatı y-up'tır. Yalnızca `q,r` değerlerini birebir kopyalamak, laboratuvar kamerasında haritayı dikey olarak ters gösterir ve adlandırılmış yönleri görsel olarak yanlış eşler.

Adapter bu nedenle açık bir axial baz yansıması uygular:

```
Eldoria (q, r)  ->  Lab (q + r, -r)
Lab (q', r')    ->  Eldoria (q' + r', -r')
```

Bu dönüşüm:
- Altı komşuluğu ve hex uzaklığını korur.
- Eldoria'nın EAST / NORTH_EAST / NORTH_WEST / WEST / SOUTH_WEST / SOUTH_EAST yönlerinin ekrandaki konumunu korur.
- Kare koordinat dönüşümü değildir.
- Local map hücresi ile world-map yerleşimini birbirine dönüştürmez; her iki tip için ayrı, açık fonksiyon kullanılır.

Laboratuvar `HexLayout.radius` değeri Eldoria'nın `hex_size` değerine karşılık gelir. Eldoria'nın y-down origin ve camera center değerleri, laboratuvarın y-up `WorldPoint` çerçevesine aktarılırken y ekseninde yansıtılır. Eldoria'nın mevcut map sözleşmesi yalnızca pointy-top desteklediği için flat-top layout adapter tarafından reddedilir.

## 4. Uygulanan adapter

Yeni modül: `application/hex_world_geometry_bridge.py`

Sorumlulukları:
- `HexCoord`, `LocalHexPosition`, `WorldHexPosition` ile laboratuvar `AxialCoord` arasında kapsamı koruyan dönüşümler.
- Eldoria `HexDirection` değerlerinin laboratuvar axial delta karşılıkları.
- Eldoria y-down world origin, camera center ve hex size değerlerinden pointy-top `HexLayout` üretimi.
- Map-local hücre ile laboratuvar `WorldPoint` arasında ileri/ters dönüşüm.
- Core `WorldId` ile laboratuvar `WorldId` sarmalayıcıları arasında dönüşüm.
- Eldoria `EntityPosition` değerinden laboratuvar `CellAddress` üretimi ve geri dönüşte beklenen world ID eşleşmesinin zorunlu tutulması.

Adapter, laboratuvarın `HexWorld` map registry'sini veya `EntityWorldCoordinator` registry'sini Eldoria'nın ana otoritesi hâline getirmez. Mevcut `application.HexMapDefinition` ve `application.HexWorldRuntime` sahipliği korunur.

## 5. Test kapsamı

Yeni test dosyası: `tests/test_application/test_hex_world_geometry_bridge.py`

Test edilen sözleşmeler:
1. Local axial dönüşüm round-trip.
2. Geometry-only `HexCoord` dönüşüm round-trip.
3. World-map placement dönüşüm round-trip; local position ile tip ayrımı.
4. Altı yönün komşuluk ve ekran yönü eşleşmesi.
5. Laboratuvar `WorldScreenTransform` ile Eldoria `WorldTransform` ekran koordinatlarının aynı hücrelerde, farklı origin/camera/zoom değerleriyle eşitliği.
6. Hücre merkezinden world-point'e ve geri dönüş.
7. Flat-top layout'ın açıkça reddedilmesi.
8. World/map identity wrapping ve cross-world address reddi.
9. Boş map ID'nin reddi.

## 6. Bilinçli olarak ertelenen konular

- Laboratuvar `EntityId` ile Eldoria actor/entity kimliğinin eşlenmesi.
- `EntityRecord`, `EntityWorldCoordinator` ve Eldoria actor registry arasında sahiplik kararı.
- Sürekli `WorldPoint` hareketi ile Eldoria'nın hücre/occupancy konumunun tek otorite altında birleştirilmesi.
- Physics body, collision footprint ve spatial index bağlantısı.
- Tick/simulation orchestration.
- Kamera ve renderer'ın ana oyun akışına alınması.
- Map definition, sparse cell override ve persistence sahipliği.

Bu konular sonraki dilimlerin kapsamıdır. Bu rapor bunlara önceden karar vermez.

## 7. Doğrulama

- Adapter commit: `de9545f85bd7cb69f6cb55e091b77818644520a1`
- Test commit / doğrulanan HEAD: `360befef8b704d05fd4d64a0cdd4ab3d0501920f`
- GitHub Actions run: [#44510873444](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44510873444)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platform: 2.147 test, 235 subtest başarılı; 59 pygame deprecation uyarısı.
- Ruff, legacy cleanup boundary, compileall, wheel/izole kurulum ve release verification başarılı.

## 8. Sonraki dilim

**Aşama 16 — Actor Identity ve Movement Ownership Bridge.**

Önce Eldoria `WorldActorRegistry` / Core entity kimlikleri ile laboratuvar `EntityId` / `EntityRecord` ilişkisinin tekil kimlik sözleşmesi belirlenecek. Sonra `HexWorldRuntime` occupancy konumu ile laboratuvarın sürekli hareket/transform state'inin aynı entity için iki bağımsız konum otoritesi oluşturmadan nasıl bağlanacağı tasarlanacak.

Bu sahiplik kararı ve testleri geçmeden laboratuvar entity registry'si ana oyun akışına bağlanmayacak.
