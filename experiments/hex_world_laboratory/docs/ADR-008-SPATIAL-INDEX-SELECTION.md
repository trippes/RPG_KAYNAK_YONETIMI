# ADR-008 — Spatial İndeks Seçimi ve Kullanım Sınırları

- **Durum:** Kabul edilen teknik karar (Aşama 8 uygulama sonucu)
- **Tarih:** 17 Kasım 2026
- **Bağlam:** Aşama 8 performans ve doğruluk benchmarkları

## Karar

1. Mevcut linear AABB taraması `gather_candidates()` korunur ve küçük engel kümelerinde varsayılan yol olmaya devam eder.
2. Physics için isteğe bağlı `ObstacleSpatialIndex` adaptörü UniformGrid kullanır.
3. Genel UniformGrid varsayılan hücre boyutu 128 dünya birimidir. Map/obstacle boyut dağılımı biliniyorsa 64 veya 256 gibi değerler açıkça seçilebilir.
4. Quadtree generic Spatial katmanında deneysel alternatif olarak tutulur; Aşama 8'de Physics adaptörünün varsayılanı yapılmaz.
5. Hex topoloji sorguları axial koordinat alanında doğrudan üretilir; fiziksel grid veya quadtree hex komşuluğunun yerine geçmez.
6. Spatial index harita ömrü boyunca yeniden kullanılmalıdır; hareket tick'inde yeniden oluşturulmaz.
7. Broadphase yalnızca aday seçer; narrowphase ve solver nihai collision kararını verir.

## Ölçüm dayanağı

GitHub Actions Ubuntu 26.04 / Python 3.12 benchmarklarında:
- 50.000 engelde grid, dört veri dağılımında linear taramadan yaklaşık 33–661 kat daha hızlı sorgu verdi.
- Quadtree grid'den daha az bellek kullandı; ancak aynı ana benchmarkta sorgu ve update maliyeti genellikle daha yüksekti.
- Mixed-size 50.000 engelde grid-64 yaklaşık 335 MB kullanırken grid-256 yaklaşık 48 MB'a indi.
- 128 dünya birimi, uniform/clustered profillerinde dengeli genel ayar oldu. Mixed-size profilde 256 daha iyi bellek/sorgu dengesi verdi.
- 100 engelde indeksin sorgu avantajı sınırlıdır; build maliyeti nedeniyle linear yol korunur.

Bu sonuçlar CI runner üzerindeki göreli ölçümlerdir; hedef kullanıcının cihazında mutlak süre garantisi değildir.

## Sonuçlar ve ödünleşimler

- Küçük listelerde ek indeks kurulum/bellek maliyeti doğurulmaz.
- Büyük ve uzun ömürlü haritalarda UniformGrid önemli sorgu kazancı sağlar.
- Büyük boyut farkları olan engellerde hücre boyutunu büyütmek gerekir; aksi durumda grid bucket belleği artar.
- Quadtree bellek açısından güçlü bir alternatif olarak korunur; ileride gerçek oyun verisiyle yeniden değerlendirilir.
- Otomatik threshold veya runtime'da kendi kendine algoritma değiştirme bu aşamada eklenmez; map lifecycle ve gerçek workload daha sonra netleştirilebilir.

## Kapsam dışı

A*, Dijkstra, click-to-move, rota üretimi, NPC/entity yakınlık sistemi ve ana oyuna entegrasyon bu karara dahil değildir.
