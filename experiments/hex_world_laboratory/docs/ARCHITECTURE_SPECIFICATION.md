# Hex World Laboratory — Mimari Sözleşme

> **Durum:** Taslak sözleşme — aşama bazında kesinleştirilecek  
> **Üst belge:** [HEX_WORLD_LAB_MASTER_PLAN.md](HEX_WORLD_LAB_MASTER_PLAN.md)  
> **Kapsam:** Laboratuvarın hedef mimari sınırları ve veri sözleşmeleri

## 1. Amaç

Bu belge, Hex World Laboratory içinde geliştirilecek sistemlerin sorumluluklarını, veri akışını ve birbirleriyle kuracağı ilişkileri tanımlar. Henüz uygulanmış kodun açıklaması değildir. Gerçek uygulama, ilgili aşama planı ve kullanıcı onayı sonrasında bu sözleşmeye göre geliştirilir.

Bu belgede kesinleşmemiş teknik seçimler açıkça **AÇIK KARAR** olarak işaretlenir. Bunlar varsayılan değer gibi ele alınamaz.

## 2. Tasarım ilkeleri

1. Hex dünya topolojisi canon'dur.
2. Hücre adresi, sürekli fiziksel konum ve ekran konumu farklı kavramlardır.
3. Geometri ve simülasyon çekirdeği Pygame'den bağımsız tutulur.
4. Dünya verisi, simülasyon ve çizim birbirinin sorumluluğunu üstlenmez.
5. Çarpışmanın nihai doğruluğu gerçek hex geometriye dayanır.
6. Optimizasyon, doğruluk referansının yerine geçmez.
7. Her dönüşüm açık parametrelerle tanımlanır ve test edilir.
8. Katmanlar arasında döngüsel bağımlılık kurulmaz.

## 3. Koordinat ve uzay sözleşmesi

### 3.1 Hex hücre uzayı

Hücreler axial koordinat çifti `(q, r)` ile adreslenir. Bu adres, harita kimliğiyle birlikte değerlendirilir; tek başına tüm dünya genelinde benzersiz olduğu varsayılmaz.

Cube koordinatları, axial koordinatlarla matematiksel işlemleri desteklemek için türetilebilir. Cube koordinatlarının saklanıp saklanmayacağı henüz kararlaştırılmamıştır.

### 3.2 Dünya uzayı

`WorldPosition(x, y)`, dünya düzlemindeki sürekli ve kesirli konumu temsil eder. Hareketli varlıkların fiziksel konumunun temel kaynağıdır. Hücre sınırından geçişte konum hücre merkezine yuvarlanmaz.

Dünya biriminin piksel, metre benzeri soyut birim veya başka bir ölçek olması **AÇIK KARAR**dır. Ölçek, geometri aşamasında belirlenip tek sözleşme halinde belgelenmelidir.

### 3.3 Ekran uzayı

`ScreenPosition(x, y)`, kamera ve viewport dönüşümünden sonra elde edilen ekran koordinatıdır. Yalnızca input/çizim sınırında kullanılır; fiziksel konum olarak saklanmaz.

### 3.4 Dönüşümler

Aşağıdaki dönüşüm sorumlulukları ayrı ve test edilebilir olmalıdır:

- Axial hücre adresi → dünya hücre merkezi.
- Dünya konumu → karşılık gelen axial hücre.
- Hex hücre adresi → köşe ve kenar geometrisi.
- Dünya konumu → ekran konumu.
- Ekran konumu → dünya konumu.

Dönüşümlerde kullanılacak yönelim, başlangıç açısı, hex boyutu, origin ve viewport parametreleri örtük sabitler olarak farklı modüllere dağıtılamaz.

### 3.5 Sınır davranışları

Hex kenarı/köşesi üzerindeki noktaların hücre ataması için deterministik tie-break kuralı tanımlanmalıdır. Harita dışı konum, boş hücre ve geçersiz harita kimliği davranışları da açıkça belirtilmelidir. Bu kurallar ilgili geometri ve dünya aşamalarında karara bağlanır.

## 4. Hedef katmanlar ve sorumlulukları

| Katman | Sorumluluk | Bağımlılık sınırı |
|---|---|---|
| Geometry | Axial/cube matematiği, merkez, köşe, kenar, mesafe ve dönüşüm | Pygame ve oyun içeriği bilmez |
| World | Harita kimliği, hücre verisi, sınırlar ve topoloji | Ekran koordinatı bilmez |
| Movement | Hareket niyeti, hız, ivme ve konum entegrasyonu | Kamera/render bilmez |
| Physics | Gövde, çarpışma, engel çözümü ve hareket kısıtları | Görev/ekonomi kuralları bilmez |
| Spatial | Yakınlık sorgusu ve aday indeksleme | Nihai geometri/çarpışma kararını vermez |
| Camera | View transform, takip, zoom ve viewport | Dünya state'ini değiştirmez |
| Rendering | Hücre/varlık çizimi, katmanlama ve debug çizimleri | Simülasyon state'ini değiştirmez |
| Entities | Oyuncu/NPC/kaynak kimliği ve konum bileşenleri | Kendi geometri standardını üretmez |
| Interaction | Hedef seçimi ve etkileşim menzili sorguları | Ayrı koordinat sistemi tanımlamaz |
| Simulation | Tick sırası ve sistem orkestrasyonu | Katmanların iç işleyişini tek yerde kopyalamaz |
| Diagnostics | Ölçüm, debug overlay, kayıt ve teşhis | Üretim mantığına gizli yan etki eklemez |

