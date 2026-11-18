# Aşama 11 — Sağlamlık, Regresyon ve Performans Doğrulaması

> **Belge türü:** Aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** GENEL PLAN KULLANICI TARAFINDAN ONAYLANDI — TEKNİK PLAN ONAYI BEKLENİYOR  
> **Ön koşul:** Aşama 0–10 tamamlandı ve kabul edildi  
> **Tek laboratuvar başlatıcısı:** `python -m hex_world_lab`

---

## 1. Amaç

Aşama 11'in amacı, Aşama 0–10 boyunca kurulan hex dünya altyapısının yalnızca küçük kabul sahnesinde değil; büyük harita, yüksek entity sayısı, yoğun engel, değişken frame-time ve uzun süreli çalışma koşullarında da doğru, kararlı ve ölçülebilir biçimde çalıştığını doğrulamaktır.

Bu aşama yeni oynanış sistemi ekleme aşaması değildir. Öncelik, mevcut mimarinin sınırlarını kontrollü biçimde zorlamak, darboğazları ölçmek, doğruluk ve performans regresyonlarını ortaya çıkarmak, yalnızca kanıtlanmış sorunları sınırlı kapsamda düzeltmek ve entegrasyon hazırlığı öncesinde teknik riskleri görünür hâle getirmektir.

**Temel ilke:** Önce doğruluk ve tekrarlanabilirlik; ardından performans ölçümü ve gerekçeli optimizasyon. Ölçüm yapılmadan performans iyileşmesi iddia edilmeyecektir.

## 2. Mevcut mimarideki yeri

Aşama 10 sonunda laboratuvarda aşağıdaki altyapılar bir araya getirilmiş ve kabul edilmiştir:

- Hex geometri, dünya modeli ve harita yaşam döngüsü.
- Sürekli oyuncu hareketi, çarpışma ve fizik çözümü.
- Kamera, world/screen dönüşümü ve render görünürlük sistemi.
- UniformGrid/Quadtree tabanlı spatial altyapı ve entity spatial adapter.
- Oyuncu, NPC ve kaynak için ortak entity kimliği/konum modeli.
- Hedef seçimi ve etkileşim menzili sorguları.
- Yoldaş ilişki ve FOLLOW/WAIT/RETURN komut verisi.
- 60 TPS sabit tick düzeni ve merkezi SimulationTickCoordinator.
- Render snapshot ve render akışında authoritative state değişmezliği.

Aşama 11 bu sistemleri yeniden tasarlamayı değil, gerçekçi ve kontrollü yük profilleri altında birlikte davranışlarını sınamayı hedefler.

## 3. Bağlayıcı kararlar ve kapsam sınırları

### 3.1 Korunacak davranışlar

- Tek laboratuvar başlatıcısı `python -m hex_world_lab` olarak kalacaktır.
- Simülasyon 60 TPS sabit tick sözleşmesini ve Aşama 10'da doğrulanan tick sırasını koruyacaktır.
- Render, kamera ve tanılama katmanları authoritative dünya/entity state'ini değiştirmeyecektir.
- Hex topolojisi, gerçek çarpışma geometrisi ve brute-force doğruluk referansları korunacaktır.
- Spatial index optimizasyonu doğruluk kaynağına dönüştürülmeyecektir.
- Testler sabit seed ve belgelenmiş senaryo parametreleriyle tekrarlanabilir olacaktır.

### 3.2 NPC, kaynak ve yoldaş sınırı

- NPC'ler ve kaynaklar stres senaryolarında da sabit konumlu entity'ler olarak kalacaktır.
- FOLLOW, WAIT ve RETURN yalnızca Aşama 9'da tanımlanan ilişki/komut verisi olarak kalacaktır.
- NPC devriyesi, gezinme, otonom karar veya gerçek yoldaş takibi eklenmeyecektir.
- Rastgele hareket testleri gerekiyorsa yalnızca oyuncu hareket girdisi veya test amaçlı sentetik hareket dizileri kullanılacaktır; bu, NPC hareket sistemi oluşturmak anlamına gelmez.

