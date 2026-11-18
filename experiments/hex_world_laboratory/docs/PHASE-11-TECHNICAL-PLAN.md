# Aşama 11 — Teknik Uygulama ve Doğrulama Planı

> **Belge türü:** Ayrıntılı teknik plan  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Plan dayanağı:** Onaylanmış `PHASE-11-GENERAL-PLAN.md`  
> **Durum:** TEKNİK PLAN HAZIR — KULLANICI ONAYI BEKLENİYOR  
> **Kod uygulaması:** Başlamadı  
> **Tek laboratuvar başlatıcısı:** `python -m hex_world_lab`

---

## 1. Teknik hedef ve bağlayıcı sınırlar

Aşama 11; Aşama 0–10'da kabul edilen geometri, hareket, fizik, spatial index, entity/world lifecycle, simülasyon ve render altyapısını kontrollü yük altında doğrular. Yeni oynanış sistemi veya yeni mimari katman hedeflenmez.

Bağlayıcı kararlar:

- Yalnızca `experiment/hex-world-laboratory` dalında çalışılır.
- `main` ve `demo_eldoria` dallarına yazılmaz.
- NPC, kaynak ve yoldaş konumları testler boyunca sabit kalır.
- FOLLOW/WAIT/RETURN komutları yalnızca mevcut ilişki/komut verisi olarak kalır.
- Rastgeleleştirilmiş hareket yalnızca oyuncu girdisi için kullanılabilir; seed sabitlenir.
- 60 TPS ve Aşama 10 tick sırası korunur.
- Render ve kamera authoritative state değiştiremez.
- `python -m hex_world_lab` tek başlatıcıdır.
- A*, Dijkstra, click-to-move, pathfinding, AI, toplama/ekonomi, savaş/görev/diyalog, çevre sanatı, harita editörü ve Godot geçişi kapsam dışıdır.
- Teknik planın onayı gelmeden uygulama başlamaz.

## 2. Depo denetimi ve mevcut başlangıç noktası

Plan, laboratuvarın mevcut kaynak ve test yapısı incelenerek hazırlanmıştır. Başlıca mevcut bileşenler:

| Sorumluluk | Mevcut modül / test |
|---|---|
| Tick orkestrasyonu | `src/hex_world_lab/simulation/tick_coordinator.py` |
| Hareket ve çarpışma | `simulation/collision_aware_movement_system.py`, `physics/solver.py`, `physics/continuous.py` |
| Tick scheduler | `application/demo_tick_pump.py` |
| Entity/world yaşam döngüsü | `application/entity_world_coordinator.py` |
| Entity spatial index | `entities/spatial_index.py` |
| Genel spatial yapılar | `spatial/grid.py`, `spatial/quadtree.py` |
| Render görünürlüğü | `rendering/visibility.py`, `rendering/snapshot.py` |
| FPS eşdeğerliği | `tests/integration/test_movement_demo_fps.py` |
| Tick zaman borcu ve retry | `tests/integration/test_demo_tick_pump.py` |
| Entity/map lifecycle | `tests/integration/test_entity_world_lifecycle.py` |
| Spatial differential | `tests/unit/test_spatial_indexes.py` |
| Fizik solver | `tests/unit/test_physics_solver.py` |
| Tick uzun dönem tutarlılığı | `tests/integration/test_simulation_tick_flow.py` |
| Mevcut benchmarklar | `benchmarks/benchmark_*.py` |

Mevcut benchmark profilleri arasında entity spatial için 100/1.000/10.000 entity; render görünürlüğü için 61/128/256/1.000/10.000/50.000 hücre; çarpışmalı hareket için 1/10/100/1.000 aktör; tick ve render snapshot için 120 işlem/batch bulunmaktadır.

Aşama 10 CI referansı:
- Laboratuvar: 759 test.
- Core Quality Linux: 2.222 test.
- Core Quality Windows: 2.222 test.
- Tick ortalaması: 177.5944 µs/tick.
- Render snapshot ortalaması: 219.3906 µs/snapshot.
- Bu sayılar yalnızca ilgili CI runner/ölçüm yöntemi için tarihsel referanstır; donanımlar arası mutlak eşik değildir.

## 3. İş paketleri ve teknik uygulama sırası

### 11.1 — Denetim ve baseline sabitleme

