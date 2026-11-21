# Eldoria — Aşama 2.1 Kod Envanteri ve Davranış Sözleşmesi

- **Proje:** Eldoria RPG
- **Depo:** `trippes/RPG_KAYNAK_YONETIMI`
- **Dal:** `experiment/map-cleanup`
- **Başlangıç commit'i:** `a925f70438021a35f4316fb64dff96ac37d3b45b`
- **Aşama:** 2.1 — NPC algılama ve çevre tarama kod envanteri
- **Durum:** Kod incelemesi tamamlandı; ölçüm/baseline aşamasına geçiş için bulgular hazır
- **İnceleme tarihi:** 21 Kasım 2026
- **Dayanak:** `reports/phase-2-npc-perception-environment-scan-architecture-plan.md`
- **Önceki aşama:** `reports/phase-1-npc-simulation-orchestration-closure.md`

---

## 1. Yönetici özeti

Aşama 2.1 kapsamında NPC devriye, kaçınma ve yoldaş sistemlerinin gerçek kaynak kodu incelendi; çevre adaylarının nasıl üretildiği, hangi işlemlerin tekrarlandığı ve mevcut mekânsal indeksin sahipliği doğrulandı.

**En önemli sonuç:** Eldoria'da NPC/aktör broad-phase sorgusu için kullanılabilir bir mekânsal indeks zaten vardır. `HexWorldRuntime`, `UniformGridIndex` kullanır ve `query_spatial_candidates(map_id, bounds)` arayüzünü sunar. Bu nedenle ikinci bir spatial index eklemek için şu aşamada teknik gerekçe yoktur.

Kodda üç ana tekrar/maliyet alanı görülmüştür:

1. Her sabit simülasyon adımında devriye ve kaçınma sistemleri NPC kayıtlarının tamamını dolaşır; yalnızca ilgili davranış durumundaki NPC'ler sonraki işlemlere geçer.
2. Kaçınma sistemi yakın NPC'leri mekânsal indeksten sorgular; her kaçan NPC için ayrıca yerel kaçış hücreleri üretir ve adaylar üzerinde path sorgusu yapar.
3. Yoldaş takip hedefi seçimi, altı komşu hücreyi değerlendirerek birden fazla path sorgusu yapabilir. Hedef, mevcut takip aralığı dolduğunda yeniden seçilir.

Ayrıca devriye, kaçınma ve yoldaş güncellemelerinin her biri kendi sonunda NPC overlap çözümünü çağırmaktadır. Bu, algılama maliyetinden ayrı bir çarpışma/komşuluk maliyetidir; ancak aynı merkezi simülasyon adımında tekrarlandığı için ölçüm envanterine dahil edilmelidir.

Bu rapor **kod envanteri ve davranış sözleşmesidir**. Henüz benchmark çalıştırılmamış, performans kazanımı iddia edilmemiş ve kaynak kodu değiştirilmemiştir.

---

## 2. İncelenen kaynaklar

### Uygulama kodu

| Dosya | İncelenen sorumluluk |
|---|---|
| `application/gameplay_service.py` | Merkezi NPC orkestrasyonu, alt sistemlerin oluşturulması/önbelleği, overlap çağrıları |
| `application/npc_behavior_system.py` | Devriye durumundaki NPC'lerin taranması, waypoint ve path sorguları |
| `application/npc_avoidance.py` | Tehdit mesafesi, kaçış hücresi adayları, pathfinding ve yakın NPC sorgusu |
| `application/companion_commands.py` | Yoldaşların oyuncuya göre takibi, hedef seçimi ve pathfinding |
| `application/hex_world_runtime.py` | Aktör konumu, occupancy, mekânsal indeks, path sorgusu |
| `core/domain/spatial/uniform_grid_index.py` | Uniform-grid broad-phase veri yapısı ve sorgu sırası |
| `application/dynamic_actor_collision.py` | NPC-NPC ve NPC-oyuncu fiziksel overlap sorguları |
| `application/hex_actor_binding.py` | Aktörlerin mekânsal runtime'a bağlanması |
| `application/hex_physics_bridge.py` | Statik harita/fizik snapshot'ı |

### Mevcut testler

- `tests/test_application/test_npc_simulation_orchestration.py`
- `tests/test_application/test_npc_behavior_system.py`
- `tests/test_application/test_npc_avoidance.py`
- `tests/test_application/test_companion_commands.py`
- `tests/test_application/test_dynamic_actor_collision.py`

