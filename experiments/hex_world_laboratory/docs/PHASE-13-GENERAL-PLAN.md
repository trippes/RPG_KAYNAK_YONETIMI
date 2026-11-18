# Aşama 13 — Genel Prosedürel Grafik ve Çizim Altyapısı

> **Belge türü:** Genel aşama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Ön koşul:** Aşama 12 resmen kapatıldı (18 Kasım 2026)  
> **Durum:** KULLANICI TARAFINDAN ONAYLANDI — 18 KASIM 2026  
> **Uygulama durumu:** Başlamadı

## 1. Amaç ve gerekçe

Aşama 12'de ağaç, kaya ve çalı görselleri Pygame çizim koduyla üretildi. Bu çalışma, çevresel nesnelerin görsel tanımını, anchor/bounds verisini ve fiziksel collider'ını birbirinden ayırmanın mümkün olduğunu kanıtladı. Ancak çizim kodu henüz farklı nesne ailelerinin ortak geometri, renk, şekil bileşeni ve varyasyon kurallarını paylaşabileceği genel bir altyapı değildir.

Aşama 13'ün amacı; Aşama 12'de doğrulanmış görsel kaliteyi ve mimari sınırları koruyarak, yeni çevresel görsellerin her defasında baştan çizilmesini önleyen, yeniden kullanılabilir ve deterministik bir prosedürel grafik altyapısı oluşturmaktır.

Bu aşama bir sanat editörü veya kullanıcı arayüzü geliştirme aşaması değildir. Öncelik, kod tarafından kullanılabilen güvenilir çizim yapı taşları ve bunları kullanan örnek nesne profilleridir.

## 2. Hedefler

1. Çizim işlemlerini tekrar kullanılabilir geometrik yardımcılar ve görsel bileşenler halinde düzenlemek.
2. Çizim koordinatları, yüzey ölçeği, şeffaflık ve çizim sırası için tutarlı bir sözleşme oluşturmak.
3. Renk paleti ve malzeme renk rampalarını doğrulanabilir veri olarak yönetmek.
4. Nesne kimliği ve açık seed üzerinden tekrarlanabilir görsel varyasyon üretmek.
5. Ağaç, kaya ve çalı profillerini ortak altyapıya taşıyarak geriye dönük görsel davranışı korumak.
6. En az iki yeni çevresel görsel profiliyle altyapının farklı şekil ailelerinde yeniden kullanılabildiğini göstermek.
7. Üretilen yüzeyleri mevcut renderer, sprite anchor, Y-sort, culling ve çevresel nesne sözleşmeleriyle uyumlu tutmak.
8. Test, benchmark ve görsel kanıtlarla doğrulanabilir bir temel hazırlamak.

## 3. Kapsam

### 3.1 Dahil olanlar

- **Çizim koordinat ve yüzey sözleşmesi:** Mantıksal çizim ölçüleri, çıktı yüzeyi, ölçekleme/supersampling yaklaşımı, şeffaf yüzeyler ve sınır davranışı.
- **Geometri yardımcıları:** Nokta/vektör dönüşümleri, çokgenler, çizgiler, eğriler veya eğrisel hatlar, elipsler, daireler, sınır kutuları ve ortak şekil üretim fonksiyonları. Kesin API teknik planda belirlenecek.
- **Çizim bileşenleri:** Dal, yaprak kümesi, gövde/kök, kaya yüzeyi/faset, çalı kütlesi, çim ve küçük bitki/çiçek kümeleri gibi farklı profillerde tekrar kullanılabilen parçalar.
- **Palet ve renk rampaları:** RGB doğrulaması, renk rolleri, gölge/orta/ışık tonları ve profil bazlı palet seçimi.
- **Deterministik varyasyon:** Açık seed ve nesne kimliğiyle aynı girdiden aynı görselin üretilmesi; global rastgele durumdan bağımsızlık.
- **Profil tanımları:** Geometri, bileşen, palet ve varyasyon parametrelerini bir araya getiren veri odaklı görsel profil yaklaşımı.
- **Yüzey üretimi ve kayıt:** Üretilen Pygame Surface nesnelerinin mevcut asset/renderer sınırına aktarılması; tekrar üretim yerine güvenli önbelleklemenin değerlendirilmesi.
- **Mevcut çevresel nesnelerin uyarlanması:** Ağaç, kaya ve çalı profillerinin ortak altyapıyı kullanması.
- **Yeni örnek profiller:** En az iki yeni çevresel profil ailesi. Önerilen doğrulama örnekleri çim kümesi ve küçük çiçek/bitki kümesidir; nihai seçim teknik plan denetiminde netleştirilecek.
- **Tanılama ve doğrulama:** Görsel sınırlar, anchor, bileşen yerleşimi ve seed bilgisini gerektiğinde incelemeyi kolaylaştıran geliştirici kanıtları.
- **Performans:** Üretim maliyeti, önbellek davranışı, yüzey belleği ve çizim/başlatma maliyetinin ölçülmesi.

