# Hex Oynanış İçeriği — Bağımlılık ve Veri Açığı Denetimi

**Durum:** Aşama 16.2.3 / Katman 3 teknik denetimi  
**Dal:** `experiment/map-cleanup`  
**Amaç:** Mevcut kare içerik sistemlerinin hex runtime'a taşınması için gerçek veri bağımlılıklarını ve eksik içerik noktalarını belirlemek.  
**Kısıt:** Kare `[x,y]` koordinatları axial `[q,r]` koordinatlarına otomatik çevrilmez. Bu belge hiçbir NPC, kaynak, pazar veya konteyner için yeni koordinat atamaz.

## 1. Mevcut hex dünya

`content/demo_eldoria/world.json` yedi axial haritayı tanımlar:

- `hex_forest_demo`
- `hex_clearing_demo`
- `hex_northeast_demo`
- `hex_northwest_demo`
- `hex_west_demo`
- `hex_southwest_demo`
- `hex_southeast_demo`

Dünya belgesinin kapsam metadatası `hex_maps_only` der. Bu veri bir köy/başlangıç alanı veya yerleşik NPC/pazar alanı tanımlamaz.

Mevcut `placements/*.json` dosyaları sahne nesneleri içindir: ağaç, çalı, kaya ve bitki gibi görsel/çarpışma nesneleri. Bunlar NPC, kaynak düğümü, pazar veya konteyner gameplay yerleşim kataloğu değildir.

Hex haritalarında bulunan landmark örnekleri:

- `hex_forest_demo`: `demo_ore_vein`
- `hex_clearing_demo`: `clearing_waystone`

`demo_ore_vein`, mevcut 22 kaynak düğümünün `node_id` veya `landmark_id` değerlerinden biri değildir. Bu nedenle mevcut kaynak verisine otomatik bağlanamaz.

## 2. Sistem bazında bağımlılık matrisi

| Sistem | Mevcut veri | Hex tarafındaki eksik | Sonuç |
|---|---|---|---|
| NPC | `npcs.json` içinde 4 NPC; dördü de `village_id` ve kare `[x,y]` konumunda | Hex axial NPC yerleşimi ve hex köy/başlangıç alanı yok | Yerleşim verisi olmadan NPC entegrasyonu tamamlanamaz |
| Kaynak | `resources.json` içinde 22 düğüm; 8 kare harita kimliğine dağılmış; her düğüm landmark'a bağlı | Mevcut hex landmark'ı kaynak düğümü kimliğiyle eşleşmiyor; diğer hex haritalarda kaynak yerleşimi yok | Kaynak düğümleri için açık axial yerleşim gerekir |
| Pazar | `starter_content.json` içinde 1 pazar: `village_inn`; `village_id`, `[20,23]` ve `innkeeper_mira` bağlantılı | Hex pazar konumu ve hex NPC yerleşimi yok | Pazar, NPC ve harita yerleşimi birlikte tasarlanmalı |
| Konteyner / dünya nesnesi | `WorldObjectPlacement` kare `world_id + location_id + x + y + width + height` kullanır | Hex axial footprint/occupancy yerleşim sözleşmesi yok | Kare placement tipi axial haritada kullanılamaz |
| Görev / diyalog | Görev ve diyalog akışları NPC kimliklerine ve etkileşim servislerine bağlanır | NPC'lerin hex konumu ve hex etkileşim çözümleyicisi yok | NPC yerleşimi ve spatial interaction API sonrasında taşınabilir |
| Kayıt / yükleme | `ActorSnapshot` legacy kare `location_id + Position` bilgisini saklar; `GameApplication` kare harita kataloğunda doğrular | Hex runtime/entity konumu ana `SaveDocument` içinde saklanmıyor | Hex snapshot ve sürümlü restore sözleşmesi ayrıca tasarlanmalı |
| UI | Ana ekran, dünya haritası ve HUD artık açık legacy spatial API'sini kullanır; hex ekranı runtime'ı kullanır | Hex NPC/kaynak/pazar/konteyner arayüz bağları henüz yok | UI konum okuma sınırı taşındı; gameplay içeriği bekliyor |

