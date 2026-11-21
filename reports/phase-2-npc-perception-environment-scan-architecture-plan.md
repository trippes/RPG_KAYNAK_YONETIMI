# Eldoria — Aşama 2 Genel ve Ayrıntılı Teknik Mimari Planı
## NPC Algılama ve Çevre Tarama Maliyetlerinin Azaltılması

- **Proje:** Eldoria RPG
- **Depo:** `trippes/RPG_KAYNAK_YONETIMI`
- **Çalışma dalı:** `experiment/map-cleanup`
- **Aşama:** 2 — NPC algılama ve çevre tarama maliyetlerinin azaltılması
- **Durum:** Plan — uygulama henüz yapılmadı
- **Plan türü:** Genel yol haritası ve ayrıntılı teknik mimari sözleşmesi
- **Hazırlanma tarihi:** 21 Kasım 2026
- **Dayanak Aşama 1 raporu:** `reports/phase-1-npc-simulation-orchestration-closure.md`
- **Dayanak teknik denetim:** `reports/experiment-map-cleanup-hareket-mimarisi-performans-teknik-denetimi.md`

---

## 1. Yönetici özeti

Aşama 2'nin amacı, NPC'lerin oyuncuyu, diğer NPC'leri ve çevredeki ilgili varlıkları algılamak için yaptığı tekrar eden mesafe, komşuluk, yakınlık ve çevre taramalarının maliyetini ölçmek ve davranış semantiğini bozmadan azaltmaktır.

Aşama 1'de `GameplayService.advance_npc_simulation(delta_seconds)` ile merkezi NPC simülasyon giriş noktası oluşturulmuş; devriye → kaçınma → yoldaş sırası korunmuş, alt sistemlere aynı sabit zaman adımı aktarılmış ve kaçınma sistemi nesnesinin yaşam döngüsü önbelleğe alınmıştır. Bu mimari Aşama 2'nin orkestrasyon sınırıdır ve korunacaktır.

Aşama 1 raporu, nesne yaşam döngüsü önbelleğinin algılama sonuçlarını, mesafe hesaplarını veya path sorgularını henüz önbelleğe almadığını açıkça belirtir. Dolayısıyla Aşama 2, bu yeni veri/algılama maliyetlerini teşhis etmek için doğal devam aşamasıdır.

**Temel karar:** İlk olarak salt inceleme ve ölçüm yapılacaktır. Ölçüm sonucu ve mevcut kodun gerçek davranışı anlaşılmadan tarama sıklığı düşürülmeyecek, algılama sonucu cache'lenmeyecek, davranış kuralları değiştirilmeyecek ve yeni bir mekânsal indeks varsayımla eklenmeyecektir.

**Başarı tanımı:** Aynı simülasyon girdisi ve aynı dünya durumunda NPC'lerin algılama/karar sonuçları korunurken, tekrarlanan aday taramaları ve pahalı sorguların sayısı ile toplam maliyeti ölçülebilir biçimde azaltılmalıdır. Başlangıç baseline'ı alınmadan sayısal performans kazanımı iddia edilmeyecektir.

---

## 2. Kapsam ve aşama sınırları

### 2.1. Aşama 2 kapsamına girenler

1. NPC algılama kodunun çağrı noktalarını, sıklığını ve çağrı zincirini çıkarmak.
2. NPC başına ve simülasyon adımı başına çevre tarama sayısını ölçmek.
3. Tekrarlanan mesafe, yakınlık, komşuluk ve hedef/varlık sorgularını tespit etmek.
4. NPC–oyuncu ve NPC–NPC algılama/etkileşim adaylarının maliyetini ayırmak.
5. Mevcut mekânsal indeks, spatial query veya snapshot altyapısının varlığını ve gerçek kullanımını doğrulamak.
6. Uygun olduğunda aday kümesini daraltmak; kesin algılama koşullarını mevcut davranış kodunda korumak.
7. Cache/snapshot kullanılacaksa veri sahipliğini, anahtarını, geçerlilik süresini ve invalidation koşullarını tanımlamak.
8. Mantıksal NPC algılaması ile görsel/animasyon güncellemelerinin maliyet ve sıklık bakımından ayrımını incelemek.
9. 1/10/25/50/100 NPC ölçek senaryolarında karşılaştırılabilir benchmark üretmek.
10. Test, telemetri ve CI korumalarını eklemek.

### 2.2. Bu aşamanın dışında kalanlar

