# Eldoria — Aşama 2 Kare Izgara Chunk ve Cache Altyapısı

**Tarih:** 23 Kasım 2026  
**Aşama:** 2 — Türetilmiş grid chunk/cache  
**Hedef dal:** `experiment/map-cleanup`  
**Durum:** Kod ve testler eklendi; CI doğrulaması ve gerçek donanım benchmark'ı çıkış kapısıdır.

## 1. Kapsam

Aşama 1'deki saf hex–square coverage hesabı, haritanın tamamını tek seferde üretmek zorunda kalmadan kare grid parçaları üretebilecek şekilde genişletildi. Üzerine içerik parmak izli, sınırlı kapasiteli LRU chunk cache eklendi.

Bu aşamada A*, oyuncu/NPC hareketi, fizik, çarpışma, animasyon, kamera ve save/load değiştirilmedi. Kare grid hâlâ türetilmiş veridir; kayıt dosyasına yazılmaz.

## 2. Uygulama

### 2.1 Sınırlı coverage üretimi

`build_square_grid_coverage()` artık isteğe bağlı `grid_bounds=(min_x, min_y, max_x, max_y)` kabul eder. Sınırlar dahilî grid koordinatlarıdır. Parametre verilmediğinde Aşama 1'deki tam harita davranışı korunur.

Chunk üretimi sırasında:
- Haritanın hex poligonları kanonik geometri fonksiyonundan elde edilir.
- Kesişim hesabı yalnızca istenen chunk'ın kare hücreleriyle sınırlandırılır.
- Chunk, kendi kapsadığı dikdörtgendeki WALKABLE/BLOCKED/PARTIAL/OUTSIDE hücrelerini taşır.
- Negatif grid koordinatları Python floor-division semantiğiyle deterministik chunk kimliği alır.

Böylece tüm haritanın kare hücre kayıtları aynı anda belleğe alınmak zorunda değildir. Tek chunk oluşturulurken hex tanımları taranır; bu aşamada hex poligonlarının tamamı için ayrı, kalıcı bir global indeks eklenmemiştir.

### 2.2 Cache anahtarı ve invalidation

`square_grid_geometry_fingerprint()` SHA-256 içerik parmak izi üretir. Anahtar şu girdileri kapsar:
- map_id;
- kare hücre boyutu ve hex yarıçapı;
- grid origin ve hex origin;
- sıralı geçerli axial hücre koordinatları;
- her hücrenin terrain_id ve blocked değeri.

`HexMapDefinition` immutable olduğundan mevcut modelde artan bir geometry revision alanı yoktur. Bu nedenle tahminî revision sayacı eklemek yerine, navigasyon coverage sonucunu etkileyen gerçek içerik üzerinden fingerprint kullanılmıştır. Aynı map_id altında terrain/blocked/geometri girdisi değişirse cache anahtarı değişir ve eski chunk yeni girdiye hizmet etmez.

Landmark/prop collider geometrisi mevcut coverage algoritmasının girdisi değildir. İleride bu tür statik engeller kare navigasyon walkability'sine dahil edildiğinde, bunların ilgili geometry fingerprint'e ve invalidation sözleşmesine eklenmesi gerekir.

### 2.3 LRU ve eşzamanlı erişim

`SquareGridChunkCache`:
- varsayılan 16×16 grid hücreli chunk kullanır;
- varsayılan en fazla 64 chunk saklar;
- LRU sırasıyla eski chunk'ları çıkarır;
- hit, miss, eviction ve entry sayılarını raporlar;
- cache sözlüğü ve sayaç erişimini kilit altında tutar;
- değişmez `SquareGridCoverageMap` sonuçlarını döndürür.

Cache kapasitesi ve chunk boyutu constructor parametreleridir; henüz nihai performans kararı değildir. Cache mevcut `UniformGridIndex` ile aynı yapı değildir: biri türetilmiş navigasyon coverage'ını, diğeri runtime broadphase adaylarını temsil eder.

## 3. Benchmark

Yeni komut dosyası:

```powershell
python scripts/benchmark_square_grid_cache.py
```

İsteğe bağlı parametreler:

```powershell
python scripts/benchmark_square_grid_cache.py --chunk-size 16
python scripts/benchmark_square_grid_cache.py --map content/demo_eldoria/hex_maps/starting_valley.json
```

Komut Başlangıç Vadisi üzerinde 16 ve 8 dünya birimi çözünürlüklerini ayrı ayrı ölçer. JSON çıktısı şunları içerir:
- chunk ve kare hücre sayısı;
- yürünebilir hücre sayısı;
- soğuk chunk üretim süresi;
- sıcak cache lookup süresi;
- tracemalloc retained/peak bellek ölçümleri;
- cache hit/miss/eviction/entry sayıları.

Bu rapora tahminî benchmark rakamı yazılmamıştır. Gerçek süre ve bellek sonuçları hedef donanımda komut çalıştırılarak alınmalıdır. CI test başarısı performans benchmark'ı yerine geçmez.

## 4. Test kapsamı

Yeni `tests/test_application/test_square_grid_cache.py` şu davranışları sınar:
- chunk'ların birleştirilmesiyle tam coverage haritasının hücre hücre yeniden elde edilmesi;
- aynı istekte cache hit ve aynı immutable nesnenin dönmesi;
- aynı map_id altında blocked/terrain içeriği değişince fingerprint invalidation;
- fingerprint'in set iterasyon sırasından etkilenmemesi;
- kapasite dolduğunda LRU eviction;
- negatif grid koordinatlarının chunk'lara atanması;
- geçersiz chunk girdilerinin reddedilmesi.

Aşama 1'in tam harita coverage testleri de korunur; sınırlı üretim eklenmesi eski API davranışını değiştirmemelidir.

## 5. Değişmeyen sözleşmeler

- HexMapDefinition ve axial dünya kanonik kaynaktır.
- Kare grid oyuncu/NPC için birincil navigasyon uzayı olma kararını korur.
- Kare grid türetilmiştir; save schema değişmez.
- Aktör konumu sürekli WorldPoint olarak kalır; grid hücre merkezine snap yapılmaz.
- Physics son fiziksel doğruluk otoritesidir.
- UniformGridIndex broadphase sorumluluğunu korur.
- Bu aşamada A* veya hareket input'u eklenmez.

## 6. Aşama 2 çıkış kapısı

Aşama 3'e geçmeden önce:
1. CI'da yeni ve mevcut testlerin tamamı geçmeli.
2. Yerel benchmark 8/16 çözünürlüklerinde çalıştırılmalı.
3. Üretim süresi, retained/peak bellek ve chunk sayısı kaydedilmeli.
4. Gerekirse chunk boyutu/cache kapasitesi ölçüme göre ayarlanmalı.
5. Çözünürlük seçimi yalnızca bu aşamadaki coverage maliyetine göre kesinleştirilmemeli; Aşama 3'te A* rota maliyeti ve collider geçit testleri de hesaba katılmalı.

**Sonuç:** Aşama 2, kare grid coverage'ını chunk bazında tembel üretip sınırlı LRU cache içinde tekrar kullanabilen altyapıyı sağlar. Nihai grid çözünürlüğü henüz seçilmemiştir.
