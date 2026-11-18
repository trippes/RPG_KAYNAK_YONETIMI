# Aşama 12 — Çevresel Nesne Mimarisi ve Dünya Görsel Zenginleştirmesi

> **Belge türü:** Aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Hedef:** Görselden bağımsız, genişletilebilir çevresel nesne altyapısı oluşturmak  
> **Durum:** RESMEN KAPATILDI — PROSEDÜREL UYGULAMA VE KULLANICI KABULÜ BAŞARILI  
> **Ön koşul:** Aşama 11 tamamlandı ve kullanıcı tarafından kabul edildi  
  > **Uygulama durumu:** Prosedürel çizim ve son collider hizalama düzeltmeleri tamamlandı; 800 laboratuvar testi, Linux/Windows Core Quality, benchmark, görsel artifact ve kullanıcı masaüstü kabulü başarılı.

## 18 Kasım 2026 kapsam revizyonu — bağlayıcı karar

Aşama 12, çevresel nesne mimarisini ve bu mimariyi doğrulayan yalnızca üç kod çizimi prototipini (ağaç, kaya, çalı) kapsar. Hazır PNG/JPG/WebP dosyaları bu prototiplerin görsel kaynağı olarak kullanılmayacaktır; yüzeyler Pygame çizim primitifleri ve deterministik geometriyle koddan üretilecektir.

Aşama 12 içinde çizim fonksiyonları, paletler, geometri ve nesne profilleri ayrık/parametrelenebilir tutulur. Ağaçta kök-gövde, dallar, farklı tonlarda yaprak kümeleri, hacim, ışık ve gölge; kayada çok yüzeyli hacim ve ışık-gölge; çalıda kümelenmiş yapraklar ve alt gölge bulunur. Üç nesne aynı sanat yönü ve harita ölçeği kalitesini hedefler. Ground Anchor, Depth Anchor, Visual Bounds, Canopy Bounds ve Collision Geometry çizimden bağımsız kalır. Çizim collider üretmez. Aynı parametreler deterministik sonuç verir.

Aşama 12 dışında: genel amaçlı grafik motoru, serbest biçimli çizim arayüzü, fareyle dal/yaprak düzenleme, içerik kütüphanesi, dosya içe/dışa aktarma aracı, bina/karakter/NPC çizim paketi, animasyon/rig/wind sistemi ve ana oyun entegrasyonu.

Aşama 13, farklı içerik türlerini destekleyen genel prosedürel grafik/çizim altyapısıdır. Aşama 14, bu altyapıyı kullanan Content Editor ve görsel düzenleme araçlarıdır. İki aşama da ayrıca planlanıp onaylanacaktır.

Önceki doğrulama raporundaki tree_test.png kopyası yeni karar kapsamında kabul edilmez; PNG tabanlı sunum geçici/ret edilmiş prototiptir. Önceki test/CI sonuçları yalnızca o commit'teki teknik kod için geçerlidir; prosedürel görsel kabul kanıtı değildir. Aşama 12'nin görsel uygulaması, testleri, benchmarkı, CI ve manuel kabulü yeniden tamamlanmalıdır.

---

## 1. Belgenin amacı

Bu belge, Eldoria Hex World Laboratory kapsamında Aşama 12'nin hedeflerini, kapsamını, iş paketlerini, beklenen teslimatlarını, kabul koşullarını ve çalışma sınırlarını tanımlar.

Aşama 12'nin amacı, altıgen dünya üzerinde ağaç, kaya, çalı ve benzeri çevresel nesnelerin tutarlı biçimde temsil edilmesini sağlayacak bir mimari kurmaktır. Bu mimari, çevresel nesnelerin yalnızca birer görsel dosyadan ibaret olmasını önlemeli; görsel sunum, dünya konumu, derinlik sıralaması ve fiziksel etkileşim sorumluluklarını birbirinden ayırmalıdır.

İlk somut prototip ağaç olacaktır. Ağaç prototipi, farklı çevresel nesne türlerinin aynı temel mimariyi kullanıp kullanamayacağını değerlendirmek için referans örnek görevi görecektir.

Bu belge bir **genel plan** niteliğindedir. Dosya/sınıf düzeyindeki teknik tasarım, mevcut kodla eşleştirme, değişiklik listesi, test ayrıntıları ve manuel kabul adımları sonraki teknik mimari planında hazırlanacaktır. Bu belgenin yazılması tek başına uygulama izni vermez.

## 2. Mevcut durum ve gerekçe

Aşama 0–11 boyunca laboratuvarda hex geometri, dünya modeli, sürekli hareket, fizik/çarpışma, kamera, render, spatial index, entity altyapısı, simülasyon orkestrasyonu ve sağlamlık doğrulaması tamamlanmıştır.

Aşama 11, 18 Kasım 2026 tarihinde otomatik doğrulama ve kullanıcı manuel kabul kapılarının tamamlanmasıyla kapatılmıştır. Bu nedenle Aşama 12, doğrulanmış dünya altyapısının üzerinde yeni bir görsel dünya katmanı geliştirmeye odaklanabilir.

