# Eldoria — Modüler Yapı ve İnşa Sistemi Yol Haritası

**Durum:** Gelecek çalışma planı — uygulama başlamadı  
**Hedef dal:** `experiment/map-cleanup`  
**Kapsam:** Mimari tasarım, veri sözleşmeleri, runtime, içerik, entegrasyon ve doğrulama  
**Bağlayıcı sınır:** Bu belge mevcut hareket/harita temizliği çalışmasının kapsamını genişletmez. İnşa sistemi, ayrıca açıkça başlatılana kadar yalnızca plan olarak kalır.

## 1. Amaç ve ürün hedefi

Oyuncunun ve NPC'lerin yapı parçalarını üretebildiği, hassas konumlarda yerleştirebildiği, parçaları birleştirerek işlevsel yapılar oluşturabildiği genel amaçlı bir sistem tasarlamak.

Sistem yalnızca önceden tanımlanmış bina prefab'larını yerleştirmekle sınırlı olmayacaktır. Zemin, duvar, kapı, pencere, çatı ve destek gibi parçalar ortak yapı sözleşmeleri üzerinden bir araya gelebilmelidir. Aynı altyapı oyuncu inşasını, NPC inşasını ve dünya tarafından önceden oluşturulmuş yapıları desteklemelidir.

Üretim tesisleri bu altyapının özel bir kullanım biçimidir; ayrı ve paralel bir bina/tesis motoru oluşturulmayacaktır.

## 2. Değişmez mimari ilkeler

1. **Hex dünya kanonik kalır.** Dünya bölgeleri, arazi, sahiplik, harita sınırları ve dünya ölçeğindeki ilişkiler mevcut hex dünya modeline bağlı kalır.
2. **İnşa hassasiyeti ayrı bir uzamsal sözleşmedir.** Yapı parçalarının konum, yön, yükseklik, bağlantı ve hizalama gereksinimleri hex hücre merkezlerine zorlanmaz. İnşa koordinat sistemi hex dünya koordinatlarıyla açık ve deterministik dönüşüm kurar.
3. **Tek yapı altyapısı kullanılır.** Oyuncu, NPC veya dünya kaynağı tarafından oluşturulması yapı verisinin ve runtime kurallarının farklılaşmasına neden olmaz. Oluşturan aktör yalnızca sahiplik/menşe ve yetki bilgisidir.
4. **Veri ile davranış ayrılır.** Parça tanımları ve tarifler içerik verisidir; yerleştirme, bağlantı, destek, hasar ve etkileşim kuralları domain/application davranışıdır. İçerik dosyaları çalıştırılabilir kod taşımaz.
5. **Tek authoritative konum ve sahiplik kaynağı korunur.** Yapı sistemi ikinci bir dünya, entity registry, fizik motoru veya hareket otoritesi kurmaz. Mevcut runtime sahipliğiyle açık adaptörler üzerinden bütünleşir.
6. **Üretim tesisi yapı yeteneğidir.** Bir atölye, fırın veya benzeri tesis; genel yapı bileşenleri, etkileşim noktaları ve üretim kabiliyetleriyle tanımlanır.
7. **Kademeli ve kanıtlı entegrasyon yapılır.** Her aşama otomatik test, regresyon, performans kanıtı ve gerektiğinde oyun içi manuel kabul olmadan tamamlanmış sayılmaz.

## 3. Uzamsal model için tasarım sınırı

İnşa koordinat sistemi mevcut hex dünya koordinatlarının yerine geçmez. İki modelin sorumlulukları ayrıdır:

- **Hex dünya:** Hangi dünya bölgesinde bulunulduğu, arazi/biome, dünya sınırı, bölgesel kurallar ve dünya ölçeğindeki sahiplik.
- **İnşa uzayı:** Yapı parçasının hassas konumu, yönelimi, yüksekliği/kat seviyesi, bağlantı yüzleri, snap/hizalama ve yapı içi geometrisi.
- **Sürekli fizik/aktör konumu:** Oyuncu ve NPC hareketinin mevcut authoritative konum sözleşmesi. Yapı çarpışma geometrisi bu sisteme engel/şekil olarak sunulur; aktör konumunu yapı sistemi yönetmez.
- **Navigasyon ızgarası:** Hareket/pathfinding için türetilmiş sistem. İnşa ızgarasıyla aynı şey değildir ve ona bağlanmak zorunda değildir.

İnşa koordinat sisteminin dünya ölçeği, birim boyutu, eksen yönü, dönüşüm hassasiyeti ve quantization politikası Aşama 1'de mevcut HexCoord/WorldPoint ve renderer/physics sözleşmeleri incelenerek kararlaştırılacaktır. Bu değerler ölçüm ve geometri testleri olmadan sabitlenmeyecektir.