- Yeni NPC zekâsı veya yeni algılama davranışı tasarlamak.
- Devriye, kaçınma, yoldaş davranış kurallarını yeniden yazmak.
- NPC hareket/fizik integratörünü değiştirmek.
- Statik/dinamik çarpışma çözümünü birleştirmek veya yeniden tasarlamak.
- Pathfinding algoritmasını değiştirmek; yalnızca algılama/çevre taramasıyla doğrudan ilişkili path sorgularının çağrı maliyeti ölçülebilir.
- Harita terrain render optimizasyonu, terrain chunk sistemi veya kamera interpolasyonu.
- Görsel LOD politikasını davranışsal algılamanın yerine geçirmek.
- NPC'lerin algılama sıklığını ürün/tasarım kararı olmadan azaltmak.
- Oyuncunun veya NPC'lerin algılama mesafesi, görüş açısı, hedef önceliği ya da tepki gecikmesini değiştirmek.

### 2.3. Ayrı hareket yol haritasıyla numaralandırma çakışması

Hareket ve performans teknik denetim raporunun kendi 6 aşamalı yol haritasında “Aşama 2” hareket fiziği/akıcılık konusudur. Bu belge ise Aşama 1 NPC orkestrasyon kapanış raporunun açıkça tanımladığı **Aşama 2 — NPC algılama ve çevre tarama maliyetlerinin azaltılması** çalışmasını ele alır. İki bağımsız yol haritasının aşama numaraları birbirine karıştırılmamalıdır. Bu belge hareket fiziği aşamasını başlatmaz.

---

## 3. Aşama 1'den devralınan mimari sözleşme

### 3.1. Korunacak merkezi akış

```text
GameWindow / sabit adım oyun döngüsü
                |
                v
GameplayService.advance_npc_simulation(delta_seconds)
                |
                +--> advance_npc_patrols(delta_seconds)
                |
                +--> advance_npc_avoidance(delta_seconds)
                |
                +--> advance_companions(delta_seconds)
                |
                v
       hareket etmiş NPC kimlikleri
       tekilleştirilmiş sıralı tuple
```

Bu sıra Aşama 1'in kanonik sözleşmesidir. Aşama 2, algılama ve çevre tarama optimizasyonlarını mevcut alt sistemlerin içinde veya onların kullandığı ayrıştırılmış yardımcı bileşenlerde ele alabilir; ancak merkezi orkestrasyonun sorumluluğunu davranış sınıflarına dağıtmamalıdır.

### 3.2. Değişmezler

- `GameplayService` orkestrasyon sahibidir; NPC davranış kurallarının sahibi hâline getirilmemelidir.
- Devriye → kaçınma → yoldaş çağrı sırası korunur.
- Alt sistemlere aynı `delta_seconds` değeri aktarılır.
- NPC simülasyonu mevcut sabit zaman adımlı clock/accumulator üzerinden çalışmaya devam eder.
- Aşama 1'deki kaçınma sistemi nesne cache anahtarı ve yaşam döngüsü davranışı regresyona uğratılmamalıdır.
- Mevcut NPC hareketi, çarpışma/overlap çözümü ve davranış sonuçları korunmalıdır.
- Test double/adaptörleri için mevcut kontrollü uyumluluk yolu sebepsiz yere kaldırılmamalıdır.
- Aşama 2'de performans ölçümü yapılırken ölçüm kodunun kendisi önemli bir maliyet oluşturmamalıdır.

### 3.3. Aşama 1 telemetrisinin sınırı

Aşama 1 kapanış raporundaki frame ve NPC simülasyon süreleri farklı gözlem örneklerinden gelen teşhis verileridir; kontrollü benchmark veya makine bağımsız garanti değildir. NPC simülasyon alt sistemleri henüz ayrı ayrı ölçülmemektedir. Bu nedenle Aşama 2 ilk olarak alt sistem ve algılama operasyonları seviyesinde baseline oluşturmalıdır.

---

## 4. Genel uygulama planı

### Aşama 2.1 — Kod envanteri ve davranış sözleşmesi çıkarımı

**Amaç:** Algılama ve çevre taramasının nerede, ne zaman ve hangi verilerle yapıldığını kanıtlamak.

İşler:
- NPC devriye, kaçınma, yoldaş ve ilgili algılama sınıflarının çağrı zincirini çıkarmak.
- Oyuncu/NPC/çevre adaylarının nereden alındığını belirlemek.
- Her taramanın tam koleksiyon mu, mekânsal sorgu mu kullandığını kaydetmek.
- Mesafe, görüş/yarıçap, takım/ilişki, görünürlük ve hedef uygunluğu kontrollerinin sırasını belgelemek.
- Aynı tick içinde aynı veriye yönelik tekrar eden sorguları belirlemek.
- Algılama sonucu ile davranış kararı arasındaki sınırı tanımlamak.