### 3.2 Kapsam dışı

- Content Editor, görsel parametre düzenleme pencereleri ve etkileşimli çizim arayüzü (Aşama 14).
- Kullanıcının fareyle ağaç/bitki çizdiği genel amaçlı editör.
- Harita üretimi, biyom dağılımı, arazi/zemin dokusu üretimi veya dünya oluşturma algoritmaları.
- Sprite animasyonu, rüzgâr, parçacık, hava durumu, ışıklandırma ve atmosfer simülasyonu.
- Ses, savaş, görev, ekonomi, NPC AI veya yoldaş hareket sistemleri.
- Yeni fizik/çarpışma sistemi veya mevcut collider'ların görsel boyuta göre otomatik türetilmesi.
- Ana oyuna entegrasyon, `demo_eldoria` veya `main` dalında değişiklik.
- Godot'a geçiş veya yeni grafik motoru.
- Hazır PNG/JPG/WebP görsellerini prosedürel altyapının yerine koymak.

## 4. Korunacak mimari ilkeler

1. **Görsel ve fiziksel veri ayrıdır.** Visual Bounds, Ground Anchor, Depth Anchor, Canopy Bounds ve Collision Geometry mevcut sözleşmelerine uygun kalır. Çizim bileşeni collider üretme veya değiştirme yetkisi kazanmaz.
2. **Dünya konumu değişmez.** Çizim koordinatları yalnızca yüzey içi yerel koordinatlardır; WorldPoint/WorldPosition yerine kullanılamaz.
3. **Render ve simülasyon ayrıdır.** Prosedürel yüzey üretimi authoritative entity, physics, spatial veya simulation state'ini değiştirmez.
4. **Pygame sınırda kalır.** Geometri/parametre hesapları mümkün olduğunca Pygame'den bağımsız saf Python olarak tasarlanır; Surface üretimi ve pygame.draw çağrıları rendering adaptöründe tutulur.
5. **Deterministik üretim esastır.** Aynı profil, parametreler, palet ve seed aynı sonucu üretmelidir. Global random state değiştirilmemelidir.
6. **Mevcut görsel kabul korunur.** Ağaç gövdesi/yaprak geçişi, kaya silueti/collider hizası, anchor ve Y-sort davranışları gerilememelidir.
7. **Ölçmeden optimize edilmez.** Önbellek ve üretim stratejileri benchmark ile değerlendirilir.
8. **Tek başlatıcı korunur.** Laboratuvar `python -m hex_world_lab` ile açılmaya devam eder.

## 5. Önerilen iş paketleri

### 13.1 — Mevcut prosedürel çizim altyapısının denetimi

**Amaç:** Aşama 12 kodunu ve testlerini inceleyerek tekrar eden işlemleri, sabitlenmiş görsel davranışları ve ayrıştırılması gereken sorumlulukları belirlemek.

İşler:
- Ağaç/kaya/çalı çizicilerini, EnvironmentArtPalette ve asset kayıt akışını incelemek.
- Surface boyutları, supersampling, çizim koordinatları, renk doğrulaması ve anchor ilişkilerini belgelemek.
- Mevcut testlerin koruduğu görsel ve veri sözleşmelerini listelemek.
- Pygame API davranışlarını güncel Context7 belgeleriyle doğrulamak.
- Yeniden kullanılabilir olması gereken bileşenleri ve profil özelinde kalması gereken çizimleri ayırmak.

