# Aşama 8 — Mekânsal İndeksleme ve Performans Karşılaştırması
> **Belge türü:** Aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — 8.1–8.8 UYGULAMA VE OTOMATİK DOĞRULAMA TAMAM, GÖRSEL KABUL BEKLENİYOR  
> **Hazırlanma tarihi:** 17 Kasım 2026  
> **Ön koşul:** Aşama 0–7 tamamlandı ve kabul edildi

---

## 1. Amaç

Aşama 8'in amacı, dünya büyüdükçe yakınlık ve çarpışma adaylarını bulma maliyetini kontrol altında tutabilecek mekânsal sorgulama yaklaşımlarını araştırmak ve ölçmektir.

Bu aşamada temel soru şudur:

**Eldoria'nın altıgen dünya modelinde, bir konum veya nesne çevresindeki olası adayları bulmak için hangi yaklaşım yeterince doğru, hızlı, düşük bellek maliyetli ve bakımı kolaydır?**

Bir optimizasyonun yalnızca teorik olarak daha hızlı olması yeterli değildir. Gerçek laboratuvar veri kümelerinde ölçülebilir fayda sağlaması, referans çözümle aynı aday kümesini üretmesi ve güncelleme maliyetinin de hesaba katılması gerekir.

Aşama 8 bir araştırma, prototipleme ve karşılaştırma aşamasıdır. Belirli bir indeksleme yöntemi peşinen seçilmiş değildir.

## 2. Mevcut mimarideki yeri

Master Plan'daki katman ayrımına göre mekânsal sorgulama, `Spatial` katmanının sorumluluğundadır.

Bu katmanın görevi:
- Yakınlık ve aday sorgularını hızlandırmak.
- Sorgu alanıyla ilişkili olabilecek hücreleri veya nesneleri daraltılmış bir aday kümesi olarak döndürmek.
- İndeks verisini güncel tutmak veya gerektiğinde yeniden oluşturmak.
- Referans geometri ve dünya verisiyle tutarlı kalmak.

Bu katman:
- Dünya geometrisinin sahibi değildir.
- Fizik veya çarpışma kararını vermez.
- Hareketli varlıkların authoritative konumunu değiştirmez.
- Kamera, ekran koordinatı veya render verisine bağımlı olmaz.
- Broadphase adaylarını kesin çarpışma sonucu olarak sunmaz.

Mekânsal indeks, mevcut Geometry, World ve Physics sözleşmelerinin üzerine yardımcı bir sorgu katmanı olarak konumlandırılacaktır.

## 3. Araştırılacak yaklaşımlar

### 3.1 Doğrudan hex komşuluk taraması — referans yöntem

Mevcut hex koordinat sistemi ve komşuluk kuralları kullanılarak sorgu merkezinin çevresindeki hücreler doğrudan taranır.

Bu yöntem performans karşılaştırmasının referans noktası olacaktır. Basitliği, doğruluğu ve bakım maliyeti nedeniyle küçük/orta ölçekli sahnelerde yeterli olup olmadığı ölçülecektir.

### 3.2 Hex tabanlı komşu hücre sorgusu

Sorgu yarıçapı ve hex komşuluk ilişkileri kullanılarak aday hücre kümesi oluşturulur. Dünya mesafesi veya hücre mesafesiyle ifade edilen sorguların sınır davranışı netleştirilir.

Bu yaklaşımın hangi sorgu türlerinde uygun olduğu ve fiziksel dünya mesafesi kullanan sorgular için aday kümesini eksiksiz kapsayıp kapsamadığı incelenecektir.

### 3.3 Spatial hash / grid yardımcı indeksi

Sürekli dünya koordinatındaki nesneleri veya hücreleri sabit boyutlu uzamsal bölmelere yerleştiren yardımcı indeks prototipi hazırlanacaktır.

Araştırılacak konular:
- Bölme boyutunun sorgu ve nesne ölçeğine etkisi.
- Bir nesnenin tek bölmede mi, kapladığı tüm bölmelerde mi tutulacağı.
- Bölme sınırlarında aday kaybının önlenmesi.
- Hareketli nesnelerin indeks güncelleme maliyeti.
- Boş bölmeler ve seyrek/düzensiz dağılımlarda bellek davranışı.

### 3.4 Kare alt bölümlere ayırma yaklaşımı

Kare alt bölümlere ayırma, hex dünyanın yerine geçen yeni bir harita geometrisi olarak değil, yalnızca aday bulmayı hızlandırabilecek yardımcı bir indeks olarak değerlendirilecektir.

Bu yaklaşımın hex topolojisiyle nasıl birlikte çalıştığı, aday üretiminde yanlış negatif oluşturup oluşturmadığı ve ek karmaşıklığa değip değmediği ölçülecektir.

