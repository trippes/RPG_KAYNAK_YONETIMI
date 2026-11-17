# Aşama 9 — Varlıklar ve Etkileşimler

> **Belge türü:** Aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — 9.1–9.9 UYGULANDI; MANUEL KABUL BEKLENİYOR  
> **Hazırlanma tarihi:** 17 Kasım 2026  
> **Ön koşul:** Aşama 0–8 tamamlandı ve kabul edildi  
> **Uygulama durumu:** 9.1–9.9 tamamlandı; otomatik test ve Linux/Windows CI başarılı; manuel kabul bekleniyor

---

## 1. Amaç

Aşama 9'un amacı, Eldoria hex dünyasında oyuncu, NPC ve kaynak nesnelerinin aynı dünya-konum sözleşmesini kullanan tutarlı varlıklar olarak temsil edilmesini ve bu varlıklar arasında güvenilir hedef seçimi/yakınlık etkileşimi sorgularının kurulmasını sağlamaktır.

Bu aşamanın temel sorusu şudur:

**Oyuncu, NPC ve kaynak gibi farklı türdeki varlıklar; farklı görsel boyutlara, fiziksel gövdelere ve konum davranışlarına sahip olsalar bile aynı dünya koordinat sistemi içinde nasıl tanımlanmalı, bulunmalı ve etkileşim hedefi olarak seçilmelidir?**

Aşama 9, varlık kimliği, konum, görsel zemin ankrajı, fiziksel gövde ilişkisi ve etkileşim sorgularının mimari temelini oluşturur. Amaç tam bir NPC yapay zekâsı, kaynak toplama oynanışı veya nihai sanat paketi geliştirmek değildir.

## 2. Mevcut mimarideki yeri

Aşama 9, Aşama 0–8'de kurulan Geometry, World, Movement, Physics, Camera, Rendering ve Spatial katmanlarının üzerinde çalışır.

- **Geometry / World:** Hex adresi, harita kimliği ve dünya koordinatı için doğruluk kaynağıdır.
- **Movement:** Hareketli varlıkların sürekli `WorldPosition` durumunu günceller.
- **Physics:** Varlığın fiziksel gövdesini ve çarpışma temaslarını yönetir.
- **Rendering:** Görsel sprite'ı ve foot-anchor/zemin temas noktasını sunar.
- **Spatial:** Yakın adayları ve hedef olabilecek varlıkları verimli biçimde bulur.
- **Entities:** Varlık kimliği, türü ve konum/transform bileşenlerinin sahipliğini tanımlar.
- **Interaction:** Hedef seçimi, etkileşim menzili ve etkileşime uygun adayların belirlenmesini sağlar.

Varlık ve etkileşim katmanları mevcut alt katmanların kurallarını yeniden uygulamaz. Özellikle kamera zoom'u, ekran pikseli, sprite merkezi veya AABB broadphase sonucu authoritative dünya konumu ya da kesin etkileşim kararı olarak kullanılamaz.

## 3. Kapsam

### 3.1 Varlık kimliği ve yaşam döngüsü

- Oyuncu, NPC ve kaynak varlıklarının ortak kimlik sözleşmesini belirlemek.
- Kimliğin varlık türünden ve konumundan bağımsız olmasını sağlamak.
- Varlık oluşturma, kayıt, sorgulama ve kaldırma yaşam döngüsünü tanımlamak.
- Aynı kimliğin aynı dünya/harita kapsamında tekil olmasını ve kaldırılmış varlıkların sorgularda görünmemesini sağlamak.
- Varlık türü ve türe özgü veriyi ortak kimlik/konum sözleşmesinden ayırmak.

### 3.2 Konum ve transform modeli

- Hareketli varlıkların sürekli `WorldPosition` kullanmasını sürdürmek.
- Hücreye sabit nesnelerin `HexCoord`/harita adresiyle tanımlanmasını ve dünya konumunun geometri sözleşmesinden türetilmesini sağlamak.
- Varlık konumu, yönelimi ve gerekliyse ölçek bilgisinin sorumluluklarını belirlemek.
- Dünya konumu ile türetilmiş hex hücre adresi arasındaki ilişkiyi açık hale getirmek.
- Bir varlığın harita kimliğini konumunun ayrılmaz parçası olarak ele almak.