**İncelenecek alanlar**
- Aşama 6–10 kapanış/uygulama raporları.
- `tests/unit`, `tests/integration`, `tests/acceptance`.
- `benchmarks/`, `scripts/` ve CI workflow'ları.
- Mevcut benchmarkların ölçtüğü/ölçmediği maliyetler.

**Yapılacaklar**
1. Test ve benchmark envanteri çıkarılır; mevcut testler yeniden yazılmadan kapsadıkları invariant'lar listelenir.
2. Aşama 10 tick/snapshot benchmarkı aynı kod ve aynı runner sınıfında tekrar çalıştırılır.
3. Her ölçüm çıktısına Python sürümü, OS/platform, processor bilgisi, seed, warm-up ve tekrar sayısı eklenir.
4. Aynı makinede en az üç bağımsız benchmark oturumu alınır; ortanca oturum baseline olarak raporlanır.
5. Tarihsel Aşama 10 sonucu ile yeni ölçüm arasındaki fark, ortam eşdeğer değilse regresyon olarak etiketlenmez.

**Teslimat:** `reports/PHASE-11-BASELINE-REPORT.md` ve baseline JSON artifact'i.

### 11.2 — Deterministik stres senaryosu altyapısı

**Önerilen yeni modüller**
- `scenarios/stress_profiles.py`: profil tanımları ve doğrulama.
- `scenarios/stress_builders.py`: harita, engel ve entity fixture üreticileri.
- `tests/stress/`: uzun süreli ve yüksek yük senaryoları.
- `scripts/run_phase_11_stress.py`: stres profillerini seçerek çalıştıran komut satırı girişi.

Üreticiler mevcut `HexWorld`, `HexMapDefinition`, `EntityWorldCoordinator`, `EntityRecord`, `UniformGrid`, `HexMapCollisionGeometry` ve mevcut fizik veri tiplerini kullanır. Yeni alternatif world/entity/spatial modeli oluşturulmaz.

**Standart profil matrisi**

| Boyut | Profiller |
|---|---|
| Entity sayısı | 100 / 1.000 / 10.000 |
| Entity dağılımı | uniform seyrek / tek merkezde kümeli / çok kümeli |
| Harita hücresi | 256 / 1.000 / 10.000 / 50.000 |
| Engel profili | seyrek / yoğun kümeli / bitişik duvar / dar geçit / köşe kümeleri |
| Entity lifecycle | 1 / 100 / 1.000 işlem batch'i |
| Harita sayısı | tek harita / çok harita unload-reload çevrimi |

Her senaryo `seed`, profil adı, boyutlar ve başlangıç koşullarını JSON olarak raporlar. Seed varsayılanı test dosyasında açıkça sabitlenir; CI çıktısı seed'i tekrar çalıştırmaya yetecek şekilde kaydeder. Aşırı bellek tüketimi olasılığı bulunan 10.000 entity ve 50.000 hücre profilleri önce tek başına ölçülür; CI süre/bellek sınırları doğrulanmadan bütün profiller aynı job'a yığılmaz.

### 11.3 — Simülasyon, hareket ve zamanlama

**Mevcut API sözleşmeleri**
- `SimulationTickCoordinator.advance_tick(tick_number)`
- `DemoTickPump.pump()` ve mevcut sabit tick/zaman borcu davranışı.
- `CollisionAwareMovementSystem.step(tick_number, intent)`
- `MovementState`, `MovementIntent`, `EntityTransform`.

**Test senaryoları**
1. Aynı seed ile üretilen oyuncu input dizisi aynı başlangıç state'inden iki kez çalıştırılır; tick numarası, son MovementState, cell tracker ve entity transform birebir karşılaştırılır.
2. Aynı bir saniyelik simülasyon 30/60/120 FPS render gruplamasıyla çalıştırılır; mevcut FPS eşdeğerliği testi genişletilir.
3. Frame-time dizileri: sabit 1/30, 1/60, 1/120; kesirli aralıklar; kısa süreli 100–250 ms sıçramalar; uzun süreli birikmiş tick borcu.
4. 3.600 tick mevcut referans korunur; 36.000 tick stres testi ayrı stress profiline eklenir.
5. Tick coordinator input örnekleme, movement, cell tracking ve entity sync sırası doğrulanır.
6. Her alt aşamada kontrollü hata enjeksiyonu ile retry sırasında tamamlanan adımın ikinci kez uygulanmadığı kontrol edilir.
7. Her tick sonunda MovementState pozisyonu = player EntityTransform pozisyonu ve spatial query üyeliği doğrulanır.

