# Eldoria — Altıgen Harita İçerik Hazırlama Rehberi

**Durum:** Hedef içerik sözleşmesi taslağı; mevcut loader henüz bunu desteklemez.  
Mevcut kare `map-authoring.md` sözleşmesi Aşama 0'da değiştirilmemiştir.

## 1. Paket ilkeleri

Altıgen haritalar mevcut `content/<package_id>/maps/` paket düzeninin devamı olarak tasarlanır. Manifest bir harita klasörünü işaret eder; loader JSON dosyalarını otomatik keşfeder. Yeni harita eklemek için Python koduna veya merkezi harita listesine ihtiyaç duyulmamalıdır.

Harita ID'leri kararlı kalmalıdır. NPC, resource, quest, market ve save referansları koordinat yerine mümkün olduğunca map/entity ID kullanmalıdır.

## 2. Koordinat standardı

- Geometri: axial `(q,r)`.
- Görsel yönelim: pointy-top.
- Tam olarak altı komşu yönü vardır.
- q/r tam sayıdır; bool ve float kabul edilmez.
- Koordinatlar sıfır tabanlıdır; negatif axial değerler geçerlidir.
- Yerel hücre koordinatı yalnızca kendi `map_id` bağlamında anlamlıdır.
- Dünya bölge koordinatı ile yerel harita hücre koordinatı aynı tür olarak kullanılmaz.
- Piksel koordinatları JSON gameplay hücre alanlarında tutulmaz.

| direction | dq | dr |
|---|---:|---:|
| east | +1 | 0 |
| north_east | +1 | -1 |
| north_west | 0 | -1 |
| west | -1 | 0 |
| south_west | -1 | +1 |
| south_east | 0 | +1 |

Karşı yönler: east/west, north_east/south_west, north_west/south_east.

## 3. Harita topolojisi: geçerli hücre maskesi

Harita dikdörtgen veya düzenli altıgen olmak zorunda değildir. Authoring verisinin authoritative bölümü geçerli axial hücre kümesidir. Haritada bulunmayan koordinat ile var olan fakat engelli koordinat farklıdır.

Önerilen gelecek şema (örnektir, mevcut loader tarafından kabul edilmez):

```json
{
  "schema_version": 2,
  "map_id": "mistwood",
  "name": "Sisli Orman",
  "geometry": {
    "layout": "pointy_top",
    "coordinate_system": "axial",
    "shape": "masked",
    "valid_cells": [[0,0], [1,0], [0,1], [1,-1], [2,-1]]
  },
  "terrain": {
    "default_tile": "grass",
    "overrides": []
  },
  "starting_cell": null,
  "blocked_cells": [],
  "features": [],
  "landmarks": [],
  "transitions": [],
  "world_position": {"q": 0, "r": 0}
}
```

`valid_cells` tek gerçek topoloji kaynağıdır. Opsiyonel bounds, editör/performans metadata'sıdır; hücrenin varlığını belirlemez. Terrain override ve blocked hücreler geçerli hücrelere referans vermelidir. Harita şekli düzensiz olabilir: kıyı, mağara, ada, nehir kıvrımı, dar geçit veya zindan.

## 4. Arazi, engel ve nesne hücreleri

Her feature, landmark, NPC, resource ve geçiş hücresi aynı valid-cell kontrolünden geçer. Geçilemezlik, hücrenin haritada bulunmamasıyla karıştırılmaz.

Büyük nesneler `width × height` kare footprint ile temsil edilmemelidir. Gelecek model, nesnenin kapladığı açık hücre kümesini axial koordinatlarla tanımlar. Nesne hücresi geçerli olmalı, overlap kuralları tek bir occupancy servisi tarafından uygulanmalıdır.

Resource node kimliği, landmark kimliği ve map kimliği korunur. Kaynak miktarı, yenilenme, toplama süresi ve ekonomi verileri geometri şemasına taşınmaz.

## 5. Haritalar arası geçiş

Gelecek transition kaydı en az:
- `id`, `source_map_id`, `exit_direction`
- `target_map_id`, `target_entry_direction`
- `source_cells`, `target_cells`
- `active`, `traversal_mode`

alanlarını taşır. Hedef giriş yönü çıkış yönünün karşı yönüdür. İki yönlü bağlantıda hedef haritada ters kayıt bulunur ve hücre eşlemesi tersine çevrilir. Tek yönlü çıkış için reciprocal kayıt zorunlu değildir. Her haritanın altı yönünün tamamını kullanması gerekmez.

Dünya axial komşuluğu, oyuncunun geçebileceği bir kapı/çıkış olduğu anlamına gelmez. Fiziksel geçiş ayrıca aktif ve doğrulanmış olmalıdır.

## 6. Görsel metadata

Gameplay koordinatı q/r olarak kalır. Renderer, pointy-top axial merkezini piksele çevirir. Görsel sprite anchor/pivot bilgisi gameplay hücresinden ayrı metadata olmalıdır. Kamera pan/zoom ve ekran DPI ölçeği ayrı dönüşüm katmanlarıdır.

Fareyle seçim, pikseli axial kesirli koordinata geri dönüştürür, cube-round uygular ve valid-cell maskesini kontrol eder. Maskede olmayan noktada seçim yoktur; en yakın hücreye sessizce snap edilmez.

## 7. İçerik doğrulama kuralları

Loader şu kontrolleri yapmalıdır:
1. Schema version ve zorunlu alanlar.
2. Benzersiz map/feature/landmark/transition ID'leri.
3. Axial koordinatların tam sayı olması.
4. Hücre koordinatlarının valid_cells içinde olması.
5. NPC/resource/market/quest referanslarının mevcut map ve entity ID'lerine bağlanması.
6. Transition source/target hücrelerinin ilgili haritalarda bulunması.
7. Yön/karşı yön eşleşmesi.
8. Bidirectional reciprocal kayıt ve ters hücre eşlemesi.
9. Büyük nesne occupancy çakışmaları.
10. Tek başlangıç haritası/hücresi kuralı.

İçerik hatası yükleme sırasında açıkça reddedilir; geçersiz hücre başka bir hücreye otomatik taşınmaz.

## 8. Mevcut içerikten geçiş

Mevcut `docs/content/map-authoring.md` kare schema v1 sözleşmesidir. Bu rehber onun yerine geçmez; uygulama aşamasında yeni schema ayrı sürümlendirilir. Mevcut dokuz haritanın koordinatları Aşama 0'da değiştirilmemiştir.

Dönüşüm sırasında map_id, NPC/resource/landmark/quest kimlikleri korunur. Her eski x/y hücresi ve yerleştirilmiş nesne için axial eşleme manifesti tutulur. Otomatik odd-r→axial dönüşüm yalnızca taslak üretir; geçiş koridorları, nehir/köprü, köy yapıları ve kritik etkileşim hücreleri içerik bazlı gözden geçirilir.