### 3.3 Görsel ankraj ve fiziksel gövde ilişkisi

- Sprite'ın görsel merkezi ile zemine temas/foot-anchor noktasını ayırmak.
- Fiziksel çarpışma gövdesinin görsel sprite boyutundan bağımsız tanımlanmasını korumak.
- Foot-anchor'ın world-to-screen dönüşümü ve Y-sort/depth sıralamasıyla tutarlı çalışmasını sağlamak.
- Farklı görsel boyutlardaki oyuncu, NPC ve kaynak nesnelerinin aynı zemin konumu sözleşmesini kullanmasını sağlamak.
- Aşama 7'de doğrulanmış render/depth davranışını geriye dönük bozmamak.

### 3.4 Etkileşim menzili ve hedef seçimi

- Etkileşim türüne göre dünya mesafesi veya hex mesafesi kullanımını belirlemek.
- Sürekli fiziksel mesafe kullanan menzillerde `WorldPosition` tabanlı ölçümü esas almak.
- Hücre/topolojik kural gerektiren etkileşimlerde hex mesafesini açıkça seçmek.
- Kamera zoom'u ve pencere boyutunun etkileşim menzilini değiştirmediğini doğrulamak.
- Fareyle hedef seçimi ve yakın hedef bulma sorgularını kurmak.
- Birden fazla hedef aynı anda uygunsa deterministik seçim/tie-break kuralı tanımlamak.
- Etkileşime uygunluk, menzil içinde olma ve hedefin geçerliliği kontrollerini birbirinden ayırmak.

### 3.5 Spatial indeks entegrasyonu

- Aşama 8'de kabul edilen Spatial API ve Physics adaptörünü incelemek.
- NPC ve kaynak gibi sorgulanabilir varlıkların mekânsal indeksle nasıl temsil edileceğini belirlemek.
- Ekleme, taşıma, kaldırma ve harita değiştirme işlemlerinde indeks tutarlılığını korumak.
- Harita kimliği farklı olan varlıkların sorgu sonuçlarına karışmasını önlemek.
- İndeksin yalnızca aday bulduğunu; kesin etkileşim menzili ve hedef geçerliliği kararının Interaction katmanında verildiğini doğrulamak.
- Hareketli varlıklar için indeks güncelleme sırasını ve güncellik garantisini tanımlamak.

### 3.6 Yoldaş ilişkisi ve komut altyapısı

- NPC'nin bağımsız dünya varlığı olma durumunu koruyarak oyuncuyla yoldaş ilişkisine katılabilmesini sağlayacak ilişki/sahiplik modelini tanımlamak.
- Yoldaşlık durumunu NPC kimliğinden ve dünya konumundan ayrı, açık bir ilişki olarak temsil etmek.
- Yoldaşın komut durumlarını ve ileride genişletilebilir komut sözleşmesini belirlemek: **FOLLOW** (oyuncuyu takip et), **WAIT** (bulunduğu yerde bekle) ve **RETURN** (oyuncunun yanına dön).
- Yoldaş ilişkisinin kurulması, sona ermesi, harita değişimi ve NPC yaşam döngüsüyle etkileşimini tanımlamak.
- Bu aşamada yalnızca veri modeli, ilişki yaşam döngüsü ve komut altyapısı/arayüz sınırlarını kurmak; gerçek otonom hareketi uygulamamak.

### 3.7 Harita değişimi ve sahiplik

- Varlığın hangi dünya ve haritaya ait olduğunu açıkça belirlemek.
- Harita geçişinde varlığın taşınması, yeni haritaya yeniden bağlanması veya eski haritadan kaldırılması politikalarını tanımlamak.
- Önceki haritaya ait Spatial kayıtlarının ve sorgu referanslarının temizlenmesini sağlamak.
- Harita değişimi sırasında geçersiz/eskimiş entity referanslarının kullanılmasını engellemek.