### 3.3 Kapsam dışı

- NPC AI, algı, günlük rutin, devriye veya otonom hareket.
- Yoldaş takip/steering/formation/pathfinding davranışları.
- A*, Dijkstra, click-to-move veya rota planlama.
- Kaynak toplama, üretim, envanter transferi ve ekonomi.
- Yeni savaş, görev, diyalog veya ilerleme sistemi.
- Nihai çevre sanatı, animasyon/ses paketi veya görsel tasarım yenilemesi.
- Harita editörü veya genel amaçlı içerik üretim aracı.
- Godot'a geçiş.
- `main` veya `demo_eldoria` dallarına kod aktarımı ya da entegrasyon.
- Ölçümle gerekçelendirilmemiş büyük mimari refaktör.

Bu başlıklardan biri gerekli görünürse önce bulgu ve etkisi raporlanır; mevcut aşamanın kapsamına kendiliğinden eklenmez.

## 4. İş paketleri

### 11.1 — Mevcut doğrulama ve performans altyapısının denetimi

- Aşama 6–10 kapanış raporları, mevcut testler, benchmarklar ve CI iş akışlarını incelemek.
- Mevcut benchmarkların hangi sistemleri ve yük seviyelerini ölçtüğünü haritalamak.
- Aynı ölçümü tekrar eden veya artık geçerli olmayan benchmark/testleri belirlemek.
- Aşama 10 tick/render snapshot sonuçlarını başlangıç referansı olarak kaydetmek.
- Ölçüm ortamı, Python sürümü, işletim sistemi, seed, ısınma ve tekrar sayısı sözleşmesini netleştirmek.
- Testlerdeki mevcut boşlukları ve bilinen riskleri listelemek.

**Çıktı:** Başlangıç ölçüm raporu, test/benchmark envanteri ve risk listesi.

### 11.2 — Ölçeklenebilir stres senaryolarının oluşturulması

Aşağıdaki profiller için kontrollü test senaryoları hazırlamak:

- Büyük hex harita ve farklı harita yoğunlukları.
- Yüksek entity sayısı; mevcut entity spatial benchmarkındaki 100, 1.000 ve 10.000 varlık profillerini başlangıç karşılaştırma noktası olarak kullanmak.
- Seyrek, kümelenmiş ve karma boyutlu entity dağılımları.
- Seyrek, yoğun ve bitişik engel kümeleri.
- Dar geçit, çoklu temas ve harita sınırına yakın hareket senaryoları.
- Entity oluşturma/silme/taşıma yoğunluğu ve spatial index güncelleme yükü.
- Birden fazla harita arasında yükleme, boşaltma ve yeniden yükleme döngüleri.

Senaryo boyutları bellek ve çalışma süresi gözlemleriyle kademeli artırılacaktır. Test ortamının kapasitesini aşan profiller kontrollü biçimde işaretlenecek; başarısızlık nedeni ayrıştırılmadan sonuç performans hatası olarak sınıflandırılmayacaktır.

**Çıktı:** Parametreleri belgelenmiş, sabit seed ile tekrar üretilebilen stres senaryosu matrisi.

### 11.3 — Simülasyon, hareket ve zamanlama sağlamlığı

- Oyuncu hareketini sabit seed ile üretilmiş uzun input dizileriyle sınamak.
- 30/60/120 FPS render koşullarında simülasyon sonucunun aynı kalmasını doğrulamak.
- Düzensiz frame-time, kısa süreli büyük frame-time sıçraması ve art arda tick işleme senaryolarını test etmek.
- Uzun süreli hareket, harita sınırı, engel kenarı, dar geçit ve çoklu temas koşullarında konum/çarpışma doğruluğunu izlemek.
- Simülasyon tick'i, MovementState, EntityTransform ve EntitySpatialIndex tutarlılığını uzun test boyunca karşılaştırmak.
- Tick callback hatası ve yeniden deneme durumlarında kısmi güncelleme/çift uygulama riskini sınamak.

