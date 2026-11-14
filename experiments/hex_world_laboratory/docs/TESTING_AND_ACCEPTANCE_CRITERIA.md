# Hex World Laboratory — Test ve Kabul Ölçütleri

> **Durum:** Test stratejisi ve aşama kabul sözleşmesi  
> **Üst belge:** [HEX_WORLD_LAB_MASTER_PLAN.md](HEX_WORLD_LAB_MASTER_PLAN.md)

## 1. Amaç

Bu belge, laboratuvar iddialarının hangi kanıtla doğrulanacağını ve aşamaların hangi koşullarda kapatılabileceğini tanımlar. Test sonuçları ölçülmeden başarı ilan edilmez.

## 2. Test seviyeleri

### 2.1 Unit test
Tek fonksiyon veya sınıfın davranışını sınar. Geometri, koordinat dönüşümü, mesafe, hareket integrasyonu ve çarpışma matematiğinin temel doğrulama aracıdır.

### 2.2 Property-based test
Birçok girdi üzerinde değişmezleri kontrol eder. Örnekler:
- axial → world → axial dönüşümünün tolerans içinde geri dönmesi.
- Hex merkezlerinin doğru hücre adresine dönmesi.
- Komşuluk ilişkilerinin simetrisi.
- Mesafe değerlerinin negatif olmaması ve bilinen aksiyomları sağlaması.
- Aynı simülasyon girdisinin aynı koşullarda aynı sonucu üretmesi.

Kullanılacak property-testing kütüphanesi ayrıca onaylanıp bağımlılık olarak eklenebilir; başlangıçta standart pytest parametrizasyonu yeterli olabilir.

### 2.3 Integration test
Birden fazla katmanın birlikte çalışmasını sınar. Örnekler: Geometry + World, Movement + Physics, Camera + Rendering, Entities + Spatial.

### 2.4 Acceptance test
Kullanıcının gözlemleyebileceği uçtan uca davranışı doğrular. Örneğin oyuncunun hex sınırını geçerken kesintisiz ilerlemesi veya engel kenarı boyunca kayabilmesi.

### 2.5 Visual test
Çizim hizası, hücre sınırları, foot-anchor, y-sort, kamera ve collider overlay gibi yalnızca sayısal testlerle yeterince doğrulanamayan çıktıları inceler. Görsel kanıt ekran görüntüsü veya kayıtla raporlanır.

### 2.6 Performance benchmark
Frame time, sorgu gecikmesi, bellek, entity sayısı ve güncelleme maliyetini ölçer. Benchmark koşulları sabitlenmeden iki yaklaşım karşılaştırılmaz.

### 2.7 Regression test
Önceden düzeltilmiş sorunların yeniden oluşmadığını doğrular. Her giderilen kritik hata için uygun regresyon testi eklenir.

## 3. Test ortamı ve tekrarlanabilirlik