**Çıktılar:** Denetim notu, mevcut sözleşme listesi, tekrar kullanım adayları ve riskler.

**Kabul koşulları:** Aşama 12 kodu ve testleri anlaşılmış; mevcut davranışın hangi testlerle korunduğu açıkça gösterilmiş olmalıdır.

### 13.2 — Ortak çizim ve koordinat sözleşmesi

**Amaç:** Bütün çizicilerin aynı yüzey/koordinat kurallarıyla çalışmasını sağlamak.

İşler:
- Mantıksal ölçü ile çıktı piksel ölçüsünün ilişkisini tanımlamak.
- Ölçekleme ve supersampling sorumluluğunu tekleştirmek.
- Şeffaf yüzey, alpha kanalı, clipping ve çizim sınırlarını tanımlamak.
- Yerel koordinatların nesne anchor'ına göre nasıl yorumlanacağını belirlemek.
- Çizim yardımcılarının dönüş değerlerini ve hata davranışlarını belirlemek.

**Çıktılar:** Çizim sözleşmesi ve test edilebilir temel API tasarımı.

**Kabul koşulları:** Farklı profiller aynı koordinat/yüzey sözleşmesini kullanmalı; yüzey boyutu ve anchor hesapları tekrarlanabilir olmalıdır.

### 13.3 — Yeniden kullanılabilir geometri ve şekil yardımcıları

**Amaç:** Profil çizimlerinde tekrarlanan temel şekil ve geometri işlemlerini ortaklaştırmak.

İşler:
- Çokgen, çizgi, elips/daire ve gerekli eğrisel şekil yardımcılarını değerlendirmek.
- Nokta dönüşümü, ölçekleme, döndürme ve yerel yerleşim işlemlerini tanımlamak.
- Sınır kutusu ve çizim alanı hesaplarını tutarlı hale getirmek.
- Geçersiz parametre, sıfır/negatif boyut ve sınır dışı koordinat davranışını test etmek.
- Yardımcıları genel amaçlı dev bir çizim sınıfına dönüştürmeden küçük sorumluluklara ayırmak.

**Çıktılar:** Geometri/şekil yardımcıları ve birim testleri.

**Kabul koşulları:** Yardımcılar saf ve tekrarlanabilir olmalı; Pygame bağımlılığı zorunlu olmayan hesaplarda bulunmamalı; sınır durumları test edilmelidir.

### 13.4 — Palet, renk rolleri ve malzeme rampaları

**Amaç:** Renk yönetimini tekil RGB sabitlerinden tekrar kullanılabilir palet ve renk rolü yaklaşımına taşımak.

İşler:
- Mevcut EnvironmentArtPalette alanlarını ve uyumluluğunu değerlendirmek.
- Gölge, ana ton, ışık, vurgu ve temas gölgesi gibi renk rollerini belirlemek.
- Palet doğrulaması ve eksik/uyumsuz renk davranışını tanımlamak.
- Ağaç, kaya, çalı ve yeni profillerde ortak palet kullanımını göstermek.
- Palet değişiminin geometri, anchor ve collider üzerinde etkisi olmadığını test etmek.

**Çıktılar:** Palet/renk rampası sözleşmesi ve örnek paletler.

**Kabul koşulları:** Paletler doğrulanabilir olmalı; renk değişimi nesne geometrisini veya fiziksel alanı değiştirmemelidir.

### 13.5 — Deterministik varyasyon ve profil parametreleri

**Amaç:** Aynı nesne ailesinde kontrollü görsel çeşitlilik sağlamak ve tekrar üretilebilirliği korumak.

İşler:
- Seed'in hangi girdilerden türetileceğini ve API'ye nasıl verileceğini belirlemek.
- Aynı seed ve aynı parametrelerle aynı çıktıyı doğrulamak.
- Farklı seed'lerin tanımlı parametre aralıklarında görsel farklılık ürettiğini doğrulamak.
- Global random state'in etkilenmediğini test etmek.
- Profil parametrelerini doğrulamak; geçersiz değerleri sessizce kabul etmemek.
- Seed'in nesne kimliği, harita kaydı ve ilerideki içerik kaydıyla ilişkisini teknik planda değerlendirmek.

**Çıktılar:** Deterministik varyasyon sözleşmesi, parametre doğrulama yaklaşımı ve regresyon testleri.

