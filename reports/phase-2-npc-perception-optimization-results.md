# Aşama 2 — NPC Algılama ve Çevre Tarama Optimizasyonu Teknik Sonuç Raporu

**Durum:** Uygulama, karşılaştırmalı benchmark ve CI doğrulamaları tamamlandı. Resmî Aşama 2 kapanış raporu, kullanıcı onayı sonrasında hazırlanacaktır.

## 1. Kapsam ve referanslar

- Çalışma dalı: `experiment/map-cleanup`
- Mimari plan: `reports/phase-2-npc-perception-environment-scan-architecture-plan.md`
- Aşama 2.1 envanteri: `reports/phase-2.1-npc-perception-code-inventory.md`
- Karşılaştırma başlangıç commit'i (optimizasyon öncesi): `cd8196f426468d0ee853fd32cd77513a44f4cbcd`
- Ölçülen optimize edilmiş commit: `8d40d6d1fde6bb8a3fb400f19a3b3958cb09bab1`

Bu çalışma, Aşama 1'de kapatılan merkezi NPC simülasyon orkestrasyonunu değiştirmedi. Devriye → kaçınma → yoldaş güncelleme sırası ve aynı simülasyon adımıyla çalışma sözleşmesi korundu.

## 2. Uygulanan teknik değişiklikler

### 2.1 İsteğe bağlı ölçüm altyapısı

Yeni `application/npc_simulation_metrics.py` modülü, runtime'a isteğe bağlı bağlanan `NPCSimulationMetrics` sınıfını sağlar. Ölçüm nesnesi bağlanmadığında sistem adımları saat okumaz ve ölçüm örneği üretmez.

Kaydedilen başlıca değerler:

- Devriye, kaçınma, yoldaş ve toplam NPC simülasyon adımı süreleri
- NPC kayıt taraması ve davranışa uygun NPC sayıları
- Kaçınma tehdit mesafesi kontrolleri ve yarıçap nedeniyle elenen NPC'ler
- Yoldaş hedef yenileme sayıları
- Runtime entity doğrulama, path sorgusu, mekânsal sorgu ve aday sayıları
- Pathfinder arama süresi
- NPC/NPC overlap çözümleyici çağrısı, mekânsal sorguları ve ayrı çalışma süresi

Süre özetleri p50, p95, p99, medyan, toplam ve maksimum değerleri içerir.

### 2.2 Tekrarlanan entity doğrulamalarının kaldırılması

`HexMovableEntity` görünümü, doğrulanmış `continuous_position` bilgisini zaten taşır. Aynı entity için hemen ardından `runtime.continuous_position(...)` çağrısı yapmak ikinci bir `entity()` doğrulaması ve mekânsal indeks tutarlılık kontrolü oluşturuyordu.

Bu tekrarlar aşağıdaki noktalarda kaldırıldı:

- `NPCBehaviorSystem`
- `NPCAvoidanceSystem`
- `CompanionCommandService`
- `HexWorldRuntime.patrol_target`
- `HexGameplayView._advance_npc_visuals`

Her simülasyon aşaması kendi güncel entity görünümünü almaya devam eder. Aşamalar arasında ortak, uzun ömürlü bir tick snapshot/cache oluşturulmadı; çünkü devriye aşaması konumları değiştirdikten sonra kaçınma ve yoldaş aşamalarının güncel konumu görmesi gerekir.

### 2.3 Mekânsal aday taraması kararı

Yeni bir spatial index eklenmedi. Mevcut `UniformGridIndex` ve `query_spatial_candidates` API'si ayrıştırma, separation ve overlap sorgularında kullanılmaya devam ediyor.

Kaçınma sisteminin tüm NPC kayıtlarını taramasını doğrudan spatial AABB aday sorgusuna dönüştürmedim. Tehdit mesafesi aktörün sürekli konum/anchor noktasına göre hesaplanırken indeks collider AABB'sini tutuyor; collider yerel ofseti nedeniyle yalnızca collider AABB'sine göre yapılan yarıçap sorgusu, anchor'ı yarıçap içinde olan bir NPC'yi dışarıda bırakabilir. Davranış sözleşmesini riske atan bu aday filtresi uygulanmadı.

Devriye ve yoldaş taramaları da davranış türüne/komut durumuna göre tüm ilgili kayıtları işler; bunlar için güvenli bir yakınlık filtresi bulunmuyor.

### 2.4 Mantıksal simülasyon ve görsel güncelleme

