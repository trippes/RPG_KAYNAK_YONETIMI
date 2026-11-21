# Eldoria RPG — Aşama 3.5 Uzun Rota Planlama Performans İncelemesi ve İyileştirme Planı

**Çalışma dalı:** `experiment/map-cleanup`  
**İnceleme tarihi:** 21 Kasım 2026  
**Durum:** A* erken maliyet elemesi, CI ve aynı runner üzerinde koridor + geniş engelli harita benchmark karşılaştırması doğrulandı; manuel oyun içi kabul testleri bekliyor  
**Kapsam:** İlk click-to-move rota planlamasında 100 hücrelik rotanın yüksek maliyetinin azaltılması

## 1. Yönetici özeti

CI benchmark'ında 100 hücrelik ilk rota planlaması yaklaşık **974 ms** ölçülmüştür. Aynı rota kurulduktan sonraki cache'li intent adımları yaklaşık **0,03 ms** seviyesindedir. Cache davranışı başarılıdır; darboğaz ilk planlama maliyetidir.

Kaynak kod incelemesi, A* algoritmasının kendisinden önce kenar doğrulama hattının ölçülmesini gerektiren güçlü bir aday göstermektedir:

`HexWorldRuntime.path_to` → `HexPathfinder.find_path` → komşu hücre doğrulaması → `edge_validator` → `HexPhysicsSnapshot.can_reach_cell` → `resolve_cell_step` → native `resolve_continuous_motion`.

Benchmark, her A* kenar doğrulamasında fiziksel erişilebilirlik kontrolü yapmaktadır. Bu kontrol gerçek çarpışma geometrisi ve native statik engel indeksi üzerinden geçer. Uzun rotalarda tekrarlanan bu maliyetin toplam süreye etkisi henüz ayrı ölçülmemiştir. Bu nedenle rapor, kesin kök nedenin kanıtlandığını değil, ölçümle doğrulanması gereken birincil adayın belirlendiğini kaydeder.

## 2. İncelenen gerçek kod

İnceleme, `experiment/map-cleanup` dalındaki aşağıdaki dosyalara dayanır:

| Dosya | İncelemedeki bulgu |
|---|---|
| `scripts/benchmark_player_click_move.py` | Gerçek runtime A* + occupancy + immutable native physics snapshot kullanır; 1/10/100 hücre senaryolarını ölçer. |
| `application/hex_world_runtime.py` | `path_to` entity, map ve occupancy verisini alır; aramayı `HexPathfinder.find_path` metoduna devreder. |
| `application/hex_pathfinding.py` | `heapq`, axial hex distance heuristic, `came_from` ve `cost_so_far` ile A* uygular. Her aday komşuda maliyet iyileştirmesi önce kontrol edilir; yalnızca iyileştiren adaylarda MovementRules ve varsa edge validator çalıştırılır. |
| `application/hex_physics_bridge.py` | `can_reach_cell`, hücre merkezleri arasındaki adımı `resolve_cell_step` ile fiziksel olarak doğrular. |
| `application/hex_movement_rules.py` | Komşuluk, map maskesi, hareket izni, bloklu hücre ve terrain kısıtlarını doğrular. |
| `application/hex_map_definition.py` | Map hücrelerini immutable `frozenset` ve `MappingProxyType` ile tutar; `has_cell` ve `get_cell` üyelik erişimleri sunar. |
| `application/hex_occupancy.py` | Dinamik engelleri occupancy kayıtlarından üretir; `blocked_cells` sorgusu her path query başında alınır. |

## 3. Benchmark'ın ölçtüğü ve ölçmediği şeyler

Benchmark yöntemi:
- Gerçek `HexWorldRuntime` A* ve occupancy kullanır.
- `HexPhysicsSnapshot` ve native statik fizik geometrisi kullanır.
- Aynı rota için doğrudan tekrarlanan `path_to` çağrısını, tek aktif cache'li route ile karşılaştırır.
- Rota uzunlukları 1, 10 ve 100 hücredir.
- Önceki CI çalışmasında 20 iterasyon kullanılmıştır.

Önceki CI ölçümü:

| Rota | İlk/direct path planning p50 | Cache'li intent p50 |
|---:|---:|---:|
| 1 hücre | 0,262 ms | 0,026 ms |
| 10 hücre | 11,545 ms | 0,029 ms |
| 100 hücre | 969,737 ms | 0,029 ms |

100 hücrede cache hit oranı %95, 1 path query, 19 cache hit, 0 replan, 0 invalidation ve 0 başarısız adımdır.