**Önemli ayrım:** 30/60/120 FPS testinde aynı tick başına input dizisi kullanılmalıdır. Render frame başına input örnekleme sayısı farklı olduğu için, frame bazlı rastgele input üretimiyle determinism iddiası kurulmaz.

### 11.4 — Entity, spatial ve world lifecycle

**Test edilecek işlemler**
- Register, transform update, activate/deactivate, remove.
- Map load, unload, reload ve remove.
- Companion recruit, command update ve dismiss.
- Aynı entity'nin birden çok map index'inde stale kaydı kalmaması.
- Spatial query ve brute-force referansının karşılaştırılması.

**Differential doğruluk**
- Her seed ve yük profilinde sorgu alanları üretilir.
- Indexed aday kümesi ile brute-force AABB intersection kümesi karşılaştırılır.
- Sıralama semantiği ayrı tutulur; önce küme eşitliği, sonra API'nin deterministik sıralama sözleşmesi doğrulanır.
- False negative, yinelenen ID, silinmiş entity veya pasif entity sonucu başarısızlıktır.
- EntitySpatialIndex'in interaction bounds davranışı, mevcut `bounds_for` ve `differential_candidates` sözleşmelerine göre test edilir.

**Hareketsizlik invariant'ı**
NPC ve kaynakların konumları senaryo başında kaydedilir. Bütün tick, lifecycle ve companion command işlemlerinden sonra aynı kalmalıdır. FOLLOW/WAIT/RETURN hiçbir testte hareket üretmemelidir.

### 11.5 — Fizik ve geometri sınır testleri

**Test edilecek modüller**
- `physics/broadphase.py`
- `physics/continuous.py`
- `physics/hex_geometry.py`
- `physics/narrowphase.py`
- `physics/solver.py`
- `physics/spatial_adapter.py`
- `geometry/` koordinat ve tolerans fonksiyonları.

**Senaryo grupları**
- Engelden uzakta yüksek hızlı hareket.
- Tek duvar boyunca teğetsel kayma.
- İki/üç yüzeyin oluşturduğu köşe.
- Dar koridor ve sınırda hareket.
- Hex kenarının iki tarafı, vertex yakınlığı ve çok küçük epsilon farkları.
- Negatif dünya koordinatları.
- Sıfır displacement, küçük displacement ve ardışık ters yön girdileri.
- Engellerin farklı giriş sırası ile aynı solver sonucu.

**Kabul invariant'ları**
- Broadphase yalnızca aday toplar; nihai çarpışma narrowphase/solver geometrisinden gelir.
- Çözüm sonrası açıklanamayan penetration kalmaz; mevcut toleranslar kullanılır, gelişigüzel tolerans büyütülmez.
- Aynı başlangıç ve input aynı sonucu verir.
- Engellerin sırası sonucu değiştirmez.
- Hatalı/NaN/sonsuz input'lar kontrollü reddedilir veya mevcut doğrulama sözleşmesine göre ele alınır.

### 11.6 — Performans ve bellek ölçümü

**Ölçüm alanları**
- Tick coordinator toplam maliyeti.
- Collision-aware movement ve physics çözüm maliyeti.
- UniformGrid build/update/query maliyeti.
- EntitySpatialIndex build/update/query maliyeti.
- Brute-force sorgu referans maliyeti.
- Render culling, snapshot ve render maliyeti.
- Map/entity lifecycle batch maliyeti.
- Bellek başlangıç, tepe ve son değerleri.

**İstatistik**
- Ortalama, median, p95 ve p99.
- Ölçüm adedi, warm-up adedi, seed.
- Entity/hücre/engel/obstacle candidate sayısı.
- Mümkünse `tracemalloc` ile Python allocation current/peak; OS RSS mevcut platformda güvenilir biçimde ölçülebiliyorsa ayrı metadata olarak kaydedilir.
- Ölçüm kodunun kendi overhead'i açıklanır; bellek sayıları Python heap ile process RSS olarak birbirine karıştırılmaz.

**Ölçüm protokolü**
1. Her benchmarkta en az bir warm-up.
2. Küçük/orta profillerde en az 20 batch; yüksek maliyetli profillerde en az 7 batch veya önceden belirlenmiş minimum örnek sayısı.
3. Her batch'te sabit sayıda işlem; batch süreleri üzerinden percentile.
4. Üç bağımsız oturum; oturumlar arası median ana karşılaştırma.
5. Aynı OS, Python sürümü, runner tipi ve güç/iş yükü koşulları olmadan mutlak süre kıyaslanmaz.
6. Benchmark sonucu JSON artifact'e yazılır.

