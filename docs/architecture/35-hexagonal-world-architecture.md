# Eldoria — Altıgen Dünya Mimarisi Teknik Sözleşmesi

**Durum:** Aşama 0 tasarım kararı. Henüz uygulanmış değildir.  
**Referans dal/commit:** `demo_eldoria` / `5e77ef0cd70d1bc439ef2eb0bd2d5b86302ef9fc`

## 1. Amaç ve değişmez sınırlar

Bu belge kare tabanlı yerel haritaları ve dünya konumlarını altıgen mekânsal modele taşımak için hedef sözleşmeyi tanımlar. Aşama 0'da yalnızca inceleme ve dokümantasyon yapılır. `Position`, `MapDefinition`, `LocalMapDefinition`, JSON içerikleri, hareket, çizim ve kayıt kodu değiştirilmez.

Korunacak kazanımlar: veri odaklı `content/demo_eldoria/` paketi, manifest üzerinden otomatik harita keşfi, JSON referans doğrulaması, harita kimlikleri, kaynak/NPC/görev içeriklerinin ayrılığı ve sürümlendirilmiş kayıt zarfı.

Feet, hücre başına mesafe, hareket puanı, hız, savaş menzili ve tur bütçesi bu sözleşmenin dışındadır.

## 2. Koordinat alanları ve tip güvenliği

### 2.1 Ortak geometri

Temel matematiksel değer `HexCoord(q, r)` olacaktır. İki alan da sıfır tabanlı tam sayıdır; bool, float, NaN ve sonsuz değerler reddedilir. Değer immutable, yapısal eşitlikli ve hash edilebilir olmalıdır. Aynı q/r çifti aynı koordinat değeridir.

HexCoord yalnızca geometri işlemlerini bilir: altı komşu, yönle öteleme, toplama/çıkarma ve altıgen uzaklık. Harita sınırı, geçilebilirlik, kimlik, piksel veya oyun kuralı bilmez.

### 2.2 Anlamsal koordinat türleri

Tek bir HexCoord matematiği kullanılır; fakat ham HexCoord her API'de serbestçe dolaşmamalıdır. Ayrı, runtime'da ayırt edilebilir sarmalayıcı türler önerilir:

- `WorldHexPosition`: dünya haritasındaki bölge hücresi.
- `LocalHexPosition`: belirli bir yerel haritanın içindeki hücre.
- `ScreenPoint` / `WorldPixelPoint`: yalnızca sunum katmanının kayan noktalı piksel koordinatları.

Yerel koordinatın geçerliliği `(map_id, LocalHexPosition)` bağlamında değerlendirilir. Aynı q/r başka bir haritada farklı hücreyi gösterir. Dünya koordinatı yerel hücre olarak, piksel noktası HexCoord olarak örtük biçimde kabul edilmez. Genel `core.domain.spatial.Position` korunur; fiziksel/serbest dünya uzayındaki konum ihtiyaçları için kalır.

### 2.3 Yön standardı — tek kaynak

Pointy-top axial yön sırası ve sabitleri:

| Yön | dq | dr | Karşı yön |
|---|---:|---:|---|
| EAST | +1 | 0 | WEST |
| NORTH_EAST | +1 | -1 | SOUTH_WEST |
| NORTH_WEST | 0 | -1 | SOUTH_EAST |
| WEST | -1 | 0 | EAST |
| SOUTH_WEST | -1 | +1 | NORTH_EAST |
| SOUTH_EAST | 0 | +1 | NORTH_WEST |

Yön enum'u ile yön offset tablosu tek canonical modülde tutulmalıdır. Komşuluk, opposite, geçiş doğrulama, yol bulma ve UI yön eşlemesi bu kaynaktan türetilir; ekran veya servis içinde ayrı yön listeleri tanımlanmaz. Karşı yön işlemi iki kez uygulandığında başlangıç yönünü vermelidir.

### 2.4 Temel işlemler

- `neighbor(c, d) = c + offset(d)`
- `add(a,b)=(a.q+b.q,a.r+b.r)`
- `subtract(a,b)=(a.q-b.q,a.r-b.r)`
- `distance(a,b)=max(|dq|, |dr|, |dq+dr|)`
- Eşdeğer formül: `(|dq|+|dr|+|dq+dr|)/2`

Mesafe yalnızca topolojik hücre adımı sayısıdır. Fiziksel ölçü, feet veya hareket maliyeti değildir.

## 3. Pointy-top piksel dönüşümü

Hex boyutu `s`, merkezden köşeye uzaklıktır. Yerel axial koordinatın harita piksel merkezine dönüşümü:

