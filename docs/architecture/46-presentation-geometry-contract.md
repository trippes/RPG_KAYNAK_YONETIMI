# Aşama 8.4 — Konum ve Görsel Metadata Geometri Sözleşmesi

## Durum

Aşama 8.4 kapsamında tanımlanmıştır. Bu belge, mevcut Pygame sunum hattının gerçek tüketim biçimlerini esas alır. Amaç yeni bir dünya koordinat sistemi veya fizik motoru kurmak değil; var olan alanların birimlerini, referans noktalarını ve sınırlarını açık hâle getirmektir.

## 1. Koordinat uzayları ve birimler

| Alan | Birim / uzay | Referans | Açıklama |
|---|---|---|---|
| Hex placement `q`, `r` | Tam sayı axial hücre koordinatı | İlgili hex map | Hücre kimliğidir; piksel değildir |
| `offset_x`, `offset_y` | Dünya sunum pikseli | Hücre merkezi | Placement'ı hücre merkezinden yatay/dikey kaydırır |
| Asset `width`, `height` | Kaynak PNG pikseli | Görsel dosya | İkisi de 0 ise mevcut sözleşmedeki kaynak boyutu sentinel'idir; tek başına sıfır geçersizdir |
| `scale` | Boyutsuz çarpan | Kaynak PNG ölçüsü | Kaynak dosyayı değiştirmez; çizim boyutunu belirler |
| `anchor` | Normalize koordinat [0, 1] | Sprite dikdörtgeni | (0,0) sol üst, (1,1) sağ alt |
| `collision`, `collision_box` | Yerel dünya pikseli AABB | Ground anchor | x/y negatif olabilir; genişlik/yükseklik pozitif olmalıdır |
| `depth_offset` | Dünya sunum pikseli | Ana depth çizgisi | Ana sıralama noktasına eklenen ince ayardır |
| `footprint` | Pozitif tam sayı map-cell boyutu | Map hücre modeli | Piksel veya sprite boyutu değildir |
| `layer` | Kontrollü sembolik değer | Render katman sırası | underlay, ground, canopy, overlay |

Placement ofsetleri kamera zoom'u ile birlikte ölçeklenir. `q/r` hücre koordinatları zoom veya sprite scale ile çarpılmaz. Kaynak PNG ölçüsü, ölçekli çizim ölçüsü ve collision geometrisi birbirinden bağımsız kalır.

## 2. Anchor ve pivot

Asset `anchor` değeri sprite dikdörtgenine göre normalize edilmiş iki bileşenli bir referans noktasıdır. Genel sahne nesnelerinde bu nokta sprite'ın yerleştirildiği ground/presentation anchor olarak kullanılır; aynı zamanda sprite dikdörtgeninin bu noktaya göre çizilmesini sağlar.

Bu nedenle mevcut genel asset modelinde ayrı bir transform pivot alanı yoktur. Bu aşamada yeni bir `pivot` alanı eklenmemiştir: gerçek runtime tüketicisi tek anchor kullanmaktadır ve veriyi iki alana bölmek davranış değişikliğine yol açardı.

Ağaçlar için mevcut özel `TreeSkeleton` adaptörü zaten iki ayrı normalize referans tanımlar:
- `ground_anchor`: PNG'nin zemin/yerleşim noktası.
- `depth_anchor`: ağacın ön/arka sıralamasını belirleyen gövde/zemin derinlik çizgisi.

Ağaç çizimi ground anchor'a, ağaç depth hesabı ise skeleton depth anchor'a dayanır. Ağaç rig/atlas varsayılanı kapalı kalır; bu sözleşme PNG tabanlı mevcut çizimi değiştirmez.

Anchor bileşenleri sonlu sayısal değer olmalı ve 0–1 aralığında bulunmalıdır. Anchor collision kutusu değildir ve collision alanını otomatik ölçeklendirmez.

## 3. Kaynak boyutu ve Draw Scale

Kaynak PNG genişliği/yüksekliği asset metadata'sındaki iki değerle temsil edilir:
- `width = 0` ve `height = 0`: kaynak PNG boyutunu dosyadan çöz.
- İkisi de pozitif: metadata boyutları kaynak PNG ile eşleşmelidir.
- Yalnızca birinin sıfır olması geçersizdir.

Draw scale için teknik aralık `0.01 <= scale <= 8.0` olarak sabitlenmiştir. Değer sonlu ve pozitif olmalıdır. Bu aralık içerik hatasıyla yanlışlıkla sıfıra yakın veya aşırı büyük sprite üretimini engeller.

Çizim boyutu:

```text
visual_width  = source_width  * asset.scale
visual_height = source_height * asset.scale
screen_size   = visual_size   * camera_zoom
```

PNG dosyasının kendisi yeniden boyutlandırılmaz. Renderer'ın ölçekli yüzey cache'i asset kimliği ve hedef piksel boyutlarını anahtar olarak kullanmaya devam eder. Collision kutusu draw scale'den otomatik türetilmez.

## 4. Placement konumu ve ofset

