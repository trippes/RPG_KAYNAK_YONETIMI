# Eldoria — Aşama 2 Kapanış Raporu
## NPC Algılama ve Çevre Tarama Maliyetlerinin Azaltılması

- **Proje:** Eldoria RPG
- **Depo:** `trippes/RPG_KAYNAK_YONETIMI`
- **Dal:** `experiment/map-cleanup`
- **Aşama:** 2 — NPC algılama ve çevre tarama maliyetlerinin azaltılması
- **Durum:** Tamamlandı
- **Rapor türü:** Teknik uygulama, performans karşılaştırması ve doğrulama kapanışı
- **Dayanak mimari plan:** `reports/phase-2-npc-perception-environment-scan-architecture-plan.md`
- **Aşama 1 kapanış raporu:** `reports/phase-1-npc-simulation-orchestration-closure.md`
- **Aşama 2.1 envanter raporu:** `reports/phase-2.1-npc-perception-code-inventory.md`
- **Aşama 2 teknik sonuç raporu:** `reports/phase-2-npc-perception-optimization-results.md`

---

## 1. Yönetici özeti

Aşama 2'nin amacı NPC algılama ve çevre tarama maliyetlerini kaynak kodu üzerinden çıkarmak, gerçek darboğazları ölçmek ve mevcut davranış kurallarını değiştirmeden güvenli optimizasyonları uygulamaktı.

Çalışma altı alt aşamada yürütüldü: kod envanteri ve davranış sözleşmesi, ölçüm altyapısı ve baseline, aday üretimi/mekânsal indeks değerlendirmesi, tekrarlı sorguların kontrollü azaltılması, mantıksal simülasyon ile görsel güncellemenin ayrımı ve son doğrulamalar.

Başlıca uygulama sonucu, NPC entity görünümü üzerinden zaten doğrulanmış sürekli konumun hemen ardından tekrar `runtime.continuous_position(...)` çağrılarak aynı entity doğrulamasının ve mekânsal indeks tutarlılık kontrolünün yeniden yapılmasının önlenmesidir. Bu tekrarlar devriye, kaçınma, yoldaş komutları, runtime hedef çözümleme ve görsel güncelleme yollarında giderildi.

Aynı koşullarda yapılan baseline/optimize benchmark karşılaştırmasında entity doğrulama sayısı senaryoya göre **%29,5–44,4** azaldı. Toplam NPC simülasyon adımı p50 süresi scan profilinde yaklaşık **%37–43**, aktif davranış profilinde 10–100 NPC aralığında yaklaşık **%14,6–16,9** iyileşti.

Her tam registry taramasını spatial query ile değiştirmek güvenli olmadığı için yapılmadı. İncelenen mevcut indeks collider AABB verisi üzerinden aday üretirken tehdit mesafesi actor anchor/continuous position üzerinden değerlendiriliyor. Collider yerel ofseti, yalnızca AABB sorgusuyla geçerli bir anchor adayının kaybedilmesi riskini doğurabilir. Bu nedenle davranış eşdeğerliği kanıtlanmamış bir broad-phase filtresi eklenmedi.

Aktif kaçınma profilinde pathfinding kaynaklı yüksek gecikme tespit edildi. Bu darboğaz ölçüldü ancak Aşama 2'nin kapsamı dışında olan pathfinding algoritması değiştirilmedi; bulgu sonraki performans çalışmasına devredildi.

**Kapanış kararı:** Aşama 2'nin tanımlı kapsamındaki envanter, ölçüm, güvenli tekrar doğrulama optimizasyonu, benchmark ve otomatik doğrulama işleri tamamlandı. Aşağıda belirtilen pathfinding ve tam registry taraması konuları çözülmüş kabul edilmemektedir.

## 2. Başlangıç mimarisi ve Aşama 1'den devralınan sözleşme

Aşama 1'de oluşturulan merkezi giriş noktası korunmuştur:

```text
GameplayService.advance_npc_simulation(dt)
    ├── advance_npc_patrols(dt)
    ├── advance_npc_avoidance(dt)
    └── advance_companions(dt)
```

Aşağıdaki sözleşmeler Aşama 2 boyunca değiştirilmedi:

1. Merkezi orkestrasyon sahibi `GameplayService` olarak kaldı.
2. Devriye → kaçınma → yoldaş güncelleme sırası korundu.
3. Alt sistemlere aynı sabit zaman adımı aktarıldı.
4. NPC davranış kararları, PATROL/FLEE/FOLLOW/WAIT anlamları ve mevcut eşikler değiştirilmedi.
5. Alt sistemlerin sıralı hareket güncellemelerinden sonra güncel konumları görmesi korundu; alt sistemler arasında eski veri taşıyan ortak bir tick snapshot/cache eklenmedi.
6. Aşama 1'deki kaçınma sistemi nesnesi cache yaşam döngüsüne müdahale edilmedi.
7. NPC overlap/fizik çözümünün davranış sahipliği ve çağrı noktaları değiştirilmedi.
8. Kamera görünürlüğü, NPC mantıksal simülasyonunu durdurmak için kullanılmadı.

Aşama 1 raporunda da belirtildiği gibi sistem nesnesinin yeniden kullanılması, algılama sonuçlarının veya konum sorgularının otomatik olarak cache'lendiği anlamına gelmiyordu. Aşama 2 bu ayrı maliyet sınıfını ele aldı.

## 3. Alt aşamaların tamamlanma durumu

### 2.1 — Kod envanteri ve davranış sözleşmesi

**Tamamlandı.**

Devriye, kaçınma ve yoldaş sistemlerinin çağrı zinciri; registry taramaları; entity/position erişimleri; path sorgusu noktaları; mevcut mekânsal indeksin rolü ve overlap çözümünün ayrı maliyet sınıfı olduğu belgelendi.

İncelenen ana alanlar:
- `application/gameplay_service.py`
- `application/npc_behavior_system.py`
- `application/npc_avoidance.py`
- `application/companion_commands.py`
- `application/hex_world_runtime.py`
- `core/domain/spatial/uniform_grid_index.py`
- `application/dynamic_actor_collision.py`
- `application/hex_actor_binding.py`
- `application/hex_physics_bridge.py`
- İlgili NPC davranış, kaçınma, yoldaş, orkestrasyon ve dinamik çarpışma testleri

Çıkış belgesi: [Aşama 2.1 kod envanteri](phase-2.1-npc-perception-code-inventory.md).

### 2.2 — Ölçüm altyapısı ve baseline

**Tamamlandı.**

İsteğe bağlı ölçüm altyapısı `application/npc_simulation_metrics.py` içinde oluşturuldu. Ölçüm nesnesi bağlanmadığında simülasyon adımları zaman okuma/örnek toplama maliyetine girmez.

Ölçüm kapsamı:
- Devriye, kaçınma, yoldaş ve toplam simülasyon adımı süreleri
- Registry tarama ve uygun aktör sayıları
- Tehdit mesafesi kontrolleri ve yarıçap nedeniyle elenen NPC'ler
- Yoldaş hedef yenilemeleri
- Entity doğrulama, path sorgusu, spatial query ve aday sayıları
- Pathfinder arama süresi
- Overlap çözümleyici çağrıları, spatial query ve ayrı overlap süresi

Süre dağılımları p50, p95, p99, ortalama/toplam ve maksimum değerlerle raporlanabilir hâle getirildi.

### 2.3 — Aday üretimi ve mekânsal indeks değerlendirmesi

**Tamamlandı; güvenli olmayan aday filtresi uygulanmadı.**

Mevcut `UniformGridIndex` ve `query_spatial_candidates(map_id, bounds)` altyapısı doğrulandı. Yeni bir paralel spatial index eklenmedi.

Kaçınma sisteminin tam registry taramasını doğrudan collider AABB sorgusuna çevirmek, anchor noktası üzerinden yapılan mevcut kesin mesafe kontrolüyle aynı aday kümesini garanti etmiyor. Collider yerel ofseti nedeniyle yanlış negatif olasılığı bulunduğundan bu değişiklik uygulanmadı. Devriye ve yoldaş taramaları da yakınlık temelli değil, davranış/komut uygunluğu temelli taramalar olduğundan aynı spatial filtreye uygun değildi.

Bu karar optimizasyon eksikliği değil, mevcut davranış sözleşmesini kanıtlanmamış bir broad-phase filtresiyle riske atmama kararıdır.

### 2.4 — Tekrarlı sorguların kontrollü azaltılması

**Tamamlandı.**

`HexMovableEntity` görünümünden alınan sürekli konum zaten entity doğrulaması içermektedir. Aynı entity için hemen ardından `runtime.continuous_position(entity_id)` çağırmak ikinci bir `entity()` doğrulaması ve indeks tutarlılık kontrolü oluşturuyordu.

Bu gereksiz tekrarlar şu alanlarda kaldırıldı:
- `NPCBehaviorSystem`
- `NPCAvoidanceSystem`
- `CompanionCommandService`
- `HexWorldRuntime.patrol_target`
- `HexGameplayView._advance_npc_visuals`