**Çıkış kapısı:** Kaynak dosyaları, fonksiyonlar, çağrı sayıları ve davranış semantiği içeren mevcut durum haritası. Bu kapı geçilmeden optimizasyon uygulanmaz.

### Aşama 2.2 — Ölçüm ve baseline

**Amaç:** Gerçek maliyeti NPC sayısı ve sorgu türüne göre ayırmak.

İşler:
- Devriye, kaçınma ve yoldaş alt sistemlerinin sürelerini ayrı ölçmek.
- Algılama/çevre tarama fonksiyonlarının çağrı sayısını ve toplam süresini ölçmek.
- Aday sayısı, kabul edilen aday sayısı ve kesin kontrol sayısını ayırmak.
- Mesafe/komşuluk/path sorgusu sayılarını ölçmek.
- 1/10/25/50/100 NPC senaryolarını aynı harita ve aynı simülasyon koşullarında çalıştırmak.
- Ortalama yanında p50/p95/p99 ve frame spike sayısını raporlamak.

**Çıkış kapısı:** Tekrarlanabilir baseline raporu ve darboğazların etki sırasına göre listesi.

### Aşama 2.3 — Aday üretimini daraltma mimarisi

**Amaç:** Her NPC'nin tüm dünya aktörlerini taraması gerekiyorsa, mevcut altyapıdan yararlanarak yalnızca olası yakın adayları üretmek.

İşler:
- Mevcut spatial index/grid/partition/query altyapısını incelemek.
- Uygun ve doğru bir mevcut indeks varsa yeniden kullanmak.
- Yoksa, benchmark ve veri sahipliği incelemesinden sonra en küçük gerekli broad-phase çözümünü tasarlamak.
- Broad-phase aday üretimi ile narrow-phase kesin algılama koşullarını ayırmak.
- Oyuncu ve NPC adaylarını deterministik ve tekrarsız biçimde sunmak.

**Çıkış kapısı:** Aday kümesinin mevcut davranışın ihtiyaç duyduğu bütün geçerli hedefleri içerdiğini kanıtlayan testler.

### Aşama 2.4 — Tekrarlı sorguların kontrollü yeniden kullanımı

**Amaç:** Aynı simülasyon adımında veya aynı geçerlilik penceresinde değişmeyen veriyi gereksiz yere yeniden hesaplamamak.

İşler:
- Bir simülasyon tick'i için ortak immutable perception/query snapshot gerekip gerekmediğini değerlendirmek.
- Aynı NPC/aynı tick için tekrarlanan mesafe ve aday sorgularını paylaşmak.
- Cache anahtarı ve invalidation koşullarını tanımlamak.
- Hareket eden aktör, runtime değişimi, NPC ekleme/çıkarma, harita/navigasyon değişimi ve oyuncu değişiminde geçersizleştirmeyi doğrulamak.
- Tick sınırını aşan cache kullanımını ancak veri sürümü ve davranış gecikmesi kanıtlanabiliyorsa değerlendirmek.

**Çıkış kapısı:** Cache açık/kapalı koşulunda aynı algılama sonuçları ve geçersizleştirme regresyon testleri.

### Aşama 2.5 — Mantıksal simülasyon ve görsel güncelleme ayrımı

**Amaç:** Görsel güncellemelerin algılama maliyetini gereksiz yere tetiklemesini önlemek.

İşler:
- NPC mantıksal simülasyon, algılama, animasyon ve render güncellemelerinin çağrı zincirini ayırmak.
- Görünürlük bilgisinin yalnızca görsel işlere uygulanmasını sağlamak.
- Kamera dışında kalan NPC'lerin dünya açısından önemli mantıksal algılamalarını kesmemek.
- Uzak NPC güncelleme sıklığına ihtiyaç varsa bunun oyun tasarımına etkisini ayrı karar olarak sunmak.

**Çıkış kapısı:** Kamera görünürlüğü değişse de dünya davranışı/algılama sonuçlarının tanımlı sözleşmeye uygun kalması.

### Aşama 2.6 — Doğrulama, benchmark ve kapanış

**Amaç:** Optimizasyonun doğruluğunu ve ölçülebilir etkisini kanıtlamak.

İşler:
- Önceki davranış regresyon testlerini çalıştırmak.
- Aday kümesi, cache invalidation ve deterministik sıralama testlerini çalıştırmak.
- 1/10/25/50/100 NPC benchmark'larını baseline ile karşılaştırmak.
- Windows/Linux CI ve ilgili kalite kontrollerini doğrulamak.
- Kazanımları ve kalan darboğazları kapanış raporuna yazmak.

**Çıkış kapısı:** Davranış eşdeğerliği kanıtlanmış, maliyet düşüşü baseline ile gösterilmiş ve CI başarılı.