Önemli sınırlamalar:
- Bu benchmark'ın haritası `q` ekseninde tek hücre genişliğinde düz bir koridordur; geniş, dallanan veya engelli gerçek oyun haritasının tüm arama davranışını temsil etmez.
- Benchmark Linux CI runner / Python 3.11.18 ölçümüdür; oyuncunun yerel bilgisayarının performansı olarak yorumlanamaz.
- `target_arrival_time_ms` ölçülmemektedir. Bu çalışma hedefe frenleme/varış süresini doğrulamaz.
- Mevcut benchmark A* düğüm genişletme sayısını, kenar doğrulayıcı çağrı sayısını ve fizik doğrulayıcı toplam süresini ayrı raporlamaz.

## 4. Kaynak koddan doğrulanan performans adayları

### 4.1 Birincil aday: A* kenar doğrulamasının fizik motoruna gitmesi

`HexPathfinder.find_path` komşuları gezerken:
1. Komşu axial koordinatı `LocalHexPosition` değerine dönüştürür.
2. Occupancy ve map blocked koşullarını kontrol eder.
3. `MovementRequest` oluşturur ve `MovementRules.evaluate` çağırır.
4. `edge_validator` verilmişse fiziksel kenar doğrulamasını çağırır.

Benchmark'ın edge validator'ı `snapshot.can_reach_cell(source, target, body)` biçimindedir. Bu çağrı `resolve_cell_step` ve native `resolve_continuous_motion` yoluna girer. Bu nedenle A*'ın her aday kenarı yalnızca ucuz bir hücre komşuluğu kontrolü değildir.

**Sonuç:** Öncelikle bu hattın çağrı sayısı ve toplam/ortalama süresi ölçülmelidir. Kenar doğrulama maliyeti baskın çıkarsa, ilk optimizasyon alanı burasıdır.

### 4.2 İkincil aday: Komşu hücre başına tekrarlanan doğrulamalar ve nesne üretimi

A* her komşu için `LocalHexPosition`, `EntityPosition` ve `MovementRequest` oluşturur; ardından `MovementRules.evaluate` map üyeliği, adjacency, profil, blocked cell ve terrain kontrollerini yapar. Bir kısmı arama döngüsünde daha önce bilinen koşullarla örtüşebilir.

Bu kontrollerin maliyeti fizik kenar doğrulamasına kıyasla ölçülmeden sadeleştirme yapılmamalıdır. Özellikle domain kuralını atlayan kestirme bir yol oluşturulmamalıdır.

### 4.3 İkincil aday: Arama alanı / heuristic davranışı

Mevcut heuristic, axial hex distance; her adımın maliyeti 1 olduğundan birim maliyetli hex grid için admissible ve tutarlı bir alt sınırdır. `heapq` kullanımı da doğru veri yapısı tercihidir.

Bununla birlikte:
- Düz, dar benchmark koridoru açık ve dallanan haritalardaki node expansion davranışını göstermez.
- A* frontier tie-break sırası ve genişletilen node sayısı ayrıca raporlanmalıdır.
- Heuristic'i keyfî biçimde büyütmek optimal en kısa yol garantisini bozabilir.

**Karar:** Heuristic ağırlığını artırmak veya A*'ı başka algoritmayla değiştirmek bu aşamada önerilmez.

### 4.4 Occupancy snapshot maliyeti

`HexWorldRuntime.path_to`, arama başlamadan önce `HexOccupancyRegistry.blocked_cells` çağırır. Bu çağrı registry snapshot'ını tarar. Dinamik occupancy değişebildiği için bu veri uzun ömürlü ve geçersizleştirmesiz cache'lenemez.

Bu adım ayrı ölçülmelidir. Maliyet baskın değilse değişiklik yapılmamalıdır.

## 5. Önerilen uygulama planı

### Paket A — Ölçüm ve teşhis (önce yapılacak)

Benchmark'a yalnızca opt-in/benchmark amaçlı sayaçlar eklenmesi:
- Genişletilen A* node sayısı.
- Komşu aday sayısı.
- Map/rule kontrollerinden geçen kenar sayısı.
- `edge_validator` çağrı sayısı.
- Edge validator toplam süresi ve çağrı başına p50/p95.
- A* çekirdek arama süresi.
- Occupancy blocked-cell snapshot süresi.
- Üretilen rota uzunluğu ve başarısız arama sayısı.