## 4. İş paketleri

Teknik mimari plan hazırlanırken aşağıdaki iş paketleri dosya ve API düzeyinde ayrıntılandırılacaktır.

### 9.1 — Mevcut entity, world ve render sözleşmelerinin denetimi
- Laboratuvardaki mevcut entity/position/interaction iskeletini incelemek.
- World identity, map identity, `WorldPosition`, axial koordinat ve Physics gövde sözleşmelerini eşlemek.
- Aşama 7 foot-anchor/Y-sort ve Aşama 8 Spatial API ile uyum noktalarını belirlemek.
- Eksik, çakışan veya yinelenen sorumlulukları raporlamak.

### 9.2 — Entity kimliği ve yaşam döngüsü
- Kimlik, tür ve kayıt sözleşmesini tasarlamak.
- Oluşturma, kayıt, sorgulama ve kaldırma işlemlerini tanımlamak.
- Tekillik, sahiplik ve geçersiz referans davranışlarını belirlemek.

### 9.3 — Position/transform ve harita adresi
- Hareketli ve hücreye sabit varlık konumlarını ayırmak.
- WorldPosition ile türetilmiş HexCoord ilişkisinin kurallarını belirlemek.
- Map/world identity kapsamını tüm varlık sorgularına taşımak.
- Varlık konumunun tek authoritative kaynağını korumak.

### 9.4 — Foot-anchor ve fiziksel gövde bağlama
- Entity transform, görsel anchor ve Physics body arasındaki eşlemeyi kurmak.
- Sprite boyutu, anchor ve collider ölçülerini birbirinden ayırmak.
- Farklı varlık boyutları için test sahneleri hazırlamak.
- Render sıralaması ve kamera dönüşümüyle bütünleşik doğrulama yapmak.

### 9.5 — Etkileşim menzili ve hedef seçimi
- Dünya mesafesi ve hex mesafesi kullanım kurallarını uygulamak.
- Fareyle hedef seçimi ve yakın hedef sorgusunu oluşturmak.
- Birden fazla aday için deterministik hedef seçimini tanımlamak.
- Hedef geçerliliği ve etkileşim menzili kontrollerini test etmek.

### 9.6 — Spatial indeks ve harita yaşam döngüsü entegrasyonu
- NPC/kaynak varlıklarını uygun Spatial indeks adaptörüne bağlamak.
- Hareket, ekleme ve kaldırma sonrasında indeks güncelliğini doğrulamak.
- Harita sınırı ve harita değişimi senaryolarını ele almak.
- Yanlış harita veya kaldırılmış varlık döndürülmesini engellemek.

### 9.7 — Yoldaş ilişki ve komut altyapısı
- NPC'nin oyuncuya yoldaş olarak katılma/ayrılma ilişki modelini kurmak.
- Yoldaş komut durumlarını (FOLLOW, WAIT, RETURN) veri düzeyinde temsil etmek.
- Komutların henüz hareket üretmediğini; yalnızca doğrulanabilir durum/komut geçişleri sağladığını garanti etmek.
- Yoldaş ilişkisinin NPC kimliği, harita sahipliği ve yaşam döngüsüyle tutarlılığını test etmek.

### 9.8 — Oyuncu, NPC ve kaynak prototip sahnesi
- Aynı haritada oyuncu, en az bir NPC ve farklı konumlarda kaynak nesneleri oluşturmak.
- Hareketli ve hücreye sabit varlıkları birlikte göstermek.
- Hedef seçimi, menzil içi/dışı ve yakın hedef sorgularını görünür biçimde sınamak.
- Test sahnesini tekrarlanabilir ve otomatik testlere uygun hale getirmek.

