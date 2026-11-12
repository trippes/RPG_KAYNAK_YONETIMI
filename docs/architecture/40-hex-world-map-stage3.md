# Eldoria — Aşama 3: Altıgen Dünya Haritası ve Karşılıklı Geçişler

**Durum:** Uygulandı; nihai doğrulama GitHub Actions Linux ve Windows sonuçlarına bağlıdır.  
**Dal:** `demo_eldoria`  
**Dünya şeması:** JSON `schema_version: 1`  
**Yerel altıgen harita şeması:** JSON `schema_version: 2` (değişmedi)  
**Content package manifest:** JSON `schema_version: 1` (geriye uyumlu, opsiyonel `world_map` alanı eklendi)

## 1. Koordinat sınırları

Üç kavram birbirinden ayrıdır:

- `HexCoord(q, r)`: geometri matematiği ve altı yönlü axial işlemler.
- `LocalHexPosition(q, r)`: bir altıgen yerel haritanın içindeki hücre.
- `WorldHexPosition(q, r)`: bir yerel haritanın dünya üzerindeki yerleşimi.

`WorldHexPosition` immutable ve hashable bir value object'tir. Integer olmayan ve bool koordinatlar reddedilir. `from_hex_coord` ve `to_hex_coord` açık dönüşüm sınırlarıdır. Komşuluk ve uzaklık hesapları yeni geometri kopyalamaz; mevcut `HexCoord` ve `HexDirection` API'sini kullanır.

Yön standardı `HexDirection` içindeki tek kaynaktan gelir:

| Yön | dq | dr | Tersi |
|---|---:|---:|---|
| EAST | +1 | 0 | WEST |
| NORTH_EAST | +1 | -1 | SOUTH_WEST |
| NORTH_WEST | 0 | -1 | SOUTH_EAST |
| WEST | -1 | 0 | EAST |
| SOUTH_WEST | -1 | +1 | NORTH_EAST |
| SOUTH_EAST | 0 | +1 | NORTH_WEST |

## 2. Dünya domain modeli

`application/world_map_definition.py` şu immutable modelleri sağlar:

- `WorldMapPlacement(map_id, position)`: bir altıgen yerel haritaya dünya koordinatı atar.
- `WorldMapDefinition(schema_version, world_map_id, name, placements, metadata)`: dünya haritasının kimliğini, yerleşimlerini ve metadata bilgisini tutar.
- `WorldMapDefinitionError`: veri ve bağlantı doğrulama hataları.

Yerleşim indeksleri immutable mapping olarak bir kez hazırlanır. Map ID ve koordinat üzerinden arama hash tabanlıdır. Bir dünya koordinatına en fazla bir yerel harita yerleşebilir. Her yerel hex map, bu package'ın tek dünya haritasında tam olarak bir kez yer almalıdır.

Dünya tanımı yerel hücreleri, terrain kayıtlarını, landmark'ları veya feature'ları kopyalamaz; yalnızca map ID ve dünya koordinatını saklar.

## 3. Dünya JSON sözleşmesi

Demo dosyası: `content/demo_eldoria/world.json`

```json
{
  "schema_version": 1,
  "id": "eldoria_hex_world",
  "name": "Eldoria — Altıgen Dünya",
  "maps": [
    {
      "map_id": "hex_forest_demo",
      "position": { "q": 0, "r": 0 }
    }
  ],
  "metadata": {
    "scope": "hex_maps_only"
  }
}
```

Zorunlu alanlar: `schema_version`, `id`, `name`, `maps`. Her yerleşim `map_id` ve integer `position.q/r) alanlarını taşır. Bilinmeyen alanlar, eksik alanlar, yanlış tipler, yinelenen map ID'leri ve yinelenen koordinatlar reddedilir. Metadata opsiyoneldir.

Manifest'e eklenen `world_map` alanı dünya JSON dosyasının package içindeki göreli yoludur. Alanı kullanmayan eski content package'lar için dünya tanımı `None) kalır; mevcut manifest schema version artırılmamıştır.

## 4. Geçişlerin tek doğruluk kaynağı

Haritalar arası geçişin tek doğruluk kaynağı, ilgili yerel harita JSON dosyasındaki mevcut `HexMapTransition` kaydıdır. Dünya JSON'u ikinci bir bağlantı listesi tutmaz. Bu sayede aynı bağlantının iki farklı dosyada çelişkili biçimde tanımlanması önlenir.