---

## 5. Ayrıntılı teknik mimari

### 5.1. Hedef mimari — kavramsal akış

Aşağıdaki yapı hedeflenen sorumluluk ayrımını gösterir. Bu, mevcut kodda bu sınıfların bulunduğu iddiası değildir; gerçek sınıf/modül adları Aşama 2.1 envanterinde doğrulanacaktır.

```text
GameplayService.advance_npc_simulation(dt)
                    |
                    v
          NPC subsystem dispatch
        (patrol / avoidance / companion)
                    |
                    v
       PerceptionQueryCoordinator
       (tick-scoped orchestration)
                    |
          +---------+----------+
          |                    |
          v                    v
   Candidate Provider     Query Metrics
   (broad phase)          (counts / timings)
          |
          v
   Candidate Set
   (stable, unique IDs)
          |
          v
   Exact Perception Checks
   (existing rules, unchanged)
          |
          v
   Perception Result
          |
          v
   Existing NPC Behavior Policy
          |
          v
   Existing movement / collision pipeline
```

**Sorumluluklar:**

- **GameplayService:** Alt sistemlerin kanonik sırasını ve ortak simülasyon zamanını yönetir.
- **PerceptionQueryCoordinator (tasarım rolü):** Aynı tick içinde ortak sorgu bağlamı gerekiyorsa bunu sağlar; davranış kararı vermez.
- **Candidate Provider (tasarım rolü):** Broad-phase ile muhtemel adayları döndürür; kesin algılama kararı vermez.
- **Exact Perception Checks:** Mesafe, görüş, ilişki, hedef uygunluğu ve mevcut diğer koşulları aynen uygular.
- **Query Metrics:** Sorgu sayısı/süresini toplar; oyun kararlarına katılmaz.
- **NPC Behavior Policy:** Mevcut devriye/kaçınma/yoldaş davranış kurallarıdır; bu aşamada değiştirilmez.

Bu rollerin tek sınıfta birleştirilmesi zorunlu değildir. En küçük, mevcut modül sınırlarıyla uyumlu çözüm tercih edilmelidir.

### 5.2. Broad-phase ve narrow-phase ayrımı

**Broad-phase (aday üretimi):**
- Bir NPC'nin algılama yarıçapı veya sorgu alanı ile kesişebilecek aktörleri bulur.
- Amaç yanlış negatif üretmeden aday sayısını azaltmaktır.
- Kesin hedef seçimi veya davranış kararı vermez.
- Adayları kimlik bazında tekilleştirir.
- Sonuç sıralaması mevcut davranışın sıralama beklentisini korumalıdır; beklenti yoksa deterministik bir sıra tanımlanmalıdır.

**Narrow-phase (kesin kontrol):**
- Mevcut mesafe/yarıçap koşullarını uygular.
- Mevcut görüş/engel/ilişki/takım/yaşam durumu ve hedef uygunluğu koşullarını korur.
- Mevcut hedef önceliği ve eşitlik çözümünü değiştirmez.
- Broad-phase sonuçlarını davranış kararıyla karıştırmaz.

**Doğruluk kuralı:** Broad-phase, mevcut tam taramanın döndürebileceği geçerli adayları eksiltmemelidir. Fazladan aday döndürmesi performans kaybı yaratabilir ama davranış değişikliği yaratmaz; geçerli adayı atlaması ise davranış hatasıdır.

### 5.3. Mekânsal sorgu altyapısı kararı

Teknik denetim, hareket/çarpışma tarafında mekânsal indeks kullanımına işaret etmektedir; ancak bunun NPC algılama için aynı veri sahipliği, güncellik ve sorgu semantiğiyle kullanılabildiği henüz kanıtlanmış değildir.

Karar sırası:
1. Mevcut spatial index'in hangi aktörleri içerdiğini ve hangi anda güncellendiğini incele.
2. NPC hareket/konum güncellemeleri ile indeks güncelleme sırasını doğrula.
3. Algılama sorgusunun indeks üzerinden yapılmasının yanlış negatif üretmeyeceğini test et.
4. Mevcut indeks uygun değilse önce nedeni belgeleyip en küçük gerekli çözümü tasarla.
5. İkinci bir paralel indeks ancak mevcut olanın sorumlulukları açıkça yetersizse ve bakım maliyeti gerekçelendirilebiliyorsa ekle.

Belirli bir grid hücre boyutu, chunk boyutu veya indeks tipi bu aşamada sabitlenmemiştir. Bunlar harita ölçeği, NPC algılama yarıçapı, hareket sıklığı ve benchmark sonucuna göre seçilecektir.