**Çıktı:** Deterministik stres testleri ve uzun süreli simülasyon sağlamlık raporu.

### 11.4 — Entity, spatial index ve dünya yaşam döngüsü regresyonu

- Spatial sorgularını farklı yoğunluk ve dağılımlarda brute-force referansıyla karşılaştırmak.
- False negative, yinelenen aday, stale entry ve yanlış harita kaydı risklerini sınamak.
- Entity ekleme, taşıma, pasifleştirme, silme ve harita unload/reload/remove döngülerini yoğunlaştırmak.
- Etkileşim hedef seçimi ve menzil doğruluğunu yüksek entity sayısında test etmek.
- Entity registry, companion roster ve spatial index arasında yaşam döngüsü tutarlılığını doğrulamak.
- NPC/kaynak sabitliği ve yoldaş komutlarının konum değiştirmediği koşulunu regresyon testlerinde korumak.

**Çıktı:** Entity/spatial/world regresyon raporu ve gerekli yeni regresyon testleri.

### 11.5 — Fizik ve geometri sınır/stres testleri

- Çok sayıda engel ve karmaşık engel kümelerinde broadphase/narrowphase doğruluğunu sınamak.
- Yüksek hız, küçük hareket adımı, köşe teması ve dar koridor koşullarını test etmek.
- Hex polygon sınırlarında, kenar/köşe yakınında ve negatif dünya koordinatlarında hassasiyet sorunlarını araştırmak.
- Spatial broadphase sonuçlarının nihai fizik kararını etkilemediğini doğrulamak.
- Uzun süreli hareket sırasında birikimli konum sapması veya temas kararsızlığı olup olmadığını ölçmek.

**Çıktı:** Geometri/fizik stres ve regresyon raporu.

### 11.6 — Performans ve bellek ölçümü

Aşağıdaki metrikleri senaryo ve yük profili bazında ölçmek:

- Simülasyon tick süresi.
- Physics/collision güncelleme maliyeti.
- Spatial query, index build ve index update maliyeti.
- Render snapshot ve görünür alan/render maliyeti.
- Ortalama, median, P95 ve mümkün olduğunda P99 frame/tick/query süreleri.
- Entity/obstacle sayısı ve sorgu başına aday sayısı.
- Bellek kullanımı ve ölçülebiliyorsa tepe bellek tüketimi.
- Harita/entity yaşam döngüsü işlemlerinin maliyeti.

Benchmarklarda ısınma, ölçüm tekrarı, seed ve donanım/yazılım bilgileri sabitlenip raporlanacaktır. Aşama 10 sonuçları başlangıç referansı olarak saklanacaktır; farklı CI donanımlarında alınan ham süreler doğrudan eşdeğer kabul edilmeyecektir.

**Performans hedefleri için ön koşul:** Mutlak FPS veya milisaniye eşiği başlangıç profilleri ölçülmeden belirlenmeyecektir. Önce mevcut donanım/CI profillerinde baseline oluşturulacak; ardından kabul eşikleri ve anlamlı regresyon toleransları teknik planda gerekçelendirilip onaya sunulacaktır.

**Çıktı:** Karşılaştırmalı benchmark raporu, bellek ölçümleri ve gerekçeli performans hedefleri.

### 11.7 — Tanılama, hata sınıflandırması ve sınırlı düzeltmeler

- Stres testlerinde oluşan hataların yeniden üretilebilir kayıtlarını oluşturmak.
- Hataları doğruluk, yaşam döngüsü, performans, bellek, görsel sunum ve test altyapısı başlıklarında sınıflandırmak.
- Kritik hatalar için önce başarısızlığı gösteren regresyon testi eklemek.
- Yalnızca Aşama 11 hedefleri için gerekli, kapsamı sınırlı düzeltmeleri yapmak.
- Ölçümle doğrulanmayan optimizasyonları uygulamamak.
- Çözülemeyen sorunları etkisi, yeniden üretim adımı ve entegrasyon riskiyle birlikte kaydetmek.