**Eşik belirleme yöntemi**
- İlk ölçüm aşamasında performans testi yalnızca gözlemseldir.
- Eşdeğer ortamda tekrarlı baseline alındıktan sonra gürültü bandı ve oturumlar arası değişkenlik hesaplanır.
- Regresyon eşiği baseline dağılımını aşan ve tekrarlı oturumlarda görülen fark üzerinden önerilir.
- Kullanıcı onayına sunulmadan sabit CI performans başarısızlık eşiği eklenmez.
- Doğruluk testleri performans eşiğinden bağımsız ve kesin kabul kapısıdır.

### 11.7 — Hata sınıflandırması ve düzeltme protokolü

Her bulgu şu alanlarla kaydedilir:
- Kimlik, ilgili profil/seed ve tekrar komutu.
- Beklenen ve gerçekleşen davranış.
- İlk görüldüğü commit ve etkilenen modül.
- Sınıf: correctness / lifecycle / determinism / performance / memory / rendering / test infrastructure.
- Şiddet: critical / high / medium / low.
- Tekrar üretilebilirlik ve etki alanı.

Düzeltme sırası:
1. Başarısızlığı gösteren regresyon testi.
2. Kök neden analizi.
3. En küçük kapsamlı düzeltme.
4. İlgili unit + integration + stress test.
5. Etkilenen benchmarkın aynı ortamda tekrar ölçümü.
6. CI doğrulaması.

Ölçüm kanıtı olmadan optimizasyon, genel refaktör veya API değişikliği yapılmaz. Aşama sınırını aşan bulgu ayrı öneri olarak raporlanır.

### 11.8 — CI, görsel doğrulama ve kapanış

**CI iş akışları**
- `.github/workflows/hex-world-lab-ci.yml`: hızlı laboratuvar testleri ve benchmarklar; Aşama 11 çıktıları için artifact upload.
- `.github/workflows/core-quality.yml`: mevcut Linux ve Windows Core Quality doğrulaması.
- Gerekiyorsa ayrı `.github/workflows/hex-world-lab-stress.yml`: uzun süreli/high-load testleri `workflow_dispatch` ve kontrollü zamanlanmış çalışma ile. PR başına en ağır profil otomatik çalıştırılmaz.

**CI katmanları**
- Pull request / push: unit + integration + mevcut acceptance; hızlı deterministik stress smoke profili.
- Manuel stress workflow: 10.000 entity, büyük harita, lifecycle ve uzun tick profilleri.
- Benchmark artifact'leri: JSON; platform/Python/seed bilgileri dahil.
- Görsel artifact: mevcut Phase 7/9 sahne üreticileri korunur; gerekirse yoğunluk odaklı yeni sahne script'i eklenir.

**Manuel kabul**
- Kullanıcı tek laboratuvar başlatıcısıyla demo sahnesini açar.
- Oyuncu hareketi, kamera, çarpışma, seçim ve yoğun sahne çizimi gözlemlenir.
- NPC ve kaynakların yerinde kaldığı; yoldaş komutlarının hareket üretmediği doğrulanır.
- Ayrıntılı adımlar `PHASE-11-MANUAL-ACCEPTANCE-CHECKLIST.md` belgesindedir.

## 4. Önerilen dosya değişiklik listesi

Bu liste planlanan değişiklik alanıdır; gerçek uygulama sırasında 11.1 denetimi yeni gereksinim gösterirse önce plan güncellenir.

**Yeni belgeler**
- `docs/PHASE-11-TECHNICAL-PLAN.md`
- `docs/PHASE-11-MANUAL-ACCEPTANCE-CHECKLIST.md`
- `reports/PHASE-11-BASELINE-REPORT.md`
- `reports/PHASE-11-STRESS-VALIDATION-REPORT.md`
- `reports/PHASE-11-CLOSURE-REPORT.md`

**Olası yeni kod/test dosyaları**
- `scenarios/stress_profiles.py`
- `scenarios/stress_builders.py`
- `scripts/run_phase_11_stress.py`
- `tests/stress/test_simulation_stress.py`
- `tests/stress/test_entity_spatial_stress.py`
- `tests/stress/test_physics_geometry_stress.py`
- `tests/stress/test_world_lifecycle_stress.py`
- `benchmarks/benchmark_phase_11_stress.py`
- `benchmarks/benchmark_phase_11_memory.py`