## 4. İş paketleri

Çalışma, teknik plan hazırlanırken daha küçük görevlere ayrılmak üzere aşağıdaki iş paketleriyle ele alınacaktır.

### 8.1 — Mevcut sorgu davranışının ve referans çözümün belirlenmesi
- İlgili Geometry, World ve Physics API'lerini incelemek.
- Karşılaştırılacak sorgu türlerini tanımlamak.
- Doğrudan hex komşuluk taramasını doğruluk referansı olarak sabitlemek.
- Referans sonuçların deterministik ve tekrarlanabilir olmasını sağlamak.

### 8.2 — Test veri kümeleri ve ölçüm protokolü
- Küçük, orta, büyük ve çok büyük harita senaryoları hazırlamak.
- Seyrek, dengeli ve yoğun nesne dağılımlarını temsil etmek.
- Durağan ve sık hareket eden nesne senaryoları oluşturmak.
- Her senaryo için sabit tohum, sorgu sayısı, nesne sayısı ve tekrar sayısını kaydetmek.
- Ölçüm ortamını ve benchmark komutlarını belgelemek.

### 8.3 — Hex tabanlı sorgu ölçümleri
- Hex komşuluk taramasını farklı sorgu yarıçaplarında ölçmek.
- Hex hücre mesafesi ve dünya mesafesi temelli sorguları ayırmak.
- Sınır, harita kenarı ve negatif koordinat senaryolarını kapsamak.

### 8.4 — Spatial hash/grid prototipi
- Yardımcı indeksin veri sözleşmesini tasarlamak.
- Ekleme, kaldırma, taşıma ve sorgu işlemlerini prototiplemek.
- Bölme boyutunun doğruluk ve performansa etkisini ölçmek.
- İndeksin yeniden oluşturulması ve tutarlılık kontrolünü ele almak.

### 8.5 — Kare alt bölümleme prototipi
- Kare bölümlerin yalnızca broadphase amacıyla kullanımını araştırmak.
- Hex koordinatları ve dünya koordinatları arasındaki dönüşüm sınırlarını korumak.
- Bölme sınırlarında ve çoklu bölme kaplayan nesnelerde aday eksiksizliğini test etmek.

### 8.6 — Doğruluk ve regresyon karşılaştırması
- Her indeks sorgusunun sonucunu brute-force referans sonuçla karşılaştırmak.
- Aday kümesinde eksik nesne (false negative) oluşmadığını doğrulamak.
- Fazladan adayların (false positive) nihai fizik/geometry kontrolüne bırakıldığını doğrulamak.
- Nesne ekleme, kaldırma ve hareket ettirme sonrasında indeks tutarlılığını sınamak.

### 8.7 — Performans, bellek ve bakım maliyeti karşılaştırması
- Sorgu süresini ve dağılımını ölçmek.
- İndeks güncelleme maliyetini ölçmek.
- Bellek tüketimini veya makul bir bellek maliyeti göstergesini kaydetmek.
- Farklı yoğunluk ve hareket oranlarında sonuçları karşılaştırmak.
- Kod karmaşıklığı, veri tutarlılığı ve hata ayıklama maliyetini değerlendirmek.

### 8.8 — Sonuç ve mimari öneri
- Her yaklaşımın güçlü ve zayıf yönlerini raporlamak.
- Hangi veri/sorgu ölçeğinde hangi yaklaşımın anlamlı olduğunu açıklamak.
- Ölçülebilir fayda yoksa basit referans yöntemi korumak.
- Varsayılan yöntem önerisini ve gerekçesini kullanıcı onayına sunmak.

## 5. Benchmark senaryoları ve ölçütler

Benchmark senaryoları teknik planda kesinleştirilecektir. Aşağıdaki boyutların birlikte ele alınması beklenir:

| Boyut | Karşılaştırılacak durumlar |
|---|---|
| Harita büyüklüğü | Küçük, orta, büyük, çok büyük |
| Nesne yoğunluğu | Seyrek, dengeli, yoğun |
| Hareket yoğunluğu | Durağan, düşük hareket, yüksek hareket |
| Sorgu kapsamı | Dar, orta, geniş yarıçap |
| Dağılım | Düzenli, kümelenmiş, düzensiz |
| İşlem türü | İlk kurulum, sorgu, ekleme, kaldırma, taşıma |

Kaydedilecek temel ölçütler:
- Sorgu başına süre ve toplam sorgu süresi.
- Medyan ve p95 sorgu süresi.
- Aday sayısı ve gerçek eşleşme sayısı.
- İndeks oluşturma ve güncelleme süresi.
- Bellek maliyeti.
- Referans yönteme göre hızlanma/yavaşlama oranı.
- Doğruluk karşılaştırmasında eksik aday sayısı.
- Benchmark tekrarları arasındaki değişkenlik.