**Kabul koşulları:** Aynı girdi aynı sonucu vermeli; farklı seed'ler kontrollü çeşitlilik üretmeli; global rastgele durum ve simülasyon davranışı etkilenmemelidir.

### 13.6 — Yeniden kullanılabilir görsel bileşenler ve profil uyarlaması

**Amaç:** Ortak altyapının gerçek nesne ailelerinde işe yaradığını kanıtlamak.

İşler:
- Dal, yaprak kütlesi, gövde/kök, kaya yüzeyi/faset, çalı kütlesi, çim ve küçük bitki bileşenlerini değerlendirmek.
- Ağaç, kaya ve çalı profillerini ortak yardımcıları kullanacak şekilde uyarlamak.
- En az iki yeni profil ailesi oluşturmak; önerilen örnekler çim kümesi ve çiçek/bitki kümesidir.
- Bileşenlerin boyut, palet, seed ve yerleşim parametrelerini kontrollü kullanmasını sağlamak.
- Her profil için yüzey boyutu, anchor ve mevcut Environment Object sözleşmesiyle uyumu doğrulamak.

**Çıktılar:** Ortak bileşen kütüphanesi, uyarlanmış üç mevcut profil ve en az iki yeni profil.

**Kabul koşulları:** Yeni profiller ortak altyapıyı gerçekten paylaşmalı; mevcut ağaç/kaya/çalı görünümü ve collider ilişkisi bozulmamalıdır.

### 13.7 — Renderer entegrasyonu, önbellekleme ve tanılama

**Amaç:** Prosedürel üretimi mevcut render/asset akışına güvenli ve ölçülebilir biçimde bağlamak.

İşler:
- Surface üretim ve kayıt sınırını mevcut renderer ile uyumlu hale getirmek.
- Aynı profil/parametre/seed girdisinin tekrar üretimini önlemek için önbellek gerekliliğini ölçmek.
- Önbellek anahtarı, yaşam döngüsü, bellek sınırı ve temizleme davranışını tanımlamak.
- Görsel bounds, anchor ve bileşen yerleşimini incelemeye yarayan geliştirici kanıtını değerlendirmek.
- Y-sort, culling, F3 collider ve F4 anchor/bounds davranışlarının değişmediğini doğrulamak.

**Çıktılar:** Renderer adaptasyonu, gerekçelendirilmiş yüzey üretim/önbellek yaklaşımı ve tanılama kanıtı.

**Kabul koşulları:** Render ve simülasyon state'i ayrılığı korunmalı; önbellek varsa anahtar çakışması/eskimiş veri üretmemeli; bellek maliyeti ölçülmelidir.

### 13.8 — Bütünleşik test, benchmark, CI ve kullanıcı kabulü

**Amaç:** Genel altyapının doğruluğunu, mevcut sistemlerle uyumunu ve görsel kalitesini kanıtlamak.

İşler:
- Geometri, palet, parametre, seed ve yüzey üretimi unit testlerini çalıştırmak.
- Ağaç/kaya/çalı ve yeni profil aileleri için integration/regression testleri çalıştırmak.
- Y-sort, culling, anchor, debug overlay ve collider bağımsızlığını doğrulamak.
- Aynı girdinin deterministik çıktısını ve farklı seed varyasyonlarını test etmek.
- Yüzey üretim süresi, önbellek isabeti/maliyeti ve bellek kullanımını benchmark etmek.
- Linux/Windows GitHub Actions sonuçlarını kontrol etmek.
- Görsel kanıt artifact'leri ve manuel kabul kontrol listesini hazırlamak.
- Bilinen sınırlamaları ve sonraki aşama için önerileri kapanış raporuna yazmak.

**Çıktılar:** Otomatik test sonuçları, Ruff kalite sonucu, Linux/Windows CI, benchmark raporu, görsel kanıtlar, manuel kabul listesi ve kapanış raporu.

**Kabul koşulları:** Kritik testler başarılı olmalı; Ruff sonucu raporlanmalı; CI başarılı olmalı veya istisnalar gerekçelendirilmelidir; kullanıcı görsel/işlevsel kabulü vermeden aşama kapatılmamalıdır.

## 6. Test ve kalite yaklaşımı