### 5.4. Tick-scoped snapshot ve cache sözleşmesi

Öncelikli tercih, doğruluğu kolay kanıtlanabilen **tek sabit simülasyon tick'i boyunca geçerli** sorgu verisidir.

Önerilen veri modeli kavramsal olarak:
- `simulation_tick_id`
- `runtime_identity` veya runtime/world generation
- `actor_state_version` / konum snapshot sürümü
- `candidate_ids`
- isteğe bağlı önceden hesaplanmış mesafe/konum verisi

Bu alan adları mevcut API önerisi değil, gerekli kimlik/sürüm bilgilerini anlatan tasarım etiketleridir.

Kurallar:
- Snapshot, hangi dünya durumunu temsil ettiğini açıkça belirtmelidir.
- Aynı tick'te alt sistemler aynı snapshot'ı kullanacaksa güncelleme sırası tanımlanmalıdır.
- Snapshot oluşturulduktan sonra aktör konumları değişiyorsa eski snapshot'ın hangi alt sistemler için geçerli olduğu belirlenmelidir.
- Tick değişince tick-scoped cache otomatik olarak bırakılmalıdır.
- Runtime/NPC koleksiyonu/oyuncu/fizik binding değişiminde ilgili cache yeniden kurulmalıdır.
- Cache içinde mutable canlı aktör referansları tutmak yerine mümkünse immutable kimlik ve gerekli konum verisi kullanılmalıdır.
- Cache, davranış sonucunu veya hedef kararını sessizce eski veriden üretmemelidir.

**Tick dışına taşan algılama cache'i varsayılan olarak kapsam dışıdır.** Böyle bir cache ancak algılama gecikmesinin oyun tasarımı açısından kabul edilebilir olduğu açıkça onaylanırsa ayrı tasarım kararı olabilir.

### 5.5. Güncelleme sırası ve snapshot tutarlılığı

Aşama 1'in alt sistem sırası korunurken, algılama snapshot'ının hangi noktada alındığı kritik olacaktır.

Aşama 2.1 sırasında şu sorular kaynak koduyla cevaplanmalıdır:
- Devriye güncellemesi NPC konumunu değiştiriyor mu?
- Kaçınma sistemi, devriye sonrası konumu mu yoksa önceki konumu mu görmelidir?
- Yoldaş sistemi kaçınma sonrası hareket/konum verisini mi tüketiyor?
- Mevcut sistemler her biri kendi sorgusunu mu yapıyor, yoksa ortak world snapshot var mı?

Ortak snapshot kullanımı mevcut sıralı semantiği değiştirecekse bu bir performans refactor'ı olarak sessizce uygulanamaz. Önce davranış sözleşmesi belirlenmeli; gerekiyorsa ayrı onay alınmalıdır.

### 5.6. Algılama sıklığı ve zamanlama politikası

Aşama 2'nin ana hedefi tarama maliyetini azaltmak olsa da algılama sıklığını azaltmak doğrudan tepki gecikmesini değiştirir. Bu nedenle ilk tercih aynı tick'te tekrar eden işleri kaldırmak ve adayları daraltmaktır; algılama periyodunu düşürmek değildir.

İleride farklı algılama periyotları önerilirse:
- Devriye, kaçınma, oyuncu tehdidi ve yoldaş komutları için ayrı tepki gereksinimleri çıkarılmalı.
- Savaş/tehdit/çok yakın mesafe gibi kritik durumlar daha seyrek taramaya tabi tutulmamalı.
- Kademeli/staggered tarama kullanılacaksa NPC'ler arasında deterministik faz dağıtımı yapılmalı.
- En kötü algılama gecikmesi ölçülüp raporlanmalı.
- Aynı simülasyon girdisinde tekrar üretilebilirlik korunmalı.
- Periyot değişikliği davranışsal karar olarak onaya sunulmalı.

### 5.7. Mantıksal algılama ile görsel LOD ayrımı

Kamera dışında kalmak bir NPC'nin dünyayı algılamayı bırakması için tek başına yeterli gerekçe değildir.

Bu aşamada:
- Algılama/karar mantığı dünya simülasyonunun parçası olarak ele alınır.
- Görsel animasyon, sprite hazırlığı ve render görünürlüğü sunum katmanına aittir.
- Görünürlük bilgisi pahalı çizim/animasyon işlerini azaltabilir.
- Görünürlük, devriye/kaçınma/yoldaş davranışını otomatik olarak durduramaz.
- Mantıksal simülasyon LOD'si önerilecekse davranış farkı, tepki gecikmesi ve dünya tutarlılığı ayrıca belgelenir; bu aşama içinde varsayılan çözüm değildir.