### 9.9 — Doğrulama, raporlama ve aşama kabul hazırlığı
- Unit, integration, regression ve property tabanlı testleri tamamlamak.
- Entity konumu, anchor, collider ve Spatial sorgu sonuçlarını karşılaştırmak.
- Kamera zoom/viewport değişiminden bağımsız etkileşim menzilini doğrulamak.
- Performans ve indeks güncelleme maliyetini ölçmek.
- Kullanıcı manuel görsel kabul kontrol listesini hazırlamak.
- Uygulama/doğrulama raporunu ve kapanış raporu taslağını oluşturmak.

## 5. Beklenen teslimatlar

- Ortak entity kimliği ve yaşam döngüsü prototipi.
- Hareketli ve hücreye sabit varlıklar için açık konum/transform sözleşmesi.
- Entity–World–Physics–Rendering bağlantı modeli.
- Foot-anchor ve fiziksel gövde hizalama doğrulaması.
- Dünya/hex mesafesi kurallarına dayalı etkileşim menzili sistemi.
- Fareyle hedef seçimi ve yakın hedef sorgusu.
- Aşama 8 Spatial indeksine bağlı NPC/kaynak aday sorguları.
- Oyuncu-NPC yoldaş ilişkisi ve FOLLOW/WAIT/RETURN komut durumlarını temsil eden temel veri/yaşam döngüsü altyapısı.
- Oyuncu, NPC ve kaynak içeren; yoldaş ilişki/komut durumlarını da sınayan test sahnesi.
- Otomatik testler, benchmarklar ve regresyon raporu.
- Kullanıcı manuel görsel kabul kontrol listesi.
- Mimari karar ve uygulama/doğrulama belgeleri.

## 6. Kabul koşulları

Aşama 9 ancak aşağıdaki koşulların tamamı sağlandığında teknik kabul için hazır sayılır:

1. Oyuncu, NPC ve kaynaklar ortak entity kimliği ve dünya konumu sözleşmesini kullanır.
2. Hareketli varlıkların sürekli WorldPosition değeri hücre merkezine zorla yuvarlanmaz.
3. Hücreye sabit nesnelerin dünya konumu aynı geometri sözleşmesinden türetilir.
4. World identity ve map identity sorgu sonuçlarında korunur.
5. Görsel sprite merkezi, foot-anchor ve fiziksel collider birbirine karıştırılmaz.
6. Kamera zoom'u, viewport ve pencere boyutu etkileşim menzilini değiştirmez.
7. Dünya mesafesi ve hex mesafesi sorguları tanımlı kurallara göre farklı ve doğru çalışır.
8. Fareyle hedef seçimi ve yakın hedef sorgusu deterministik sonuç üretir.
9. Spatial indeks hareket, ekleme, kaldırma ve harita değişimi sonrasında güncel kalır.
10. Kaldırılmış veya başka haritaya ait varlıklar yanlış sorgu sonucu olarak dönmez.
11. Oyuncu, NPC ve kaynak aynı test sahnesinde birlikte çalışır.
12. NPC oyuncuya yoldaş olarak bağlanabilir; ilişki kurulma/sonlanma ve FOLLOW/WAIT/RETURN komut durumları tutarlı biçimde saklanıp sorgulanabilir.
13. Yoldaş komutları bu aşamada NPC'yi hareket ettirmez; gerçek takip/navigasyon davranışı kapsam dışıdır.
14. Otomatik testler, regresyon kontrolleri ve performans ölçümleri raporlanır.
15. Kullanıcı manuel görsel/işlevsel kabulünü tamamlar.
16. Aşama kapanış raporu hazırlanır ve kullanıcı kabulüyle aşama kapatılır.

## 7. Test ve doğrulama yaklaşımı

Teknik planda kesin komutlar, test dosyaları ve ölçüm eşikleri belirlenecektir. Genel test kapsamı:

- **Kimlik:** Tekillik, türden bağımsızlık, kayıt ve kaldırma.
- **Konum:** WorldPosition ↔ HexCoord tutarlılığı; negatif koordinat ve hücre sınırı durumları.
- **Harita sahipliği:** Aynı koordinatın farklı haritalarda ayrı varlıkları temsil etmesi.
- **Anchor/collider:** Sprite boyutu değişse de zemin anchor ve fizik gövdesinin doğru konumda kalması.
- **Menzil:** Sınırın hemen içi/dışı, tam sınır, farklı dünya ölçekleri ve hex komşulukları.
- **Hedef seçimi:** Fareyle seçim, eşit mesafeli adaylar ve deterministik tie-break.
- **Spatial:** Ekleme, taşıma, kaldırma, indeks güncelleme ve brute-force referansla sonuç karşılaştırması.
- **Harita geçişi:** Eski harita sorgularının yeni harita varlıklarını döndürmemesi.
- **Regresyon:** Kamera/zoom, render sıralaması, hareket ve çarpışma davranışlarının korunması.
- **Performans:** Varlık sayısı ve hareket oranına göre sorgu ve indeks güncelleme maliyetleri.

Bir doğrulama çalıştırılmadıysa başarılı sayılmaz. CI veya benchmark sonucu kullanıcı cihazında görsel kabul yerine geçmez.

## 8. Görsel kabul yaklaşımı

Kullanıcının son aşamada kontrol edebilmesi için sahnede en azından:
- Oyuncu ve birden fazla NPC/kaynak varlığı,
- Farklı sprite boyutları ve görünür foot-anchor debug işaretleri,
- Fiziksel collider debug çizimleri,
- Fareyle seçilen hedefin belirgin işareti,
- Etkileşim menzili içi/dışı göstergesi,
- Yakın hedef sorgusunun sonucunu gösteren debug bilgisi

bulunacaktır.

Bu görsel kabul, mimari davranışın doğrulanmasına yöneliktir. Nihai sanat kalitesi veya çevre dekorasyonu kabulü değildir.

## 9. Kapsam dışı ve sınırlar

Aşağıdakiler Aşama 9 kapsamında uygulanmayacaktır:

- A* / Dijkstra pathfinding ve engelleri dolaşarak hedefe yürüme.
- Click-to-move veya otomatik navigasyon.
- Tam NPC yapay zekâsı, günlük rutin, algı ve karar verme. Bunlar Aşama 10 ve/veya sonraki ayrı planlarda ele alınacaktır.
- Yoldaşların gerçek zamanlı takibi, durup beklemesi, oyuncuya yetişmesi, engelleri aşması, pathfinding ve formasyon hareketi. Aşama 9 yalnızca yoldaş ilişki/veri modeli ve komut durum altyapısını hazırlar.
- Yoldaşların savaş, savunma, saldırı, görev, envanter veya diyalog davranışlarının uygulanması.
- Kaynak toplama, üretim, envantere aktarma veya ekonomi kuralları.
- Savaş, hasar, diyalog veya görev sistemlerinin entegrasyonu.
- Nihai karakter/NPC animasyonları, ses ve sanat paketi.
- Arazi dokuları, ağaç, kaya, çalı, bitki, ışık ve atmosfer gibi dünya görsel zenginleştirmesi.
- Pygame'den Godot'a geçiş.
- `main` veya `demo_eldoria` dallarında değişiklik ya da entegrasyon.

Aşama 9 yalnızca etkileşim için hedef seçimi ve uygunluk/menzil sorgusu sağlar; seçilen hedefe ulaşmak için rota hesaplamaz ve oyun eylemini (toplama, konuşma, saldırı vb.) gerçekleştirmez.

## 10. Riskler ve önleyici yaklaşımlar