Her test raporunda mümkün olduğunca şu bilgiler bulunur:
- İşletim sistemi ve sürümü.
- Python sürümü.
- Laboratuvar commit SHA.
- Bağımlılık sürümleri.
- Test komutu.
- Rastgelelik kullanılıyorsa seed.
- Ekran çözünürlüğü ve pencere boyutu (görsel testlerde).
- Donanım profili ve yük parametreleri (benchmark'ta).

Testler grafik ortamına gereksiz yere bağımlı olmamalıdır. Pencere gerektiren kabul testleri ayrı etiketlenebilir.

## 4. Zorunlu geometri testleri

- Origin hücresi.
- Altı komşu hücre ve yön sırası.
- Pozitif/negatif axial koordinatlar.
- Uzak hücre koordinatları.
- Hex merkezleri, köşeleri ve kenarları.
- Axial/world dönüşüm döngüsü.
- Hex kenarı ve köşesindeki sınır noktaları.
- Negatif world koordinatları.
- Hex mesafesi ve komşuluk tutarlılığı.
- Farklı map origin/hex size parametreleri.

## 5. Zorunlu hareket ve fizik testleri

- Hücre merkezinden başlayıp sınırı kesintisiz geçme.
- Çok küçük hız ve çok yüksek hız.
- Yatay, dikey ve çapraz yönlerde eşdeğer hız.
- 30/60/120 FPS ve değişken frame-time karşılaştırması.
- Hızlanma, yavaşlama ve yön değiştirme.
- Tek engel, bitişik engel ve dar koridor.
- Duvar boyunca kayma ve köşe teması.
- Birden çok temas ve sıkışma durumu.
- Harita sınırı ve harita dışı hareket.
- Yüksek hızda tünelleme.
- Uzun süreli hareket birikimli hata testi.

## 6. Kamera ve render testleri

- World-to-screen ve screen-to-world dönüşüm döngüsü.
- Pan ve zoom sırasında dünya state'inin değişmemesi.
- Farklı viewport ve pencere boyutları.
- Fareyle hücre/varlık seçimi.
- Sprite foot-anchor ve collider hizası.
- Y-sort/depth sırası.
- Kamera hareketinde titreme ve subpixel sapması.
- Görünür alan culling doğruluğu.

## 7. Spatial ve entity testleri

- İndeks sorgularının brute-force referansıyla eşleşmesi.
- Aday sorgusunda false negative olmaması.
- Entity hareket ettiğinde indeks güncelliği.
- Entity silme/oluşturma sonrası stale kayıt kalmaması.
- Farklı harita kimliklerinin birbirine karışmaması.
- Etkileşim menzilinin kamera zoom'undan bağımsız olması.
- NPC ve kaynakların ortak konum sözleşmesine uyması.

## 8. Performans ölçütleri

Başlangıç FPS, entity sayısı veya milisaniye eşikleri donanım ve sahne profili doğrulanmadan sabitlenmez.

Ölçülecek metrikler:
- Ortalama frame time.
- P95 ve mümkünse P99 frame time.
- Simülasyon tick süresi.
- Physics/collision süresi.
- Spatial query süresi.
- Render süresi.
- Bellek kullanımı.
- Entity ve engel sayısı.
- İndeks kurma/güncelleme maliyeti.

Her benchmark'ta:
1. Sahne boyutu ve içerik yoğunluğu belirtilir.
2. Isınma ve ölçüm süresi sabitlenir.
3. Aynı koşulda birden fazla tekrar yapılır.
4. Ortalama ve dağılım ölçüleri raporlanır.
5. Doğruluk karşılaştırması performans ölçümünden ayrı yürütülür.

## 9. Aşama bazlı kabul kapıları

| Aşama | Asgari kabul kanıtı |
|---|---|
| 0 — Plan/sözleşme | Onaylı Master Plan, mimari sözleşme, geliştirme ve test kuralları |
| 1 — Altyapı | Temiz ortam kurulumu, açılış/kapanış, test komutu |
| 2 — Geometri | Unit/property testleri ve dönüşüm/sınır kanıtı |
| 3 — Dünya modeli | Dünya bütünlüğü ve harita kimliği testleri |
| 4 — Hareket | FPS bağımsızlığı, sürekli konum ve hareket testleri |
| 5 — Fizik | Hex kenarları, engel ve temas kabul testleri |
| 6 — Kamera | Dönüşüm ve pan/zoom testleri |
| 7 — Render | Görsel kanıt ve hizalama kontrolü |
| 8 — Spatial | Brute-force doğruluk karşılaştırması ve benchmark |
| 9 — Entity/interaction | Konum, kimlik ve menzil integration testleri |
| 10 — Simulation | Birleşik senaryo ve uzun süreli tutarlılık |
| 11 — Sağlamlık | Regresyon, stres ve performans raporu |
| 12 — Entegrasyon hazırlığı | Dosya eşleştirme, mimari ve geri dönüş planı |
| 13 — Demo entegrasyonu | Demo testleri ve kullanıcı kabulü |

## 10. Test başarısızlığı politikası

- Başarısız test saklanmaz veya rapordan çıkarılmaz.
- Test beklentisi hatalıysa test değişikliği gerekçelendirilir.
- Flaky testler (aynı kodla bazen geçen bazen kalan) çözülmeden kabul kanıtı sayılmaz.
- Görsel kontrol yapılmadıysa görsel kabul tamamlanmış sayılmaz.
- Benchmark yapılmadıysa performans iyileşmesi iddia edilmez.
- Kritik hata açıkken aşama kapatılmaz.
- İstisna kabulü gerekiyorsa kullanıcı kararı ve teknik risk rapora yazılır.

## 11. Aşama kapanış raporu şablonu

Her kapanış raporu şu alanları içermelidir:

1. Aşama adı ve hedefi.
2. Uygulanan kapsam.
3. Değişen dosyalar.
4. Alınan mimari kararlar ve ADR bağlantıları.
5. Test komutları ve ortam.
6. Toplam/geçen/başarısız/atlanmış test sayısı.
7. Görsel ve benchmark kanıtları.
8. Commit SHA.
9. Açık hata, risk ve sınırlamalar.
10. Kabul durumu: **KABUL / DÜZELTME GEREKLİ / BEKLEMEDE**.
11. Sonraki aşamaya geçiş önerisi.

Aşama ancak kabul ölçütlerinin tümü karşılandığında ve kullanıcı onayladığında kapanır.