Ölçüm kodu normal oyun çalışmasında zorunlu maliyet yaratmamalı; mevcut opt-in metrics yaklaşımı korunmalıdır. Benchmark aynı Linux runner, Python sürümü, rota boyutları ve fizik snapshot ile önceki baseline'a karşılaştırılmalıdır. En az 1/10/100 hücre senaryoları korunmalı; ayrıca geniş/dallanan ve engelli bir rota senaryosu eklenmelidir.

**Çıkış kriteri:** Toplam 100 hücre planlama süresinin hangi alt bileşenlerde harcandığı ölçümle açıklanmalı; edge validator ve A* çekirdek maliyetleri ayrı raporlanmalıdır.

### Paket B — Kenar doğrulama maliyetini azaltma (ölçüm sonucu uygunsa)

Öncelik sırası:
1. Aynı arama içindeki aynı yönlü kenarın fiziksel doğrulamasının tekrar edilmesini engelleyen, arama ömrüyle sınırlı yerel memoization değerlendirilir. Anahtar; map/snapshot, body/collider ve yönlü source-destination kimliğini güvenli biçimde ayırt etmelidir.
2. `HexPhysicsSnapshot` immutable olduğu için snapshot'a bağlı statik geometri sonucu yeniden kullanılabilir; ancak body/collider farklılıkları anahtara dahil edilmelidir.
3. Kenar geçişinin yön simetrisi kanıtlanmadan A→B sonucu B→A için kullanılmamalıdır. İlk uygulamada yönlü anahtar tercih edilir.
4. Cache yalnızca tek path query süresince yaşamalı; query sonrasında bırakılmalıdır. Böylece runtime occupancy değişiklikleriyle uzun ömürlü stale cache riski oluşmaz.
5. Dinamik occupancy ve map/profile kuralları her query'nin güncel verisiyle doğrulanmaya devam etmelidir.

Bu yaklaşım fiziksel erişilebilirlik semantiğini değiştirmeden aynı fizik hesabının gereksiz tekrarını azaltmayı hedefler. Ancak gerçek çağrı tekrarları ölçümde görülmeden memoization eklenmemelidir.

### Paket C — A* komşu döngüsünün düşük riskli optimizasyonu

Paket A'da nesne üretimi / MovementRules maliyeti anlamlı çıkarsa:
- Altı axial komşu üretiminde gereksiz dönüşüm ve tekrar eden map lookup'ları azaltılabilir.
- `valid_cells`, blocked cells, terrain ve profile kuralları için query-local read-only erişim hazırlanabilir.
- Hareket kurallarının tek otoritesi korunmalı; A* için farklı ve eksik bir geçiş kuralı kopyalanmamalıdır.
- `MovementRules.evaluate` ile eşdeğer davranış testlerle kanıtlanmadan doğrudan boolean kestirmeye geçilmemelidir.

### Paket D — Geniş harita davranışı ve algoritma kararı

Geniş/dallanan harita benchmark'ında node expansion yüksek çıkarsa:
- Hex distance heuristic'in gerçek harita maliyetleriyle uyumu incelenir.
- Engelli hücreler ve edge validator nedeniyle arama alanının nasıl genişlediği ölçülür.
- Yalnızca ölçümle kanıtlanan ihtiyaç varsa daha ileri algoritmik seçenekler değerlendirilir.
- Optimal path garantisi, deterministik tie-break ve edge validation semantiği açık kabul kriteri olarak kalır.

## 6. Korunacak mimari değişmezler

Aşağıdaki kurallar bu performans çalışmasında değiştirilemez:

1. `HexWorldRuntime` authoritative continuous position, occupancy ve spatial index sahibi kalır.
2. `HexPathfinder` runtime konumunu, occupancy'yi veya entity state'ini değiştirmez.
3. Pathfinding yalnızca rota önerir; movement commit yapmaz.
4. Statik collision → dinamik actor collision/NPC push → runtime commit sırası aynen korunur.
5. NPC push rollback ve başarısız player commit tutarlılığı bozulmaz.
6. Native physics snapshot immutable kalır; başka bir fizik motoru veya ikinci dünya otoritesi eklenmez.
7. Dynamic occupancy her yeni path query için güncel olarak dikkate alınır.
8. Edge validator tarafından reddedilen kenar hiçbir rotaya dahil edilmez.
9. A* optimal en kısa yol davranışı ve deterministik sonuçları korunur.
10. Eski kare harita/legacy demo geri getirilmez.
11. Yeni harici bağımlılık eklenmez.
12. Tüm çalışma yalnızca `experiment/map-cleanup` dalında yürütülür; başka dal açılmaz veya kullanılmaz.