Bu testler mevcut davranışın temel örneklerini korumaktadır. Ancak henüz 1/10/25/50/100 NPC ölçeklerinde sorgu sayısı ve süre dağılımını raporlayan benchmark kapsamı doğrulanmamıştır.

---

## 3. Gerçek çağrı zinciri

Aşama 1'in merkezi giriş noktası korunmaktadır:

```text
GameWindow fixed-step loop
    |
    v
GameplayService.advance_npc_simulation(dt)
    |
    +--> advance_npc_patrols(dt)
    |       +--> NPCBehaviorSystem.step(dt)
    |       +--> _resolve_npc_body_overlaps()
    |
    +--> advance_npc_avoidance(dt)
    |       +--> NPCAvoidanceSystem.step(dt)
    |       +--> _resolve_npc_body_overlaps()
    |
    +--> advance_companions(dt)
            +--> CompanionCommandService.tick(dt)
            +--> _resolve_npc_body_overlaps()
```

Kanonik sıra **devriye → kaçınma → yoldaş** şeklindedir. Her alt sisteme aynı `delta_seconds` aktarılır. Aşama 2 optimizasyonları bu sırayı, sabit zaman adımını veya alt sistemlerin veri görünürlüğü davranışını değiştiremez.

### 3.1 Devriye

Dosya: `application/npc_behavior_system.py`

- `NPCBehaviorSystem.step()` her adımda `NPCRegistry.all()` üzerinden dolaşır.
- Pasif, PATROL durumunda olmayan veya yeterli waypoint rotası bulunmayan NPC'ler elenir.
- Uygun NPC için runtime entity ve continuous position alınır.
- Hedef waypoint `patrol_target()` ile belirlenir.
- NPC mevcut waypoint hücresinde değilse `path_to()` çağrılır.
- Fizik snapshot mevcutsa sürekli hareket ve statik çarpışma doğrulaması uygulanır.

**Maliyet noktaları:** Tam NPC koleksiyonu taraması; uygun NPC başına entity/position erişimleri; yol sorgusu; fizik hareket çözümü.

**Davranış sözleşmesi:** PATROL filtresi, waypoint ilerlemesi, mevcut rota yönü, path sonucu ve sabit adım hareket miktarı değiştirilmeyecektir.

### 3.2 Kaçınma

Dosya: `application/npc_avoidance.py`

- `NPCAvoidanceSystem.step()` oyuncunun entity ve continuous position verisini alır.
- Tüm NPC kayıtları dolaşılır; yalnızca aktif FLEE NPC'leri değerlendirilir.
- NPC'nin haritası, fizik gövdesi ve oyuncuya olan Öklid mesafesi kontrol edilir.
- `AVOIDANCE_RADIUS = 64.0` eşiği uygulanır.
- `_escape_path()` mevcut hücre çevresinde `SEARCH_RADIUS_CELLS = 3` derinliğinde altı yönlü hücre genişletmesi yapar.
- Geçerli, engellenmemiş, işgal edilebilir ve oyuncudan daha uzak hücreler aday olur.
- Adaylar mevcut sıralama kuralıyla değerlendirilir; uygun yol bulunana kadar `runtime.path_to()` çağrılır.
- Hareket yönüne ek olarak `SEPARATION_RADIUS = 18.0` alanında `query_spatial_candidates()` ile yakın aktörler aranır.
- Yakın NPC'ler için konum ve mesafe hesaplanır; steering vektörü güncellenir.

**Maliyet noktaları:** Tam NPC taraması; NPC başına tehdit mesafesi; yerel hücre genişletmesi; occupancy kontrolleri; bir veya daha fazla path sorgusu; her uygun FLEE NPC için mekânsal aday sorgusu; aday başına entity/position/mesafe işlemleri.

**Davranış sözleşmesi:** Tehdit oyuncudur; harita eşleşmesi, FLEE filtresi, 64.0 yarıçapı, hücre arama derinliği, engel/occupancy kuralları, aday sıralaması, 18.0 ayrışma yarıçapı ve mevcut steering hesabı korunacaktır.

### 3.3 Yoldaş

Dosya: `application/companion_commands.py`