NPC mantıksal simülasyonu sabit adımlı gameplay güncellemesinde, görsel interpolasyon ise render güncellemesinde kalmaya devam ediyor. Kamera dışında kalan NPC'lerin simülasyonunu durduran LOD/culling davranışı eklenmedi. Görsel güncellemede de mevcut entity görünümünün sürekli konumu yeniden doğrulatılmadan kullanılıyor.

## 3. Karşılaştırmalı benchmark yöntemi

Benchmark, aynı `scripts/benchmark_npc_perception.py` betiği ve aynı ölçüm modülüyle iki ayrı kod revizyonunda çalıştırıldı:

- Baseline: `cd8196f426468d0ee853fd32cd77513a44f4cbcd`
- Optimize: `8d40d6d1fde6bb8a3fb400f19a3b3958cb09bab1`

Her revizyonda 1, 10, 25, 50 ve 100 NPC senaryoları; iki profil; 3 tekrar; her tekrar öncesinde ayrı bir dünyada 2 ısınma adımı ve ölçülen dünyada 4 adım kullanıldı. İki iş aynı Ubuntu GitHub Actions runner ailesinde ve Python 3.12 ile yürütüldü.

İki profil kullanıldı:

- **scan:** FLEE NPC'leri tehdit yarıçapının dışında tutulur, devriye rotası mevcut hücrede kalır, yoldaşlara WAIT komutu verilir. Pathfinding olmadan kayıt taraması ve tehdit mesafesi kontrolleri ölçülür.
- **active:** FLEE NPC'leri oyuncuya yakın konumlandırılır, devriye hedefi ileridedir ve yoldaşlar FOLLOW komutundadır. Aktif davranış, path sorguları ve kaçınma maliyeti ölçülür.

25/50/100 NPC senaryolarında ilk 18 NPC sabit bir davranış dağılımına sahiptir (6 devriye, 6 kaçınma, 6 yoldaş); kalan NPC'ler IDLE'dır. Böylece toplam kayıt sayısı büyürken etkin davranış yoğunluğu sabit kalır. 1 ve 10 NPC senaryolarında mevcut NPC'lerin tamamı yönetilen davranış grubundadır.

Bu benchmark algılama/karar maliyetini overlap fiziğinden ayırmak için devriye ve yoldaş fizik gövdelerini devre dışı bırakıp bu iki sistemde mantıksal hareket kullanır; FLEE gövdeleri etkindir. Bu nedenle sonuçlar kontrollü NPC algılama/AI iş yükünü temsil eder, tam fiziksel dünya benchmark'ı değildir.

## 4. Ölçüm sonuçları

### 4.1 Entity doğrulama sayısı

Aşağıdaki sayılar her senaryo için 3 tekrar ve 4 ölçüm adımının toplamıdır.

| Profil | NPC | Baseline | Optimize | Azalma |
|---|---:|---:|---:|---:|
| scan | 1 | 108 | 60 | %44,4 |
| scan | 10 | 432 | 276 | %36,1 |
| scan | 25 | 696 | 456 | %34,5 |
| scan | 50 | 696 | 456 | %34,5 |
| scan | 100 | 696 | 456 | %34,5 |
| active | 1 | 120 | 72 | %40,0 |
| active | 10 | 651 | 459 | %29,5 |
| active | 25 | 996 | 684 | %31,3 |
| active | 50 | 996 | 684 | %31,3 |
| active | 100 | 996 | 684 | %31,3 |

### 4.2 Toplam NPC simülasyon adımı süresi

Değerler milisaniyedir; her hücre baseline → optimize biçimindedir.

| Profil | NPC | p50 | p95 |
|---|---:|---:|---:|
| scan | 1 | 0,203 → 0,115 | 0,274 → 0,180 |
| scan | 10 | 0,792 → 0,489 | 0,850 → 0,564 |
| scan | 25 | 1,296 → 0,814 | 1,431 → 0,901 |
| scan | 50 | 1,309 → 0,821 | 1,379 → 0,890 |
| scan | 100 | 1,361 → 0,855 | 1,429 → 0,955 |
| active | 1 | 0,338 → 0,241 | 0,441 → 0,333 |
| active | 10 | 264,859 → 222,463 | 301,190 → 255,499 |
| active | 25 | 465,952 → 390,549 | 473,156 → 402,414 |
| active | 50 | 469,455 → 400,674 | 477,571 → 414,944 |
| active | 100 | 470,744 → 391,397 | 502,211 → 441,030 |

Özet:

- Scan profilinde p50 toplam adım süresi NPC sayısına göre yaklaşık %37–43 azaldı.
- Active profilinde 10–100 NPC aralığında p50 toplam adım süresi yaklaşık %15–17 azaldı.
- Entity doğrulama sayısı iki profilde de yaklaşık %29–44 azaldı.
- Path sorgusu sayısı baseline ve optimize revizyonlarında aynı kaldı. Kazanç, davranış/path sorgularını azaltmaktan değil, zaten doğrulanmış konumu yeniden doğrulatmaktan kaçınmaktan geldi.

### 4.3 Tarama ve pathfinding davranışı

- `patrol_registry_scanned` ve `avoidance_registry_scanned` sayaçları NPC sayısıyla aynı şekilde büyümeye devam etti. Bu aşamada tam kayıt taraması kaldırılmadı.
- Scan profilinde path sorgusu oluşmadı ve 16,67 ms eşiğini aşan simülasyon adımı görülmedi.
- Active profilde 10/25/50/100 NPC senaryolarında 12 ölçüm adımının 12'si 16,67 ms eşiğini aştı. Bu, kaçınma pathfinding işinin ayrı bir darboğaz olduğunu gösteriyor.
- Optimize sürümde pathfinder arama süresinin p95 değeri active profilde 10–100 NPC senaryolarında yaklaşık 66–74 ms aralığındaydı.
- Optimize sürümde overlap çift çözümleme p50 süresi yaklaşık 0,14–0,27 ms aralığında kaldı; active profilin yüzlerce milisaniyelik toplam süresini açıklayan ana maliyet overlap değil, kaçınma/pathfinding zinciridir.

Pathfinding algoritmasının kendisi bu aşamanın kapsamı dışında tutuldu. Dolayısıyla active profilin 16,67 ms eşiği üzerindeki sıçramaları giderilmiş değildir; sonraki performans çalışması için açık bulgu olarak bırakılmıştır.

## 5. Test ve CI doğrulamaları

Optimize edilmiş kod commit'i `8d40d6d1fde6bb8a3fb400f19a3b3958cb09bab1` üzerinde:

- **Eldoria CI:** başarılı — Windows/Linux, Python 3.11/3.12 test matrisi
- **Pytest:** `2445 passed, 59 warnings, 260 subtests passed` (Python 3.11 Ubuntu job, 26,41 saniye)
- **Unittest discovery:** dört platform/Python test job'unda başarılı
- **Ruff:** değiştirilen NPC runtime, davranış, kaçınma, yoldaş, çarpışma, görsel güncelleme, benchmark ve test dosyalarında başarılı
- **Pygame headless smoke test:** başarılı; izometrik dünya ve actor pipeline render doğrulaması başarılı
- **Core Quality:** Linux ve Windows doğrulama job'ları başarılı
- **NPC spatial benchmark workflow:** optimized benchmark ve pre-optimization baseline job'ları başarılı

İş akışı kayıtları:

- [Eldoria CI — run 44878219653](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44878219653)
- [Core Quality — run 44878219783](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44878219783)
- [NPC spatial/perception benchmark ve baseline — run 44878219693](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44878219693)

## 6. Kalan riskler ve sonraki aşama girdileri

1. Kaçınma sisteminde FLEE NPC'ler için escape-cell adayları başına ayrı path sorguları oluşabiliyor. Active benchmark'ta yüksek p95 ve 16,67 ms üzeri adım sıçramalarının ana kaynağı budur.
2. Patrol ve avoidance kayıt taramaları hâlâ O(N) ölçeğindedir. Spatial AABB aday sorgusunun actor anchor noktasına göre yanlış negatif üretebilme riski giderilmeden tarama daraltılmamalıdır.
3. Tick genelinde ortak snapshot/cache oluşturulmadı. Sistem sırası içinde pozisyon değiştiği için aşamalar arası snapshot güncelliği ayrıca tasarlanmadan cache eklenmemelidir.
4. Bu benchmark kontrollü bir yük profilidir; gerçek harita yoğunluğu, gerçek NPC davranış dağılımı ve farklı donanımlar için mutlak FPS garantisi vermez.

**Teknik değerlendirme:** Aşama 2 kapsamında doğrulanmış entity konumlarının gereksiz tekrar doğrulanması giderildi ve bu değişiklik aynı benchmark koşullarında %29–44 daha az entity doğrulaması ile ölçüldü. Kayıt taramalarını spatial aday sorgusuyla değiştirmek güvenli olmadığı için uygulanmadı. Pathfinding darboğazı ölçüldü ve sonraki aşamaya açık bulgu olarak aktarıldı.