## 7. Zorunlu test ve doğrulama matrisi

| Alan | Test beklentisi |
|---|---|
| Açık düz rota | 1/10/100+ hücre rotaları doğru hedefe ulaşır. |
| Optimalite | A* sonucu küçük referans haritalarda BFS en kısa yol uzunluğuyla eşleşir. |
| Determinizm | Aynı map/profile/occupancy girdisi aynı rotayı üretir. |
| Statik engel | Physics edge validator'ın reddettiği kenar kullanılmaz; geçerli alternatif rota bulunur. |
| Dinamik occupancy | Yeni query, değişmiş occupancy durumunu görür; eski query cache'i sonraki query'ye sızmaz. |
| Profil/collider | Farklı MovementProfile ve body collider ile önceki query sonucu yanlışlıkla paylaşılmaz. |
| Tek yönlü kenar | A→B doğrulaması B→A için varsayılmaz. |
| Ulaşılamaz hedef | `None` sonucu ve başarısızlık davranışı korunur. |
| Başlangıç/hedef sınırları | Geçersiz mask, blocked goal ve start==goal davranışı korunur. |
| Runtime bütünlüğü | Path query entity position, occupancy veya spatial index'i değiştirmez. |
| Performans | Aynı CI koşullarında 1/10/100 rota baseline/after p50/p95/p99 ve sayaçlar raporlanır. |
| Kalite | unittest, pytest, Ruff ve iki mevcut CI workflow'u başarılı olmalıdır. |

## 8. Başarı kriterleri

Optimizasyon ancak aşağıdaki koşulların tümü sağlanırsa kabul edilir:
- 100 hücrelik ilk planlama süresinde aynı CI ortamında anlamlı ve tekrarlanabilir düşüş.
- 1 ve 10 hücrelik kısa rotalarda kayda değer regresyon olmaması.
- Geniş/dallanan ve engelli haritalarda doğru, optimal ve deterministik rotalar.
- Physics edge validator ve occupancy semantiğinin korunması.
- Tüm test/CI matrislerinin başarıyla geçmesi.
- Önce/sonra benchmark çıktılarının aynı yöntem ve koşullarla karşılaştırılması.

Önerilen ilk hedef, 100 hücrelik ilk planlama süresini mevcut ~970 ms seviyesinden belirgin biçimde aşağı çekmektir. Kesin milisaniye hedefi Paket A profil sonuçları görüldükten sonra belirlenmelidir; bu rapor ölçülmemiş bir performans garantisi vermez.

## 9. Açıkça kapsam dışı / henüz doğrulanmamış

- Hedefe frenleme ve fiziksel varış süresi bu benchmark'ın konusu değildir.
- Oyuncu bilgisayarında performans ölçümü yapılmamıştır.
- Gerçek geniş oyun haritasında node expansion profili henüz alınmamıştır.
- Edge validator'ın toplam süre içindeki payı henüz ölçülmemiştir.
- Paket A tamamlanmadan kesin optimizasyon tekniği seçilmiş sayılmaz.
- Manuel oyun içi kabul testleri bu teknik incelemeyle tamamlanmış sayılmaz.

## 10. Nihai teknik karar

**Önce ölç, sonra optimize et.** İlk uygulanacak iş A* algoritmasını değiştirmek değil, mevcut pathfinding çağrı zincirini alt maliyetlerine ayıran benchmark/profil telemetrisi eklemektir. Ölçüm fiziksel kenar doğrulamasının baskın maliyet olduğunu gösterirse ilk düşük riskli optimizasyon, aynı path query süresince yönlü kenar doğrulama sonuçlarının query-local memoization ile yeniden kullanılması olacaktır. Bu sırada güncel occupancy, immutable snapshot, MovementRules, optimal path ve runtime commit sınırları korunacaktır.

## 11. CI profil ölçümü — 21 Kasım 2026

Ölçüm commit'i: `3a4e36c13ac65ed8d5dfb6c951060c8d80703e74`

Workflow: [Core Quality run 3017](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44899458761)

Artifact: `player-click-move-performance-linux` (artifact ID `14705805858`, 30 gün saklama).

Ölçüm ortamı: Python 3.11.18, Linux 7.0.0-1020-azure-x86_64, 7 ölçüm örneği ve 2 warm-up örneği. Profil ölçümü her rota için gerçek HexWorldRuntime üzerinde çalıştırılmıştır.