## 4. Aşamalar ve çıkış kapıları

### Aşama 0 — Mevcut mimari envanteri ve sınır doğrulaması

- Hex dünya, WorldPoint, renderer, kamera, physics snapshot/solver, spatial index, entity ownership, GameplayService, içerik paketi ve save/load akışları incelenir.
- Yapıların world entity, spatial object veya ayrı domain aggregate olarak hangi sınırda temsil edileceği karşılaştırılır.
- Yapıların statik/dinamik çarpışma, occupancy, render ve etkileşim çağrı zincirleri belgelenir.
- Mevcut hareket/harita çalışmalarına müdahale edilmez; yalnızca entegrasyon noktaları belirlenir.

**Çıkış kapısı:** Mevcut authoritative sahiplik, konum, fizik, içerik ve persistence sınırları kaynak kod ve testlerle belgelenmiş olmalıdır. Bu aşamada gameplay davranışı değiştirilmez.

### Aşama 1 — Genel yapı ve yapı parçası veri sözleşmeleri

- `StructureDefinition`, `StructurePartDefinition` ve gerekli kimlik/değer nesneleri için aday sözleşmeler tasarlanır.
- Parça kategorisi, boyut/şekil, bağlantı yüzleri, yönelim, kat/yükseklik, malzeme, dayanıklılık, yerleştirme koşulları ve görsel referanslar ayrıştırılır.
- Yapı örneği ile katalog tanımı ayrılır: tanım değişmez içerik verisi, örnek ise dünyadaki canlı state'tir.
- Parçaların birbirine bağlanması için port/socket/edge gibi bağlantı semantiği değerlendirilir.
- Schema sürümleme, kimlik benzersizliği, referans doğrulaması ve geçersiz tanım reddi belirlenir.

**Çıkış kapısı:** Sözleşmeler oyuncu/NPC/dünya kaynaklı yapıları aynı şekilde temsil edebilmeli; örnek state ile tanım verisi karışmamalı; geçersiz bağlantı ve referanslar deterministik reddedilmelidir.

### Aşama 2 — İnşa koordinatları ve yerleştirme sistemi

- İnşa uzayı koordinat/value object'leri ve dünya dönüşümleri tanımlanır.
- Hassas konum, yönelim, yükseklik ve snap/hizalama kuralları belirlenir.
- Önizleme (ghost), geçerli/geçersiz yerleşim sonucu ve ret nedenleri için saf doğrulama API'si tasarlanır.
- Hex arazi sınırı, dünya dışı konum, başka yapı ile çakışma, destek gereksinimi ve yetki gibi yerleştirme koşulları ayrı doğrulayıcılar olarak ele alınır.
- Yerleştirme işlemi atomik olmalı; doğrulama ile commit arasında state değişirse sonuç yeniden doğrulanmalıdır.

**Çıkış kapısı:** Koordinat dönüşümleri round-trip toleransını sağlamalı; aynı girdiler aynı sonucu üretmeli; geçersiz yerleştirme dünyayı kısmen değiştirmemelidir.

### Aşama 3 — Temel yapı bileşenleri

- Zemin, duvar, kapı ve pencere ilk yapı parçası aileleri olarak uygulanır.
- Parça bağlantıları, açıklıklar, yönelim, geçiş ve erişim yüzleri tanımlanır.
- Kapı açık/kapalı state'i ve pencere/duvar ayrımı ortak etkileşim/çarpışma sözleşmesine bağlanır.
- Parçalar tekil çizim nesneleri olarak değil, bir yapı örneğinin bileşenleri olarak yönetilir.
- İlk oynanabilir dikey dilim küçük bir yapı oluşturma, kapıdan geçme ve save/load senaryosunu kapsar.

**Çıkış kapısı:** Parçalar doğru hizalanmalı, bağlantı kuralları doğrulanmalı, kapı durumu etkileşim ve collision sonucunu değiştirmeli; parçalı ve bütün yapı görünümü tutarlı olmalıdır.

### Aşama 4 — Crafting ve malzeme gereksinimleri

- Yapı parçası üretim tarifleri mevcut kaynak/envanter/recipe/production sözleşmeleriyle ilişkilendirilir.
- Malzeme tüketimi atomik ve başarısızlıkta geri alınabilir olmalıdır.
- Üretim sonucu doğrudan dünya yerleşimi olmak zorunda değildir; parça envantere/taşınabilir stoğa üretilebilir.
- Tarif, işçilik süresi, gerekli araç/istasyon ve beceri koşulları veriyle tanımlanır.
- Kaynak stoğu ile yapı parçası stoğu arasında çift sayım veya paralel envanter oluşması engellenir.