Her simülasyon alt sistemi kendi güncel entity görünümünü almaya devam eder. Devriye hareketinden sonra kaçınma ve yoldaş sistemlerinin güncel konumu görmesi gerektiği için alt sistemler arasında ortak, eskiyebilecek snapshot/cache kurulmadı.

### 2.5 — Mantıksal simülasyon ve görsel güncelleme ayrımı

**Tamamlandı.**

NPC mantıksal simülasyonu sabit adımlı gameplay güncellemesinde kaldı; görsel interpolasyon/render güncellemesi sunum akışında kaldı. Görsel güncelleme yolundaki tekrarlı konum doğrulaması kaldırıldı.

Kamera dışı NPC'lerin mantıksal simülasyonunu durduran bir LOD/culling davranışı eklenmedi. Görünürlük, dünya açısından önemli davranış/algılamayı kesmek için kullanılmadı.

### 2.6 — Regresyon, benchmark ve CI doğrulaması

**Tamamlandı.**

Aşağıdaki test, benchmark ve kalite doğrulamaları çalıştırıldı. Son dal commit'i üzerinde Eldoria CI ve Core Quality workflow'ları da yeniden doğrulandı.

## 4. Karşılaştırmalı benchmark yöntemi

Baseline ve optimize sürümleri aynı benchmark betiği ve ölçüm altyapısıyla karşılaştırıldı:

- **Baseline commit:** `cd8196f426468d0ee853fd32cd77513a44f4cbcd`
- **Optimize edilmiş kod commit'i:** `8d40d6d1fde6bb8a3fb400f19a3b3958cb09bab1`
- **Kapanış raporu öncesi dal commit'i:** `e20e8dfd7cdd6d17fa9a982f13c6a2027a7bed7a`

Ölçekler: 1, 10, 25, 50 ve 100 NPC.

Her ölçek/profil için:
- 3 tekrar,
- her tekrar öncesi ayrı dünyada 2 ısınma adımı,
- ölçülen dünyada 4 simülasyon adımı kullanıldı.

Baseline ve optimize benchmark'ları aynı Ubuntu GitHub Actions runner ailesinde ve Python 3.12 ile çalıştırıldı.

İki farklı profil kullanıldı:

**scan profili:** FLEE NPC'leri oyuncu tehdit yarıçapı dışında; devriye rotası mevcut hücrede; yoldaş komutu WAIT. Böylece pathfinding tetiklenmeden registry taraması ve tehdit mesafesi kontrol maliyeti ölçüldü.

**active profili:** FLEE NPC'leri oyuncuya yakın; devriye hedefi ileride; yoldaşlar FOLLOW komutunda. Böylece gerçek aktif davranış zinciri ve path sorgusu maliyeti gözlemlendi.

25/50/100 NPC senaryolarında ilk 18 NPC sabit dağılımla (6 devriye, 6 kaçınma, 6 yoldaş) yönetildi; kalan NPC'ler IDLE bırakıldı. Bu yöntem toplam registry büyürken aktif davranış yoğunluğunu sabit tuttu. 1 ve 10 NPC senaryolarında mevcut NPC'lerin tamamı yönetilen gruptaydı.

Benchmark, algılama/karar maliyetini overlap fiziğinden ayırmak için devriye ve yoldaş fizik gövdelerini devre dışı bırakıp mantıksal hareket kullandı; FLEE gövdeleri etkin kaldı. Bu sonuçlar kontrollü NPC algılama/AI iş yükünü temsil eder; tam fiziksel dünya veya farklı donanımlarda FPS garantisi değildir.

## 5. Ölçüm sonuçları

### 5.1. Entity doğrulama sayısı

Her değer 3 tekrar × 4 ölçüm adımının toplamıdır.

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

### 5.2. Toplam NPC simülasyon adımı süresi

Değerler milisaniyedir; p50 ve p95 için baseline → optimize biçiminde verilmiştir.

| Profil | NPC | p50 (ms) | p95 (ms) |
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

Yorum:
- Scan profilinde p50 iyileşmesi ölçeğe göre yaklaşık %37–43'tür.
- Active profilinde 1 NPC senaryosunda p50 iyileşmesi yaklaşık %28,7; 10–100 NPC senaryolarında yaklaşık %14,6–16,9'dur.
- Entity doğrulama sayısı bütün senaryolarda yaklaşık %29,5–44,4 azalmıştır.
- Path sorgusu sayısı baseline ve optimize sürümlerinde aynı kalmıştır. Kazanç, pathfinding davranışını veya hedef kararını azaltmaktan değil, aynı konumun gereksiz yere tekrar doğrulanmasını önlemekten kaynaklanmıştır.