Dünya görsel zenginleştirmesi (arazi dokuları, bitki örtüsü, ağaç/kaya/çevre varlıkları, ışık ve atmosfer) daha önceki render aşamalarının geriye dönük eksik işi olarak ele alınmayacaktır. Bu çalışma, ayrı ve kontrollü bir kapsam olarak başlatılmaktadır.

Aşama 12'nin temel gerekçeleri:

1. Çevresel nesnelerin görsel boyutları ile fiziksel etki alanları çoğu zaman aynı değildir.
2. Bir nesnenin ekranda kapladığı alan, zemine bastığı nokta ve derinlik sıralamasında kullanılacak nokta farklı kavramlardır.
3. Görsel dosyanın değiştirilmesi, nesnenin çarpışma ve dünya yerleşimi kurallarını değiştirmemelidir.
4. Aynı temel nesne altyapısı farklı çevresel nesne türleri tarafından tekrar kullanılabilmelidir.
5. Yoğun sahnelerde çizim sıralaması, kamera dönüşümü, mekânsal sorgular ve çarpışma davranışı birlikte tutarlı kalmalıdır.

## 3. Ana hedef ve tasarım ilkesi

### 3.1 Ana hedef

Görsel sunumu, geometrik referansları ve dünya bağlantısı ayrı sorumluluklar olarak ele alan; ilk olarak ağaç prototipiyle doğrulanan, sonrasında farklı çevresel nesne türlerine genişletilebilen bir çevresel nesne mimarisi oluşturmak.

### 3.2 Temel tasarım ilkesi

**Bir çevresel nesnenin görsel dosyası değiştirildiğinde, nesnenin dünya yerleşimi, çarpışma geometrisi ve derinlik sıralaması yeniden yazılmak zorunda kalmamalıdır.**

Bu ilke, görsel varlık ile nesnenin dünyadaki davranışını birbirinden ayıran tasarımın temel kabul ölçütüdür.

### 3.3 Nesne sorumluluklarının ayrılması

Genel yaklaşımda çevresel nesne üç ana sorumluluk alanıyla ele alınacaktır:

- **Görsel sunum:** Sprite/görsel varlık, görsel boyutlar ve çizim sunumu.
- **Nesne geometrisi:** Zemin bağlantısı, derinlik referansı, fiziksel çarpışma alanı ve gerektiğinde görsel sınırlar.
- **Dünya bağlantısı:** Dünya konumu, harita kimliği ve mevcut dünya/entity altyapısıyla ilişki.

Bu ayrımın kesin sınıf ve veri yapıları teknik plan sırasında mevcut mimariye göre belirlenecektir. Genel plandaki kavramlar, peşinen belirlenmiş sınıf veya dosya isimleri değildir.

## 4. Kapsam

### 4.1 Kapsama dahil işler

- Mevcut render, Y-sort, foot-anchor ve collider altyapısının incelenmesi.
- Mevcut çevresel nesne prototiplerinin ve çizim/render altyapısının denetlenmesi; hazır raster görsellerin runtime kaynağı olarak kullanılmaması.
- Görselden bağımsız çevresel nesne geometrisi için ortak sözleşme tasarlanması.
- Ağaç nesnesinin ilk referans prototip olarak Pygame çizim primitifleriyle koddan üretilmesi.
- Kaya ve çalı görsellerinin aynı deterministik prosedürel çizim yaklaşımıyla oluşturulması.
- Çizim fonksiyonlarının renk paleti ve nesne profili parametreleriyle UI'dan bağımsız tutulması.
- Ground Anchor ve Depth Anchor kavramlarının uygulanması.
- Görsel sınırlar ile fiziksel çarpışma geometrisinin ayrılması.
- Ağaç gövdesi ve taç görsel alanı gibi farklı geometrik bölgelerin ele alınması.
- Mevcut entity, spatial ve fizik altyapısıyla gerekli entegrasyonun yapılması.
- Birden fazla nesne türünün ortak mimariye uyumunun sınanması.
- Geliştirici/debug görünümünde nesne referanslarının gösterilmesi.
- Otomatik regresyon, bütünleşik, performans ve görsel doğrulama.
- Teknik kararların, sınırlamaların ve sonuçların belgelenmesi.

### 4.2 Kapsam dışı işler

Aşağıdaki konular Aşama 12'ye kendiliğinden dahil değildir:

- NPC yapay zekâsı veya otonom NPC hareketi.
- Yoldaşların gerçek takip hareketi ve navigasyonu.
- A*, Dijkstra, pathfinding veya click-to-move.
- Kaynak toplama, kesme, madencilik, üretim veya ekonomi.
- Savaş, görev, diyalog veya ilerleme sistemleri.
- Tam dünya editörü veya genel amaçlı içerik üretim aracı.
- Nihai sanat üretim hattı, kapsamlı animasyon ve ses sistemi.
- Dinamik ışıklandırma, hava durumu ve atmosfer sistemi.
- Godot'a geçiş.
- Ana oyuna veya `demo_eldoria` dalına entegrasyon.
- `main` veya `demo_eldoria` dallarında değişiklik.
- Ölçüm veya doğrulama olmadan büyük mimari refaktör.

Bu başlıklardan biri gerekli görünürse önce gerekçesi ve etkisi raporlanır; ayrı kullanıcı onayı olmadan kapsam genişletilmez.