**Çıktı:** Hata/riske göre önceliklendirilmiş düzeltme kaydı ve güncel bilinen sorunlar listesi.

### 11.8 — Çapraz platform doğrulama ve kabul hazırlığı

- Laboratuvar testlerini ve benchmark doğrulama adımlarını çalıştırmak.
- Core Quality Linux ve Windows iş akışlarını doğrulamak.
- Test seed'lerinin ve senaryo parametrelerinin CI üzerinde tekrar üretilebilir olduğunu kontrol etmek.
- Benchmark ve stres testi artifact'lerini saklamak.
- Görsel yoğunluk senaryolarında çizim, foot-anchor, y-sort, culling, kamera ve seçim davranışlarını kontrol etmek.
- Manuel kabul kontrol listesini ve Aşama 11 kapanış raporunu hazırlamak.
- Kritik açık hata kalmadığını; kalan sınırlamaların belgeli ve kabul edilebilir olduğunu göstermek.

**Çıktı:** Linux/Windows CI kanıtları, test ve benchmark artifact'leri, manuel kabul listesi ve kapanış raporu taslağı.

## 5. Beklenen teslimatlar

- Mevcut test ve benchmark altyapısı denetim raporu.
- Büyük harita/entity/engel yük senaryoları.
- Sabit seed'li uzun süreli simülasyon ve hareket stres testleri.
- Physics, spatial, entity ve harita yaşam döngüsü regresyon testleri.
- Performans ve bellek benchmarkları.
- Aşama 10 ile karşılaştırılabilir baseline ve gerekçeli performans hedefleri.
- Hata sınıflandırma ve bilinen sorunlar listesi.
- Linux/Windows CI ve artifact kanıtları.
- Manuel görsel/işlevsel kabul kontrol listesi.
- Aşama 11 kapanış raporu.

## 6. Kabul koşulları

Aşama 11 ancak aşağıdaki koşulların tamamı sağlandığında teknik kabul için hazır sayılır:

1. Büyük harita, yüksek entity sayısı, farklı dağılımlar ve yoğun engel profilleri için tekrarlanabilir senaryolar mevcuttur.
2. Stres senaryoları sabit seed ve belgelenmiş parametrelerle yeniden çalıştırılabilir.
3. Uzun süreli simülasyon testlerinde oyuncu hareketi, entity transform ve spatial index arasında tutarsızlık birikmez.
4. 30/60/120 FPS ve değişken frame-time testlerinde simülasyon davranışı render FPS'inden bağımsız kalır.
5. Spatial sorgular brute-force doğruluk referansıyla eşleşir; false negative veya açıklanamayan stale kayıt oluşmaz.
6. Fizik ve geometri stres testlerinde kritik çarpışma, sınır veya konum doğruluğu hatası açık kalmaz.
7. Harita/entity oluşturma, silme, taşıma, unload/reload/remove döngüleri registry, companion ve spatial state'i tutarlı bırakır.
8. NPC ve kaynaklar sabit kalır; FOLLOW/WAIT/RETURN komutları konum değişikliğine yol açmaz.
9. Simülasyon, physics, spatial, render ve bellek maliyetleri tanımlı profillerde ölçülüp raporlanır.
10. Performans kabul eşikleri baseline'a dayanır; mutlak hedefler gerekçesiz belirlenmez.
11. Kritik testler geçer; flaky testler kabul kanıtı olarak kullanılmaz.
12. Tespit edilen kritik hatalar düzeltilmiş ve regresyon testleri eklenmiş olmalıdır; kalan sorunlar açıkça belgelenmelidir.
13. Laboratuvar CI, Core Quality Linux ve Windows kontrolleri başarılıdır veya istisnalar teknik gerekçeleriyle onaylanmıştır.
14. Görsel stres senaryoları ve kullanıcı manuel kabulü tamamlanır.
15. Kapanış raporu, benchmark kanıtları, commit SHA ve bilinen sınırlamalarla hazırlanır.