Aktif her geçiş için yükleyici:

1. Hedef hex map'in varlığını ve aynı dünya içinde yerleşimini doğrular.
2. Kaynak hücrelerin kaynak haritanın `valid_cells` maskesinde olduğunu doğrular.
3. Hedef hücrelerin hedef haritanın `valid_cells` maskesinde olduğunu doğrular.
4. Hedef dünya koordinatının kaynak koordinatın `exit_direction` komşusu olduğunu doğrular.
5. `target_entry_direction` değerinin çıkış yönünün tersi olduğunu doğrular.
6. `traversal_mode = "bidirectional"` ise hedef haritada ayrı bir reciprocal geçiş arar. Aynı transition ID'si aranmaz; hedef map ID, ters yönler ve kaynak/hedef hücre kümelerinin ters eşleşmesi aranır.

`traversal_mode = "one_way"` açıkça tek yönlü geçiş anlamına gelir; dönüş kaydı zorunlu değildir. `active = false` kayıtlar devre dışı editoryal placeholder kabul edilir ve dünya kenarı oluşturmaz. Bu nedenle Aşama 2 demo haritasındaki `future_hex_region` referansı, geleceğe dönük pasif placeholder olarak korunur. Aktif olmayan kayıtlar oyuncu tarafından kullanılamaz.

Transition ID benzersizliği mevcut content package yükleyicisindeki global kontrolle korunur.

## 5. Kare harita uyumluluğu

Dokuz mevcut schema-v1 kare harita aynı dosyalarda ve aynı veri modeliyle kalır. Bunların mevcut `world_position` alanları piksel/legacy dünya kataloğu koordinatlarıdır; yeni axial koordinat olarak yorumlanmaz.

Mevcut sekiz çift yönlü bağlantı ve 16 yönlü geçiş kaydı korunur. `world.map_loader`, `MapDefinition`, `WorldMap` ve kare harita başlangıç akışı değiştirilmez. Yeni `world_map` yalnızca schema-v2 altıgen harita kataloğunu kapsar. Bu ayrım, kare haritaları bu aşamada dönüştürmeden yeni hex dünya modelini kurar.

## 6. Content package entegrasyonu

`ContentPackage` artık `world_map_definition` alanını da taşır. Manifest'teki `world_map` tanımı varsa yükleyici dosyayı package kökü dışına çıkmayacak şekilde çözer, JSON'u parse eder ve tüm altıgen haritalara karşı doğrular.

Eski package'larda `world_map` alanı bulunmadığında mevcut davranış korunur. Kare harita kataloğu `map_definitions`, altıgen harita kataloğu `hex_map_definitions` olarak ayrı kalır. Dünya JSON'u yerel harita içeriğini çoğaltmaz.

Wheel dağıtımına `world.json` dahil edilmiştir.

## 7. Test kapsamı

Yeni testler:

- `tests/test_foundation/test_world_hex_position.py): immutable/hash davranışı, tip ayrımı, altı komşu ve ters yön, geometri uzaklığı.
- `tests/test_world/test_world_map_definition.py`: boş dünya, geçerli yerleşim, duplicate ID/koordinat, bilinmeyen/yerleşmemiş map, yanlış tip, reciprocal bağlantı, eksik dönüş, yanlış yön, yanlış giriş yönü, eksik hedef, geçersiz hedef hücresi, açık one-way ve pasif placeholder davranışı.
- `tests/test_application/test_content_loader.py): demo package dünya tanımının yüklenmesi ve yerleşim koordinatı.

Mevcut kare harita testleri dokuz map ID'sini, sekiz bağlantı çiftini, başlangıç konumunu ve legacy world graph'ı doğrulamaya devam eder.

## 8. Aşama 3 dışında bırakılanlar

- Kare haritaların axial dünyaya dönüştürülmesi veya yeni dünya yerleşimine alınması.
- Oyuncu/NPC hareketi, geçiş runtime'ı ve animasyon.
- Pathfinding, renderer, kamera ve harita çizimi.
- Save schema/migration.
- Feet, hareket maliyeti veya fiziksel mesafe.
- Bir content package içinde birden fazla dünya haritası kataloğu.

Bunlar sonraki aşamaların kapsamına bırakılmıştır. Demo dünya tanımı şu an yalnızca `hex_forest_demo` haritasını yerleştirir; bu, dokuz kare haritanın mevcut sistemden çıkarıldığı anlamına gelmez.