Aşama 13'te beş doğrulama ekseni kullanılacaktır:

1. **Unit:** Geometri yardımcıları, renk/palet doğrulaması, parametre şemaları, seed ve yüzey boyutları.
2. **Integration:** Profil → bileşen → Surface → asset kaydı → renderer akışı.
3. **Regression:** Aşama 12 ağaç/kaya/çalı görselleri, anchor, Y-sort, culling, collider ve debug davranışları.
4. **Determinism:** Aynı girdide aynı çıktı; farklı seed'de kontrollü varyasyon; global random state değişmezliği.
5. **Performance/visual:** Üretim süresi, bellek/önbellek maliyeti ve kullanıcı tarafından masaüstünde görsel kontrol.

Pytest laboratuvar testlerinin ana doğrulama aracı olacaktır. Ruff statik kalite denetiminde kullanılacak; gerçek CI yapılandırmasında nasıl çalıştırıldığı ve hata durumunun build'i engelleyip engellemediği teknik planın depo denetiminde doğrulanacaktır. GitHub Actions laboratuvar ve Core Quality iş akışları üzerinden otomatik kanıt sağlayacaktır. Context7, Pygame çizim/yüzey/alpha/transform API kararlarında güncel dokümantasyon kaynağı olarak kullanılacaktır.

Görsel karşılaştırma için piksel düzeyinde snapshot testi kullanılacaksa platformlar arası font/SDL/pixel-format farklılıkları dikkate alınacak; gereksiz kırılgan eşitlik testleri yerine geometrik, boyutsal ve kontrollü görsel toleranslar tercih edilecektir.

## 7. Performans ilkeleri

- Her nesne çizimi her frame yeniden üretilmemelidir; üretim zamanı ile render zamanı ayrılmalıdır.
- Yüzey önbelleği otomatik varsayım değildir; benchmark ile gerekliliği belirlenir.
- Öncelikli ölçümler: profil üretim süresi, yüzey boyutu, önbellek hit/miss, bellek kullanımı ve çok sayıda farklı seed'de üretim maliyetidir.
- 10/100/1.000 çevresel nesne profilleri gibi mevcut benchmark ölçekleri başlangıç noktası olarak değerlendirilebilir; kesin senaryolar teknik planda belirlenir.
- Donanım ve ölçüm ortamı sabitlenmeden mutlak FPS hedefi taahhüt edilmez.

## 8. Riskler ve önlemler

| Risk | Etki | Önlem |
|---|---|---|
| Ortak altyapının aşırı soyutlanması | Basit çizimlerin karmaşıklaşması | Yalnızca birden fazla profilde doğrulanan ortak davranışı soyutlamak |
| Pygame'in çekirdek geometriye yayılması | Test ve bakım zorluğu | Saf geometri ile Surface adaptörünü ayırmak |
| Seed kullanımının global random state'i etkilemesi | Test ve oyun deterministikliğinin bozulması | Yerel RNG/seed sözleşmesi ve regresyon testi |
| Palet değişiminin collider/anchor'ı etkilemesi | Görsel-fizik uyumsuzluğu | Görsel ve fiziksel veriyi bağımsız tutmak |
| Her frame yüzey üretimi | Performans ve bellek baskısı | Üretim/render ayrımı ve ölçümlü önbellek |
| Pixel-perfect testlerin platforma hassas olması | Gereksiz CI kırılmaları | Geometrik/semantik test ve kontrollü görsel tolerans |
| Aşama 14 editör kapsamının erken eklenmesi | Aşama hedefinin dağılması | Editör UI ve etkileşimli düzenlemeyi kapsam dışında tutmak |
| Aşama 12 kabul edilmiş görsellerin gerilemesi | Kullanıcı kabulünün kaybı | Mevcut profiller için regresyon kanıtı ve manuel kontrol |

## 9. Beklenen teslimatlar

