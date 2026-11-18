# Aşama 11 — Stres, Regresyon ve Çapraz Platform Doğrulama Raporu

> **Tarih:** 18 Kasım 2026  
> **Dal:** `experiment/hex-world-laboratory`  
> **Doğrulanan kod commit'i:** `7874ba566f34eed7f91bd6fa638ec8f8f9135196`  
> **Durum:** 11.1–11.8 otomatik/teknik doğrulama tamamlandı; masaüstü manuel kabulü bekleniyor.

## 1. Sonuç özeti

| Kontrol | Sonuç |
|---|---|
| Laboratuvar testleri | 774 geçti; 0 failure/error/skip |
| 36.000 tick uzun koşusu | Başarılı |
| Düzensiz frame-time / tick debt | Başarılı |
| 100 / 1.000 / 10.000 entity stress | Başarılı |
| Spatial lifecycle ve brute-force karşılaştırması | Başarılı |
| Negatif/büyük hex koordinatları | Başarılı |
| Fizik engel sırası determinism testi | Başarılı |
| Phase 11 entity spatial benchmark | 3 oturum tamamlandı |
| Phase 11 tick/render benchmark | 3 oturum tamamlandı |
| Core Quality Linux | Başarılı |
| Core Quality Windows | Başarılı |
| Manuel masaüstü kabulü | Kullanıcı kontrolü bekleniyor |

## 2. Uygulanan test ve benchmark altyapısı

Yeni/eklenen dosyalar:

- `tests/stress/test_phase_11_entity_spatial_stress.py`
- `tests/stress/test_phase_11_simulation_geometry_stress.py`
- `benchmarks/benchmark_phase_11_stress.py`
- `benchmarks/benchmark_phase_11_simulation.py`
- `.github/workflows/hex-world-lab-ci.yml` — JUnit XML ve Phase 11 benchmark artifact upload adımları.

Testler mevcut EntityRegistry, EntitySpatialIndex, SimulationTickCoordinator, DemoTickPump, geometri ve fizik API'lerini kullanır. Yeni entity/world/spatial modeli eklenmedi.

## 3. Stres ve regresyon kapsamı

### 11.2 — Ölçek ve deterministik entity senaryoları

- 100, 1.000 ve 10.000 entity.
- Sparse, clustered ve mixed dağılımlar.
- Her dağılım için sabit seed ve tekrarlanabilir query alanları.
- 1.000 kayıtla başlayan randomized lifecycle senaryosunda 900 taşıma/pasifleştirme/yeniden etkinleştirme/silme işlemi.
- Map spatial index deactivate/reactivate sonrasında candidate kayıtlarının yeniden kurulması.
- Render visibility benchmarkı 50.000 hücreye kadar mevcut CI profilleriyle yeniden çalıştırıldı.

### 11.3 — Simülasyon ve zamanlama

- 36.000 sabit tick boyunca player MovementState, EntityTransform ve spatial sync tutarlılığı doğrulandı.
- NPC ve kaynakların konumları başlangıç ve bitişte karşılaştırıldı; değişmedi.
- 100/250/150/300/200 ms frame-time dizisi bir saniyelik toplam sürede tam 60 tick üretti.
- Her pump çağrısında en fazla 8 tick sınırı korundu; bekleyen tick debt boşaltıldı.
- Mevcut 30/60/120 FPS eşdeğerlik ve tick retry testleri tam pakette tekrar geçti.

### 11.4 — Entity/spatial/world lifecycle

- 100/1.000/10.000 entity için seeded spatial query testleri.
- Sparse, clustered ve mixed dağılımlarda indexed sonuçlar brute-force AABB referansıyla karşılaştırıldı.
- False negative, stale entry, inactive entity ve duplicate sonuçlar kontrol edildi.
- NPC/resource immobility invariant'ı ve mevcut companion komutlarının hareket üretmemesi korundu.

### 11.5 — Fizik ve geometri

- Negatif ve büyük axial koordinatları içeren 5.000 seeded hex center round-trip kontrolü.
- Negatif ve geniş koordinat aralığında axial ↔ world dönüşümleri.
- Bir merkezi duvar ve 100 uzak decoy engel ile obstacle giriş sırası ters çevrildi; solver sonucu aynı kaldı.
- Mevcut physics solver, continuous collision, broadphase/narrowphase ve movement testleri tam laboratuvar paketi içinde geçti.

## 4. Performans ve bellek sonuçları

Üç bağımsız seeded oturumun medyanı:

| Entity | Index build | Update median | Update P95 | Indexed query median | Query P95 | Query P99 | Brute-force query median | Python heap peak |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 2.9447 ms | 0.04605 ms | 0.05585 ms | 0.02740 ms | 0.03357 ms | 0.03678 ms | 0.52667 ms | 0.160 MiB |
| 1.000 | 28.5944 ms | 0.04571 ms | 0.05698 ms | 0.03157 ms | 0.04076 ms | 0.05154 ms | 5.09410 ms | 1.365 MiB |
| 10.000 | 292.4345 ms | 0.04757 ms | 0.05413 ms | 0.05583 ms | 0.08219 ms | 0.09281 ms | 51.06303 ms | 11.405 MiB |

Ölçümler Linux / Python 3.12.16 runner'ında alınmıştır. Heap değerleri `tracemalloc` ölçümüdür; process RSS değildir. Query profili seyrek ve karma dağılım içerdiği için ortalama candidate sayısı düşüktür. Indexed ve brute-force süreleri yalnızca bu sabit query profili için karşılaştırılmalıdır.

Simulation/render benchmarkı, üç bağımsız oturumun medyanı:

| Ölçüm | Sonuç |
|---|---:|
| Tick ortalaması | 190.0899 µs/tick |
| 120 tick batch P95 | 22.9271 ms |
| Render snapshot ortalaması | 246.9575 µs/snapshot |
| 120 snapshot batch P95 | 29.8351 ms |

Ölçüm dağılımı ve CI runner değişkenliği nedeniyle mutlak performans eşiği tanımlanmadı. Ölçümler gözlemsel baseline olarak saklandı.

## 5. 11.7 — Hata sınıflandırması ve düzeltmeler

Bu doğrulama turunda correctness veya lifecycle test failure'ı oluşmadı; dolayısıyla uygulama çekirdeğinde kapsam dışı bir düzeltme ya da ölçümle gerekçelendirilmemiş optimizasyon yapılmadı. Benchmark metodolojisinde iki ölçüm iyileştirmesi yapıldı:

1. Spatial benchmark üç bağımsız seeded oturum ve warm-up query/update adımlarıyla genişletildi.
2. Disposable warm-up index bellek ölçümünden çıkarıldı; tracemalloc sonucu yalnızca ölçülen registry/index profiline ait olacak şekilde düzeltildi.

Her iki değişiklikten sonra tam CI yeniden çalıştırıldı.

## 6. 11.8 — CI ve artifact kanıtı

**Hex World Laboratory CI — run 44274231933:** başarılı.

**Core Quality — run 44274231885:** başarılı.

- Laboratuvar JUnit raporu ve Phase 11 spatial/tick benchmark JSON dosyaları `phase-11-validation` artifact'inde saklandı.
- Phase 7 visual scene ve Phase 9 entity scene artifact'leri yeniden üretildi.
- Map persistence, runtime persistence, movement, collision, viewport visibility, spatial index ve Phase 8 benchmark adımları başarılı tamamlandı.
- Otomatik CI'da kritik/yüksek önem dereceli bir test failure'ı görülmedi.

CI bağlantıları:
- [Hex World Laboratory CI](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44274231933)
- [Core Quality Linux/Windows](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44274231885)

## 7. Kapsam koruması

Aşama 11 boyunca:

- NPC hareketi, otonom AI veya devriye eklenmedi.
- Yoldaş FOLLOW/WAIT/RETURN komutları gerçek takip hareketine dönüştürülmedi.
- Kaynak hareketi/toplama/ekonomi eklenmedi.
- Pathfinding, A*, Dijkstra, click-to-move veya savaş/görev/diyalog sistemi eklenmedi.
- Godot geçişi veya ana oyun entegrasyonu yapılmadı.
- Tek laboratuvar başlatıcısı `python -m hex_world_lab` olarak korundu.

## 8. Kalan tek kabul kapısı

Otomatik test, benchmark, Linux/Windows CI ve görsel artifact üretimi tamamlandı. Ancak kontrol listesindeki masaüstü görsel/işlevsel maddeler kullanıcı tarafından henüz doğrulanmadı. Bu nedenle Aşama 11 henüz resmen kapatılmış sayılmaz.

Kullanıcı masaüstünde `python -m hex_world_lab` komutuyla sahneyi açıp [PHASE-11-MANUAL-ACCEPTANCE-CHECKLIST.md](../docs/PHASE-11-MANUAL-ACCEPTANCE-CHECKLIST.md) maddelerini doğrulamalıdır. Görsel kabulden sonra ayrı kapanış raporu oluşturulacaktır.
