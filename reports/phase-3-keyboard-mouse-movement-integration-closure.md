# ELDORIA RPG — Aşama 3 Klavye ve Fare Hareketinin Bütünleştirilmesi Kapanış Raporu

- **Dal:** `experiment/map-cleanup`
- **Kapanış öncesi HEAD:** `b20de2b28929a13dfd46313bc21b87b5d9592a5a`
- **Tarih:** 21 Kasım 2026
- **Teknik lider:** ChatGPT
- **Proje sahibi:** Kullanıcı
- **Durum:** Uygulama ve doğrulama kapatıldı; Aşama 3.5 teknik bağımlılık nedeniyle ertelendi. Hedefe frenlemeli varış garantisi tamamlanmış kabul edilmemiştir.

---

## 1. Yönetici özeti

Aşama 3 kapsamında klavye ve fare hareketi aynı oyuncu hareket hattında birleştirildi. Fare click-to-move için tek aktif rota, waypoint cursor, cache/invalidation ve kontrollü replan sistemi oluşturuldu. Rota smoothing yalnızca aynı doğrultudaki tek ara waypoint için, statik swept collision kanıtı ile etkinleştirildi.

Aynı hedefe tekrarlanan A* sorguları kaldırıldı. 100 örnekli performans ölçümünde 100 intent çağrısı için 1 path query, 99 cache hit ve %99 sorgu azalması doğrulandı. 100 hücrelik rota için cache-hit intent p99 yaklaşık 0,041 ms ölçüldü.

Bununla birlikte iki teknik sınır açıkça korunmuştur:

1. 100 hücrelik dar koridor senaryosunda ilk A* path query p50 yaklaşık 988 ms'dir. Cache tekrar sorguları kaldırır, ilk uzun rota planının gecikmesini ortadan kaldırmaz.
2. Mevcut `MovementIntegrator` acceleration/braking veya target-aware stopping desteklemediğinden hedefi yüksek hızda aşmama garantisi verilmemiştir. Bu gereksinim Aşama 3.5 raporuyla ertelenmiştir.

Bu nedenle Aşama 3 uygulama/CI kapanışı yapılmıştır; ancak frenlemeli hedefe varış kriteri tamamlanmış değildir. Bu rapor bu sınırlamayı gizlemez.

## 2. Alt aşama kapanış tablosu

| Alt aşama | Sonuç | Kanıt / açıklama |
|---|---|---|
| 3.1 Kaynak kodu ve davranış envanteri | **Tamamlandı** | Zorunlu 10 kaynak dosyası, runtime akışı ve mevcut testler GitHub dalından doğrulandı. Kod değişikliği yapılmadan envanter raporu hazırlandı. |
| 3.2 Birleşik hareket niyeti ve komut önceliği | **Tamamlandı** | Klavye manuel hareketi fare rotasına öncelikli; Shift/Alt modları korunuyor; etkileşimler yürüme komutu üretmiyor; focus/pause davranışı test edildi. |
| 3.3 Rota cache ve invalidation | **Tamamlandı** | Tek aktif oyuncu rotası, waypoint cursor, cache hit/miss, runtime/map/snapshot/actor/goal invalidation ve sınırlı replan uygulandı. |
| 3.4 Waypoint takibi ve path smoothing | **Tamamlandı** | Tek ara waypoint'lik collinear smoothing, swept-clearance kanıtı ve cursor segmentine bağlı proof cache eklendi. Dönüş waypoint'leri atlanmıyor. |
| 3.5 Hedefe yaklaşma ve durma | **Ertelendi** | Integrator acceleration/braking ve target-aware displacement cap desteklemiyor. 0,5 dünya birimi arrival tolerance korunuyor; yüksek hızda overshoot önleme garantisi verilmedi. |
| 3.6 Performans ve kalite doğrulaması | **Tamamlandı** | 1/10/100 hücre rotaları, 100 örnek, path p50/p95/p99, cache-hit adım süreleri, cache/replan sayaçları ve CI doğrulamaları tamamlandı. |