```text
pixel_x = s * sqrt(3) * (q + r/2)
pixel_y = s * 3/2 * r
```

Ters dönüşüm için piksel merkezine göre kesirli axial değer:

```text
q_fraction = (sqrt(3)/3 * pixel_x - 1/3 * pixel_y) / s
r_fraction = (2/3 * pixel_y) / s
```

Ters dönüşüm cube koordinatlarına geçerek `x=q, z=r, y=-x-z` invariantını koruyan cube-round algoritmasıyla yapılır. Sonuç tam sayı axial koordinata yuvarlanır; ardından ilgili haritanın geçerli hücre maskesinde olup olmadığı kontrol edilir. Maskede olmayan hücreye otomatik en yakın hücreye atlama yapılmaz.

Dönüşüm sırası: ekran pikseli → kamera/viewport ters dönüşümü → harita yerel pikseli → kesirli axial → cube rounding → LocalHexPosition → harita maskesi doğrulaması. Çizimde ters sıra uygulanır.

Kamera kaydırması dünya piksel koordinatına öteleme, yakınlaştırma ise merkez/viewport pivotuna göre tekdüze ölçek uygular. `ScaledRenderer` mevcut yüksek DPI mantıksal UI ölçeğidir; kamera zoom'u ile karıştırılmamalıdır. Fare seçimi aynı dönüşüm zincirini ters yönde kullanmalıdır. Piksel koordinatı oyun domain'ine yazılmaz.

## 4. Yerel harita topolojisi

Üç yaklaşımın karşılaştırması:

| Model | Bellek | İçerik hazırlama | Yol bulma / çizim | Düzensiz şekiller |
|---|---|---|---|---|
| Dikdörtgen sınır | Sınır içi hücreleri varsaymak ucuz; boşlukları ayrıca tutmak gerekir | Kare grid alışkanlığı kolay | Bounds kontrolü basit; tüm dikdörtgeni çizmek boş alan üretir | Delik ve girintiler için ek maske gerekir |
| Düzenli büyük altıgen | Yarıçapla hücre sayısı belirlenir: 1+3R(R+1) | Doğal altıgen alanı kolay | Komşular ve çizim basit | Mağara, kıyı, dar geçit için fazla kısıtlayıcı |
| Geçerli hücre maskesi | Hücre başına kayıt/set maliyeti O(N); yalnızca gerçek hücreler saklanır | Hücre seçimi biraz daha zahmetli; editör araçlarıyla desteklenebilir | Komşu maskede var mı kontrolü O(1) set ile; yalnızca mevcut hücre çizilir | En esnek; delik, kıyı, mağara, ada ve koridor desteklenir |

**Karar:** Geçerli hücre maskesi authoritative topoloji olacaktır. Her yerel harita, var olan axial koordinatlardan oluşan sonlu bir hücre kümesi taşır. Opsiyonel bounding box yalnızca editör/çizim optimizasyonudur; geçerlilik kararı değildir. Düzenli altıgen alan, aynı maskenin üretim kısayolu olabilir. Dikdörtgen bounds yalnızca editör çalışma alanı veya eski içerik dönüşüm girdisi olarak kalır.

Hücre verisi default terrain + hücre başına override biçiminde sıkıştırılabilir; ancak geçerli hücre kümesi açıkça tanımlanmalıdır. Bir hücrenin yokluğu ile var olan fakat geçilemeyen hücre ayrıdır.

## 5. Dünya modeli

Dünya haritasındaki her bölge `WorldHexPosition` taşır. Altıgen koordinat komşuluğu geometrik komşuluktur; tek başına seyahat izni değildir. Mevcut `WorldMap` lokasyon grafiği ve path API'si korunabilir; fakat lokasyon pozisyonu piksel tuple'ı yerine semantik dünya altıgen koordinatı olmalıdır.

Dünya haritası çizimi axial → pixel dönüşümünü kullanır. Dünya komşusu olmak ile harita geçişinin aktif/fiziksel olarak kullanılabilir olması ayrı doğrulamalardır. Aynı hücrede birden fazla bölgeye izin verilecekse ayrıca katman/realm tasarımı gerekir; Aşama 0 bunu varsaymaz.

## 6. Geçiş sözleşmesi

Her çıkış tanımı en az şu bilgileri taşır:

- `transition_id`, `source_map_id`
- `exit_direction` (altı yön enum'undan biri)
- `target_map_id`, `target_entry_direction` (exit'in karşı yönü)
- `source_cells`, `target_cells` (LocalHexPosition listeleri)
- `active`
- `traversal_mode`: `one_way` veya `bidirectional`

Bir geçiş yönü, source/target haritalarının hücre koordinatlarının birbirine eşit olmasını gerektirmez; yalnızca çıkış tarafının semantik yönünü ve hedef giriş yönünü belirtir. Kaynak ve hedef hücreler kendi haritalarının maskesinde bulunmalı ve geçilebilir olmalıdır. Çok hücreli geçişlerde hücre eşlemesi deterministik olmalıdır: eşit uzunluktaki sıralı çift listesi veya açık `cell_pairs` alanı kullanılmalı; keyfi min-distance seçimi yapılmamalıdır.

Çift yönlü geçişte hedef haritada ters kayıt bulunmalı; kaynak/hedef haritaları ve hücre eşlemeleri tersine çevrilmeli; yönler karşılıklı olmalıdır. Tek yönlü geçiş ters kayıt zorunluluğunu kaldırır. Devre dışı geçiş dünya komşuluğu olarak kalabilir ama oyuncu tarafından kullanılamaz.

Dünya komşuluğu: iki WorldHexPosition altı komşudan biriyle ayrılıyorsa geometrik ilişki. Fiziksel geçiş: aktif, doğrulanmış çıkış-giriş bağlantısı. İkisi aynı şey değildir.

## 7. Kare haritalardan dönüşüm

Kare gridin altıgene matematiksel olarak çevrilmesi, içerik tasarımının yerini tutmaz. İlk otomatik taslak için odd-r yatay offset koordinatından axial'e deterministik dönüşüm kullanılabilir:

```text
q = column - floor(row / 2)
r = row
```

Bu, eski dört cardinal komşuların axial komşu olmasını sağlar; ancak altıgen gridin ek çapraz komşulukları yeni kısa yollar açabilir. Dolayısıyla nihai topoloji ve geçilebilirlik elle doğrulanmalıdır.

Önerilen hibrit: eski her hücre/nesne için dönüşüm manifesti üret; oyuncu başlangıcı, NPC, landmark, kaynak, yapı, kapı, köprü ve geçişleri içerik bazında yeniden yerleştir; arazi/duvar gibi büyük alanları görsel ve erişilebilirlik kontrolüyle düzenle. Dönüşüm `old_map_id + old_x + old_y → new_map_id + q + r` eşlemesini kimlik bazında tutar. Çakışma, maskede olmayan hedef veya kayıp nesne varsa işlem hata verir; otomatik yakın hücreye taşıma yasaktır.

## 8. Kayıt uyumluluğu ilkeleri

Mevcut save envelope `rpg-game-save` v2'dir. Actor ve Social snapshot'larında Position x/y; Container snapshot'ında placement x/y/width/height bulunur. Core Entity Position, application actor position, NPC position ve dünya harita konumları aynı alan değildir.

Yeni save sürümü ayrı bir migration sınırıyla planlanmalıdır. Eski kare konumlar içerik paketiyle birlikte sürümlenmiş deterministik dönüşüm manifesti kullanılarak çevrilir. Save dosyası değiştirilmeden önce yedeklenir; migration yeni dosyaya yazılır, yeniden okunup doğrulanır ve ancak bundan sonra etkinleştirilir. Bilinmeyen harita, eksik eşleme, hücre çakışması veya maskede olmayan hedef açık uyumluluk hatası üretir. Eski dosya asla yerinde sessizce üzerine yazılmaz.

Migration sürüm/işlem kimliği ile idempotent olmalı; ikinci çalıştırma aynı hedef sonucu vermeli veya kaydın zaten dönüştürüldüğünü açıkça tanımalıdır. Position'ın tüm kullanımları harita hücresi sayılmamalıdır.

## 9. Etki alanı ve korunacak modüller

Doğrudan dönüşüm: spatial yeni değer nesneleri, map definition/loader, yerel harita topolojisi, hareket/pathfinding, MainScreen harita etkileşimi, world map koordinat/renderer, geçiş doğrulaması ve koordinat taşıyan persistence adapter'ları.

Uyarlama: content pack referans doğrulaması, actor/NPC/resource/object placement, camera, mouse hit testing, container placement, save migrations, map/world UI ve içerik authoring.

Korunması beklenen: ekonomi, inventory, recipe/production, tick/time scheduler, event transport, quest kimlikleri/graph, dialogue metinleri/kimlikleri, item/resource kimlikleri ve genel Position API'si (yalnızca gerçek fiziksel koordinat kullanımları). Bu modüller yalnızca konum API'sine doğrudan bağlıysa dar adaptör alır.

## 10. Aşamalı kabul kapıları

1. Aşama 0: mimari sözleşme, gerçek dosya/içerik envanteri, risk ve test planı.
2. Aşama 1: bağımsız geometri value object ve property testleri; oyun davranışı henüz taşınmaz.
3. Aşama 2: masked axial map model + JSON schema/loader; eski içerik paralel kalır.
4. Aşama 3: dünya koordinatları ve yönlü bağlantı doğrulaması.
5. Aşama 4: yerel hareket, altı komşuluk, engel ve pathfinding.
6. Aşama 5: Pygame pointy-top renderer, kamera ve fare seçimi.
7. Aşama 6: NPC/kaynak/nesne/etkileşim uyarlaması.
8. Aşama 7: save migration, içerik paketleri, uçtan uca regresyon ve eski içerik kapanışı.

Her aşama test ve kabul kapısından geçmeden sonraki aşamaya başlanmaz. Bu belge uygulamanın tamamlandığını iddia etmez.


## 11. Test ve kabul matrisi

| Aşama | Test grubu | Asgari kabul senaryoları |
|---|---|---|
| 1 | Geometri | Altı yön offset'i; her yönün opposite değeri; opposite(opposite(d))=d; komşuluk simetrisi; axial add/subtract; mesafe örnekleri ve simetrisi; aynı hücre mesafesi 0; koordinat tipi/immutability/hash; negatif q/r |
| 1 | Piksel matematiği | Hex center → pixel → axial round-trip; hücre merkezleri; altı kenar/vertex sınırında deterministik seçim; farklı hex size; sıfır/negatif size reddi |
| 2 | Harita topolojisi | Maskede var/yok hücre; blocked ile absent farkı; duplicate cell reddi; boş mask; negatif axial koordinat; farklı düzensiz maskeler; delik ve kopuk adalar |
| 2 | İçerik yükleme | JSON schema version; eksik/unknown alan; feature/landmark/transition hücrelerinin maskede olması; sadece yeni JSON haritası ekleyerek yükleme; mevcut paket loader izolasyonu |
| 3 | Dünya haritası | WorldHexPosition tip kontrolü; altı yönlü geometrik komşuluk; aynı hücre çakışma politikası; map ID benzersizliği; dünya konumlarının piksel değerleriyle karıştırılmaması |
| 3 | Geçişler | Altı yönün her biri; karşı yön eşleşmesi; iki yönlü reciprocal; tek yönlü geçiş; inactive geçiş; eksik hedef map; source/target hücrenin maskede olması; tek ve çok hücreli geçiş; hücre pair sırası; hatalı yön eşleşmesi |
| 4 | Hareket/pathfinding | Altı komşuya hareket; maskeden çıkışın reddi; engelli hücre; iki hücre arası shortest path; yeni diagonal shortcut testleri; unreachable target; disconnected mask; NPC movement; occupancy collision |
| 5 | Pygame | Pointy-top polygon çizimi; kamera pan; zoom; farklı viewport; DPI scaling ayrımı; fare hücre seçimi; hücre sınırı; maskede olmayan alan; seçilen cell ile renderer cell eşleşmesi |
| 6 | Actor ve nesne | Player/NPC aynı cell; NPC interaction; resource landmark link; object multi-cell occupancy; overlap; transfer/move; gate/bridge/structure passability |
| 7 | Persistence | Yeni axial save round-trip; eski v2 kare save migration; unknown map; mapping missing; invalid target cell; collision; backup retained; failed migration leaves original untouched; repeat migration idempotency; candidate load atomicity |
| 7 | Paket/regresyon | Yeni content package sadece JSON ile yüklenir; manifest map discovery; NPC/resource/quest ID referansları korunur; eski kare package migration path; ekonomi/inventory/production/time/quest/combat regresyonu |

### Matematiksel property testleri

- Her koordinat `c` ve yön `d` için `distance(c, neighbor(c,d)) == 1`.
- Her yön `d` için `neighbor(neighbor(c,d), opposite(d)) == c`.
- Her koordinat çifti `a,b` için `distance(a,b) == distance(b,a)`.
- `distance(a,a) == 0`; mesafe negatif olamaz.
- `distance(a,b) <= distance(a,c) + distance(c,b)`.
- Pixel round-trip, hücre merkezlerinde tam aynı axial hücreyi döndürür.
- Hücre maskesi dışındaki pixel hit-test sonucu geçersiz seçimdir; yakın hücreye sessiz snap yapılmaz.

### Regresyon koruma

Altıgen çalışması ekonomi, envanter, üretim, zaman simülasyonu, görev kimlikleri, diyalog ve savaş kurallarını değiştirmemelidir. İlgili mevcut test paketleri her aşamada çalıştırılır. Test komutunun çıktısı, test sayısı ve başarısızlık sayısı rapora eklenir; çalıştırılmayan test başarılı kabul edilmez.
