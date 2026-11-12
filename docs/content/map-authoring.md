# Harita İçerik Sözleşmesi ve Harita Oluşturma

Bu belge, Content Editor veya doğrudan JSON düzenleyicisi kullanan içerik üreticileri için hazırlanmıştır. Harita verileri `content/<paket_id>/maps/` klasöründe tutulur. Harita eklemek, kaldırmak veya boyutunu değiştirmek için Python oyun koduna dokunulmaz.

## 1. Paket yapısı

Örnek paket düzeni:

```text
content/
  my_world/
    manifest.json
    starter_content.json
    npcs.json
    quests.json
    resources.json
    maps/
      village.json
      forest.json
      mine.json
```

Paket manifestinde harita klasörü bir kez belirtilir:

```json
{
  "schema_version": 1,
  "package_id": "my_world",
  "package_version": "1.0.0",
  "files": {
    "starter": "starter_content.json",
    "npcs": "npcs.json",
    "quests": "quests.json",
    "resources": "resources.json"
  },
  "maps": "maps"
}
```

Loader, belirtilen klasördeki bütün `.json` dosyalarını otomatik keşfeder. Dosyaları manifest içine tek tek eklemek gerekmez. Klasör boşsa, bulunamıyorsa veya JSON dosyası bozuksa paket yüklenmez.

## 2. Harita JSON yapısı

Aşağıdaki örnek, desteklenen temel alanları gösterir:

```json
{
  "schema_version": 1,
  "map_id": "forest",
  "name": "Kuzey Ormanı",
  "description": "Köyün kuzeyindeki ormanlık alan.",
  "size": {
    "width": 40,
    "height": 24
  },
  "terrain": {
    "default_tile": "grass"
  },
  "world_position": [180, 50],
  "activities": ["gather", "combat", "travel"],
  "metadata": {
    "location_type": "forest",
    "biome": "temperate"
  },
  "starting_position": null,
  "blocked_tiles": [[4, 5], [4, 6]],
  "features": [
    {
      "id": "river",
      "type": "river",
      "tiles": [[18, 0], [18, 1]],
      "walkable": false
    },
    {
      "id": "bridge",
      "type": "bridge",
      "tiles": [[18, 1]],
      "walkable": true
    }
  ],
  "landmarks": [
    {
      "id": "forest_tree_01",
      "name": "Çam Ağacı",
      "description": "Odun toplanabilen yaşlı bir ağaç.",
      "position": [8, 9],
      "type": "resource",
      "visual_type": "tree",
      "walkable": true,
      "interactable": true,
      "activities": ["gather"],
      "resource_node_id": "forest_wood"
    }
  ],
  "transitions": []
}
```

### Zorunlu alanlar

- `schema_version`: Şu anda `1` olmalıdır.
- `map_id`: Paket içinde benzersiz, kararlı kimlik. Kayıtlar bu kimliği sakladığı için sonradan değiştirmeyin.
- `name`: Oyuncuya gösterilen harita adı.
- `description`: Harita açıklaması; boş metin olabilir.
- `size.width`, `size.height`: Pozitif tam sayılar.
- `terrain.default_tile`: Haritanın varsayılan zemin türü.

### Dünya konumu ve başlangıç

- `world_position`: Dünya haritasındaki koordinattır. Yerel tile koordinatı değildir. Dünya haritası bu değerlerden oluşturulur.
- `starting_position`: Oyuncunun başlangıç tile koordinatıdır. Yalnızca başlangıç haritasında bulunmalıdır. Paket tam olarak bir başlangıç haritası tanımlamalıdır.
- `activities`: Dünya haritasında bu konum için sunulan etkinlik etiketleri.
- `metadata`: İsteğe bağlı, ek içerik bilgileri. `location_type` dünya haritasında bölge türü olarak kullanılır.

## 3. Koordinat ve boyut kuralları

Koordinatlar sıfır tabanlıdır: sol üst köşe `[0, 0]`, sağ alt köşe `[width - 1, height - 1]`.

Örneğin 40×24 haritada geçerli x değerleri 0–39, y değerleri 0–23 aralığındadır. Bu kontrol şu alanlara uygulanır:

- `starting_position`
- `blocked_tiles`
- `features[].tiles`
- `landmarks[].position`
- `transitions[].from_tiles`

Geçiş hedef koordinatları ayrıca hedef haritanın gerçek boyutlarına göre doğrulanır. 16×24, 32×32 veya 40×24 gibi farklı boyutlar aynı pakette kullanılabilir.

## 4. Haritalar arası geçişler

Geçiş, kaynak haritanın `transitions` alanında tanımlanır:

```json
{
  "id": "forest_to_mine",
  "from_tiles": [[39, 12]],
  "target_map_id": "mine",
  "target_tiles": [[0, 12]],
  "direction": "east",
  "bidirectional": true
}
```

- `id`: Paket genelinde benzersiz geçiş kimliği.
- `from_tiles`: Oyuncunun çıkış yapabileceği kaynak tile'lar.
- `target_map_id`: Hedef haritanın `map_id` değeri.
- `target_tiles`: Hedef haritada oyuncunun yerleştirileceği tile'lar.
- `direction`: `north`, `south`, `east` veya `west`.
- `bidirectional`: `true` ise hedef haritada ters yönde bir geçiş de tanımlanmalıdır. `false` tek yönlü geçiştir.