| Rota | Doğrulamalı arama p50 | A* doğrulayıcısız p50 | Fizik doğrulayıcı toplam süresi p50 | Çağrı / sorgu | Ölçülen pay |
|---:|---:|---:|---:|---:|---:|
| 1 hücre | 0,382 ms | 0,093 ms | 0,283 ms | 1 | %74,05 |
| 10 hücre | 17,892 ms | 0,599 ms | 17,125 ms | 19 | %95,67 |
| 100 hücre | 1.459,950 ms | 5,583 ms | 1.451,200 ms | 199 | %99,34 |

100 hücrelik rota için fizik doğrulayıcı, toplam path query süresinin yaklaşık %99,34'ünü tüketmiştir. Doğrulayıcı kapalı teşhis koşulunda aynı rota ve aynı path sonucu 5,583 ms p50 ile bulunmuştur. Bu doğrulamasız koşul yalnızca karşılaştırma içindir; oyun davranışında fizik doğrulaması kapatılmamıştır.

### 11.1 Çağrı sayısının algoritmik açıklaması

Mevcut `HexPathfinder.find_path` komşu döngüsünde `edge_validator` çağrısı, `new_cost >= cost_so_far.get(neighbor, ...)` kontrolünden önce çalışır. Düz tek hücre genişliğindeki 100 hücre benchmark koridorunda bu sıra, daha önce daha düşük maliyetle keşfedilmiş önceki hücreye geri dönen kenarların da fizik motorunda tekrar doğrulanmasına yol açmaktadır. Ölçülen 199 çağrı, 100 hücrelik bu koridorda her yeni ileri kenar için yapılan doğrulamalara ek olarak 99 geri kenar doğrulamasının da çalıştığını göstermektedir.

Bu bulgu doğrudan, dar kapsamlı bir optimizasyon adayı verir: bir komşuya mevcut maliyetten daha iyi bir yol bulunamayacağı belli olduğunda, pahalı MovementRules ve fizik edge validator çağrılarından önce bu aday elenmelidir. Birim kenar maliyetli mevcut A* modelinde `new_cost` kontrolünün komşu döngüsünün başına alınması en güçlü ilk adaydır. Bu değişiklik uygulanmadan önce eşit/üst maliyetli kenarların atlanmasının callback sözleşmesi ve tüm pathfinding testleriyle uyumu doğrulanmalıdır.

### 11.2 Uygulanan düşük riskli optimizasyon — 21 Kasım 2026

Uygulama commit'leri:
- Pathfinding değişikliği: `82152e7bff61276c94af7d42b1908b4055b4c8d6`
- Regresyon testleri: `eeac0ad45231fdbf03a193a9908dd80667517924`
- CI Ruff kapsamı: `765263bfb79cfc5d559db35bbe38be5685c19ac3`
- 100 örnekli benchmark workflow tetikleme kapsamı: `51f9b3a70e20fe4ab72ef909684449bd2ebac98b`

`HexPathfinder.find_path` içinde `new_cost = current_cost + 1` ve `new_cost >= cost_so_far.get(neighbor, inf)` elemesi, `MovementRules.evaluate` ve `edge_validator` çağrılarının önüne taşınmıştır. Böylece mevcut en iyi maliyeti iyileştiremeyen komşular için pahalı kural/fizik doğrulamaları yapılmaz.

Callback sözleşmesi docstring ile açıklandı: `edge_validator` deterministik ve yan etkisiz bir predicate olmalıdır; yalnızca hedef düğüm için daha iyi maliyetli adaylarda çağrılır. Bu, callback'in çağrı sayısını/gözlemlenebilir yan etkilerini kullanan bir API olarak tasarlanmadığını açık hale getirir.

Eklenen regresyon testleri:
- Üç hücrelik düz koridorda yalnızca iki ileri kenar doğrulanır; daha önce daha düşük maliyetle keşfedilmiş geri kenar doğrulanmaz.
- İyileştiren bir adayın validator tarafından reddedilmesi hâlâ rotayı engeller.

Bu dar koridor için beklenen fizik doğrulayıcı çağrı sayısı 199'dan 100'e düşer. Bu sayı algoritmik çağrı sırasından çıkarılmış beklentidir; CI benchmark çıktısı alınmadan ölçülmüş performans sonucu olarak değerlendirilmemelidir. Fizik doğrulaması hiçbir zaman kapatılmamıştır.

CI kapsamı, `application/hex_pathfinding.py` Ruff kontrolünü ve pathfinding değişikliği olduğunda 100 iterasyonlu benchmark workflow'unu içerecek şekilde genişletilmiştir. Bu rapor güncellemesi sırasında CI/benchmark sonuçları henüz doğrulanmamıştır.