## 3. Gerçekleştirilen teknik değişiklikler

### 3.1 Kaynak envanteri

`reports/phase-3.1-keyboard-mouse-movement-inventory.md` dosyasında aşağıdaki gerçek modüller incelendi:

- `game_ui/movement_input.py`
- `game_ui/input.py`
- `game_ui/world_rendering/hex_gameplay_view.py`
- `game_ui/game_window.py`
- `application/continuous_player_movement.py`
- `application/gameplay_step_clock.py`
- `application/hex_world_runtime.py`
- `application/hex_pathfinding.py`
- `application/hex_physics_bridge.py`
- `application/hex_occupancy.py`

Ek olarak `core/domain/movement/integrator.py` incelenerek ivmelenme/frenleme desteği doğrulandı.

### 3.2 Birleşik input ve komut önceliği

- Manuel klavye hareketi click-to-move rotasını iptal eder ve aynı fixed step'te önceliklidir.
- Fare yalnızca yön niyeti üretir; NORMAL/RUNNING/STEALTH modu mevcut klavye hareket adapter'ından alınır.
- Shift ve Alt modları korunur.
- NPC/nesne tıklamaları etkileşim/inceleme akışında kalır; yürüme hedefi üretmez.
- Sağ tık aktif fare hedefini temizler.
- Focus kaybında klavye intent'i sıfırlanır; mevcut ürün davranışı olarak aktif fare rotası devam eder.
- Pause sırasında fizik yürütülmez; pause/resume sonrasında fare hedefi korunur.

### 3.3 Click-to-move route controller

Yeni `application/click_move_route.py` modülü tek oyuncunun tek aktif click-to-move rotasını yönetir. Genel amaçlı path cache veya NPC cache'i değildir.

Route state runtime, actor, map, hedef, immutable physics snapshot ve body bağlamına bağlıdır. Oyuncu konumu her adımda `HexWorldRuntime` üzerinden okunur. Yeni hedef, runtime/map/snapshot/body değişikliği veya oyuncunun kalan route suffix'inden sapması kontrollü replan/invalidation üretir.

Statik edge kontrolleri A* planı sırasında immutable snapshot edge validator'ıyla yapılır. Snapshot değişmediği sürece aynı statik collision sorguları fixed step başına tekrarlanmaz. Map mask ve mutable occupancy her fixed step'te kontrol edilir. Swept-clearance smoothing kanıtı cursor segmenti için cache'lenir; oyuncu kanıtlanan segmentten saparsa yeniden hesaplanır.

Bir intent çağrısında en fazla bir replan yapılır. Replan sonrası ilk edge de geçersizse komut güvenli biçimde sonlandırılır.

### 3.4 Smoothing güvenliği

Smoothing yalnızca iki ardışık axial edge aynı doğrultudaysa tek ara waypoint'i atlayabilir. İkinci hücre için map mask/occupancy kontrolü yapılır. Statik edge'ler A* sırasında doğrulanmıştır; ayrıca mevcut runtime konumundan aday waypoint'e swept collision ön kontrolü yapılır. Impact, penetration veya tam displacement eşleşmemesi halinde bir sonraki waypoint'e geri dönülür.

Gerçek hareket mevcut integrator, collision resolver ve runtime commit hattında kalır. Collision resolver devre dışı bırakılmamıştır.

### 3.5 Ölçüm altyapısı

- `scripts/benchmark_player_click_move.py` gerçek `HexWorldRuntime`, A* ve immutable physics snapshot ile 1/10/100 hücre rotalarını ölçer.
- `.github/workflows/player-click-move-benchmark.yml` benchmark'ı Linux/Python 3.12 üzerinde 100 örnekle çalıştırır ve JSON artifact üretir.
- `.github/workflows/core-quality.yml` Ruff kapsamına yeni route controller, test ve benchmark script'ini ekler.
- Yeni bağımlılık eklenmemiştir.

## 4. Performans sonuçları

Benchmark: workflow `44882884811`, job `136781805273`, 100 örnek/rota, Python 3.12.16, GitHub-hosted Linux.