Karşılaştırmalar aynı veri kümesi, aynı sorgu dizisi ve aynı çalışma ortamı üzerinde yapılacaktır. Ölçüm sonuçları tek bir ortalama sayıya indirgenmeyecek; dağılım ve tekrar edilebilirlik de raporlanacaktır.

Rastgele FPS, harita büyüklüğü veya donanım başarısı taahhüt edilmeyecektir. Eşikler mevcut laboratuvar ve referans donanım bilgileri incelendikten sonra teknik planda gerekçelendirilerek önerilecektir.

## 6. Doğruluk ve mimari ilkeler

1. **Eksiksiz aday üretimi:** İndeks, sorguyla ilişkili olabilecek geçerli hiçbir adayı atlamamalıdır.
2. **Broadphase sınırı:** İndeks yalnızca aday kümesini daraltır. Nihai çarpışma/temas kararı mevcut Geometry ve Physics katmanlarında kalır.
3. **Tek doğruluk kaynağı:** WorldPosition, hex koordinatları ve geometri sözleşmesi değiştirilmez; indeks bu verilerden türetilir.
4. **Deterministik sonuç:** Aynı dünya durumu ve aynı sorgu, aynı aday kümesini üretmelidir. Sıralama gerekiyorsa açık ve kararlı bir kural tanımlanır.
5. **Güncellik:** Nesne taşındığında, eklendiğinde veya kaldırıldığında indeks eski konuma ait geçersiz kayıt bırakmamalıdır.
6. **İzolasyon:** Spatial katmanı Pygame, kamera ve render sistemlerine bağımlı olmamalıdır.
7. **Ölçüm odaklı seçim:** Karmaşık indeks yalnızca basit yönteme göre ölçülebilir fayda sağladığında varsayılan hâle getirilir.
8. **Geri dönüş imkânı:** Referans sorgu yöntemi test ve karşılaştırma amacıyla korunur.

## 7. Test yaklaşımı

Teknik planda ayrıntılandırılmak üzere test kapsamı:

- Birim testleri: hücre/bölme eşlemesi, sorgu alanı, ekleme, kaldırma, taşıma.
- Doğruluk testleri: indeks sonucu ile brute-force referansın eşitliği/aday kapsaması.
- Sınır testleri: bölme sınırları, hex kenarları, harita sınırları, negatif ve büyük koordinatlar.
- Hareket testleri: bir bölmeden diğerine geçiş, hızlı ardışık hareket, aynı tick içinde birden fazla güncelleme.
- Tutarlılık testleri: yinelenen kayıt, stale kayıt, boş bölme, yeniden oluşturma.
- Entegrasyon testleri: World ve Physics sorgu sözleşmeleriyle uyum.
- Benchmark testleri: sabit veri, sabit sorgu dizisi ve tekrarlanabilir ölçüm.
- Regresyon testleri: Aşama 0–7 davranışlarının korunması.

Benchmark başarısı doğruluk testlerinin yerine geçmez. Performans raporuna yalnızca doğruluk kapısını geçen prototipler alınır.

## 8. Beklenen çıktılar

- Hex tabanlı referans sorgu ve ölçüm sonuçları.
- Spatial hash/grid yardımcı indeks prototipi ve ölçüm sonuçları.
- Kare alt bölümleme yaklaşımının karşılaştırma sonuçları.
- Tekrarlanabilir benchmark senaryoları ve çalıştırma yönergeleri.
- Brute-force karşılaştırmasına dayalı doğruluk testleri.
- Sorgu, güncelleme ve bellek maliyetlerini içeren karşılaştırma raporu.
- Seçilen yönteme ilişkin gerekçeli mimari öneri.
- Gerekliyse Spatial katmanına ilişkin ADR önerisi.
- Aşama sonunda kapanış raporu.

## 9. Kabul koşulları

Aşama 8 ancak aşağıdaki koşulların tamamı sağlandığında tamamlanmış sayılır:

- [ ] Referans hex sorgu yöntemi tanımlanmış ve test edilmiştir.
- [ ] En az iki indeksleme yaklaşımı karşılaştırılabilir prototip/ölçüm düzeyine getirilmiştir.
- [ ] Test senaryoları harita büyüklüğü, nesne yoğunluğu ve hareket yoğunluğunu kapsamaktadır.
- [ ] İndeks sorguları brute-force referansla doğruluk açısından karşılaştırılmıştır.
- [ ] Hiçbir geçerli adayın atlanmadığı testlerle gösterilmiştir.
- [ ] Broadphase ile nihai geometry/physics kararı arasındaki sınır korunmuştur.
- [ ] Sorgu süresi, güncelleme maliyeti ve bellek etkisi raporlanmıştır.
- [ ] Benchmark sonuçları aynı koşullarda tekrarlanabilir durumdadır.
- [ ] Optimizasyonun faydası ölçümlerle gösterilmiş veya basit yöntemin yeterli olduğu kanıtlanmıştır.
- [ ] Mimari öneri, ödünleşimler ve açık riskler belgelenmiştir.
- [ ] Otomatik testler ve Linux/Windows kalite kontrolleri başarılıdır.
- [ ] Kullanıcı tarafından gerekli görülen manuel/entegrasyon kontrolleri tamamlanmıştır.
- [ ] Kapanış raporu hazırlanmış ve kullanıcı kabulü alınmıştır.

## 10. Kapsam dışı

Aşağıdaki konular Aşama 8'e dahil değildir:

- A* veya başka bir pathfinding algoritması.
- Tıklanan hedefe karakter yürütme, rota oluşturma veya engel etrafından dolaştırma.
- NPC karar verme ve davranış sistemi.
- Entity mimarisinin bütünüyle kurulması.
- Etkileşim menzili ve hedef seçme sisteminin tamamlanması.
- Simülasyon orkestrasyonu veya dünya yaşam döngüsünün yeniden tasarlanması.
- Terrain dokuları, ağaç, kaya, bitki, ışık, atmosfer ve çevresel sanat zenginleştirmesi.
- Ana oyuna entegrasyon veya `demo_eldoria` dalına aktarım.

Bu konular Master Plan'daki kendi aşamalarında veya ayrıca onaylanmış kapsamda ele alınacaktır. Aşama 8 sırasında ihtiyaç olarak görünmeleri, kendiliğinden bu aşamaya dahil edildikleri anlamına gelmez.

## 11. Riskler ve önlemler

| Risk | Önlem |
|---|---|
| İndeksin geçerli adayı atlaması | Brute-force referansla karşılaştırma ve sınır testleri |
| Hareket sonrası eski indeks kaydı kalması | Taşıma/ekleme/kaldırma tutarlılık testleri |
| Küçük haritalarda indeksin daha yavaş olması | Basit yöntemi referans ve olası varsayılan olarak korumak |
| Bölme boyutunun tek senaryoya göre seçilmesi | Farklı yoğunluk ve sorgu yarıçaplarını ölçmek |
| Benchmark gürültüsü | Sabit veri, tekrar, medyan/p95 ve ortam kaydı |
| Bellek maliyetinin göz ardı edilmesi | Sorgu hızının yanında bellek ve güncelleme maliyetini raporlamak |
| Spatial katmanın fizik kararlarını üstlenmesi | Broadphase/narrowphase sınırını sözleşmede korumak |
| Erken optimizasyon ve gereksiz soyutlama | Ölçülebilir fayda yoksa basit yöntemi seçmek |

## 12. Çalışma sırası ve onay kapıları

Aşama 8 aşağıdaki sırayla yürütülecektir:

1. Bu genel plan kullanıcı tarafından incelenir ve onaylanır.
2. Mevcut kod ve testler yeniden, dosya bazında incelenir.
3. Ayrıntılı teknik mimari planı hazırlanır: API sözleşmeleri, veri yapıları, modül/dosya değişiklikleri, benchmark protokolü, test matrisi ve riskler.
4. Teknik plan kullanıcı onayına sunulur.
5. Yalnızca onaylanan kapsamda uygulama ve testler yapılır.
6. Benchmark ve doğruluk kanıtları toplanır.
7. Sonuç raporu ve kapanış raporu hazırlanır.
8. Kullanıcı kabulüyle aşama kapatılır.

**Bu belge tek başına uygulama izni değildir.** Genel planın onaylanması, ayrıntılı teknik planın hazırlanmasına geçiş iznidir; kod değişiklikleri teknik plan ve kapsam onayından sonra başlar.

## 13. Sonraki aşamayla ilişki

Master Plan sırasına göre Aşama 8'den sonra Aşama 9 — Varlıklar ve etkileşimler gelir. Aşama 8'de oluşturulacak Spatial sorgu sözleşmesi, ileride oyuncu, NPC ve kaynakların yakınlık/aday sorgularında kullanılabilecek şekilde tasarlanacaktır. Ancak Aşama 9'un entity ve interaction sistemleri bu aşamada uygulanmayacaktır.

---

**Plan durumu:** Kullanıcı onayı bekleniyor.  
**Uygulama durumu:** Başlatılmadı.