## 5. Veri sahipliği

- Dünya geometrisinin parametreleri tek bir yetkili yapıdan okunmalıdır.
- Hücre verisi ile hücrenin geometrik adresi ayrı kavramlardır.
- Hareketli varlığın fiziksel konumu Movement/Entity sözleşmesi kapsamında tek bir yetkili state olarak tutulmalıdır.
- Fizik, hareket state'ini kontrollü biçimde güncelleyebilir; render yalnızca okuyabilir.
- Kamera transformu dünya state'ine yazamaz.
- Spatial index, asıl entity/world state'inden türetilmiş yardımcı veridir. Kaynak state değişince indeks güncellenmeli veya yeniden kurulmalıdır.
- Debug verisi, oyunun doğruluk kaynağı olamaz.

## 6. Hareket ve fizik veri akışı

Hedef veri akışı:

1. Input adaptörü kullanıcı girdisini hareket niyetine dönüştürür.
2. Movement sistemi niyeti hız/yön/ivme kurallarına göre işler.
3. Physics sistemi hareket önerisini engel ve sınırlarla çözümler.
4. Sonuç fiziksel WorldPosition state'ine uygulanır.
5. World/Spatial katmanları gerekli hücre ve indeks bilgilerini günceller.
6. Camera ve Rendering güncel state'i okuyarak görüntüler.

Bu akışın kesin tick sırası, sabit zaman adımı kararı ve interpolasyon yöntemi simülasyon aşamasında kararlaştırılır.

## 7. Çarpışma sözleşmesi

- Hex hücre polygonları ve kenarları authoritative geometri kaynağıdır.
- AABB, bounding circle veya grid yalnızca broadphase aday toplama için kullanılabilir.
- Nihai çarpışma/temas kararı uygun gerçek şekil geometrisiyle doğrulanır.
- Hareketli varlığın görsel sprite sınırı ile fiziksel collider'ı ayrı tanımlanır.
- Foot-anchor/zemin temas noktası, sprite merkeziyle karıştırılmaz.
- Çarpışma çözümü duvar boyunca kayma, köşe teması ve birden fazla temas durumlarını ele almalıdır.

Collider şekli, sweep yöntemi ve temas toleransları **AÇIK KARAR**dır; aşama 5'te analiz ve testle seçilir.

## 8. Kamera ve render sözleşmesi

Kamera, world/screen dönüşümünün tek yetkili uygulama noktası olmalıdır. Fare seçimi de ters dönüşüm üzerinden dünya koordinatına ulaşmalıdır. Zoom, pan ve viewport değişimleri fiziksel state'i etkilemez.

Rendering:
- Geometri parametrelerini Geometry/World sözleşmesinden alır.
- Sprite foot-anchor'ını entity transformuyla eşler.
- Gerekli depth/y-sort kuralını uygular.
- Görsel interpolasyon yapabilir; ancak interpolasyon fiziksel state'e yazılmaz.

## 9. Spatial indexing sözleşmesi

Spatial index bir optimizasyon katmanıdır; dünya topolojisi değildir. Hex komşuluğu ve gerçek geometri her zaman doğruluk kaynağı kalır.

Aday yöntemler:
- Doğrudan hex komşuluk sorgusu.
- Spatial hash veya yardımcı grid.
- Kare alt bölümlere ayırma.

Yöntem seçimi benchmark sonuçlarına göre yapılır. Aday sorgusunun doğruluğu brute-force referansıyla karşılaştırılmalıdır. İndeksin yanlış/eksik aday döndürmesi kabul edilemez.

## 10. Açık mimari kararlar

Aşağıdakiler ilgili aşamalarda ADR ile kesinleştirilecektir:

- Flat-top veya pointy-top yönelimi.
- Hex boyutu ve dünya birimi.
- Origin ve harita koordinat yönleri.
- Axial/cube dönüşüm ve yön indeks sırası.
- Hücre sınırındaki tie-break kuralı.
- Harita sınırı ve boş hücre davranışı.
- WorldPosition veri tipi ve hassasiyet yaklaşımı.
- Fixed timestep / değişken timestep politikası.
- Collider şekli ve temas çözümü.
- Foot-anchor sözleşmesi.
- Kamera zoom ve viewport modeli.
- Render depth/y-sort politikası.
- Spatial index yöntemi.
- Entity/world geçiş ve kimlik politikası.

## 11. Mimari kabul kontrolü

Bir katman kabul edilmeden önce:
- Sorumluluğu ve sahip olduğu state açıkça tanımlanmış olmalı.
- Komşu katmanlarla veri alışverişi belgelenmiş olmalı.
- Pygame bağımlılığı yalnızca gerekli adaptörlerde bulunmalı.
- Döngüsel bağımlılık olmamalı.
- Unit/integration testleri bulunmalı.
- Hata ve sınır davranışları belgelenmiş olmalı.
- İlgili ADR'ler güncel olmalı.

Bu sözleşme, laboratuvarın gerçek bulgularıyla aşama bazında güncellenebilir; ancak güncelleme önce gerekçe ve kullanıcı onayı gerektirir.
