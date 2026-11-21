# Eldoria — Aşama 3.6 Click-to-Move Performans ve Kalite Raporu

- **Dal:** `experiment/map-cleanup`
- **Workflow commit'i:** `a96077270573be388537d28604662c40621a975c`
- **Route controller commit'i:** `368ac08aa60b21e520c167119dcafbba50879f79`
- **Benchmark workflow:** `44882884811`
- **Benchmark job:** `136781805273`
- **Ortam:** GitHub-hosted Linux, Python 3.12.16
- **Örnek sayısı:** Her rota uzunluğu için 100 bağımsız path-plan örneği; cache adımı için ilk plan hariç 99 cache-hit çağrısı
- **Durum:** Tamamlandı

---

## 1. Yöntem

Ölçüm gerçek `HexWorldRuntime` A* pathfinder'ını, gerçek occupancy registry'sini ve immutable `HexPhysicsSnapshot` collision edge validator'ını kullanır.

Üç sentetik rota uzunluğu test edildi: 1, 10 ve 100 geçilen hex hücresi. Harita tek hücre genişliğinde düz axial koridordur; sonuçlar dar koridor stres senaryosudur, her dünya haritasının ortalama performansı olarak yorumlanmamalıdır.

Her rota uzunluğunda:
- Aynı hedef için doğrudan tekrarlanan `runtime.path_to()` baseline'ı 100 kez ölçüldü.
- Controller'ın bağımsız route planları için path planning p50/p95/p99 ölçüldü.
- Bir kez planlanan aktif rota üzerinde 99 ek intent çağrısı yapılarak cache-hit adım maliyeti ölçüldü.
- Path query, cache hit/miss, replan, invalidation, blocked-step ve failure sayaçları kaydedildi.

## 2. Path planning ölçümleri

<text>Milisaniye; her rota uzunluğu için 100 örnek.</text>

| Rota | Baseline p50 | Baseline p95 | Baseline p99 | Controller p50 | Controller p95 | Controller p99 |
|---:|---:|---:|---:|---:|---:|---:|
| 1 hücre | 0,239 | 0,254 | 0,278 | 0,240 | 0,248 | 0,260 |
| 10 hücre | 11,654 | 11,830 | 11,916 | 11,680 | 11,761 | 12,212 |
| 100 hücre | 987,757 | 1.007,207 | 1.017,401 | 1.004,000 | 1.029,055 | 1.042,194 |

Controller'ın tek A* sorgusunun maliyeti baseline ile aynı düzeydedir. Route controller tek sorgunun maliyetini azaltmaz; aynı hedef için sorgunun tekrar edilmesini önler.

## 3. Cache-hit fixed-step maliyeti

İlk route planı ölçümünden ayrı olarak, sonraki 99 cache-hit intent çağrısının süresi:

| Rota | İlk plan (ms) | Cache-hit p50 (ms) | Cache-hit p95 (ms) | Cache-hit p99 (ms) |
|---:|---:|---:|---:|---:|
| 1 hücre | 0,287 | 0,021 | 0,025 | 0,029 |
| 10 hücre | 12,396 | 0,023 | 0,028 | 0,033 |
| 100 hücre | 1.040,737 | 0,024 | 0,029 | 0,041 |

100 hücrelik rotada cache-hit p99 yaklaşık 0,041 ms'dir. Bu, 60 Hz fizik adımının 16,67 ms zaman bütçesinin oldukça altındadır (GitHub-hosted runner üzerinde).

## 4. Cache sayaçları

Her senaryoda 100 intent çağrısı için:

| Sayaç | Sonuç |
|---|---:|
| Path query | 1 |
| Cache miss | 1 |
| Cache hit | 99 |
| Cache hit oranı | %99 |
| Replan | 0 |
| Invalidation | 0 |
| Blocked step | 0 |
| Failure | 0 |
| Path query azalması | %99 |

Böylece aynı aktif hedefin 100 çağrıda yalnızca bir A* sorgusu ürettiği doğrudan doğrulandı.

## 5. Performans yorumu

### Başarılı sonuç

- Tek aktif hedef için tekrarlanan A* sorguları kaldırıldı.
- 1/10/100 hücre rotalarında cached intent adımı p50 yaklaşık 0,02–0,024 ms aralığında kaldı.
- Statik edge kontrolleri immutable snapshot ile route planı sırasında yapılıyor.
- Sonraki fixed step'lerde map mask ve mutable occupancy kontrolü sürüyor.
- Swept-clearance smoothing kanıtı route cursor segmenti boyunca cache'leniyor; actor segmentten saparsa yeniden hesaplanıyor.
- 100 intent çağrısında 99 cache hit, 1 cache miss, sıfır replan/invalidation/failure gözlendi.

### Kalan yüksek maliyet

100 hücrelik tek hücre genişliğinde koridorda ilk path query p50 yaklaşık **988 ms**, p95 yaklaşık **1.007 saniye** ölçüldü. Route cache sonraki adımları ucuzlatır ancak ilk uzun rota planını hızlandırmaz. Bu sonuç pathfinding edge validation/static geometry maliyetinin ayrı bir optimizasyon incelemesini gerektirir.

Bu yüksek maliyet oyuncu click-to-move ölçümüdür; Aşama 2 NPC kaçınma pathfinding p95 sonuçlarıyla birleştirilmemiştir. Aşama 2 NPC spatial benchmark ayrı workflow olarak başarılı tamamlandı.

### Ölçülmeyen metrik

Hedefe gerçek varış süresi ölçülmedi. Mevcut `MovementIntegrator` target-aware braking/acceleration sağlamadığından route controller tek başına gerçek oyun zamanında güvenilir varış süresi üretemez. Bu bağımlılık Aşama 3.5 değerlendirme raporunda ertelenmiştir.

## 6. Artefakt

Ham ölçüm JSON'u: `reports/phase-3.6-player-click-move-benchmark.json`

GitHub Actions ayrıca `player-click-move-benchmark` adlı artifact'i yükledi (30 gün saklama).

**Sonuç:** Aşama 3.6 ölçüm ve kalite doğrulaması tamamlandı. Cache-hit maliyeti 60 Hz bütçesinin çok altında; 100 hücrelik ilk A* sorgusunun yüksek gecikmesi açık risk olarak kaydedildi.