## 5. Çevresel nesne modelinin kavramsal bileşenleri

Aşağıdaki bileşenler hedeflenen sorumlulukları açıklar. Bunların mevcut kodda hangi modül veya veri yapılarıyla temsil edileceği Aşama 12 teknik planında belirlenecektir.

### 5.1 Görsel katman

Görsel katman, nesnenin ekranda nasıl görüneceğini tanımlar. Aşama 12'de ağaç, kaya ve çalı hazır raster dosyası yüklenerek değil, Pygame Surface üzerine kodla çizilerek üretilecektir.

Ele alınacak kavramlar:

- Prosedürel çizim profili ve parametrelenebilir renk paleti.
- Görsel genişlik/yükseklik ve çizim alanı.
- Görsel ofseti ve ölçekleme politikası.
- Şeffaf alanların görsel sınır hesabına etkisi.
- Çizim paleti veya profilinin değiştirilmesi halinde geometrik tanımın korunması.

Görsel katman, kendi başına çarpışma kararı vermemeli ve dünya simülasyonunun authoritative konumunu değiştirmemelidir.

### 5.2 Ground Anchor — zemin bağlantı noktası

Ground Anchor, nesnenin dünya zeminine temas ettiği veya yerleşim açısından referans kabul edilen noktadır.

Ağaç için bu nokta genellikle gövdenin zemine girdiği taban bölgesidir. Büyük görselin merkezinin veya alt sınırının otomatik olarak zemin noktası kabul edilmesi doğru sonuç vermeyebilir.

Ground Anchor:

- Nesnenin dünya konumuyla tutarlı olmalı.
- Görsel boyutu değiştiğinde kendiliğinden kaymamalı.
- Harita/hücre yerleşimi ve dünya koordinatıyla ilişkilendirilebilmeli.
- Debug görünümünde açıkça işaretlenebilmeli.

### 5.3 Depth Anchor — derinlik sıralama referansı

Depth Anchor, nesnenin çizim sıralamasında kullanılacak dünya referansını tanımlar.

İlk yaklaşımda Ground Anchor ile aynı konumda olabilir; ancak mimari bu iki kavramın zorunlu olarak aynı olmasını gerektirmemelidir. İleride farklı geometrik yapıya sahip nesnelerde ayrı derinlik referansı gerekebilir.

Depth Anchor:

- Mevcut Y-sort/render sıralama sözleşmesiyle uyumlu olmalı.
- Sprite yüksekliği veya görsel dosyanın piksel boyutuna göre rastgele belirlenmemeli.
- Kamera pan/zoom işlemlerinden etkilenerek dünya konumu değiştirmemeli.
- Karakter ve çevresel nesnelerin ön/arka örtüşmesini tutarlı hale getirmeli.

### 5.4 Collision Geometry — fiziksel çarpışma geometrisi

Collision Geometry, nesnenin hareketi fiziksel olarak engelleyen bölümünü tanımlar.

Ağaç örneğinde dallar ve yapraklar geniş bir görsel alan kaplarken fiziksel engel esas olarak gövde çevresinde bulunabilir.

Bu nedenle:

- Görsel alanın tamamı otomatik olarak collider kabul edilmemeli.
- Çarpışma alanı görsel dosyadan bağımsız tanımlanabilmeli.
- Mevcut fizik ve broadphase/narrowphase sorumlulukları korunmalı.
- Collision Geometry, nesnenin dünya konumuyla tutarlı olmalı.
- Çarpışma verisi ile render verisi birbirinin yerine kullanılmamalı.

Çarpışma şeklinin (daire, polygon veya mevcut fizik altyapısına uygun başka bir temsil) seçimi teknik inceleme ve test sonucunda yapılacaktır.

### 5.5 Visual Bounds ve Canopy Bounds

**Visual Bounds**, nesnenin çizim için kapladığı görsel alanı ifade eder. Bu alan, tek başına fiziksel engel veya etkileşim alanı değildir.

**Canopy Bounds**, ağaç gibi üst bölümü geniş nesnelerde taç/yaprak alanını ayrıca temsil etmek için kullanılabilecek kavramsal bir sınırdır. Her çevresel nesne için zorunlu değildir.

Bu sınırlar gerektiğinde çizim optimizasyonu, debug gösterimi veya görsel analiz için kullanılabilir. Aşama 12'de yeni bir culling sistemi geliştirmek hedeflenmemektedir; mevcut culling altyapısının gereksiz yere değiştirilmesinden kaçınılacaktır.

### 5.6 World Placement — dünya yerleşimi

Dünya yerleşimi, nesnenin hangi dünyada/haritada ve hangi dünya koordinatında bulunduğunu tanımlar.

- Mevcut WorldPoint, EntityLocation, EntityRegistry ve dünya yaşam döngüsü sözleşmeleri incelenecek.
- Çevresel nesne için yeni bir konum standardı oluşturulmayacak.
- Hücre ilişkisi gerekiyorsa mevcut hex dünya dönüşümleri kullanılacak.
- Görsel konum ile authoritative dünya konumu ayrıştırılacak.
- Nesne oluşturma, taşıma, kaldırma ve harita yaşam döngüsü davranışları mevcut sistemlerle tutarlı olacak.

## 6. İş paketleri