- `CompanionCommandService.tick()` oyuncunun entity ve continuous position verisini alır.
- Yoldaş kayıtları dolaşılır; WAIT komutundakiler hareket hedefi üretmez.
- Pasif, kaydı bulunmayan, FLEE durumundaki veya farklı haritadaki NPC'ler elenir.
- Her FOLLOW yoldaş için oyuncuya Öklid mesafesi hesaplanır.
- `FOLLOW_DISTANCE = 64.0` içinde kalan yoldaşın hedefi temizlenir.
- Hedef yoksa veya `FOLLOW_INTERVAL` dolduysa `_select_follow_target()` çalışır.
- Hedef seçimi oyuncunun altı komşu hücresini değerlendirir; geçerli ve boş her hedef için `runtime.path_to()` çağrılabilir.
- En kısa yol, ardından koordinat sırası ile deterministik hedef seçilir.
- Seçilen hedef, takip aralığı boyunca `_targets` içinde yeniden kullanılır.

**Maliyet noktaları:** Yoldaş listesi taraması; yoldaş başına oyuncu mesafesi; hedef yenileme anında en fazla altı komşu hedef değerlendirmesi ve birden çok path sorgusu; sürekli fizik hareketi.

**Davranış sözleşmesi:** FOLLOW/WAIT komutları, FLEE ile etkileşim, 64.0 takip mesafesi, hedef yenileme aralığı, hedef seçiminin path uzunluğu ve koordinat tie-break sırası korunacaktır.

---

## 4. Mekânsal indeks doğrulaması

### 4.1 Mevcut altyapı

`HexWorldRuntime.__init__()` içinde bir `UniformGridIndex` oluşturulur. İndeks:

- Harita kimliğiyle bölümlenmiş sparse uniform-grid/spatial hash kullanır.
- Varsayılan hücre boyutu 128.0 dünya birimidir.
- Aktörün kimliğini veya otoritatif konumunu sahiplenmez; yalnızca türetilmiş AABB kayıtlarını saklar.
- Kesişen grid bucket'larından aday toplar.
- Son aşamada gerçek AABB kesişimini kontrol eder.
- Sonuç kimliklerini sıralayarak deterministik tuple döndürür.
- insert/update/remove işlemlerini destekler.

Runtime, aktör kaydında indeks girdisi oluşturur; konum değişikliklerinde indeks bounds verisini günceller; aktör silindiğinde girdiyi kaldırır. `query_spatial_candidates()` yalnızca `broadphase_enabled` olan aktörleri döndürür.

### 4.2 Kullanım ve sınırlar

Doğrudan NPC davranış sorgusu olarak doğrulanan kullanım, kaçınma sisteminin 18.0 birimlik yerel ayrışma alanıdır. NPC overlap çözümü de aynı runtime sorgusunu kullanır.

İndeksin varlığı, her algılama ihtiyacına otomatik olarak uygun olduğu anlamına gelmez. Özellikle:

- Devriye şu anda registry taramasıyla çalışır; spatial query kullanmaz.
- Kaçınmanın oyuncu tehdidi kontrolü önce her FLEE NPC için doğrudan mesafe hesabıdır.
- Yoldaşın oyuncuya uzaklık kontrolü doğrudan mesafe hesabıdır.
- Broad-phase sorgusu AABB kesişimine dayanır; kesin dairesel mesafe koşulu çağıran kodda uygulanır.
- `broadphase_enabled` ve aktör kayıt bounds değerlerinin tüm NPC türleri için doğru tanımlanıp tanımlanmadığı benchmark/karşılaştırmalı test aşamasında doğrulanmalıdır.

**Karar:** Mevcut `UniformGridIndex` yeniden kullanılmaya adaydır. İkinci indeks eklenmeyecektir. Önce mevcut indeksin kapsama, güncellik ve sorgu maliyeti ölçülecektir.

---

## 5. Önemli dolaylı maliyet: entity/position erişimi

`HexWorldRuntime.continuous_position(entity_id)`, konumu döndürmeden önce `entity(entity_id)` çağırır. `entity()` ise aktörün indeks bounds tutarlılığını mekânsal indeks sorgusuyla doğrular.

Bunun sonucu olarak şu yaygın desen:

```python
entity = runtime.entity(npc_id)
position = runtime.continuous_position(npc_id)
```

aynı NPC için entity doğrulamasını iki kez tetikleyebilir. Devriye, kaçınma ve yoldaş kodlarında bu erişim deseni görülmektedir.

Bu bulgu bir optimizasyon talimatı değildir. Önce bu doğrulamanın maliyeti ölçülmeli ve `entity()` çağrısının güvenlik/invariant rolü korunmalıdır. Otoritatif veriyi doğrulamadan döndüren bir kestirme API eklenmemelidir.

