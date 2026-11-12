# Eldoria — Altıgen Harita İçerik Hazırlama Rehberi

**Uygulanan yerel harita biçimi:** schema_version 2  
**Geometri:** pointy_top axial (q,r)  
**Content package manifest:** schema_version 1

Çalışan tam örnek: content/demo_eldoria/maps/hex_forest_demo.json. Bu dosya yalnızca test/demo içeriğidir ve başlangıç haritası değildir.

## Örnek JSON
    {
      "schema_version": 2,
      "map_id": "hex_forest_demo",
      "name": "Altıgen Orman",
      "geometry": {"type":"hex_axial","orientation":"pointy_top","coordinate_system":"axial"},
      "terrain_ids": ["grass","forest_floor","water"],
      "default_terrain": "grass",
      "valid_cells": [[0,0],[1,0],[0,-1],[-1,0],[3,2]],
      "cell_overrides": [{"q":0,"r":-1,"terrain":"water","blocked":true}],
      "features": [{"id":"river","type":"river","cells":[[0,-1]]}],
      "landmarks": [{"id":"old_tree","name":"Yaşlı Ağaç","position":[-1,0]}],
      "transitions": [{"id":"exit","source_cells":[[0,0]],"exit_direction":"east","target_map_id":"future_map","target_entry_direction":"west","traversal_mode":"one_way"}]
    }

## Alanlar ve doğrulama
- geometry.type yalnızca hex_axial; orientation yalnızca pointy_top; coordinate_system yalnızca axial.
- terrain_ids izin verilen arazi kimliklerini listeler. default_terrain ve override terrain bu listede bulunmalıdır.
- valid_cells gerçek topolojidir. Her koordinat tam olarak [q,r] ve tam sayı olmalıdır.
- cell_overrides her koordinatı en fazla bir kez tanımlar; yalnızca valid_cells içindeki hücrelere uygulanır.
- blocked true hücrenin varlığını silmez; yalnızca geçiş engelini belirtir.
- features benzersiz ID, type ve hücre listesi taşır.
- landmarks benzersiz ID, ad, konum ve opsiyonel resource_node_id taşır.
- transitions kaynak hücreleri, altı yönden çıkış yönünü, hedef map ID'sini ve opsiyonel hedef giriş bilgisini taşır. Hedef haritanın varlığı bu aşamada aranmaz.

Negatif q/r geçerlidir. Bool, float ve string koordinatlar reddedilir. Duplicate ID/koordinat, boş maske, bilinmeyen alan, bilinmeyen terrain, yanlış geometri ve maske dışı feature/landmark/transition kaynakları yükleme hatasıdır. Hata mesajı dosya yolunu ve ilgili alanı/koordinatı belirtir.

Kopuk hücre adaları ve delikler geçerlidir. Bağlantılılık, hareket, pathfinding, fiziksel mesafe ve renderer doğrulaması bu aşamanın kapsamı değildir.