### 12.1 — Mevcut görsel ve nesne altyapısının denetimi

**Amaç:** Yeni tasarım öncesinde laboratuvarda zaten bulunan sistemleri ve yeniden kullanılabilecek parçaları belirlemek.

İşler:

- Render ve Y-sort uygulamasını incelemek.
- Sprite foot-anchor ve çizim ofseti sözleşmesini incelemek.
- Entity, EntityRegistry, EntityWorldCoordinator ve Spatial Index bağlantılarını incelemek.
- Collider ve fizik geometrisinin mevcut kullanımını incelemek.
- Asset yükleme, görsel referansları ve mevcut çevresel nesne örneklerini incelemek.
- Ağaç iskeleti veya çevresel nesne prototipi olarak daha önce hazırlanmış dosyaları araştırmak.
- Mevcut dosyaların ve görsel varlıkların envanterini çıkarmak.
- Yeniden kullanılabilecek altyapıyı, eksik noktaları ve riskleri raporlamak.

**Çıktılar:**

- Mevcut mimari envanteri.
- İlgili dosya/modül listesi.
- Yeniden kullanılabilir bileşenler ve eksik sorumluluklar listesi.
- Teknik tasarım için açık sorular ve risk kaydı.

**Kabul koşulları:**

- İlgili render, entity, spatial, fizik ve asset alanları incelenmiş olmalı.
- Yeni mimari önerisi gerçek depo yapısına dayanmalı.
- Mevcut çalışan davranışları gereksiz yere yeniden yazma önerisi bulunmamalı.
- Henüz kod değişikliği yapılmadan teknik tasarıma temel oluşturacak bulgular belgelenmeli.

### 12.2 — Ortak çevresel nesne iskeleti

**Amaç:** Görsel dosyadan bağımsız, farklı nesne türlerine uyarlanabilir ortak geometrik ve yerleşim sözleşmesini oluşturmak.

İşler:

- Çevresel nesne kimliği ve türü ihtiyacını değerlendirmek.
- World Placement ile görsel sunum arasındaki bağı tanımlamak.
- Ground Anchor ve Depth Anchor verilerini temsil etmek.
- Collision Geometry'nin opsiyonel ve bağımsız olmasını sağlamak.
- Visual Bounds ve gerektiğinde Canopy Bounds kavramlarını değerlendirmek.
- Nesne türlerinin her geometrik alanı kullanmak zorunda olmadığı esnek bir yapı tasarlamak.
- Mevcut Entity/Spatial altyapısıyla ilişkiyi belirlemek.
- Geçersiz veya eksik geometri tanımlarının nasıl ele alınacağını tanımlamak.

**Çıktılar:**

- Ortak çevresel nesne sözleşmesi.
- Geometrik referansların veri modeli.
- Mimari karar kaydı veya teknik tasarım belgesi.
- Birim ve bütünleşik testlerin taslak kapsamı.

**Kabul koşulları:**

- Görsel sunum ile fiziksel geometri birbirinden ayrılmış olmalı.
- Ground Anchor ve Depth Anchor açıkça temsil edilmeli.
- Collider bulunmayan nesneler desteklenebilmeli.
- Ortak model yalnızca ağaç varsayımlarına kilitlenmemeli.
- Mevcut dünya ve koordinat sözleşmeleri korunmalı.

### 12.3 — Ağaç referans prototipi

**Amaç:** Ortak çevresel nesne mimarisini ilk somut nesne türüyle doğrulamak.

İşler:

- Ağaç çizim profilini ve palet parametrelerini belirlemek.
- Gövde, kök, dal ve yaprak kümelerini yüksek çözünürlüklü şeffaf Surface üzerine kodla çizmek.
- Prosedürel yüzeyi ortak nesne iskeletine bağlamak.
- Ground Anchor konumunu belirlemek.
- Depth Anchor konumunu belirlemek.
- Gövde için uygun Collision Geometry tanımlamak.
- Visual Bounds ve Canopy Bounds kullanımını değerlendirmek.
- Ağaç dünya konumunu mevcut hex/world/entity sözleşmesiyle ilişkilendirmek.
- Palet/çizim parametreleri değiştiğinde geometrik referansların ve collider'ın korunmasını test etmek.

**Çıktılar:**

- Gövde, kök, dal, yaprak kütleleri, ışık ve gölge katmanları kodla çizilmiş çalışan ağaç prototipi.
- Ağaç için geometrik referans tanımı.
- Görsel/çarpışma ayrımını gösteren örnek sahne.
- Otomatik prototip testleri.

**Kabul koşulları:**

- Ağaç görseli dünya üzerinde doğru zemin noktasına oturmalı.
- Gövde collider'ı görsel taç alanının tamamını kaplamamalı.
- Görsel boyut değişikliği dünya konumunu veya çarpışma tanımını kendiliğinden bozmamalı.
- Ağaç mevcut kamera ve render sistemiyle doğru çizilmeli.
- Karakterin ağacın önünden ve arkasından geçişi doğru görsel sonucu vermeli.

### 12.4 — Derinlik ve çizim sıralaması bütünleşmesi

**Amaç:** Çevresel nesnelerin karakter ve diğer dünya varlıklarıyla doğru ön/arka örtüşmesini sağlamak.