1. Mevcut prosedürel çizim altyapısı denetim kaydı.
2. Ortak çizim/yüzey/koordinat sözleşmesi.
3. Geometri ve şekil yardımcıları.
4. Palet ve renk rampası yaklaşımı.
5. Deterministik seed ve profil parametre sözleşmesi.
6. Yeniden kullanılabilir çizim bileşenleri.
7. Ortak altyapıya uyarlanmış ağaç, kaya ve çalı profilleri.
8. En az iki yeni çevresel profil ailesi.
9. Renderer entegrasyonu ve gerekiyorsa önbellekleme.
10. Unit/integration/regression/determinism testleri.
11. Ruff ve GitHub Actions kalite kanıtları.
12. Performans/bellek benchmark raporu.
13. Görsel kanıtlar ve kullanıcı manuel kabul kontrol listesi.
14. Aşama 13 kapanış raporu.

## 10. Genel kabul koşulları

Aşama 13 ancak aşağıdaki koşulların tamamı sağlandığında kapanışa hazır sayılır:

- Ortak çizim ve yüzey sözleşmesi belgelenmiş ve test edilmiş olmalı.
- Geometri yardımcıları profil çizimlerinde tekrar kullanılmalı.
- Palet ve renk rampaları doğrulanmalı.
- Aynı seed/parametre girdisi deterministik sonuç vermeli.
- Global random state değişmemeli.
- Ağaç, kaya ve çalı profilleri mevcut görsel kabulü ve fiziksel ayrımı korumalı.
- En az iki yeni çevresel profil ailesi altyapıyı kullanmalı.
- Renderer, anchor, Y-sort ve culling entegrasyonu doğru çalışmalı.
- Collider yalnızca açık fizik tanımından gelmeli; görsel şekilden otomatik türetilmemeli.
- Önbellek varsa yaşam döngüsü ve bellek davranışı test edilmiş olmalı.
- Pytest, Ruff ve Linux/Windows GitHub Actions sonuçları raporlanmalı.
- Benchmark ve görsel kanıtlar mevcut olmalı.
- Kullanıcı masaüstü görsel/işlevsel kabulünü tamamlamalı.
- Kapanış raporu değişen dosyaları, commit SHA'lerini, test/CI kanıtlarını ve bilinen sınırlamaları içermeli.
- Bütün değişiklikler yalnızca `experiment/hex-world-laboratory` dalında kalmalı.

## 11. Onay kapıları ve çalışma yöntemi

1. **Genel plan onayı:** Kullanıcı bu belgeyi ve kapsam sınırlarını inceler.
2. **Depo denetimi:** Onaydan sonra gerçek dosyalar, testler, CI ve mevcut Ruff yapılandırması yeniden incelenir.
3. **Teknik plan:** Kesin API, modül/sınıf sorumlulukları, veri akışları, dosya değişiklik listesi, test matrisi, benchmark ve manuel kabul adımları hazırlanır.
4. **Teknik plan onayı:** Kullanıcı teknik planı ayrıca onaylar.
5. **Uygulama:** Yalnızca onaylanmış iş paketleri uygulanır.
6. **Ara doğrulama:** Her iş paketi Pytest/Ruff ve ilgili CI kontrolleriyle doğrulanır.
7. **Bütünleşik doğrulama:** 13.8 kapsamında test, benchmark, artifact ve platform CI tamamlanır.
8. **Manuel kabul:** Kullanıcı masaüstünde görselleri, anchor/collider ayrımını ve mevcut laboratuvar davranışını kontrol eder.
9. **Kapanış:** Rapor hazırlanır ve Master Plan güncellenir.

**Bu genel planın hazırlanması uygulama izni değildir.** Genel plan onayından sonra teknik plan hazırlanacak; teknik plan ayrıca onaylanmadan kod değişikliği yapılmayacaktır.

## 12. Dal ve dosya güvenliği

- Planlama ve uygulama yalnızca `experiment/hex-world-laboratory` dalında yürütülür.
- `main` ve `demo_eldoria` dallarına yazılmaz ve merge yapılmaz.
- Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak korunur.
- Her GitHub yazma işleminden önce branch HEAD ve hedef dosya SHA/varlık durumu doğrulanır.
- Yazma işleminde branch açıkça belirtilir; işlem sonrası commit SHA ve korunan dalların HEAD'leri yeniden kontrol edilir.

## 13. Sonraki adım

Kullanıcı bu genel planı onaylarsa sıradaki adım, Aşama 13 teknik mimari planını hazırlamaktır. Teknik plan öncesinde kodlama yapılmayacaktır.