| Risk | Olası etki | Önleyici yaklaşım |
|---|---|---|
| Entity konumu için birden fazla authoritative kaynak | Hareket ve render sapması | WorldPosition sahipliğini tek yerde tutmak |
| Sprite merkezi ile foot-anchor karışması | Y-sort ve collider hizası bozulması | Anchor ve body'yi ayrı sözleşmelerle tanımlamak |
| Dünya mesafesi ve hex mesafesinin karıştırılması | Yanlış etkileşim menzili | Etkileşim türüne göre açık ölçüm politikası |
| Kamera zoom'unun menzili etkilemesi | Cihaza/zoom'a göre tutarsız oynanış | Tüm menzil hesaplarını dünya/topoloji uzayında yapmak |
| Spatial indeksin güncel olmaması | Eksik veya eski hedef sonuçları | Güncelleme sırasını ve yaşam döngüsü testlerini tanımlamak |
| Harita kimliğinin sorguda unutulması | Başka haritadaki hedefin seçilmesi | Map identity'yi her sorgunun zorunlu filtresi yapmak |
| Eşit mesafeli hedeflerde belirsizlik | Kararsız hedef seçimi | Deterministik tie-break kuralı |
| Kapsamın NPC AI veya kaynak oynanışına kayması | Aşamanın kontrolsüz büyümesi | Otonom davranış ve navigasyonu sonraki aşamalara ayırmak |
| Yoldaş ilişkisinin NPC kimliği/harita yaşam döngüsünden kopması | Yetim veya yanlış haritaya bağlı yoldaş kayıtları | İlişki yaşam döngüsünü entity ve map lifecycle ile birlikte doğrulamak |
| Komut durumlarının gerçek hareket gibi yorumlanması | Aşama 9 kapsamının belirsizleşmesi | FOLLOW/WAIT/RETURN değerlerini yalnızca komut/durum altyapısı olarak tanımlamak |

## 11. Uygulama yöntemi ve onay kapıları

Aşama 9, önceki aşamalardaki kabul edilmiş çalışma yöntemiyle yürütülecektir:

1. Bu genel plan kullanıcı tarafından incelenir ve onaylanır.
2. Onaydan sonra mevcut kodun ayrıntılı denetimi ve dosya bazlı teknik mimari plan hazırlanır.
3. Teknik mimari plan kullanıcı tarafından ayrıca onaylanır.
4. 9.1–9.9 uygulaması tek bir kontrollü çalışma akışında tamamlanır; alt işler kodlanır, test edilir ve doğrulanır.
5. Otomatik testler, Linux/Windows CI, regresyon ve benchmark sonuçları raporlanır.
6. Kullanıcıya manuel görsel kabul kontrol listesi sunulur.
7. Kullanıcı görsel/işlevsel kabulünü bildirdikten sonra kapanış raporu ve Master Plan güncellemesi yapılır.

Genel ve teknik plan onay kapıları tamamlanmıştır. Uygulama yalnızca onaylanmış teknik plan kapsamında yürütülmüştür; resmî kapanış kullanıcı manuel kabulinden sonra yapılacaktır.

## 12. Uygulama ve sonraki adım

Aşama 9 Genel Planı kullanıcı tarafından onaylanmış, ayrıntılı teknik mimari plan ayrıca onaylandıktan sonra 9.1–9.9 uygulaması tamamlanmıştır.

- Uygulama/doğrulama raporu: [PHASE-09-IMPLEMENTATION-VALIDATION-REPORT.md](../reports/PHASE-09-IMPLEMENTATION-VALIDATION-REPORT.md)
- Manuel kabul listesi: [PHASE-09-MANUAL-ACCEPTANCE-CHECKLIST.md](PHASE-09-MANUAL-ACCEPTANCE-CHECKLIST.md)
- İnteraktif demo: `python scripts/run_phase_09_demo.py`

**Sonraki adım:** Kullanıcının yerel bilgisayarında manuel görsel/işlevsel kabul. Bu kabul bildirildikten sonra Aşama 9 kapanış raporu ve Master Plan kapatma güncellemesi hazırlanacaktır.

---

**Özet karar:** Aşama 9, oyuncu/NPC/kaynak varlıklarının ortak dünya-konum modelini, hedef seçimi/etkileşim menzili sorgularını ve oyuncu-NPC yoldaş ilişkisinin temel veri/komut altyapısını kuracaktır. FOLLOW, WAIT ve RETURN komutları bu aşamada yalnızca durum/ilişki sözleşmesi olarak temsil edilir; gerçek takip hareketi, pathfinding, NPC AI, kaynak toplama oynanışı ve nihai çevre sanatı bu aşamanın kapsamı dışındadır.
