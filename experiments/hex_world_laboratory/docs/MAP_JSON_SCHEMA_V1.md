# Hex Map JSON Schema v1

Bu belge, Hex World Laboratory Aşama 3.6 kapsamında kullanılan harita başlangıç verisi biçimini açıklar.

## Dosya yapısı

Bir harita dosyası UTF-8 JSON nesnesidir. Şema sürümü `schema_version: 1` olarak belirtilir.

```json
{
  "schema_version": 1,
  "world_id": "eldoria",
  "map_id": "starting_valley",
  "name": "Başlangıç Vadisi",
  "layout": {
    "orientation": "pointy_top",
    "radius": 1.0,
    "origin": { "x": 0.0, "y": 0.0 }
  },
  "cells": [
    {
      "q": 0,
      "r": 0,
      "terrain_id": "grass",
      "is_walkable": true,
      "has_obstacle": false,
      "metadata": { "biome": "meadow" }
    }
  ]
}
```

## Alan sözleşmesi

| Alan | Tür | Kural |
|---|---|---|
| `schema_version` | integer | Yalnızca 1 desteklenir; boolean kabul edilmez |
| `world_id`, `map_id` | string | Boş olamaz |
| `name` | string | Boş veya yalnızca whitespace olamaz |
| `layout.orientation` | string | `flat_top` veya `pointy_top` |
| `layout.radius` | number | Sonlu ve sıfırdan büyük |
| `layout.origin.x/y` | number | Sonlu |
| `cells` | array | Boş olabilir; yalnızca mevcut hücreleri listeler |
| `cells[].q/r` | integer | Boolean olamaz; negatif değer geçerlidir |
| `cells[].terrain_id` | string | Boş olamaz |
| `cells[].is_walkable` | boolean | Zorunlu |
| `cells[].has_obstacle` | boolean | Zorunlu |
| `cells[].metadata` | object veya null | İç içe JSON değerleri içerebilir |

Tanınmayan alanlar reddedilir. Her hücrede `(q, r)` çifti harita içinde benzersiz olmalıdır. Hücrelerin bitişik olması gerekmez. Metadata dizileri immutable modelde tuple olarak tutulur; nesneler salt okunur kopyalara dönüştürülür. `null` ve boş nesne `{}` birbirinden farklıdır.

JSON nesnelerindeki yinelenen anahtarlar ve standart dışı NaN/Infinity sabitleri reddedilir. Dosya yükleme önce bütün içeriği doğrular, sonra tek bir immutable `HexMapDefinition` oluşturur. Dosya katmanı `HexWorld` veya `MapRegistry` üzerinde kayıt oluşturmaz.

## Python API

Laboratuvar kökünde:

```python
from pathlib import Path

from hex_world_lab.world.persistence import (
    load_map_file,
    save_map_file,
    serialize_map,
)

map_definition = load_map_file(
    Path("scenarios/maps/starting_valley.json")
)

# Yeni dosya oluşturur; hedef varsa hata verir.
save_map_file(map_definition, Path("my_map.json"), mode="create")

# Yalnızca açıkça istenirse mevcut dosyanın yerini alır.
save_map_file(map_definition, Path("my_map.json"), mode="replace")

json_text = serialize_map(map_definition)
```

`save_map_file` varsayılan olarak `create` modundadır. Geçici dosya hedefle aynı dizinde oluşturulur. Yeni dosya oluşturma, atomik hard-link işlemiyle mevcut hedefi ezmeden tamamlanır; değiştirme ise `os.replace` kullanır. Atomiklik garantisi dosya sistemi ve platform özelliklerine bağlıdır.

## Kapsam sınırı

Bu biçim yalnızca `HexMapDefinition` başlangıç verisini saklar. `HexWorldRuntime` alan override'ları, entity/NPC/kaynak nesneleri, oyuncu durumu ve oyun kayıtları bu dosyanın parçası değildir. Runtime kalıcılığı Aşama 3.7'de ayrı tasarlanacaktır.