### Path planning

| Rota | Baseline p50 | Baseline p95 | Baseline p99 |
|---:|---:|---:|---:|
| 1 hücre | 0,239 ms | 0,254 ms | 0,278 ms |
| 10 hücre | 11,654 ms | 11,830 ms | 11,916 ms |
| 100 hücre | 987,757 ms | 1.007,207 ms | 1.017,401 ms |

Controller'ın bağımsız plan örnekleri baseline ile aynı seviyededir. Cache ilk A* sorgusunun maliyetini azaltmaz.

### Cache-hit intent adımı

| Rota | p50 | p95 | p99 |
|---:|---:|---:|---:|
| 1 hücre | 0,021 ms | 0,025 ms | 0,029 ms |
| 10 hücre | 0,023 ms | 0,028 ms | 0,033 ms |
| 100 hücre | 0,024 ms | 0,029 ms | 0,041 ms |

100 hücrelik rota cache-hit p99 değeri yaklaşık 0,041 ms'dir; GitHub runner ölçümünde 60 Hz fixed-step bütçesi olan 16,67 ms'nin çok altındadır.

### Cache sayaçları

100 intent çağrısında her üç senaryo için:
- Path query: 1
- Cache miss: 1
- Cache hit: 99
- Cache hit oranı: %99
- Path query azalması: %99
- Replan: 0
- Invalidation: 0
- Blocked step: 0
- Failure: 0

### Kalan performans riski

100 hücrelik tek hücre genişliğindeki axial koridorda ilk path query p50 yaklaşık 988 ms'dir. Bu stres senaryosu her dünya haritasının ortalaması değildir; yine de uzun click-to-move rotalarında ilk komut gecikmesi riski olarak kaydedilmiştir. Bu maliyetin azaltılması ayrı bir pathfinding/static collision edge validation incelemesi gerektirir.

Oyuncu click-to-move ölçümleri Aşama 2 NPC kaçınma pathfinding p95 ölçümleriyle birleştirilmemiştir.

Hedefe gerçek varış süresi ölçülmemiştir; Aşama 3.5 bağımlılığı nedeniyle bu metrik üretilmemiştir.

## 5. Test ve kalite doğrulaması

Son kaynak/test davranışı için GitHub Actions:

- **Eldoria CI:** `44882884853`
- **Core Quality:** `44882884795`
- **NPC spatial benchmark:** `44882633343`
- **Player click-move benchmark:** `44882884811`

### Pytest matrisi

| Platform | Python | Sonuç |
|---|---:|---|
| Ubuntu | 3.11 | **2.466 passed** |
| Ubuntu | 3.12 | **2.466 passed** |
| Windows | 3.11 | **2.466 passed** |
| Windows | 3.12 | **2.466 passed** |

Her matris koşusunda 59 warning ve 260 subtest passed raporlandı. Test başarısızlığı yoktur.

### Diğer kontroller

- Ruff: **All checks passed**
- Core Quality Linux verify: başarılı
- Core Quality Windows verify: başarılı
- Release-candidate verification: başarılı
- Pygame headless smoke test: başarılı
- Aşama 2 NPC spatial benchmark baseline ve benchmark job'ları: başarılı
- Player click-move benchmark 100 örnek: başarılı, JSON artifact yüklendi

Uyarıların başlıcaları mevcut `pygame.image.tostring` deprecation warning'leri ve GitHub Actions runner'ın Node.js 20 action uyarısıdır; bunlar test başarısızlığı değildir.

## 6. Korunan mimari kararlar — kabul kontrolü