## 3. Kanıtlanmış içerik sayıları

- NPC: 4 kayıt; tümü `village_id` üzerinde.
- Kaynak düğümü: 22 kayıt; kare konum kimlikleri `forest_id`, `south_forest`, `west_forest`, `east_forest`, `north_mine`, `south_mine`, `west_mine`, `east_mine`.
- Pazar: 1 kayıt; `village_inn`, `village_id`, `innkeeper_mira`.
- Hex dünya: 7 harita.
- Hex sahne placement belgeleri: `hex_forest_demo` ve `hex_clearing_demo`; içerikleri çevresel sahne nesneleri.

Bu sayılar mevcut depo içeriğinin denetimidir; yeni içerik veya koordinat önerisi değildir.

## 4. Önerilen teknik sıra

1. NPC, kaynak, pazar ve konteyner için kare placement tiplerinden ayrı bir axial gameplay placement sözleşmesi tanımla. Asgari alanlar: `entity_id`, `map_id`, `q`, `r`; gerekirse tür/footprint/interaction metadata.
2. Placement kataloğunu içerik kimliklerine bağla. Her referansın gerçekten var olduğunu, haritanın hücre maskesinde bulunduğunu, tekrar eden entity placement olmadığını ve occupancy çakışmalarını doğrula.
3. Şema ve doğrulayıcıyı boş/örnek olmayan test verisiyle doğrula; mevcut kare içeriklerini dönüştürme.
4. Oyun tasarımıyla axial koordinatları açıkça belirlendikten sonra NPC ve kaynak yerleşimlerini tek tek ekle.
5. Pazar yerleşimini, bağlı NPC yerleşimiyle birlikte tanımla.
6. Konteyner/dünya nesneleri için hex footprint ve occupancy davranışını ayrı sözleşmeyle taşı.
7. Görev/diyalog etkileşimlerini NPC kimliği + hex spatial context üzerinden bağla.
8. Hex runtime snapshot/restore belgesini sürümlü biçimde ekle. Eski kare kayıtları olduğu gibi koru; otomatik koordinat dönüşümü veya sessiz relocation yapma.

## 5. Açık engeller ve kapsam dışı kararlar

Aşağıdakiler teknik olarak varsayılamaz; oyun içeriği/tasarım kararı gerektirir:

- Hex dünyasında köyün/başlangıç alanının hangi harita olacağı.
- Dört NPC'nin axial harita ve hücre yerleşimleri.
- 22 kaynak düğümünün hangi bölümünün hex dünyaya taşınacağı ve her düğümün axial konumu.
- Pazarın hangi haritada ve hangi hücrede bulunacağı.
- Konteyner ve diğer etkileşimli nesnelerin axial footprint/konumları.
- Eski kare kayıtların saklanması, yalnızca kare modunda açılması veya kullanıcıya açık kurtarma akışı.

Bu kararlar netleşmeden mevcut kare içerikleri silinmez, eski dokuz kare harita azaltılmaz ve demo dalına entegrasyon yapılmaz.

## 6. Kabul ölçütleri

- Her hex gameplay entity için tek, açık axial placement kaydı.
- Hiçbir kare koordinat otomatik dönüştürülmemiş.
- Tüm referanslar içerik kimliği üzerinden doğrulanmış.
- Occupancy ve footprint çakışmaları yükleme sırasında yakalanıyor.
- NPC/kaynak/pazar/konteyner etkileşimleri runtime spatial context kullanıyor.
- Hex runtime save/load testleri round-trip doğrulaması yapıyor.
- Eski kare kayıtlar için açık, kayıpsız ve belgelenmiş politika bulunuyor.
- Pytest, Ruff, paketleme ve Linux/Windows CI başarılı.