---

## 6. Tekrarlanan overlap çözümü — ayrı maliyet sınıfı

`GameplayService.advance_npc_patrols()`, `advance_npc_avoidance()` ve `advance_companions()` her biri kendi davranış adımından sonra `_resolve_npc_body_overlaps()` çağırır.

Bu metot `DynamicActorCollisionResolver.resolve_npc_pairs()` ve `resolve_npc_player_contacts()` işlemlerini yürütür. NPC-NPC çözümü NPC gövdelerini dolaşır ve her NPC için runtime spatial candidate sorgusu yapar.

Bu işlem algılama/target seçimi değildir; fiziksel overlap çözümüdür. Aşama 2'nin algılama optimizasyonu kapsamına doğrudan taşınmamalıdır. Ancak merkezi simülasyon adımında üç alt sistemden tekrar çağrıldığı için ayrı sayaç ve zaman ölçümüyle maliyeti görünür kılınmalıdır.

**Kısıt:** Overlap çözüm çağrılarını tekleştirmek veya orkestrasyon dışına taşımak Aşama 2.1'in kararı değildir. Böyle bir değişiklik hareket/çarpışma davranışına dokunur ve ayrı davranış eşdeğerliği kanıtı gerektirir.

---

## 7. Mevcut mimaride bulunmayan/kanıtlanmayan bileşenler

İncelenen gerçek çağrı zincirinde aşağıdaki genel amaçlı bileşenler bulunmadı:

- Ortak bir `PerceptionQueryCoordinator`
- NPC sistemleri arasında paylaşılan tick-scoped perception snapshot
- NPC hedef/algılama sonuçlarını saklayan ortak cache
- Alt sistemler arası aday sorgusu/mesafe sonucu paylaşımı
- NPC sayısına göre ölçeklenmiş sorgu sayaçları ve benchmark raporu

`HexPhysicsSnapshot`, statik harita/fizik geometrisi için kullanılan bir snapshot'tır; NPC algılama snapshot'ı değildir. `UniformGridIndex` ise aktör AABB broad-phase altyapısıdır; hedef seçimi veya kesin algılama kararı vermez.

Bu ayrım mimari tasarımda korunmalıdır.

---

## 8. Ölçüm için önerilen sayaç noktaları

Aşama 2.2'de davranış koduna etkisi en az olacak biçimde aşağıdaki sayaçlar eklenmelidir:

| Sayaç | Artırılacağı nokta |
|---|---|
| patrol_registry_scanned | Devriye döngüsünde incelenen her NPC |
| patrol_eligible | PATROL filtresinden geçen NPC |
| patrol_path_queries | Devriye `path_to` çağrısı |
| avoidance_registry_scanned | Kaçınma döngüsünde incelenen her NPC |
| avoidance_eligible | Aktif FLEE ve harita/fizik kontrollerini geçen NPC |
| avoidance_radius_rejects | Tehdit yarıçapı dışında kalan NPC |
| escape_cells_considered | Kaçış aday üretiminde değerlendirilen hücre |
| escape_path_queries | Kaçış adayı için `path_to` çağrısı |
| avoidance_spatial_queries | Yakın aktörler için `query_spatial_candidates` çağrısı |
| avoidance_spatial_candidates | Bu sorgulardan dönen toplam aday |
| avoidance_distance_checks | Yakın NPC'ler için kesin mesafe kontrolü |
| companion_registry_scanned | Yoldaş döngüsünde incelenen her kayıt |
| companion_distance_checks | Yoldaş–oyuncu mesafe hesabı |
| companion_target_refreshes | Yeni takip hedefi seçimi |
| companion_path_queries | Komşu hedef başına `path_to` çağrısı |
| runtime_entity_validation_queries | Entity tutarlılık kontrolü/spatial query sayısı |
| overlap_resolver_calls | NPC alt sistemlerinden overlap çözüm çağrısı |
| overlap_spatial_queries | NPC çiftleri için broad-phase sorgusu |

Sayaçlar test ve benchmark bağlamında etkinleştirilmeli; üretim döngüsünde pahalı loglama veya her sorguda yüksek maliyetli zaman ölçümü yapılmamalıdır. Sayaçların davranış kararlarına etkisi olmamalıdır.

Zaman ölçümü ayrı ayrı devriye, kaçınma, yoldaş, overlap çözümü ve toplam NPC simülasyonu için yapılmalıdır.