### 11.3 Sonuç ve karar

Fiziksel kenar doğrulamasının uzun rota darboğazındaki baskın payı ölçümle kanıtlanmıştır. İlk optimizasyon uygulanmıştır; kabul kararı için aynı CI koşullarında 1/10/100 hücre benchmark sonuçları ve tüm test matrisleri beklenmektedir. Fizik doğrulaması tamamen kaldırılmamış, yalnızca daha iyi bir rota adayı üretmeyen komşulardaki tekrar çağrılar elenmiştir.


### 11.4 Optimizasyon sonrası CI benchmark doğrulaması — 21 Kasım 2026

Benchmark workflow: [Player click-move benchmark run 44899885580](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44899885580)  
Benchmark artifact: `player-click-move-benchmark` (artifact ID `14705627764`).  
Kaynak commit: `51f9b3a70e20fe4ab72ef909684449bd2ebac98b`.  
Ortam: Python 3.12.16, Linux 7.0.0-1020-azure-x86_64, her ana senaryo için 100 iterasyon.

| Rota | Doğrudan path planning p50 | p95 | p99 | Fizik edge validator çağrısı / sorgu | Cache'li intent adımı p50 |
|---:|---:|---:|---:|---:|---:|
| 1 hücre | 0,317 ms | 0,334 ms | 0,395 ms | 1 | 0,030 ms |
| 10 hücre | 8,332 ms | 8,801 ms | 9,390 ms | 10 | 0,035 ms |
| 100 hücre | 659,100 ms | 671,400 ms | 701,184 ms | 100 | 0,035 ms |

Aynı artifact içindeki ek profil ölçümünde doğrulamalı 100 hücrelik arama p50 değeri 664,176 ms, edge validator kapalı tanısal A* çekirdeği p50 değeri 3,946 ms ve edge validator çağrısı 100 olarak raporlanmıştır. Validator kapalı ölçüm yalnızca teşhis amaçlıdır; oyun yol bulmasında fiziksel kenar doğrulaması etkin kalır.

**Çağrı sayısı kabulü:** Önceki profiler çalışmasında aynı düz koridor yapısı için 100 hücre rotada 199 doğrulayıcı çağrısı ölçülmüştü. Optimizasyon sonrası 100 iterasyonlu benchmark artifact'ında her sorguda 100 çağrı ölçülmüştür. Böylece beklenen 199 → 100 çağrı azalması doğrulanmıştır.

**Performans karşılaştırması sınırı:** Önceki 1.459,950 ms profil p50 ölçümü Python 3.11.18 ve 7 örnekli ayrı profiler koşulundan; bu benchmark ise Python 3.12.16 ve 100 iterasyonlu benchmark koşulundan gelmiştir. Bu nedenle bu iki eski ölçüm doğrudan önce/sonra hızlanma oranı hesaplamak için eşdeğer değildi. Bu karşılaştırma açığı, aynı runner üzerinde yapılan kontrollü karşılaştırmayla 11.5 bölümünde giderilmiştir.

CI doğrulaması:
- Benchmark workflow `44899885580`: success.
- Son rapor commit'ine ait Eldoria CI workflow `44899899819`: success; beş işin tamamı başarılı.
- Core Quality workflow `44899899753`: success.

**Karar:** A* erken maliyet elemesi test ve CI doğrulamasını geçti; uzun düz rotadaki fiziksel kenar doğrulayıcı çağrı sayısı yarıya yakın azaltıldı. Aynı koşullarda önce/sonra karşılaştırması 11.5 bölümünde tamamlanmıştır. Geniş/dallanan ve engelli harita performansı ile manuel oyun içi kabul testleri hâlâ açık doğrulama alanlarıdır.


### 11.5 Aynı runner üzerinde kontrollü önce/sonra karşılaştırması — 21 Kasım 2026

Optimizasyon öncesi baseline commit: `7490aad580a169a37ad6ef0678ebe0efbc4f16c7`  
Optimize edilmiş commit: `08e9c7c4cbaad6461c03c44407b520b529f6e25d`  
Karşılaştırma workflow: [Player click-move benchmark run 44901126109](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44901126109)  
Artifact: `player-click-move-same-runner-comparison` (artifact ID `14706157483`).