### 5.3. Tarama ölçeklenmesi ve pathfinding bulgusu

- Devriye ve kaçınma registry tarama sayaçları NPC kayıt sayısıyla büyümeye devam etmektedir; tam tarama kaldırılmamıştır.
- Scan profilinde path sorgusu oluşmamış ve ölçülen adımlarda 16,67 ms eşiği aşılmamıştır.
- Active profilinde 10/25/50/100 NPC senaryolarının her birinde 12 ölçüm adımının 12'si 16,67 ms eşiğini aşmıştır.
- Optimize sürümde active profil pathfinder arama süresi p95'i 10–100 NPC senaryolarında yaklaşık 66–74 ms aralığındadır.
- Overlap çözümleme maliyeti ayrı ölçülmüştür ve active profilin yüzlerce milisaniyeye ulaşan adım sürelerini açıklayan ana maliyet değildir. Ana darboğaz kaçınma/pathfinding zinciridir.

**Önemli performans sınırı:** Aşama 2, aktif kaçınma profilindeki 16,67 ms üzeri adım sıçramalarını çözmüş değildir. Pathfinding algoritması kapsam dışında bırakılmış ve sonraki performans çalışmasına devredilmiştir.

## 6. Davranış eşdeğerliği ve bilinçli olarak yapılmayan değişiklikler

Aşağıdaki davranış değişiklikleri yapılmadı:
- NPC algılama/tehdit mesafeleri veya eşikleri değiştirilmedi.
- NPC davranışlarının tarama sıklığı düşürülmedi.
- Tick dışına taşan algılama sonucu cache'i eklenmedi.
- Alt sistemlerin güncel konum görünürlüğünü değiştirecek ortak snapshot eklenmedi.
- Tam registry taramaları, yanlış negatif riski bulunan AABB filtresiyle değiştirilmedi.
- Yeni spatial index eklenmedi.
- Overlap çözümleme çağrıları birleştirilmedi veya yeniden sıralanmadı.
- Kamera görünürlüğüne bağlı mantıksal NPC LOD'si eklenmedi.
- Pathfinding algoritması değiştirilmedi.

Bu sınırlar, aşamanın davranış koruma şartının parçasıdır. Bu nedenle aday taraması tarafında ölçülebilir işlem azaltımı elde edilmeyen alanlar açıkça belirtilmiştir; güvenli olmayan bir optimizasyon başarı gibi sunulmamıştır.

## 7. Test, kalite ve GitHub Actions sonuçları

### 7.1. Pytest ve unittest

Optimize edilmiş kod revizyonunda Ubuntu / Python 3.11 pytest job sonucu:
- **2.445 passed**
- **59 warnings**
- **260 subtests passed**
- Pytest çalışma süresi: yaklaşık 26,41 saniye

Windows/Linux ve Python 3.11/3.12 CI matrisindeki test job'ları başarılı tamamlandı. Unittest discovery de dört ortam job'unda başarılıydı.

### 7.2. Ruff ve Pygame

- Ruff, değiştirilen NPC runtime, davranış, kaçınma, yoldaş, çarpışma, görsel güncelleme, benchmark ve ilgili test dosyalarında başarılı.
- Pygame headless smoke test başarılı.
- İzometrik dünya ve actor pipeline render smoke doğrulaması başarılı.

### 7.3. Son dal commit'i üzerinde GitHub Actions

Kapanış raporu öncesi son dal commit'i `e20e8dfd7cdd6d17fa9a982f13c6a2027a7bed7a` için workflow'lar tekrar kontrol edildi:

**Eldoria CI — başarılı**
- [GitHub Actions run 44878519986](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44878519986)
- Windows / Python 3.11: başarılı
- Ubuntu / Python 3.11: başarılı
- Windows / Python 3.12: başarılı
- Ubuntu / Python 3.12: başarılı
- Pygame headless smoke test: başarılı

**Core Quality — başarılı**
- [GitHub Actions run 44878519975](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44878519975)
- Linux verify: başarılı
- Windows verify: başarılı

**Karşılaştırmalı benchmark**
- [NPC spatial/perception benchmark run 44878219693](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44878219693)
- Baseline ve optimize benchmark job'ları tamamlandı.

Son dal commit'inde Eldoria CI ve Core Quality'nin tüm job'ları GitHub API üzerinden `completed / success` olarak doğrulandı.