---

## 9. Aşama 2.1 davranış sözleşmesi

Aşağıdaki değişmezler sonraki optimizasyonlarda korunacaktır:

1. Merkezi giriş noktası `GameplayService.advance_npc_simulation(dt)` olarak kalır.
2. Devriye → kaçınma → yoldaş sırası değişmez.
3. Her alt sistem aynı sabit `dt` değerini alır.
4. PATROL, FLEE, FOLLOW ve WAIT durumlarının anlamı değişmez.
5. Oyuncu tehdit/hedef aktörü olarak kalır; algılama mesafeleri ve mevcut eşikler değişmez.
6. Mevcut pathfinding, occupancy, statik fizik ve sürekli hareket doğrulamaları korunur.
7. Aday üretimi yalnızca broad-phase olabilir; kesin davranış koşullarının yerine geçemez.
8. Geçerli adaylar kaybedilemez; aday sırası hedef seçimini etkiliyorsa mevcut sıra/tie-break korunur.
9. Kamera görünürlüğü mantıksal algılamayı durdurmak için gerekçe olamaz.
10. Aşama 1'deki sistem nesnesi cache yaşam döngüsü ve runtime kimlik sınırları bozulamaz.
11. Tick dışına taşan algılama cache'i veya daha seyrek tarama bu aşamada varsayılan çözüm değildir.
12. Overlap/fizik çözümünün sorumluluğu algılama optimizasyonuna karıştırılamaz.

---

## 10. Riskler ve henüz cevaplanmamış sorular

- `UniformGridIndex` için 128.0 hücre boyutunun gerçek NPC yoğunluğu ve bounds dağılımında uygun olup olmadığı ölçülmedi.
- Runtime indeksinin her aktör kaydı için `broadphase_enabled` ve `local_spatial_bounds` değerleri incelenen NPC senaryoları genelinde henüz doğrulanmadı.
- Devriye/kaçınma/yoldaş sistemlerinin aynı tick içinde konum değişikliklerini hangi sırayla gördüğü korunmalı; ortak snapshot bu görünürlüğü değiştirebilir.
- `runtime.entity()` içindeki indeks tutarlılık kontrolünün maliyeti ölçülmedi.
- Path sorgularının toplam süresi ve occupancy snapshot üretim maliyeti ayrıştırılmadı.
- Üç overlap çağrısının toplam maliyeti henüz ölçülmedi; bu ayrı çarpışma çalışmasına devredilmelidir.
- NPC koleksiyonunun gerçek sıralama sözleşmesi ve içerik büyüklüğü benchmark senaryolarında açıkça sabitlenmelidir.

---

## 11. Aşama 2.1 çıkış kapısı değerlendirmesi

| Kriter | Sonuç |
|---|---|
| Devriye/kaçınma/yoldaş çağrı zinciri | Kaynak koduyla çıkarıldı |
| Adayların kaynağı | Registry taraması ve mevcut spatial index olarak ayrıştırıldı |
| Mevcut mekânsal indeks | `UniformGridIndex` doğrulandı |
| Path sorgusu noktaları | Kaynak kodunda belirlendi |
| Tekrarlanan entity/position erişimleri | Tespit edildi |
| Overlap maliyeti | Algılamadan ayrı sınıf olarak tespit edildi |
| Davranış değişmezleri | Belgelenmiş durumda |
| Ölçek benchmark baseline'ı | Aşama 2.2'ye devredildi |
| Optimizasyon uygulaması | Bilinçli olarak yapılmadı |

**Aşama 2.1 sonucu:** Kod envanteri ve davranış sözleşmesi tamamlandı. Aşama 2.2 — ölçüm altyapısı ve baseline tasarımına geçilebilir. Ancak optimizasyon seçimi için önce 1/10/25/50/100 NPC benchmark sonuçları alınmalıdır.

---

## 12. Sonraki adım

Aşama 2.2'de önce sayaçların en düşük müdahaleyle ekleneceği tasarlanmalı; ardından sabit NPC senaryolarında baseline ölçülmelidir. Sayaçların ölçüm overhead'i ayrıca kontrol edilmeli ve baseline raporu optimizasyon öncesi commit'e bağlanmalıdır.

Bu raporla birlikte herhangi bir davranış kodu, mekânsal indeks, cache, tarama sıklığı veya fizik/overlap akışı değiştirilmemiştir.
