# Aşama 16 — Market Hex Spatial Anchor

Tarih: 19 Kasım 2026  
Dal: `experiment/map-cleanup`  
Durum: **MARKET ANKRAJI NPC KONUMUNDAN TÜRETİLİYOR; LINUX/WINDOWS CI BAŞARILI**  
Önceki denetim: [Market ve Container Spatial Ownership Audit](64-phase-16-market-container-spatial-ownership-audit.md)

## 1. Amaç

Market'i ikinci bir world entity veya position owner yapmadan, mevcut `MarketProfile.npc_id` ilişkisi üzerinden axial dünyaya bağlamak.

## 2. Uygulama

Yeni `application/market_hex_anchor.py` / `MarketHexAnchorService`:

- Market kimliğini ve ekonomik state'i mevcut `Market` runtime'ından çözer.
- Market profile içindeki `npc_id` ile `NPCSpatialBindingService` üzerinden mevcut NPC spatial entity'sini bulur.
- `position(market_id)` çağrısı NPC'nin o andaki `EntityPosition` değerini döndürür.
- Market hareketli değildir ve kendi HexWorldRuntime entity/occupancy kaydı oluşturulmaz.
- NPC hareket ettiğinde sonraki market anchor sorgusu yeni konumu döndürür.
- NPC kaydı, actor kaydı, world scope veya spatial kayıt eksikse kontrollü `MarketHexAnchorError` üretilir.

`GameplayService.market_hex_anchor`, aktif SessionBundle içindeki Market ve NPC binding üzerinden oluşturulan salt servis görünümüdür; yeni mutable state sahibi değildir.

## 3. Legacy alan kararı

`MarketProfile.location_id` mevcut domain ve save/load şemasında tutulur. Bu değer:
- Hex map ID olarak yorumlanmaz.
- Axial koordinat içermez.
- Market'in gerçek spatial konumu olarak kullanılmaz.
- Bu adapter tarafından değiştirilmez veya dönüştürülmez.

Market'in mevcut mekânsal ankrajı yalnızca `npc_id` ile bağlı NPC'nin HexWorldRuntime konumudur. Market alışveriş etkileşimi için komşuluk/mesafe kuralı bu dilimde eklenmemiştir; böyle bir kural oyun tasarımı kararı gerektirir.

## 4. Container için korunan sınır

Aşama 16.4 öncesi Container entegrasyonu bekletilmiştir:

- ContainerInstance bir Core `entity_id` ile ilişkilidir; Core Entity'nin eski `Position(x,y)` alanı axial konum değildir.
- World membership için canonical kaynak `WorldMembershipService.world_id_for(entity_id)` olmalıdır; Core Entity üzerindeki eski world projection kullanılmamalıdır.
- `ContainerManager.inventory_custody(container_id)` ve `parent_of(container_id)` doluysa container taşınan/nested durumdadır ve world placement alamaz.
- Container yalnızca world membership sahibi ve custody dışında ise world-placed kabul edilebilir.
- ContainerSnapshot `placements` alanı bugün boş üretilir; mevcut yükleme yolu dolu legacy placement kayıtlarını reddeder.
- Henüz axial placement record, footprint, collision/blocking metadata veya save/load round-trip sözleşmesi yoktur.

Bu nedenle ContainerHexBindingService bu commit serisinde oluşturulmamıştır. Önce typed axial placement ve persistence sözleşmesi tanımlanacaktır. Eski Core `Position(x,y)` verisi hiçbir koşulda axial konuma çevrilmeyecektir.

## 5. Test kapsamı

`tests/test_application/test_market_hex_anchor.py` doğrular:

1. Market position NPC'nin mevcut spatial position değerinden türetilir.
2. Legacy `location_id` axial map ID veya koordinat olarak yorumlanmaz.
3. NPC hareket ettiğinde market anchor sorgusu otomatik yeni konumu döndürür.
4. Market için ikinci HexWorldRuntime entity kaydı oluşmaz.
5. NPC spatial registration yoksa anchor reddedilir.
6. Bilinmeyen market profili reddedilir.
7. Başka world'e bağlı NPC actor, aktif world market ankrajı olarak kullanılamaz.

## 6. CI doğrulaması

- Doğrulanan kod commit'i: `a2f4b9c774c0c6d08ce1e061a94cc128e04f532b`
- GitHub Actions: [#44516179038](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44516179038)
- Linux: başarılı.
- Windows: başarılı.
- Her iki platformda: **2.191 test + 235 subtest başarılı**.
- Release-candidate verification: iki platformda başarılı.
- Linux Ruff: NPC/resource/physics/geometry/market bridge modülleri ve ilgili testler başarılı.
- Legacy map cleanup boundary: başarılı.
- 59 pygame deprecation uyarısı mevcut; test başarısızlığı değildir.

## 7. Sonraki teknik kapı

Container için typed axial placement ve save/load round-trip tasarlanacak. Placement kaydı, Core entity world membership'i, container custody ilişkisi, map maskesi ve açık fiziksel footprint/blocking metadata ile birlikte doğrulanmalıdır. Bu sözleşme tamamlanmadan container world placement veya yeni container koordinatı oluşturulmayacaktır.