**Çıkış kapısı:** Yetersiz malzeme üretimi reddetmeli; başarılı üretim doğru miktarda tüketim ve çıktı üretmeli; save/load ve hata enjeksiyonu atomikliği korumalıdır.

### Aşama 5 — Çarpışma, hareket ve etkileşim entegrasyonu

- Yapı parçalarının collision şekilleri mevcut physics snapshot/solver sistemine adaptörle sunulur.
- Kapı ve benzeri değişken parçaların collision state'i kontrollü biçimde güncellenir.
- Oyuncu/NPC hareketi, yapıların içinden geçme, kapı kullanma ve dar geçitlerden geçme senaryolarıyla doğrulanır.
- Yapı etkileşim hedefleri mevcut etkileşim mesafesi/hedef seçimi sözleşmelerine bağlanır.
- Navigasyon engel güncellemeleri mevcut kare-grid navigasyon mimarisiyle uyumlu ve türetilmiş cache invalidation üzerinden ele alınır; inşa koordinatları navigasyon hücrelerine eşitlenmez.

**Çıkış kapısı:** Yapı collision'ı mevcut fizik otoritesini kullanmalı; oyuncu ve NPC aynı kurallara tabi olmalı; yerleştirme/kaldırma/kapı durumu değişikliği collision ve navigasyon sonuçlarına doğru yansımalıdır.

### Aşama 6 — Çatı, kat ve destek sistemi

- Çatı, kat döşemesi, merdiven ve destek/kolon gibi bileşen aileleri tasarlanır.
- Taşıyıcı bağlantılar ve yük aktarımı için ilk sürümde uygulanacak sade ve deterministik kurallar belirlenir.
- Desteksiz parça, geçersiz kat bağlantısı ve yapısal bütünlük kaybı sonuçları tanımlanır.
- Dikey hareket ve katlar arası erişim, mevcut aktör konumu/kamera/render sözleşmeleriyle birlikte değerlendirilir.
- Fiziksel simülasyon gerektirmeyen yapısal doğrulama tercih edilir; gerçekçi mühendislik simülasyonu hedeflenmez.

**Çıkış kapısı:** Destek/bağlantı grafı deterministik olmalı; geçersiz yapı genişlemesi reddedilmeli veya tanımlı hasar/çökme kuralı üretmeli; çok katlı erişim manuel olarak doğrulanmalıdır.

### Aşama 7 — Hasar, onarım ve yükseltme

- Parça ve yapı dayanıklılığı, hasar türü ve hasar state'i tanımlanır.
- Onarım tarifleri mevcut crafting/malzeme tüketimiyle bütünleştirilir.
- Yükseltme, mevcut parçayı yeni tanım/state'e kontrollü dönüştürür; kimlik ve bağlantı sürekliliği korunur.
- Parça kaldırma/yıkımın bağlı parçalar, destek ve içerik üzerindeki etkisi belirlenir.
- Hasar/onarım olayları deterministik ve kaydedilebilir olmalıdır.

**Çıkış kapısı:** Hasar, onarım ve yükseltme state geçişleri test edilmeli; malzeme tüketimi atomik olmalı; bağlantı ve destek tutarlılığı korunmalıdır.

### Aşama 8 — NPC kullanımı ve üretim entegrasyonu

- NPC'lerin yapı parçası üretmesi, taşıması, depolaması ve yerleştirmesi için genel iş/aktivite sözleşmeleri tanımlanır.
- Oyuncu ve NPC aynı placement validator ve yapı runtime API'sini kullanır.
- NPC inşa planı, görev/iş hedefi ve kaynak tahsisi olarak temsil edilir; NPC'ye özel ikinci bir inşa motoru kurulmaz.
- Atölye, fırın ve benzeri üretim tesisleri genel yapı örneğine bağlı capability/interaction/production tanımlarıyla çalışır.
- Dünya tarafından önceden oluşturulan yapılar da aynı tanım ve runtime yükleme yolundan geçer.

**Çıkış kapısı:** Oyuncu, NPC ve başlangıç dünyası yapıları aynı doğrulama/yerleştirme/persistence hattını kullanmalı; tesisler ayrı yapı sistemi oluşturmadan üretim başlatabilmelidir.

### Aşama 9 — Kayıt/yükleme, migration ve performans

- Yapı örnekleri, parça state'leri, bağlantılar, hasar, sahiplik ve üretim capability state'i için sürümlü snapshot tasarlanır.
- Save/load candidate validation ve atomik aktivasyon ilkeleri korunur.
- Statik geometri, collision proxy ve navigasyon etkileri türetilmiş/cache verisi olarak ele alınır; kanonik olmayan cache verileri zorunlu save alanı yapılmaz.
- Büyük yapı sayıları için chunk/region partition, lazy load, spatial query ve render culling ölçülür.
- Save boyutu, yükleme süresi, placement doğrulama maliyeti, collision sorguları, bellek ve frame-time benchmark'ları hazırlanır.