Mevcut hex placement şemasında `q/r` ilgili haritanın axial hücresini seçer. `offset_x/y` ise o hücrenin ekrandaki/dünyadaki merkezine göre yerel dünya-piksel farkıdır:

```text
anchor_x = cell_center_x + offset_x
anchor_y = cell_center_y + offset_y
```

Kamera zoom'u bu ofseti sunum sırasında ölçekler. Ofsetin işareti serbesttir; negatif değerler geçerlidir. Değerler boolean, NaN veya sonsuz olamaz.

Bu sözleşme yalnızca mevcut hex placement modelini tarif eder. Kare haritaların kendi x/y koordinat ve yerleşim modeli korunur; kare haritaya axial q/r zorlanmaz.

## 5. Collision ve footprint

Collision kutusu yerel dünya-piksel AABB'sidir: `(x, y, width, height)`. x/y ground anchor'a göredir; negatif x/y, kutunun anchor'ın soluna veya üstüne uzanması anlamına gelir. Genişlik ve yükseklik sonlu ve kesinlikle pozitif olmalıdır. Collision yokluğu `null` ile ifade edilir; sıfır alanlı kutu collision yokluğu yerine kullanılamaz.

Önemli mevcut-runtime sınırı: `HexWorldView` şu anda collision kutusunun geometrisini oyuncu hareketinde alt-hücre çarpışması olarak kullanmaz. Kutunun veya asset collision varsayılanının bulunması, placement'ın axial hücresinde mevcut occupancy katmanına bir bloklayıcı kaydedilmesini sağlar. Dolayısıyla mevcut oyun davranışı hücre tabanlıdır; bu metadata doğrulaması fizik motoru veya yeni hassas çarpışma davranışı eklemez.

`footprint` pozitif tam sayı map-cell boyutlarıdır; sprite piksel ölçüsü değildir. Mevcut hex blocker kaydı yalnızca placement'ın `q/r` hücresini işaretler; footprint'i genişletip birden fazla hücreyi bloke etmez. Footprint'in occupancy üzerinde çok hücreli etkisi ayrı bir runtime kararı gerektirir ve bu aşamada yapılmamıştır.

Asset `collision` varsayılanı ve placement `collision_box` override'ı birbirinden bağımsızdır. Placement kutusu varsa o örneğin collision metadata'sı olarak saklanır; yoksa asset varsayılanı blocker var/yok kararında kullanılır. İkisi de yoksa placement için blocker kaydı üretilmez.

## 6. Depth ve layer

Render katmanları ve sıraları tek yerde tanımlıdır:

| Layer | Sıra |
|---|---:|
| underlay | 0 |
| ground | 1 |
| canopy | 2 |
| overlay | 3 |

Önce layer sırası, sonra nesnenin depth/Y değeri kullanılır. Genel sprite nesnesinde ana depth referansı world anchor Y değeridir. Ağaçlarda `TreeSkeleton.depth_y` özel depth anchor'ı ve kaynak sprite ölçüsünü kullanır. Asset ve placement ince ayarları toplanır:

```text
effective_depth_offset = asset.depth_offset + placement.depth_offset
```

Bu offset dünya pikseli birimindedir ve zoom ile ölçeklenir; ana depth/Y-sort noktasının yerini almaz.

Aynı layer ve depth değerinde deterministik ikincil sıralama korunur: map q/r, drawable türü ve object/landmark kimliği. Oyuncu–ağaç ön/arka sıralamasının kabul edilen davranışı değişmez.

## 7. Uygulanan kod sözleşmesi

- `game_ui/assets/asset_definition.py`: Draw scale sınırları; anchor normalizasyonu; collision AABB pozitif alan ve sonlu sayı doğrulaması.
- `game_ui/world_rendering/scene_object.py`: ortak layer sırası; placement offset/depth finite doğrulaması; axial q/r ve footprint tam sayı kuralları; collision AABB doğrulaması; render nesnesi anchor/visual geometry doğrulaması.
- `game_ui/hex_world_view.py`: mevcut sıralama davranışını değiştirmeden ortak layer sırası sabitini tüketir.

Şema sürümü 1 korunmuştur. Mevcut JSON alan adları ve demo değerleri değiştirilmemiştir. Anchor ve pivot alanları bölünmemiş; PNG, harita, kamera, hareket, occupancy ve renderer algoritmaları yeniden tasarlanmamıştır.

## 8. Bilinçli olarak ertelenen işler

- Sprite transform pivot'u ile ground anchor'ı genel asset şemasında ayrı alanlara ayırmak.
- Collision AABB'lerini hücre tabanlı occupancy yerine hassas oyuncu çarpışmasında kullanmak.
- Footprint'i birden fazla hex/kare hücreye genişleten occupancy davranışı.
- Placement override olarak scale/anchor eklemek.
- Yeni editor UI, önizleme veya yerleştirme araçları.

Bu işler mevcut 8.4 hedefi için gerekli değildir ve ayrı tasarım/uyumluluk kararı olmadan eklenmemelidir.