Çift yönlü geçişte hedef dosyaya ters kayıt ekleyin. Ters kaydın `from_tiles` alanı ilk geçişin `target_tiles` koordinatlarıyla, `target_tiles` alanı ise ilk geçişin `from_tiles` koordinatlarıyla eşleşmelidir.

Dünya haritasının komşuluk grafiği bu geçişlerden oluşturulur. Dünya haritasında komşu olmak, yerel haritada otomatik geçiş oluşturmaz; yerel çıkış koordinatları ayrıca tanımlanmalıdır.

## 5. Zemin, özellik ve görseller

Mevcut Pygame çizim sistemi şu zemin türlerini destekler: `grass`, `dirt`, `sand`, `stone`.

Mevcut arazi özellikleri: `river`, `bridge`, `wall`.

Mevcut landmark görselleri: `tree`, `mine`, `gate`, `forge`, `inn`, `market`, `house`, `tower`, `building`.

Görsel türleri merkezi stil kayıtlarından çizilir. Bilinmeyen zemin veya görsel türleri sessizce başka bir harita stiline dönüştürülmez; kontrollü varsayılan görünüm ve tanı mesajı kullanılır. Yeni bir çizim şekli motor yeteneği gerektiriyorsa kod değişikliği gerekir; mevcut desteklenen türleri kullanmak için gerekmez.

## 6. NPC, kaynak, görev ve pazar referansları

Diğer içerik dosyaları haritalara `location_id` ile bağlanır. Yeni paketlerde doğrudan harita `map_id` değerini kullanın.

NPC kaydı:
- `location_id` mevcut bir haritayı göstermelidir.
- `position` haritanın sınırları içinde olmalıdır.

Kaynak düğümü:
- `location_id` mevcut bir haritayı göstermelidir.
- `landmark_id` o haritada bulunmalıdır.
- Haritadaki landmark'ın `resource_node_id` alanı kaynak kaydının `id` değeriyle eşleşmelidir.

Görev:
- `giver_npc_id` mevcut NPC'yi göstermelidir.
- `collect` hedefi mevcut kaynak düğümünü, `talk` hedefi mevcut NPC'yi göstermelidir.

Pazar:
- `location_id` mevcut haritayı, `npc_id` mevcut NPC'yi göstermelidir.

Paket yüklenirken bu referanslar doğrulanır. Hata mesajında ilgili içerik kaydı ve eksik referans belirtilir.

## 7. Harita ekleme

1. Paket içindeki `maps/` klasörüne yeni bir JSON dosyası ekleyin.
2. Dosyanın `map_id` değerini kararlı ve benzersiz belirleyin.
3. Boyutları, zemin türünü ve dünya konumunu yazın.
4. Haritayı başlangıç haritası yapacaksanız `starting_position` ekleyin. Paket genelinde yalnızca bir haritada bulunmalıdır.
5. Var olan haritalarla bağlantı kuracaksanız her iki dosyanın `transitions` alanını düzenleyin.
6. NPC, kaynak, görev veya pazar yerleştirecekseniz ilgili içerik dosyalarında aynı `map_id` değerini kullanın.
7. Paket doğrulamasını ve testleri çalıştırın.

Yeni harita için Python dosyası, merkezi harita listesi veya manifest içinde tek tek dosya kaydı eklenmez.

## 8. Harita kaldırma ve kayıt uyumluluğu

Bir haritayı kaldırmadan önce NPC, kaynak, görev, pazar ve geçiş referanslarını güncelleyin. Haritayı kullanan kayıtlar da değerlendirilmelidir.

Aktif paket dünyasına ait bir kayıt, artık bulunmayan haritayı veya yeni boyutların dışında kalan oyuncu koordinatını içeriyorsa yükleme açık uyumluluk hatası verir. Oyuncu başka haritaya taşınmaz ve koordinatı sessizce düzeltilmez. Eski haritayı geri ekleyin veya açık bir kayıt migration/redirect işlemi hazırlayın.

Harita kimliklerini değiştirmek yerine mevcut kimliği koruyun. Bu, kayıtların ve içerik referanslarının kararlı kalmasını sağlar.

## 9. Hata mesajlarını yorumlama

- **Missing map / missing target map:** `target_map_id` veya `location_id` değerini mevcut dosyaların `map_id` değerleriyle karşılaştırın.
- **Outside map bounds:** Hatalı koordinatı haritanın width/height değerlerine göre düzeltin.
- **Reciprocal transition required:** Çift yönlü çıkışın ters kaydını hedef haritaya ekleyin veya geçiş gerçekten tek yönlüyse `bidirectional: false` kullanın.
- **Unknown landmark/resource node:** Harita landmark kimliğiyle kaynak kaydındaki `landmark_id` ve `resource_node_id` değerlerini eşleştirin.
- **Starting map count:** Tam olarak bir haritada `starting_position` bulunduğundan emin olun.

İçerik paketini başlatmadan önce doğrulayın. Doğrulama hatalarını düzeltmeden bozuk paketi oyuna yüklemeyin.