### 5.8. Determinizm ve sıralama

Mekânsal indekslerin veya hash tabanlı koleksiyonların aday sırası kararlı olmayabilir. Mevcut kod hedefleri ilk eşleşmeye göre seçiyorsa sıra değişimi oyuncunun gözlemlediği davranışı değiştirebilir.

Bu nedenle:
- Aday kimlikleri tekrarsız olmalıdır.
- Gerekli yerde mevcut sıralama korunmalıdır.
- Sıralama sözleşmesi yoksa kararlı bir tie-break kuralı belirlenmelidir.
- Aynı başlangıç durumu ve aynı tick girdileri aynı algılama sonuçlarını üretmelidir.
- Testlerde yalnızca aday sayısı değil, aday kimlikleri ve seçilen hedef de karşılaştırılmalıdır.

---

## 6. Ölçüm ve benchmark tasarımı

### 6.1. Toplanacak metrikler

| Metrik | Açıklama |
|---|---|
| NPC toplamı | Simülasyona kayıtlı NPC sayısı |
| NPC alt sistem süreleri | Devriye, kaçınma, yoldaş ayrı süre |
| Algılama çağrı sayısı | Algılama/çevre sorgusu toplam çağrı |
| NPC başına sorgu | NPC başına ortalama ve dağılım |
| Aday sayısı | Broad-phase tarafından döndürülen aday |
| Kesin kontrol sayısı | Narrow-phase mesafe/görüş vb. kontrol |
| Kabul edilen hedef | Kesin koşullardan geçen aday |
| Mesafe hesabı sayısı | Gerçek mesafe hesaplarının adedi |
| Komşuluk sorgusu | Spatial/neighborhood query adedi |
| Path sorgusu | Algılama zincirinde gerçekten tetiklenen path query |
| Cache hit/miss | Tick-scoped cache yeniden kullanım oranı |
| Snapshot üretim süresi | Ortak sorgu bağlamı oluşturma maliyeti |
| NPC simülasyon süresi | Alt sistemlerin toplamı |
| Frame time p50/p95/p99 | Kare süresi dağılımı |
| Frame spike | Belirlenen eşik üzerindeki kare sayısı |

Metrikler mümkün olduğunca sayaç tabanlı ve düşük maliyetli olmalıdır. Ayrıntılı zaman ölçümü debug/benchmark modunda açılabilir. Her sayaç için hangi kod yolunda arttığı belgelenmelidir.

### 6.2. Benchmark matrisi

| Senaryo | NPC sayısı | Amaç |
|---|---:|---|
| B1 | 1 | Sabit maliyet / tek aktör tabanı |
| B2 | 10 | Küçük karşılaşma |
| B3 | 25 | Orta yoğunluk |
| B4 | 50 | Yoğun alan |
| B5 | 100 | Ölçek davranışı |

Tüm senaryolarda:
- Aynı harita, oyuncu konumu ve terrain kullanılmalı.
- NPC başlangıç konumları ve davranış durumları sabitlenmeli.
- Aynı simülasyon tick sayısı çalıştırılmalı.
- Isınma ve ölçüm aralıkları ayrılmalı.
- Ölçüm öncesi/sonrası aynı test ortamı kullanılmalı.
- Ortalama tek başına kabul ölçütü sayılmamalı; p50/p95/p99 ve çağrı sayıları birlikte raporlanmalı.
- Donanım ve Python sürümü rapora eklenmeli.

### 6.3. Başlangıç baseline'ı

Optimizasyon öncesi baseline:
1. Mevcut kodla benchmark senaryolarını çalıştır.
2. Her senaryoda en az birkaç tekrar al; tekrar sayısını benchmark betiği belirlesin ve raporlasın.
3. Süre ve sayaç dağılımlarını kaydet.
4. En pahalı sorgu sınıfını belirle.
5. Ölçüm gürültüsünü ve test makinesi bilgilerini raporla.

Aşama 1 raporundaki 15.96–27.69 ms frame ortalaması ve 8.97–19.14 ms NPC simülasyon ortalaması gibi gözlemsel aralıklar yalnızca tarihsel teşhis bağlamıdır; bu benchmark'ın baseline değeri olarak kopyalanmamalıdır.

---

## 7. Test mimarisi ve doğrulama

### 7.1. Davranış eşdeğerliği testleri