İşler:

- Mevcut Y-sort algoritmasının ve sıralama anahtarının incelenmesi.
- Depth Anchor'ın render sıralamasına bağlanması.
- Ground Anchor ile Depth Anchor'ın aynı veya farklı olduğu senaryoları değerlendirmek.
- Ağaç arkasında kalan karakter ve ağaç önünde kalan karakter senaryolarını test etmek.
- Aynı derinlikte veya birbirine çok yakın referans noktalarında deterministik sıralamayı doğrulamak.
- Kamera pan, zoom ve viewport değişiminde sıralama kararlılığını kontrol etmek.
- Mevcut entity çizim sıralamasında regresyon oluşmadığını doğrulamak.

**Çıktılar:**

- Çevresel nesneler için Y-sort entegrasyonu.
- Örtüşme test senaryoları.
- Görsel regresyon kanıtları.

**Kabul koşulları:**

- Karakter ağaç arkasındayken ağaç doğru biçimde önde görünmeli.
- Karakter ağaç önündeyken karakterin gövdeyle örtüşmesi doğru olmalı.
- Görsel yüksekliği veya dosya boyutu sıralama kararını yanlış yönlendirmemeli.
- Aynı koşullarda sıralama sonucu deterministik olmalı.
- Mevcut oyuncu/entity render davranışı bozulmamalı.

### 12.5 — Çarpışma ve etkileşim geometrisi

**Amaç:** Çevresel nesnenin görsel alanı ile fiziksel engel alanını birbirinden ayırarak mevcut fizik ve mekânsal sistemlere bağlamak.

İşler:

- Ağaç gövdesi çarpışma geometrisini mevcut fizik sistemine bağlamak.
- Görsel taç alanının fiziksel engel oluşturmamasını doğrulamak.
- Collision Geometry'nin world placement ile tutarlı kalmasını sağlamak.
- Spatial broadphase ve fizik narrowphase sınırlarını korumak.
- Birden fazla yakın ağaç ve bitişik engel senaryolarını sınamak.
- Harita sınırları ve negatif koordinatlarda yerleşim/çarpışma davranışını kontrol etmek.
- Nesne oluşturma, kaldırma ve harita yaşam döngüsünde collider/spatial kayıtlarının tutarlılığını doğrulamak.
- Etkileşim alanı gerekirse fiziksel collider'dan ayrı bir kavram olarak ele almak; ancak etkileşim oynanışı geliştirmemek.

**Çıktılar:**

- Ağaç collider entegrasyonu.
- Fizik/spatial regresyon testleri.
- Geometri hizalama ve sınır testi raporu.

**Kabul koşulları:**

- Karakter ağaç gövdesinin içinden geçmemeli.
- Ağaç taç görselinin genişliği gereksiz fiziksel engel oluşturmamalı.
- Broadphase yalnızca aday toplama görevinde kalmalı; nihai çarpışma kararı mevcut narrowphase sözleşmesine dayanmalı.
- Nesne kaldırıldığında collider ve spatial kayıtları stale kalmamalı.
- Mevcut hareket ve çarpışma davranışlarında regresyon olmamalı.

### 12.6 — Ortak mimarinin farklı nesne türleriyle doğrulanması

**Amaç:** Ağaç için oluşturulan mimarinin tek bir nesne türüne özel olmadığını göstermek.

Değerlendirilebilecek nesne türleri:

- Kaya/büyük kaya: Görsel sınırından daha küçük veya farklı şekilli fiziksel taban alanı.
- Çalı: Görsel alanı bulunabilen, ancak fiziksel engeli olmayan veya sınırlı olan nesne.
- Heykel: Belirgin zemin bağlantısı ve fiziksel gövdesi bulunan nesne.
- Sandık: Görsel, zemin ve fiziksel sınırları daha yakın olabilen nesne.

İşler:

- Her türün ortak sözleşmeyle temsil edilme uygunluğunu değerlendirmek.
- En az iki farklı geometrik profile sahip nesne örneği seçmek.
- Nesneye özgü opsiyonel alanları belirlemek.
- Aynı ortak sistemin farklı anchor ve collider tanımlarını desteklediğini göstermek.
- Görsel dosya değişimi ve farklı boyut senaryolarını sınamak.

**Çıktılar:**

- Farklı nesne profilleriyle doğrulama sahnesi.
- Ortak/opsiyonel alanların kullanım örnekleri.
- Gerekirse mimari sözleşme güncellemesi.

**Kabul koşulları:**

- Ortak mimari en az ağaç dışında iki farklı nesne profiline uyarlanabilmeli.
- Her nesnenin gereksiz alanları doldurması gerekmemeli.
- Nesneye özgü davranışlar ortak altyapıya özel durum yığını olarak eklenmemeli.
- Doğrulama örnekleri otomatik testlerle desteklenmeli.

Not: Bu iş paketi kapsamlı bir çevresel içerik kataloğu veya sanat paketi üretme hedefi değildir. Amaç mimari esnekliği kanıtlamaktır.

### 12.7 — Geliştirici tanılama ve debug görünümü

**Amaç:** Çevresel nesnelerin geometrik referanslarını görsel olarak incelemeyi ve hataları teşhis etmeyi kolaylaştırmak.