**Mevcut dosyalarda muhtemel genişletmeler**
- `benchmarks/benchmark_simulation_tick.py`
- `benchmarks/benchmark_entity_spatial.py`
- `benchmarks/benchmark_collision_aware_movement.py`
- `benchmarks/benchmark_render_visibility.py`
- `tests/integration/test_movement_demo_fps.py`
- `tests/integration/test_simulation_tick_flow.py`
- `tests/integration/test_entity_world_lifecycle.py`
- `tests/unit/test_spatial_indexes.py`
- `tests/unit/test_physics_solver.py`
- `.github/workflows/hex-world-lab-ci.yml`

Dosyaların tamamının değiştirilmesi zorunlu değildir. Mevcut test yeterli kapsama sahipse tekrar yazılmaz.

## 5. Risk yönetimi

| Risk | Kontrol |
|---|---|
| CI süresinin uzaması | Smoke ve full stress profillerini ayırmak |
| 10.000 entity/50.000 hücre bellek baskısı | Kademeli profilleme, timeout ve bellek kaydı |
| Rastgele testte tekrar üretilememe | Sabit seed + input/parametre JSON'u |
| FPS testinde input örnekleme farkı | Tick bazlı input dizisi |
| Benchmark gürültüsü | Aynı runner, warm-up, çoklu oturum |
| OS RSS ölçümünün platforma göre değişmesi | Python heap ve process RSS'yi ayrı raporlamak |
| Testin kendi üretici maliyetini ölçmesi | Setup ve timed section ayrımı |
| Kapsamın NPC AI'ya kayması | NPC/resource/companion immobility invariant |
| Yanlış performans regresyonu | Baseline eşdeğerliği ve tekrarlı oturum şartı |

## 6. Kabul kapıları

Aşama 11 teknik kapanış için:

1. Seed ve parametreleri kaydedilmiş stres senaryoları tekrar üretilebilir.
2. Aynı seed/input ile simülasyon sonucu deterministiktir.
3. 30/60/120 FPS ve düzensiz frame-time altında aynı tick/input dizisi eşdeğer sonuç üretir.
4. Tick retry tamamlanmış alt aşamaları çift uygulamaz.
5. MovementState, player EntityTransform ve spatial üyelikleri uzun koşuda tutarlıdır.
6. Spatial query brute-force referansıyla eşleşir; false negative/stale/duplicate kayıt yoktur.
7. Map/entity lifecycle ve companion ilişkileri tutarlı kalır.
8. NPC ve kaynak konumları değişmez; companion komutları hareket oluşturmaz.
9. Fizik/geometri stres testlerinde kritik penetration, boundary veya determinism hatası kalmaz.
10. Tick, physics, spatial, render ve bellek maliyetleri metadata ile raporlanır.
11. Performans hedefleri ölçülmüş baseline'a dayanır; donanım farklılığı gözetilir.
12. Kritik ve yüksek önem dereceli düzeltmeler regresyon testiyle korunur.
13. Laboratuvar CI ve Core Quality Linux/Windows başarılıdır; istisnalar açıkça onaylanır.
14. Görsel test artifact'leri üretilmiş ve kullanıcı manuel kabulü tamamlanmıştır.
15. Kapanış raporu commit SHA, CI run kimlikleri, benchmark artifact'leri ve kalan sınırlamaları içerir.

## 7. Aşama yürütme sırası ve onay kapıları

1. Kullanıcı bu teknik planı inceler ve ayrıca onaylar.
2. Onaydan sonra 11.1 baseline denetimi yapılır.
3. Her alt aşama tamamlandığında test/benchmark kanıtı raporlanır.
4. Bulgu kapsamı değiştirecekse uygulama durdurulur ve onay istenir.
5. 11.8 sonunda CI ve görsel kabul hazırlığı tamamlanır.
6. Kullanıcı masaüstünde manuel kabulü gerçekleştirir.
7. Kapanış raporu ve Master Plan güncellenir.

**Bu belge teknik tasarım onayı içindir; tek başına kod uygulama izni değildir.**

---

**Nihai karar:** Aşama 11; mevcut Hex World Laboratory altyapısının kontrollü, deterministik ve ölçülebilir sağlamlık doğrulamasıdır. NPC/yoldaş/kaynak hareketi, AI, pathfinding ve ana oyuna entegrasyon bu aşamanın dışında kalır.