- Tam tarama ve optimize aday üretimi aynı geçerli aday kimliklerini üretir.
- Aynı NPC için seçilen hedef değişmez.
- Mesafe sınırındaki (tam eşik, eşik altı, eşik üstü) sonuçlar değişmez.
- Oyuncu/NPC yaşam durumu, ilişki/takım ve diğer filtreler aynı sonucu verir.
- Aynı tick'te birden fazla alt sistemin sorgu yapması mevcut sıra ve veri görünürlüğü sözleşmesini bozmaz.
- Aday sıralaması davranış sonucunu değiştirmez veya tanımlı kararlı tie-break ile korunur.
- Kamera görünürlüğü mantıksal algılama sonucunu değiştirmez.

### 7.2. Cache ve invalidation testleri

- Aynı tick ve aynı veri sürümünde cache hit oluşur.
- Yeni tick'te tick-scoped cache temizlenir veya yeni bağlam üretilir.
- NPC ekleme/çıkarma cache'i doğru şekilde geçersizleştirir.
- Oyuncu aktör/runtime/fizik binding değişimi eski cache'in kullanılmasını önler.
- Aktör konum değişimi snapshot sözleşmesine uygun şekilde ele alınır.
- Harita/navigasyon verisi değişikliği ilgili sorguyu geçersizleştirir.
- Cache kapalı ve açık sonuçları davranış bakımından eşdeğerdir.

### 7.3. Performans testleri

- 1/10/25/50/100 NPC senaryolarında sorgu sayısı ve süre ölçülür.
- NPC sayısı arttığında maliyet eğrisi raporlanır.
- Broad-phase sonrası aday sayısının düşmesi doğrulanır.
- Cache hit/miss oranı ve cache bakım maliyeti raporlanır.
- Ölçüm kapalı/açık maliyet farkı belirlenir.
- Donanım gürültüsüne duyarlı kesin FPS eşiği birim testine konmaz; benchmark raporları karşılaştırmalı tutulur.

### 7.4. Mevcut testlerle uyumluluk

Aşama 1'de eklenen:
- `tests/test_application/test_npc_simulation_orchestration.py`
- `tests/test_game_ui/test_game_window_rendering.py`

testleri korunmalı ve yeni testler bunların üzerine eklenmelidir. Devriye, kaçınma, yoldaş, NPC çarpışma ve GameplayService regresyon testleri de çalıştırılmalıdır.

---

## 8. Önerilen modül ve dosya sınırları

Aşağıdaki liste hedef sorumlulukları gösterir; gerçek dosya adları Aşama 2.1 kod envanterinden sonra mevcut mimariye göre seçilecektir.

| Sorumluluk | Yerleşim ilkesi |
|---|---|
| Merkezi orkestrasyon | Mevcut `application/gameplay_service.py` korunur |
| Algılama aday sorgusu | Mevcut perception/sensing modülünde veya en küçük ayrıştırılmış uygulama bileşeninde |
| Spatial query adaptörü | Mevcut mekânsal indeks varsa onu saran dar arayüz; yoksa gerekçeli yeni bileşen |
| Tick snapshot/cache | Sahipliği açık, tick ömrü sınırlı uygulama bileşeni |
| Kesin algılama kuralları | Mevcut NPC davranış/domain kodunda korunur |
| Telemetri | Mevcut telemetry/frame metrics yapısına uyumlu, davranıştan bağımsız |
| Benchmark | Test/benchmark araçlarında, oyun davranış kodundan ayrı |

**Mimari ilke:** Algılama adaylarını bulmak, kesin algılama kararı vermek ve NPC davranışını yürütmek ayrı sorumluluklardır. Yeni bir genel amaçlı framework veya gereksiz soyutlama katmanı oluşturulmayacaktır.

---

## 9. Riskler ve azaltma stratejileri

| Risk | Etki | Azaltma |
|---|---|---|
| Broad-phase yanlış negatif üretir | NPC geçerli hedefi algılamaz | Tam tarama karşılaştırmalı eşdeğerlik testleri |
| Cache eski konum kullanır | Tepki/kaçınma yanlış olur | Tick ve veri sürümüyle sınırlama, invalidation testleri |
| Aday sırası değişir | Hedef seçimi değişebilir | Mevcut sıra veya deterministik tie-break |
| Tarama sıklığı düşürülür | Tepki gecikmesi artar | İlk sürümde periyot azaltmama; ayrı onay ve gecikme testi |
| Görünürlük mantıksal simülasyonu durdurur | Kamera dışında dünya davranışı bozulur | Render LOD ve mantıksal simülasyonu ayırma |
| İkinci spatial index eklenir | Bellek ve bakım maliyeti artar | Önce mevcut indeksi doğrulama |
| Telemetri maliyeti büyür | Ölçüm performansı bozar | Sayaçları hafif tutma, ayrıntılı timing'i opsiyonel yapma |
| Aşırı genel coordinator tasarlanır | Mimari karmaşıklık | Mevcut modüllere en küçük entegrasyon |
| Aşama 1 orkestrasyonu geriler | Çağrı sırası/zaman tutarlılığı bozulur | Merkezi servis entegrasyon regresyon testleri |