Gösterilmesi değerlendirilecek bilgiler:

- Ground Anchor işareti.
- Depth Anchor işareti/çizgisi.
- Collision Geometry sınırı.
- Visual Bounds.
- Canopy Bounds.
- Nesne kimliği ve türü.
- Dünya/harita konumu.

İşler:

- Mevcut debug overlay ve tuş davranışlarını incelemek.
- Yeni görünümü mevcut tanılama sistemine uygun şekilde eklemek.
- Normal oyun görünümünü değiştirmeden debug bilgilerini açıp kapatmak.
- Kamera pan/zoom sırasında debug geometrisinin nesneyle hizalı kalmasını doğrulamak.
- Debug çiziminin authoritative simülasyon state'ini değiştirmediğini test etmek.

**Çıktılar:**

- Çevresel nesne debug görünümü.
- Debug kullanım yönergesi.
- Görsel hizalama testleri.

**Kabul koşulları:**

- Anchor ve collider referansları anlaşılır biçimde görülebilmeli.
- Debug görünümü kapalıyken normal render temiz kalmalı.
- Kamera hareketi ve zoom sırasında debug işaretleri nesneyle birlikte doğru görünmeli.
- Debug çizimi entity, physics veya spatial state üzerinde yan etki oluşturmamalı.

### 12.8 — Bütünleşik doğrulama, performans ve kullanıcı kabulü

**Amaç:** Çevresel nesne mimarisinin mevcut laboratuvar altyapısıyla birlikte doğru, kararlı ve görsel olarak kabul edilebilir olduğunu doğrulamak.

İşler:

- Ortak nesne sözleşmesi için unit testleri çalıştırmak.
- Render/Y-sort, entity/spatial ve physics entegrasyon testlerini çalıştırmak.
- Farklı çizim paletleri ve nesne geometrileriyle regresyon testleri yapmak.
- Birden fazla çevresel nesnenin bulunduğu sahneleri sınamak.
- Kamera pan/zoom ve pencere boyutu değişimlerini kontrol etmek.
- Anchor, görsel sınır ve collider hizasını görsel olarak doğrulamak.
- Nesne oluşturma/kaldırma ve harita yaşam döngüsünü test etmek.
- Render, spatial query ve çarpışma maliyetlerini uygun profillerde ölçmek.
- Linux ve Windows CI iş akışlarını doğrulamak.
- Benchmark/test artifact'lerini saklamak.
- Manuel görsel/işlevsel kabul kontrol listesini tamamlamak.
- Kapanış raporunu hazırlamak.

**Çıktılar:**

- Otomatik test ve regresyon kanıtları.
- Linux/Windows CI sonuçları.
- Performans karşılaştırma raporu.
- Manuel kabul kontrol listesi.
- Aşama 12 kapanış raporu taslağı.

**Kabul koşulları:**

- Kritik unit, integration ve regression testleri başarılı olmalı.
- Linux ve Windows Core Quality kontrolleri başarılı olmalı veya istisnalar açık teknik gerekçeyle raporlanmalı.
- Çevresel nesne geometrisi mevcut fizik ve spatial sözleşmelerini bozmamalı.
- Görsel kabul senaryoları kullanıcı tarafından doğrulanmalı.
- Bilinen sorunlar ve sınırlamalar raporda açıkça belirtilmeli.
- Kullanıcı manuel kabulü olmadan aşama kapatılmış sayılmamalı.

## 7. Test ve doğrulama yaklaşımı

Aşama 12'de aşağıdaki test türleri kullanılacaktır:

1. **Unit test:** Anchor, bounds, nesne tanımı ve geometri yardımcılarının tekil doğruluğu.
2. **Integration test:** Çevresel nesne + render, Y-sort, physics, entity ve spatial sistemleri.
3. **Regression test:** Aşama 6–11 boyunca kabul edilmiş kamera, hareket, çarpışma, render ve yaşam döngüsü davranışları.
4. **Visual acceptance:** Karakter/çevresel nesne örtüşmesi, zemin oturması, anchor ve collider hizası.
5. **Lifecycle test:** Nesne ekleme, kaldırma, harita unload/reload ve spatial kayıt tutarlılığı.
6. **Performance benchmark:** Nesne sayısı arttıkça render, sorgu ve çarpışma maliyetlerinin gözlenmesi.
7. **Cross-platform validation:** Linux ve Windows CI.

Testler mümkün olduğunca sabit seed ve tekrarlanabilir parametrelerle yürütülecektir. Test çalıştırılmadıysa başarılı olarak raporlanmayacaktır. Görsel olarak kontrol edilmeyen davranış için görsel kabul iddiasında bulunulmayacaktır.

## 8. Performans yaklaşımı

Aşama 12'nin önceliği yeni bir optimizasyon algoritması geliştirmek değil, çevresel nesne altyapısının mevcut sistemlere getirdiği maliyeti ölçmektir.

İzlenecek alanlar:

- Nesne başına render hazırlık maliyeti.
- Y-sort sıralama maliyeti.
- Collision Geometry aday toplama ve narrowphase maliyeti.
- Spatial index kayıt/güncelleme maliyeti.
- Visual Bounds/Canopy Bounds hesaplarının maliyeti.
- Debug görünümünün açık ve kapalı olduğu durumların maliyet farkı.
- Nesne sayısı ve sahne yoğunluğu arttığında bellek davranışı.