**Çıkış kapısı:** Save/load round-trip ve bozuk kayıt reddi başarılı olmalı; migration geriye dönük uyumu korumalı; hedef donanımda tanımlı aktör/yapı senaryoları performans bütçesini karşılamalıdır.

## 5. Ortak test ve kabul matrisi

| Alan | Zorunlu doğrulama |
|---|---|
| Kimlik/veri | Duplicate ID, eksik referans, geçersiz schema ve desteklenmeyen sürüm |
| Koordinat | Dünya ↔ inşa uzayı round-trip, hassasiyet ve sınır davranışı |
| Yerleştirme | Geçerli zemin, dünya dışı, çakışma, yasak arazi, yetki ve atomiklik |
| Bağlantı | Yanlış yön, uyumsuz port, açıklık, kopuk parça ve tekrar bağlantı |
| Temel parçalar | Zemin/duvar/kapı/pencere hizası ve görsel tutarlılık |
| Crafting | Malzeme yeterliliği, atomik tüketim, çıktı ve başarısızlık |
| Fizik | Duvar engeli, kapı açık/kapalı, dar geçit ve NPC/oyuncu eşitliği |
| Yapısal bütünlük | Destek, kat, çatı ve geçersiz kaldırma |
| Lifecycle | Hasar, onarım, yükseltme ve yıkım |
| NPC | Üretim, taşıma, yerleştirme ve kaynak tahsisi |
| Persistence | Round-trip, migration, bozuk snapshot ve atomik restore |
| Performans | Parça sayısı, yapı sayısı, collision query, render ve save/load maliyeti |

Her aşama için unit, integration ve gerektiğinde end-to-end testler ayrı tutulur. Manuel kabul gereken görsel/fiziksel davranışlar otomatik testlerin yerine geçmez; ayrıca kaydedilir.

## 6. Mimari riskler ve önlemler

| Risk | Önlem |
|---|---|
| İnşa ızgarasının hex dünya modelini gölgelemesi | Hex dünya kanonik; dönüşüm tek yönlü ve açık sözleşmeyle yönetilir |
| İnşa ve navigasyon ızgaralarının karıştırılması | Ayrı koordinat türleri, ayrı API ve ayrı cache |
| İkinci entity/physics otoritesi | Mevcut registry, runtime ve physics adaptörleri yeniden kullanılır |
| Oyuncu ve NPC için farklı kurallar | Tek placement validator ve tek yapı runtime API |
| İçerik dosyalarının davranış koduna dönüşmesi | Veri-only schema ve domain/application kural sınırı |
| Üretim tesislerinin ayrı sisteme dönüşmesi | Facility davranışı yapı capability'si olarak modellenir |
| Çok sayıda parçanın performansı düşürmesi | Ölçüm, chunking, spatial query, cache ve görünür alan önceliği |
| Save verisinin türetilmiş geometriyle şişmesi | Yalnızca kanonik state kaydedilir; cache yeniden üretilir |
| Destek/çökme kurallarının aşırı karmaşıklaşması | İlk sürümde basit, deterministik bağlantı ve destek modeli |

## 7. Başlangıçta kapsam dışı tutulanlar

Aşağıdakiler ayrıca planlanmadıkça bu yol haritasının hedefi değildir:

- Serbest biçimli voxel arazi kazma veya araziyi yeniden şekillendirme.
- Gerçekçi statik/dinamik mühendislik ve sonlu elemanlar simülasyonu.
- Ağ çok oyuncululuğu ve eşzamanlı ortak inşa.
- Oyuncu/NPC hareket sistemini yeniden yazmak.
- Hex dünya haritasını kare/ızgara dünya haritasına dönüştürmek.
- Yapı parçaları için bağımsız envanter, entity registry, physics engine veya save sistemi kurmak.

## 8. Başlatma ve değişiklik yönetimi

Bu yol haritasının Git dalında bulunması, uygulamanın başladığı veya mevcut iş kapsamına alındığı anlamına gelmez.

Uygulamaya geçiş için açık başlangıç kararı gerekir. Başlangıçta önce Aşama 0 tamamlanır; mevcut mimariyle uyumsuzluklar ve gerekli kararlar raporlanır. Her aşama için ayrı görev/kabul ölçütleri ve gerekiyorsa ayrı mimari karar kaydı açılır.

Bu belge yalnızca `experiment/map-cleanup` dalına ait planlama dokümanıdır. `main`, `demo_eldoria` veya `experiment/hex-world-laboratory` dallarına otomatik aktarım/merge yapılmaz. Mevcut harita temizliği ve hareket çalışmasının kapsamına bu belge nedeniyle yeni iş eklenmez.