---

## 10. Uygulama sırası ve değişiklik politikası

1. Önce Aşama 2.1 envanterini tamamla.
2. Davranış sözleşmesini ve kritik çağrı sırasını yazılı hâle getir.
3. Ölçüm noktalarını en az müdahaleyle ekle.
4. Baseline benchmark'larını çalıştır ve raporla.
5. En büyük ve kanıtlanmış maliyete göre tek bir optimizasyon seç.
6. Önce davranış eşdeğerliği testlerini ekle.
7. Optimizasyonu küçük bir değişiklik kümesi olarak uygula.
8. Eski/yeni benchmark'ı aynı koşullarda karşılaştır.
9. Tüm regresyon testlerini ve CI kontrollerini çalıştır.
10. Bir sonraki optimizasyona ancak önceki değişiklik doğrulandıktan sonra geç.

Her değişiklik küçük ve izlenebilir commit'lerle yapılmalıdır. Birden fazla optimizasyon aynı commit'e yığılmamalıdır. Davranış semantiğini etkileyen bir bulgu ortaya çıkarsa kod değişikliği durdurulmalı ve karar proje sahibine sunulmalıdır.

---

## 11. Kabul kriterleri

Aşama 2 ancak aşağıdaki koşullar birlikte karşılandığında kapatılabilir:

| Kriter | Kabul koşulu |
|---|---|
| Kod envanteri | Algılama ve çevre tarama çağrı zinciri belgelenmiş |
| Baseline | 1/10/25/50/100 NPC için tekrarlanabilir ölçüm var |
| Ölçüm | Alt sistem, sorgu sayısı, aday sayısı ve süreler ayrıştırılmış |
| Davranış | Mevcut algılama/target seçim semantiği regresyona uğramamış |
| Aday üretimi | Broad-phase geçerli adayları eksiltmiyor |
| Cache | Anahtar, yaşam süresi ve invalidation açıkça test edilmiş |
| Determinizm | Aynı girdide aynı algılama sonucu ve hedef seçimi |
| Zamanlama | Sabit adım ve Aşama 1 alt sistem sırası korunmuş |
| Görünürlük | Kamera dışı olma mantıksal algılamayı kendiliğinden durdurmuyor |
| Performans | En az bir gerçek darboğazda baseline'a göre ölçülebilir maliyet düşüşü gösterilmiş |
| Test | NPC, GameplayService ve GameWindow regresyonları başarılı |
| CI | İlgili Windows/Linux ve kalite kontrolleri başarılı |
| Raporlama | Önce/sonra sonuçları, sınırlamalar ve kalan işler kapanış raporunda kayıtlı |

Sayısal performans hedefleri baseline görülmeden sabitlenmemiştir. Aşama 2.2 tamamlandığında ölçüm sonuçlarına göre proje sahibiyle birlikte hedef eşikler belirlenmelidir.

---

## 12. Aşama 2 sonunda beklenen çıktılar

1. NPC algılama/çevre tarama mevcut durum ve çağrı zinciri raporu.
2. Ölçüm altyapısı ve benchmark senaryoları.
3. Baseline performans raporu.
4. Onaylanmış hedef mimari ve davranış eşdeğerliği sözleşmesi.
5. Uygulanmış optimizasyon(lar) ve bunların testleri.
6. Önce/sonra performans karşılaştırması.
7. CI doğrulama kaydı.
8. Aşama 2 kapanış raporu ve sonraki aşamaya devredilen işler.

---

## 13. Nihai teknik karar

Aşama 2'nin yönü **NPC algılama ve çevre tarama maliyetlerini azaltmaktır**. İlk teslimat kod optimizasyonu değil; kod envanteri, davranış sözleşmesi ve ölçülebilir baseline olacaktır.

Aşama 1'in merkezi `GameplayService` orkestrasyonu, sabit zaman adımı ve mevcut devriye → kaçınma → yoldaş sırası korunacaktır. Öncelik; tam koleksiyon taramalarını ve tekrar eden sorguları kanıtla tespit etmek, broad-phase aday üretimini mevcut mekânsal altyapıyla uyumlu biçimde değerlendirmek ve aynı tick içindeki tekrarlı hesapları güvenli şekilde yeniden kullanmaktır.

**Bu belge yalnızca plan ve mimari sözleşmedir. Kaynak kodu, testler, oyun davranışı veya yapılandırma üzerinde herhangi bir uygulama değişikliği yapıldığı anlamına gelmez.**