Mutlak FPS veya milisaniye eşikleri, mevcut referans ortamı ve ölçüm sonuçları görülmeden belirlenmeyecektir. Önce baseline oluşturulacak; gerekiyorsa teknik planda gerekçeli kabul eşikleri tanımlanacaktır. Ölçümle desteklenmeyen optimizasyon yapılmayacaktır.

## 9. Mimari sınırlar ve korunacak kararlar

Aşama 12 boyunca aşağıdaki kararlar korunacaktır:

- Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak kalır.
- Pygame mevcut laboratuvar aracı olmaya devam eder; Godot geçişi yapılmaz.
- Geometry, World, Movement, Physics, Spatial, Camera, Rendering, Entities ve Simulation sorumlulukları korunur.
- WorldPosition/WorldPoint authoritative dünya konumudur; ekran koordinatı veya sprite pikseli dünya konumunun yerine geçmez.
- Kamera ve render authoritative simülasyon state'ini değiştirmez.
- Broadphase aday toplar; nihai fizik kararı narrowphase/geometri doğrulamasına dayanır.
- Mevcut entity ve spatial lifecycle sözleşmeleri korunur.
- NPC ve kaynaklar bu aşamada otonom hareket kazanmaz.
- FOLLOW/WAIT/RETURN yoldaş komutları hareket uygulamasına dönüşmez.
- Laboratuvar ana oyundan izole kalır.

## 10. Riskler ve önleyici yaklaşımlar

| Risk | Olası etki | Önleyici yaklaşım |
|---|---|---|
| Görsel alanın collider olarak kullanılması | Karakterin dallara/yapraklara çarpması | Visual Bounds ve Collision Geometry'yi ayırmak |
| Anchor'ın sprite boyutuna bağlanması | Görsel değişiminde nesnenin zeminden kayması | Anchor'ı bağımsız geometrik veri olarak tutmak |
| Depth Anchor'ın belirsiz olması | Hatalı ön/arka örtüşme | Açık sıralama sözleşmesi ve görsel test |
| Ortak modelin yalnızca ağaca göre tasarlanması | Kaya/çalı gibi türlerde özel durum birikmesi | Birden fazla nesne profiliyle erken doğrulama |
| Entity ve statik çevresel nesne sorumluluklarının karışması | Gereksiz lifecycle/AI bağımlılıkları | Mevcut entity mimarisini inceleyip en dar entegrasyonu seçmek |
| Spatial kayıtların stale kalması | Hatalı sorgu ve çarpışma adayları | Oluşturma/kaldırma lifecycle regresyonları |
| Debug çiziminin state değiştirmesi | Render/simülasyon tutarsızlığı | Debug görünümünü salt okunur tutmak |
| Aşırı erken sanat/asset kapsamı | Teknik hedefin içerik üretimine kayması | Önce mevcut asset envanteri ve tek ağaç prototipi |
| Ölçümsüz optimizasyon | Gereksiz karmaşıklık ve regresyon | Önce baseline, sonra kanıta dayalı düzeltme |
| Laboratuvarın ana oyuna taşması | Korunan dallarda istenmeyen değişiklik | Dal izolasyonu ve commit öncesi doğrulama |

## 11. Beklenen teslimatlar

Aşama 12 sonunda aşağıdaki çıktılar beklenmektedir:

1. Mevcut render/entity/physics/asset altyapısı denetim raporu.
2. Ortak çevresel nesne sözleşmesi ve mimari kararı.
3. Görselden bağımsız anchor/bounds/collision tanımı.
4. Çalışan ağaç prototipi.
5. Depth Anchor tabanlı çizim sıralaması entegrasyonu.
6. Collision Geometry entegrasyonu.
7. Ortak mimariyi doğrulayan en az iki ek nesne profili.
8. Geliştirici debug görünümü ve kullanım yönergesi.
9. Otomatik unit/integration/regression testleri.
10. Performans ve bellek ölçüm özeti.
11. Linux/Windows CI ve artifact kanıtları.
12. Manuel görsel/işlevsel kabul kontrol listesi.
13. Aşama 12 kapanış raporu.

Teslimatların kesin dosya isimleri ve konumları teknik plan sırasında belirlenecektir.

## 12. Aşama 12 genel kabul koşulları

Aşama 12 ancak aşağıdaki koşulların tamamı sağlandığında kapanışa hazır sayılır:

1. Mevcut render, Y-sort, entity, spatial, physics ve asset altyapısı denetlenmiş ve bulguları belgelenmiş olmalıdır.
2. Çevresel nesne görsel sunumu ile geometrik/dünya sorumlulukları ayrılmış olmalıdır.
3. Ground Anchor ve Depth Anchor açık ve test edilebilir şekilde temsil edilmelidir.
4. Visual Bounds ile Collision Geometry birbirinden bağımsız olmalıdır.
5. Ağaç prototipi mevcut hex dünya ve kamera sisteminde doğru konumlanmalıdır.
6. Karakterin ağacın önünden ve arkasından geçişinde doğru çizim sıralaması elde edilmelidir.
7. Ağaç gövdesi fiziksel engel oluşturmalı; taç görseli gereksiz çarpışma oluşturmamalıdır.
8. Görsel dosya değişikliği geometrik referansları bozmamalıdır.
9. Ortak mimari ağaç dışında en az iki farklı nesne profiliyle doğrulanmalıdır.
10. Nesne oluşturma/kaldırma ve harita yaşam döngüsü entity/spatial/physics tutarlılığını korumalıdır.
11. Debug görünümü normal render ve authoritative simülasyon state'inden ayrılmış olmalıdır.
12. Kritik otomatik testler başarılı olmalı; başarısızlıklar gizlenmemeli veya kapsam dışı bırakılmamalıdır.
13. Linux ve Windows CI kontrolleri başarılı olmalı veya istisnalar açıkça belgelenmelidir.
14. Performans etkisi ölçülmeli ve sonuçlar ortam/senaryo bilgileriyle raporlanmalıdır.
15. Kullanıcı masaüstü görsel/işlevsel kabul kontrol listesini tamamlamalıdır.
16. Kapanış raporu değişen dosyaları, test sonuçlarını, CI run kimliklerini, commit SHA'lerini ve bilinen sınırlamaları içermelidir.
17. Bütün çalışmalar yalnızca `experiment/hex-world-laboratory` dalında tutulmalıdır.

## 13. Onay kapıları ve çalışma yöntemi

Aşama 12 aşağıdaki kapılarla yürütülecektir:

1. **Genel plan onayı:** Kullanıcı bu belgeyi ve kapsam sınırlarını inceler.
2. **Depo denetimi:** Genel plan onaylandıktan sonra mevcut laboratuvar dalı ve ilgili dosyalar yeniden incelenir.
3. **Teknik mimari plan:** Sınıf/modül sorumlulukları, veri akışları, dosya değişiklik listesi, test matrisi ve manuel kabul senaryoları hazırlanır.
4. **Teknik plan onayı:** Kullanıcı teknik planı ayrıca onaylar.
5. **Uygulama:** Yalnızca onaylanmış iş paketleri uygulanır.
6. **Ara doğrulama:** Her iş paketi kendi testleri ve kanıtlarıyla doğrulanır.
7. **Bütünleşik doğrulama:** 12.8 kapsamında testler, benchmarklar, CI ve artifact'ler tamamlanır.
8. **Manuel kabul:** Kullanıcı masaüstü görsel/işlevsel kontrolleri gerçekleştirir.
9. **Kapanış:** Kapanış raporu ve gerekli durum belgeleri güncellenir.

Genel planın hazırlanması uygulama izni anlamına gelmez. Teknik plan onayı olmadan kod değişikliği yapılmaz. Kullanıcının ayrıca belirttiği sınırlar, bu belgedeki genel ifadelerden önce gelir.

## 14. Dal ve dosya güvenliği

- Bütün Aşama 12 planlama ve uygulama değişiklikleri yalnızca `experiment/hex-world-laboratory` dalında tutulacaktır.
- `main` ve `demo_eldoria` dallarına yazılmayacaktır.
- Bu aşamada ana oyuna entegrasyon veya merge yapılmayacaktır.
- Her GitHub yazma işleminden önce aktif laboratuvar dalının HEAD'i doğrulanacaktır.
- Yeni dosya oluşturulmadan önce aynı yolun mevcut olmadığı kontrol edilecektir.
- Her yazma işleminde branch açıkça belirtilecek ve commit SHA yeni branch HEAD'iyle karşılaştırılacaktır.
- Korunan dalların değişmediği işlem sonrasında yeniden doğrulanacaktır.
- Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak korunacaktır.

## 15. Sonraki adım

Bu genel planın kullanıcı tarafından onaylanması halinde sıradaki iş, Aşama 12 teknik mimari planını hazırlamaktır.

Teknik plan en az şu başlıkları içerecektir:

- 12.1 depo denetiminde incelenecek gerçek dosya ve modüller.
- Çevresel nesne veri modelinin mevcut mimariye göre kesinleştirilmesi.
- Ground Anchor, Depth Anchor, Visual Bounds, Canopy Bounds ve Collision Geometry veri sözleşmeleri.
- Ağaç prototipinin dosya ve bileşen bazlı tasarımı.
- Render/Y-sort, physics ve spatial entegrasyon sınırları.
- Her alt aşama için değişecek/oluşturulacak dosyaların listesi.
- Otomatik test matrisi ve performans ölçüm yöntemi.
- Kullanıcının masaüstünde uygulayacağı görsel kabul senaryoları.
- Riskler, geri dönüş yaklaşımı ve alt aşama bağımlılıkları.

**Kapanış kararı — 18 Kasım 2026:** Aşama 12'nin 12.1–12.8 kapsamı tamamlandı. Kullanıcı, prosedürel ağaç/kaya/çalı görsellerini ve özellikle ağaç gövdesi ile kaya collider hizalamasını masaüstünde kabul etti. Otomatik testler ve Linux/Windows CI başarılıdır. Aşama 12 resmen kapatılmıştır. Sonraki aşama ayrıca planlanıp kullanıcı onayına sunulacaktır.