| Mimari karar | Sonuç |
|---|---|
| Klavye ve fare aynı ContinuousPlayerMovementController/fizik hattını kullanır | **Korundu** |
| HexWorldRuntime oyuncunun kanonik konum sahibidir | **Korundu** |
| NPC ve oyuncu hareket optimizasyonları ayrıdır | **Korundu** |
| Aşama 2 NPC algılama/çevre tarama optimizasyonları | **Korundu; NPC benchmark başarılı** |
| NPC davranış orkestrasyon sırası | **Değiştirilmedi** |
| Spatial index/occupancy yanlış negatif riski | **Spatial index ve occupancy algoritmaları değiştirilmedi** |
| 60 Hz fixed-step sözleşmesi | **Korundu** |
| Collision resolver | **Devrede; devre dışı bırakılmadı** |
| Authoritative runtime konumu | **Korundu; görsel konum kullanılmadı** |
| Gereksiz mimari katman/bağımlılık | **Eklenmedi; yalnızca tek oyuncu route controller ve benchmark altyapısı eklendi** |

## 7. Önemli commit'ler

- Aşama 3.1 envanter tabanı: `dcd31cbacaec0fdee905891de05ec3212fd4c27b`
- Aşama 3.2 birleşik input: `51fe2f486e79c043cfa51061ec34a7e7e9af5270`
- Aşama 3.3 route cache ilk uygulama: `d8625de5cda6920eff1a9039fc79758cc7f3092b`
- Aşama 3.3 cache/metrics düzeltmesi: `cf574b029ea4ba57ce6f95e545430ede9130aabe`
- Aşama 3.4 swept collision doğrulamalı smoothing: `62bc84b7ad41ba5ec0e4492f0591018990e66e60`
- Aşama 3.6 cached swept proof / fixed-step performans optimizasyonu: `368ac08aa60b21e520c167119dcafbba50879f79`
- Static edge doğrulamasının snapshot-scope regresyon testi: `b93765e4b1d584ef17e2ad5c57504c96c0148fec`
- Player benchmark workflow: `a96077270573be388537d28604662c40621a975c`

## 8. Rapor ve artefakt listesi

1. `reports/phase-3.1-keyboard-mouse-movement-inventory.md`
2. `reports/phase-3.2-input-arbitration-closure.md`
3. `reports/phase-3.3-click-move-route-cache-closure.md`
4. `reports/phase-3.4-waypoint-smoothing-closure.md`
5. `reports/phase-3.5-target-approach-stopping-assessment.md`
6. `reports/phase-3.6-player-click-move-performance.md`
7. `reports/phase-3.6-player-click-move-benchmark.json`
8. `reports/phase-3-keyboard-mouse-movement-integration-closure.md` (bu rapor)

## 9. GitHub çalışma disiplini ve son durum

- Çalışma yalnızca `experiment/map-cleanup` dalında yapıldı.
- Ana dala merge yapılmadı.
- Başka dala geçilmedi.
- Kullanıcıdan gelen yerel değişiklikleri ezebilecek bir local checkout işlemi yapılmadı; GitHub remote branch üzerinden dosya/commit işlemleri gerçekleştirildi.
- GitHub remote branch değişiklikleri commit edilmiştir. Kullanıcının bilgisayarındaki commit edilmemiş yerel working tree durumu GitHub üzerinden görülemez ve bu raporda temiz olduğu iddia edilmez.

**Yeni bir aşamaya başlanmadı.** Bu kapanış raporundan sonra çalışma durdurulmuştur. Sonraki aşamaya geçiş için proje sahibinin onayı beklenecektir.

---

## 10. Nihai karar

Aşama 3'ün input bütünleştirme, route cache/invalidation, güvenli waypoint smoothing, performans ölçümü ve CI doğrulaması tamamlandı.

Aşama 3.5 hedefe frenlemeli yaklaşma/durma garantisi, mevcut MovementIntegrator bağımlılığı nedeniyle açıkça ertelenmiştir. Bu nedenle Aşama 3, **bir teknik bağımlılığı belgelenmiş olarak kapatılmıştır**; yüksek hızda hedefi aşmama kriteri tamamlandı veya kanıtlandı şeklinde sunulmamaktadır.

100 hücrelik ilk A* sorgusunun yaklaşık 1 saniyelik gecikmesi de sonraki pathfinding performans incelemesi için açık risk olarak bırakılmıştır.

Proje sahibinin onayı olmadan yeni aşamaya geçilmeyecektir.
