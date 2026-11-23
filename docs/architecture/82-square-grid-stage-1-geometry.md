# Eldoria — Aşama 1 Kare Izgara Geometri Prototipi

**Tarih:** 23 Kasım 2026  
**Aşama:** 1 — Saf geometri prototipi  
**Hedef dal:** experiment/map-cleanup

## 1. Kapsam

Bu aşamada kanonik altıgen dünya üzerine bağımsız kare grid geometrisi ve hex–square coverage hesabı eklendi. Oyuncu/NPC hareketi, A*, cache, physics, save/load, kamera ve animasyon entegrasyonu yapılmadı.

## 2. Eklenen geometri sözleşmesi

- SquareGridCoord(x, y) tam sayı kare hücre kimliğidir.
- WorldPoint y-down dünya düzlemi değişmez koordinat otoritesidir.
- grid_origin, (0, 0) kare hücrenin merkezidir; varsayılanı dünya (0, 0) noktasıdır.
- Dünya noktası grid kimliğine çevrilirken floor(delta / cell_size + 0.5) kullanılır. Hücre sınırlarının sağ/alt hücreye ait olduğu deterministik yarı açık sınır kuralı uygulanır.
- Grid hücresi merkezine dönüşüm ve dört köşe/bounds fonksiyonları saf Python'dur; Pygame import etmez.
- pointy_top_hex_corners() mevcut axial dönüşümle aynı geometri kaynağını kullanır.

## 3. Coverage modeli

build_square_grid_coverage() her geçerli hex poligonunu aday kare hücrelerle kesiştirir. Sutherland–Hodgman dikdörtgen kırpması ve shoelace alan hesabı gerçek kesişim alanını verir. Böylece tek hücre birden fazla hex'e ait alanları ayrı ayrı kaydedebilir.

Sınıflandırma:
- OUTSIDE: geçerli hex alanıyla pozitif kesişim yok.
- PARTIAL: kare hücrenin tamamı geçerli hex alanıyla kaplı değil.
- BLOCKED: hücre tam kaplı, ancak kesiştiği hex alanlarından en az biri engelli.
- WALKABLE: hücrenin tamamı geçerli hex alanıyla kaplı ve engelli hex alanıyla kesişmiyor.

Sınıflandırma muhafazakârdır. Kısmi map-edge hücreleri yürünebilir kabul etmez. Bu, physics swept-collider çözümünün alternatifi değildir.

## 4. Çözünürlük kıyaslaması

Başlangıç Vadisi için 8 ve 16 dünya birimi çözünürlükleri aynı coverage algoritmasından geçirilir. Testler:
- iki çözünürlükteki grid hücre alanlarının toplamının 61 geçerli hex alanına eşit olduğunu;
- her iki çözünürlükte PARTIAL, BLOCKED ve OUTSIDE sınıflarının bulunduğunu;
- 8 birim çözünürlükte üretilen grid hücre sayısı ve tam kaplı yürünebilir hücre sayısının 16 birimden fazla olduğunu

doğrular. Bu kıyas çözünürlüğü nihai olarak seçmez; daha ince grid'in daha fazla navigasyon detayı karşılığında daha çok hücre ürettiğini gösterir. Pathfinding ve gerçek aktör collider genişliği sonraki aşamalarda ölçülecektir.

## 5. Test matrisi

- Pozitif/negatif grid koordinatlarında center round-trip.
- Offset grid origin.
- Hücre kenarı tie-break determinism.
- Kare bounds ve corner sırası.
- Geçersiz koordinat, boyut ve origin türleri.
- Tek hex için alan korunumu.
- Tam kaplı ve geçilebilir hücre.
- Engelli hex kesişimi.
- Kısmi harita sınırı ve dış hücre.
- Bir kare hücrenin birden fazla hex ile kesişmesi.
- Başlangıç Vadisi 8/16 çözünürlük karşılaştırması ve toplam harita alanı korunumu.

## 6. Değişmeyen sistemler

Bu aşamada altıgen map şeması, valid_cells, axial sahiplik, mevcut continuous WorldPoint aktör konumu, physics solver, broadphase UniformGridIndex, save schema, player/NPC hareket sistemi ve locomotion animasyonu değiştirilmedi. Yeni coverage verisi kayda yazılmaz; yalnızca geometry prototipi için üretilir.

## 7. Sonraki aşama

Aşama 2, bu deterministik coverage sonucunu chunk tabanlı türetilmiş cache'e dönüştürme, map geometry revision anahtarıyla invalidation ve bellek/üretim maliyeti ölçümünü ele alacaktır. Aşama 3'te kare grid birincil A* navigasyon grafı olacaktır; axial A* kalıcı global rota sistemi olarak korunmayacaktır.
