# Eldoria — Aşama 3.6 Click-to-Move Performans ve Kalite Raporu

- **Dal:** `experiment/map-cleanup`
- **Ölçüm commit'i:** `368ac08aa60b21e520c167119dcafbba50879f79`
- **Benchmark workflow:** `44882633380`
- **Benchmark job:** `136781054297`
- **Ortam:** GitHub-hosted Linux, Python 3.12.16
- **Örnek sayısı:** Her rota uzunluğu için 20 bağımsız path-plan örneği; cache adımı için ilk plan hariç 19 cache-hit çağrısı
- **Durum:** Ölçüm tamamlandı

---

## 1. Yöntem

Ölçüm gerçek `HexWorldRuntime` A* pathfinder'ını, gerçek occupancy registry'sini ve immutable `HexPhysicsSnapshot` collision edge validator'ını kullanır.

Üç sentetik rota uzunluğu test edildi: 1, 10 ve 100 geçilen hex hücresi. Harita, tek hücre genişliğinde düz axial koridordur; bu nedenle sonuçlar dar koridor stres senaryosudur, her dünya haritasının ortalama performansı olarak yorumlanmamalıdır.

Her rota uzunluğunda:
- Aynı hedef için doğrudan tekrarlanan `runtime.path_to()` baseline'ı ölçüldü.
- Controller'ın bağımsız route planları için path planning p50/p95/p99 ölçüldü.
- Bir kez planlanan aktif rota üzerinde 19 ek intent çağrısı yapılarak cache hit adım maliyeti ölçüldü.
- Path query, cache hit/miss, replan, invalidation, blocked-step ve failure sayaçları kaydedildi.

## 2. Path planning ölçümleri

<text>Milisaniye; 20 örnekli ölçüm, p99 örnek dağılımının üst ucudur.</text>

| Rota | Baseline p50 | Baseline p95 | Baseline p99 | Controller p50 | Controller p95 | Controller p99 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 hücre | 0,276 | 0,315 | 0,375 | 0,274 | 0,294 | 0,302 |
| 10 hücre | 13,397 | 13,821 | 13,874 | 13,380 | 13,500 | 13,801 |
| 100 hücre | 1.134,148 | 1.140,382 | 1.140,703 | 1.134,217 | 1.145,819 | 1.152,848 |

Controller'ın gerçek A* sorgu maliyeti baseline ile aynı düzeydedir; route controller tek sorgunun maliyetini sihirli biçimde azaltmaz. Kazanç, aynı hedef için bu sorgunun tekrar edilmesini önlemesidir.

## 3. Cache-hit fixed-step maliyeti

İlk route planı ölçümünden ayrı olarak, sonraki 19 cache-hit intent çağrısının süresi:

| Rota | İlk plan (ms) | Cache-hit p50 (ms) | Cache-hit p95 (ms) | Cache-hit p99 (ms) |
|---:|---:|---:|---:|---:|
| 1 hücre | 0,365 | 0,026 | 0,032 | 0,034 |
| 10 hücre | 14,163 | 0,030 | 0,037 | 0,045 |
| 100 hücre | 1.147,509 | 0,032 | 0,045 | 0,052 |

100 hücrelik senaryoda cache-hit p95 yaklaşık 0,045 ms'dir. Bu, 60 Hz fizik adımının 16,67 ms zaman bütçesinin oldukça altındadır (GitHub-hosted runner üzerinde).

## 4. Cache sayaçları

Her senaryoda 20 intent çağrısı için:

| Sayaç | Sonuç |
|---|---:|
| Path query | 1 |
| Cache miss | 1 |
| Cache hit | 19 |
| Cache hit oranı | %95 |
| Replan | 0 |
| Invalidation | 0 |
| Blocked step | 0 |
| Failure | 0 |
| Path query azalması | %95 |

Bu ölçümdeki cache hit oranı 20 çağrı üzerinden hesaplanmıştır. Oyun 60 fixed step/saniye çalışırken aynı hedefin 60 step boyunca değişmediği durumda beklenen sorgu davranışı 1 plan + 59 hit'tir; benchmark'ın 20 çağrılık oranı doğrudan 60 çağrıya eşitlenmemelidir.

## 5. Performans yorumu

### Başarılı sonuç

- Tek aktif hedef için tekrarlanan A* sorguları kaldırıldı.
- Cached intent adımı 1/10/100 hücre rotalarında yaklaşık 0,03 ms p50 düzeyinde kaldı.
- Statik edge kontrolleri immutable snapshot ile route planı sırasında yapılıyor.
- Sonraki fixed step'lerde map mask ve mutable occupancy kontrolü sürüyor.
- Swept-clearance smoothing kanıtı route cursor segmenti boyunca cache'leniyor; actor segmentten saparsa yeniden hesaplanıyor.

### Kalan yüksek maliyet

100 hücrelik tek hücre genişliğinde koridorda ilk path query p50 yaklaşık **1,13 saniye** ölçüldü. Route cache sonraki adımları ucuzlatır ancak ilk uzun rota planını hızlandırmaz. Bu sonuç, pathfinding edge validation/static geometry maliyetinin ayrı bir optimizasyon incelemesini gerektirdiğini gösterir.

Bu yüksek maliyet oyuncu click-to-move ölçümüdür; Aşama 2 NPC kaçınma pathfinding p95 sonuçlarıyla birleştirilmemiştir. Aşama 2 NPC spatial benchmark ayrı workflow olarak başarılı tamamlandı.

### Ölçülmeyen metrik

Hedefe gerçek varış süresi ölçülmedi. Mevcut `MovementIntegrator` target-aware braking/acceleration sağlamadığından route controller tek başına gerçek oyun zamanında güvenilir varış süresi üretemez. Bu bağımlılık Aşama 3.5 değerlendirme raporunda ertelenmiştir.

## 6. Artefakt

Ham ölçüm JSON'u: `reports/phase-3.6-player-click-move-benchmark.json`

Workflow ayrıca `player-click-move-benchmark` adlı GitHub Actions artifact'i yükledi (30 gün saklama).

**Sonuç:** Aşama 3.6 ölçüm ve kalite doğrulaması tamamlandı. Cache-hit maliyeti 60 Hz bütçesinin çok altında; 100 hücrelik ilk A* sorgusunun yüksek gecikmesi açık risk olarak kaydedildi.