## 8. Kalan riskler ve sonraki aşamaya devredilen işler

1. **Kaçınma/pathfinding maliyeti:** FLEE aktörler için kaçış hücreleri değerlendirilirken birden fazla path sorgusu oluşabiliyor. Active benchmark'ta yüksek p95 ve frame bütçesi aşımlarının temel kaynağıdır. Ayrı pathfinding optimizasyon aşamasında ele alınmalıdır.
2. **O(N) registry taramaları:** Devriye ve kaçınma sistemleri tam kayıt taramasını sürdürmektedir. Anchor noktası ile collider AABB arasındaki fark nedeniyle mevcut spatial query'nin yanlış negatif üretmediği kanıtlanmadan filtreleme yapılmamalıdır.
3. **Tick snapshot tutarlılığı:** Alt sistemler sırayla konum değiştirdiğinden ortak snapshot tasarımı, aşamalar arası güncel veri görünürlüğünü bozabilir. Ayrı sürümleme/invalidation tasarımı olmadan eklenmemelidir.
4. **Benchmark temsil gücü:** Benchmark kontrollü ve tekrar edilebilir bir profil sağlar; gerçek oyun haritasının yoğunluğu, gerçek oyuncu davranışı, uzun süreli simülasyon ve farklı donanımlardaki sonuçları tek başına garanti etmez.
5. **Warnings:** Pytest çıktısında 59 warning raporlanmıştır. Testler başarılı olsa da bu uyarılar ayrı bakım/temizlik çalışmasında sınıflandırılabilir.

## 9. Teslim edilen belgeler ve teknik artefaktlar

- [Aşama 2 mimari planı](phase-2-npc-perception-environment-scan-architecture-plan.md)
- [Aşama 2.1 kod envanteri](phase-2.1-npc-perception-code-inventory.md)
- [Aşama 2 teknik sonuç ve benchmark raporu](phase-2-npc-perception-optimization-results.md)
- [Aşama 2 kapanış raporu](phase-2-npc-perception-optimization-closure.md)

Ana teknik artefaktlar:
- `application/npc_simulation_metrics.py`
- `scripts/benchmark_npc_perception.py`
- NPC davranış/konum erişim yollarındaki gereksiz tekrar doğrulamaların giderilmesi
- İlgili regresyon testleri ve benchmark/CI workflow sonuçları

## 10. Kabul ölçütleri ve nihai karar

| Kabul ölçütü | Sonuç |
|---|---|
| Kaynak kodu envanteri ve davranış sözleşmesi çıkarıldı | Karşılandı |
| Ölçüm altyapısı eklendi ve ölçüm maliyeti opsiyonel tutuldu | Karşılandı |
| Baseline ve optimize benchmark karşılaştırması yapıldı | Karşılandı |
| 1/10/25/50/100 NPC senaryoları çalıştırıldı | Karşılandı |
| Mevcut spatial index'in uygunluğu incelendi | Karşılandı; yanlış negatif riski nedeniyle filtre uygulanmadı |
| Tekrarlanan entity/position doğrulamaları azaltıldı | Karşılandı |
| Mantıksal simülasyon ve görsel güncelleme ayrımı korundu | Karşılandı |
| NPC davranış eşikleri ve orkestrasyon sırası korundu | Karşılandı |
| Regresyon testleri ve Ruff doğrulaması başarılı | Karşılandı |
| Windows/Linux, Python 3.11/3.12 CI matrisi başarılı | Karşılandı |
| Pygame headless smoke test başarılı | Karşılandı |
| Son dal commit'inde GitHub Actions başarılı | Karşılandı |
| Kalan darboğazlar ve kapsam dışı konular belgelendi | Karşılandı |

### Nihai karar

**Aşama 2 — NPC Algılama ve Çevre Tarama Maliyetlerinin Azaltılması tamamlanmıştır.**

Bu kapanış, bu raporda belirtilen kapsam için geçerlidir. Aktif kaçınma/pathfinding darboğazı, O(N) registry taramalarının güvenli biçimde daraltılması ve olası tick snapshot mimarisi tamamlanmış iş olarak değerlendirilmemelidir. Bunlar sonraki teknik aşamalara girdi olarak bırakılmıştır.

Aşama 1'in merkezi orkestrasyon mimarisi korunmuş; Aşama 2'de doğrulanmış konumların gereksiz tekrar doğrulanması giderilmiş ve kazanım baseline karşılaştırmasıyla ölçülmüştür.