**Kontrollü koşullar:**
- Her iki sürüm aynı GitHub Actions job'unda, aynı Ubuntu runner üzerinde art arda çalıştırıldı.
- Python sürümü her iki ölçümde de `3.12.16`.
- Runner: `Linux-7.0.0-1016-aws-x86_64-with-glibc2.43`.
- Her revizyon ayrı sanal Python ortamına kuruldu.
- Benchmark betiğinin Git blob SHA değeri iki revizyonda da aynıdır: `c6b95598ddce6814e1bbcb33f5b12e60a62c9bdb`.
- 1, 10 ve 100 hücrelik senaryoların her biri 100 iterasyonla ölçüldü.
- Aynı benchmark kodu, aynı rota geometrisi, aynı ölçüm yöntemi ve aynı fizik doğrulama koşulları kullanıldı.

| Rota | Baseline p50 | Optimize p50 | p50 değişimi | Baseline p95 | Optimize p95 | Baseline p99 | Optimize p99 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 hücre | 0,271 ms | 0,275 ms | +%1,51 | 0,290 ms | 0,298 ms | 0,311 ms | 0,354 ms |
| 10 hücre | 13,389 ms | 7,201 ms | -%46,22 | 13,700 ms | 7,309 ms | 13,837 ms | 7,364 ms |
| 100 hücre | 1.127,525 ms | 569,077 ms | -%49,53 | 1.135,994 ms | 573,855 ms | 1.138,558 ms | 574,810 ms |

Negatif p50 değişimi optimize sürümün daha hızlı olduğunu gösterir. 1 hücrelik kısa rotadaki yaklaşık %1,5 artış küçük mutlak farktır (yaklaşık 0,004 ms); bu ölçüm tek başına anlamlı bir regresyon kanıtı değildir. Buna karşılık 10 ve 100 hücrelik rotalarda belirgin ve tutarlı düşüş vardır.

**Fizik edge validator çağrı sayısı:**

| Rota | Baseline çağrı / sorgu | Optimize çağrı / sorgu | Değişim |
|---:|---:|---:|---:|
| 1 hücre | 1 | 1 | Değişmedi |
| 10 hücre | 19 | 10 | 19 → 10 |
| 100 hücre | 199 | 100 | 199 → 100 |

100 hücrelik rota için:
- p50 planlama süresi 1.127,525 ms'den 569,077 ms'ye düştü.
- Ölçülen p50 iyileşmesi yaklaşık **%49,53**.
- p95 1.135,994 ms'den 573,855 ms'ye düştü.
- p99 1.138,558 ms'den 574,810 ms'ye düştü.
- Fizik kenar doğrulama çağrısı sorgu başına 199'dan 100'e düştü.

10 hücrelik rotada da p50 yaklaşık %46,22 azaldı. 1 hücrelik rotada doğrulama çağrı sayısı değişmedi ve süre farkı çok küçüktür. Sonuç, optimizasyonun hedeflenen uzun rotalarda etkili olduğunu ve kısa rotalarda anlamlı bir performans cezası oluşturmadığını gösterir.

**CI sonucu:** Karşılaştırma workflow'u `44901126109` başarıyla tamamlandı. Aynı commit için Core Quality `44901126114` ve Eldoria CI `44901126104` workflow'ları da başarılı tamamlandı.

**Teknik karar:** Aynı runner/Python/benchmark koşullarında yapılan kontrollü ölçüm, A* erken maliyet elemesinin hedeflenen performans iyileştirmesini sağladığını doğrulamıştır. Uzun rota optimizasyonu otomatik test ve CI açısından kabul edilmiştir. Bununla birlikte bu sonuç yalnızca mevcut düz koridor benchmark'ı için geçerlidir; geniş/dallanan/engelli haritalar ve oyun içi manuel hareket kabul testleri ayrıca doğrulanmalıdır.


### 11.6 Geniş engelli harita benchmark'ı ve aynı runner karşılaştırması — 21 Kasım 2026

Karşılaştırma workflow: [Player click-move benchmark run 44902615737](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44902615737)  
Artifact: `player-click-move-same-runner-comparison` (artifact ID `14706229692`).  
Baseline commit: `7490aad580a169a37ad6ef0678ebe0efbc4f16c7`  
Optimize edilmiş benchmark commit: `ea8b075e3e9b13514e08eb1e23425fc52889cbc9`  
Ortam: Python `3.12.16`, `Linux-7.0.0-1020-azure-x86_64-with-glibc2.43`, her senaryo için 20 iterasyon.