## 7. Test ve doğrulama yaklaşımı

- **Unit/property:** Geometri, fizik, koordinat ve veri yapısı sınırları.
- **Integration:** Movement + Physics + Simulation, Entity + Registry + Spatial, World lifecycle + Companion roster.
- **Determinism:** Aynı seed, başlangıç state'i ve input dizisiyle tekrarlı sonuç karşılaştırması.
- **Stress:** Yük profilleri ve uzun süreli çalışma.
- **Differential:** Spatial ve fizik aday sorgularının doğruluk referansıyla karşılaştırılması.
- **Regression:** Önceden kabul edilmiş hareket, kamera, render, seçim ve lifecycle davranışları.
- **Performance:** Sabit koşullarda tekrarlı ölçüm ve dağılım raporu.
- **Visual/acceptance:** Yoğun sahnelerde hizalama, culling, y-sort, kamera ve etkileşim gözlemi.
- **Cross-platform:** Linux ve Windows CI.

Başarısız testler rapordan çıkarılmaz. Test altyapısı hatası ile uygulama hatası birbirinden ayrılır. Performans sonucu yalnızca ölçüm ortamı ve senaryo parametreleriyle birlikte yorumlanır.

## 8. Riskler ve önleyici yaklaşımlar

| Risk | Etki | Önleyici yaklaşım |
|---|---|---|
| Gerçekçi olmayan stres profili | Sonuçların gerçek kullanım yükünü temsil etmemesi | Birden fazla dağılım ve kademeli yük profili |
| CI donanımının değişmesi | Yanlış performans regresyonu yorumu | Ortam metadata'sı ve aynı ortamda baseline karşılaştırması |
| Rastgele testlerin tekrarlanamaması | Hatanın yeniden üretilememesi | Sabit seed ve kayıtlı input dizisi |
| Büyük senaryoların test süresini aşması | CI kararsızlığı | Hızlı PR profili ve daha uzun ayrı stres profili |
| Erken optimizasyon | Gereksiz karmaşıklık ve regresyon | Önce ölçüm, sonra hedefli düzeltme |
| Spatial index'in doğruluk kaynağı sayılması | Eksik hedef/çarpışma adayı | Brute-force ve gerçek geometri referansları |
| Stres testinde kapsamın oynanışa kayması | Aşama sınırının bozulması | NPC/yoldaş/kaynak hareketini kapsam dışı tutmak |
| Bellek/CPU sorununun yanlış sınıflandırılması | Yanlış düzeltme | Profiling kanıtı ve ayrı hata kategorileri |

## 9. Onay kapıları ve uygulama yöntemi

1. Bu genel plan kullanıcı tarafından incelenir ve onaylanır.
2. Onaydan sonra mevcut kod ve benchmarklar dosya/API düzeyinde yeniden denetlenir.
3. Aşama 11 Teknik Mimari Planı, senaryo matrisi, dosya değişiklik listesi, benchmark metodolojisi ve kabul eşikleri hazırlanır.
4. Teknik plan kullanıcı tarafından ayrıca onaylanır.
5. Yalnızca onaylanan kapsamda 11.1–11.8 uygulaması başlatılır.
6. Her iş paketi test ve ölçüm kanıtlarıyla doğrulanır.
7. Laboratuvar CI, Core Quality Linux/Windows ve benchmark artifact'leri tamamlanır.
8. Kullanıcı manuel kabulü alınır; ardından kapanış raporu ve Master Plan güncellenir.

Genel planın hazırlanması uygulama izni anlamına gelmez. Teknik plan ve uygulama için ayrı açık onay gerekir.

---

**Özet karar:** Aşama 11, Eldoria Hex World Laboratory altyapısının sağlamlık, regresyon ve performans doğrulamasıdır. Büyük harita, yüksek entity yoğunluğu, yoğun engel ve uzun süreli simülasyon senaryoları ölçülecektir. NPC, kaynak ve yoldaş hareketi eklenmeyecek; ana oyuna entegrasyon yapılmayacaktır.