**Yöntem:** Baseline ve optimize sürüm aynı GitHub Actions job'unda, aynı runner üzerinde art arda ve ayrı sanal ortamlar içinde çalıştırıldı. Her iki sürümde aynı benchmark betiği kullanıldı; benchmark betiği optimize checkout'tan alınarak baseline ortamında da çalıştırıldı. Koridor senaryoları 1/10/100 hücre, geniş engelli harita senaryoları 10/30 hücre olarak ölçüldü. Geniş engelli haritada başlangıç-hedef doğrultusundaki bir hücre bloklu olduğundan doğrulayıcısız tanısal yol, geçerli fiziksel rotadan farklılaşabilir.

| Harita / rota | Baseline p50 | Optimize p50 | p50 değişimi | Baseline p95 | Optimize p95 | Baseline p99 | Optimize p99 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Koridor, 1 hücre | 0,469 ms | 0,468 ms | -%0,06 | 0,526 ms | 0,526 ms | 0,584 ms | 0,609 ms |
| Koridor, 10 hücre | 22,263 ms | 11,957 ms | -%46,29 | 22,949 ms | 12,214 ms | 23,588 ms | 12,969 ms |
| Koridor, 100 hücre | 1.826,184 ms | 913,721 ms | -%49,97 | 1.837,578 ms | 920,546 ms | 1.840,472 ms | 946,573 ms |
| Geniş engelli, 10 hücre | 258,717 ms | 90,043 ms | -%65,20 | 267,899 ms | 91,767 ms | 269,663 ms | 92,076 ms |
| Geniş engelli, 30 hücre | 1.737,505 ms | 521,877 ms | -%69,96 | 1.744,709 ms | 527,344 ms | 1.756,348 ms | 527,690 ms |

**Fiziksel kenar doğrulayıcı çağrıları / sorgu:**

| Harita / rota | Baseline | Optimize | Azalma |
|---|---:|---:|---:|
| Koridor, 1 hücre | 1 | 1 | Değişmedi |
| Koridor, 10 hücre | 19 | 10 | 9 çağrı |
| Koridor, 100 hücre | 199 | 100 | 99 çağrı |
| Geniş engelli, 10 hücre | 168 | 57 | 111 çağrı |
| Geniş engelli, 30 hücre | 528 | 157 | 371 çağrı |

Optimize edilmiş sürümde fizik edge validator'ın tahmini toplam süre payı koridor 100 hücrede %99,22; geniş engelli 10 hücrede %97,86 ve 30 hücrede %98,90 olarak ölçülmüştür. Bu sonuç, A* erken maliyet elemesinin çağrı sayısını düşürdüğünü doğrularken, fiziksel kenar doğrulamasının kalan path-planning maliyetinin hâlâ baskın bileşeni olduğunu da gösterir. Bu nedenle bu çalışma fizik doğrulamasını kaldırma gerekçesi değildir; sonraki performans çalışmaları fiziksel doğruluk ve callback sözleşmesini koruyarak yürütülmelidir.

**Rota doğruluğu uyarısı:** Geniş engelli haritada validator kapalı tanısal A* rotası, fiziksel olarak doğrulanmış rotayla aynı değildir (10 hücrede 11'e karşı 12 düğüm; 30 hücrede 31'e karşı 32 düğüm). Bu beklenen bir tanısal farktır; validator kapalı sonuç oyun rotası olarak kullanılmamıştır. Ölçümde doğrulamalı baseline ve optimize sürüm rota düğüm sayıları aynı kalmıştır.

**Cache gözlemi:** Her senaryoda 20 intent çağrısının 19'u cache hit olmuş, path query sayısı 1'de kalmış, cache hit oranı %95, replan/invalidation/blocked step/failure sayıları 0 olmuştur. Cache'li intent adımı p50 değerleri yaklaşık 0,05 ms seviyesindedir. Bu metrikler ilk rota planlama maliyetinden ayrıdır.

**CI sonucu:** Benchmark workflow `44902615737` başarıyla tamamlandı. Aynı çalışma dalındaki Eldoria CI `44902615739` ve Core Quality `44902615948` workflow'ları da başarıyla tamamlandı.

**Teknik karar:** Aynı runner üzerinde ölçülen koridor ve geniş engelli harita sonuçları, optimize sürümün kısa rotada anlamlı regresyon oluşturmadan orta/uzun rotalarda p50 planlama süresini yaklaşık %46–70 aralığında düşürdüğünü göstermektedir. Fiziksel edge validation ve runtime mimari değişmezleri korunmuştur. Geniş engelli benchmark kabul edilmiştir. Gerçek oyun sahnesindeki hareket, duvar kayması, NPC itişi ve rollback davranışları için manuel kabul testleri hâlâ yapılmalıdır.
