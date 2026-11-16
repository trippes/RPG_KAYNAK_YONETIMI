# Aşama 4 — Sürekli Hareket Sistemi Genel Planı

> **Belge türü:** Aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** GENEL PLAN KULLANICI TARAFINDAN ONAYLANDI — TEKNİK MİMARİ PLANI HAZIRLANACAK  
> **Tarih:** 16 Kasım 2026  
> **Ön koşul:** Aşama 3 genel kapanış raporu kullanıcı tarafından kabul edildi.

---

## 1. Amaç

Aşama 4'ün amacı, Eldoria'nın altıgen dünya modelinde hareketli varlıkların hücreden hücreye sıçramadan, kesintisiz ve sürekli dünya koordinatlarında hareket edebilmesini sağlayacak temel hareket altyapısını oluşturmaktır.

Aşama 3 ile dünya, harita, hücre, başlangıç verisi ve runtime değişikliklerinin veri modeli kuruldu. Aşama 4 bu dünyanın içinde hareket edebilen varlıklar için ilk simülasyon katmanını oluşturacaktır.

Bu aşamanın sonunda laboratuvarda Pygame'den bağımsız bir hareket çekirdeği ve bu çekirdeğe kullanıcı girdisi iletebilen ince bir girdi adaptörü bulunması hedeflenir. Hareketin engellerle fiziksel etkileşimi bu aşamanın hedefi değildir; çarpışma ve fizik Aşama 5'te ele alınacaktır.

## 2. Aşama 3'ten devralınan sözleşmeler

Aşama 4 aşağıdaki mevcut kararları korumalıdır:

1. **Axial `(q, r)` hücre adresidir.** Hücre komşuluğu, topoloji ve hücre verisi için kullanılır; hareketli varlığın kesirli fiziksel konumunun yerine geçmez.
2. **WorldPosition sürekli dünya konumudur.** Hareketli varlığın fiziksel konumunu temsil eder. Hücre merkezine otomatik yuvarlama veya snap uygulanmaz.
3. **ScreenPosition ekran koordinatıdır.** Hareket çekirdeğinin authoritative konumu olamaz.
4. **Hex geometri authoritative kalır.** Bir dünya konumunun hangi hücreye karşılık geldiği Aşama 2 geometri API'si üzerinden belirlenir; hareket modülü kendi hex dönüşüm matematiğini kopyalamaz.
5. **Dünya ve harita kimlikleri korunur.** Aynı axial koordinat farklı haritalarda aynı fiziksel dünya bağlamı anlamına gelmez.
6. **Pygame bağımlılığı sınırlandırılır.** Hareket matematiği ve simülasyon çekirdeği grafik penceresi olmadan test edilebilir olmalıdır.
7. **Aşama 3 veri modeli değiştirilmez.** Hareket için gerekli yeni bir dünya/varlık sözleşmesi ihtiyacı çıkarsa mevcut veri modelini sessizce genişletmek yerine gerekçesi ve etkisi ayrıca değerlendirilir.

## 3. Ürün davranışı ve hedeflenen kullanıcı deneyimi

Hareketin oyuncuya hissettirmesi gereken temel davranışlar şunlardır:

- Karakter bir hücrenin merkezinden hareket etmeye başlayabilir ve hücre içinde herhangi bir kesirli konumda bulunabilir.
- Karakter hücre sınırına ulaştığında durmak veya merkezden merkeze atlamak zorunda değildir.
- Hücre sınırını geçerken fiziksel konumu ve hareketi kesintisiz devam eder.
- Yatay, dikey ve çapraz hareketlerde yön kaynaklı hız avantajı oluşmaz.
- Hareket yönü değiştirildiğinde konumda ani sıçrama oluşmaz.
- Girdi bırakıldığında seçilen hareket modeline uygun biçimde durur.
- Aynı simülasyon süresi ve aynı hareket girdisi, farklı çizim kare hızlarında karşılaştırılabilir fiziksel sonuç üretir.
- Hareket çekirdeği yalnızca oyuncuya özel tasarlanmaz; ileride NPC ve diğer hareketli varlıklar aynı çekirdeği kullanabilecek şekilde genel tutulur.

Bu aşama karakter animasyonu veya nihai görsel hareket kalitesi üretmeyi hedeflemez. Öncelik fiziksel konumun ve zaman davranışının doğruluğudur.

## 4. Kapsam içi işler

### 4.1 Sürekli dünya konumu sözleşmesi

Hareketli varlığın konumunu kesirli dünya koordinatlarıyla temsil eden veri sözleşmesi kesinleştirilecektir.

Bu kapsamda:
- WorldPosition'ın alanları, doğrulaması ve aritmetik davranışı belirlenecek.
- Dünya koordinatlarının işaret ve eksen yönü mevcut geometri sözleşmesiyle tutarlı olacak.
- Konum ile hücre adresi birbirinden ayrı tutulacak.
- Konumdan mevcut hücre adresine erişim, Aşama 2 dönüşüm API'sini kullanacak.
- Sayısal hassasiyet, geçersiz değerler ve büyük koordinat davranışları değerlendirilecek.

Dünya birimi, konum tipinin kesin alanları ve API isimleri teknik mimari planında belirlenecektir. Bunlar bu genel planla peşinen sabitlenmiş değildir.

### 4.2 Hareket durumu ve hareket modeli

Bir hareketli varlığın hareketini tanımlamak için gereken en küçük durum kümesi belirlenecektir.

Değerlendirilecek kavramlar:
- Mevcut fiziksel konum.
- Hareket yönü veya hız vektörü.
- Hız büyüklüğü ve izin verilen üst sınır.
- Kullanıcı veya başka bir sistem tarafından iletilen hareket niyeti.
- Gerekli görülürse ivmelenme ve yavaşlama davranışı.
- Durma ve yön değiştirme kuralları.

Sabit hızla hareket ile ivmeli hareket seçenekleri gereksinim ve test sonuçlarına göre değerlendirilecektir. Gereksiz fizik karmaşıklığı bu aşamaya taşınmayacaktır. İvme, sürtünme veya atalet gibi davranışlar ancak hedeflenen kontrol hissi için gerekli ve test edilebilir bulunursa plana alınacaktır.

### 4.3 Zaman yönetimi ve simülasyon güncellemesi

Hareketin render kare hızına bağlı olmaması sağlanacaktır.

Değerlendirilecek yaklaşımlar:
- Değişken delta time ile güncelleme.
- Sabit simülasyon zaman adımı (fixed timestep).
- Sabit simülasyon adımı ile bağımsız çizim sıklığının birlikte kullanılması.

Seçim; doğruluk, kararlılık, uygulama karmaşıklığı, büyük frame-time sıçramaları ve düşük donanım maliyeti bakımından karşılaştırılacaktır.

Büyük zaman farklarının tek bir güncellemede sınırsız hareket üretmesine izin verilmeyecek. Gerekli zaman biriktirme, adım sınırı veya telafi politikası teknik tasarım ve deneylerle belirlenecektir. Seçilen politika deterministik testlerle belgelenmelidir.

### 4.4 Girdi adaptörü

Klavye girdisi, hareket çekirdeğinin içine gömülmeyecektir.

Girdi adaptörü:
- Tuş durumlarını hareket niyetine dönüştürecek.
- Aynı anda birden fazla yön tuşuna basılmasını ele alacak.
- Çapraz girdinin normalize edilmesini veya eşdeğer hız kuralını sağlayacak.
- Girdi yokluğu, tuş bırakma ve yön değiştirme davranışlarını açıkça iletecek.
- Pygame'e bağımlı olabilir; fakat hareket çekirdeği Pygame'i bilmeyecektir.

Joystick/gamepad desteği bu aşamada zorunlu değildir. Adaptör sözleşmesi ileride başka girdi kaynaklarının eklenmesini engellememelidir.

### 4.5 Dünya modeliyle ilişki

Hareketli varlığın dünya konumu ile bulunduğu hex hücre arasındaki ilişki doğrulanacaktır.

- Hücre adresi konumdan türetilir; konum hücre adresinden her güncellemede yeniden oluşturulmaz.
- Hücre geçişleri yalnızca konumun hangi hücreye karşılık geldiğini değiştirebilir; fiziksel konumu sıfırlamaz.
- Önceki hücreyi koruyan sınır tie-break kuralı mevcut geometri sözleşmesine uygun biçimde kullanılabilir.
- Harita sınırı ve harita dışı konum davranışı, çarpışma/engel çözümü yapılmadığı gerçeği dikkate alınarak açıkça belgelenir.
- Hareket çekirdeği harita hücrelerini her frame gereksiz yere taramaz veya bütün haritaları yüklemez.

Bu aşamada engel, duvar veya geçilebilirlik alanlarına göre hareketi durdurma/engelden kaçınma uygulanmayacaktır. Bunlar Aşama 5'in sorumluluğudur.

### 4.6 Test prototipi ve teşhis

Hareketin doğruluğunu inceleyebilmek için mümkün olan en küçük prototip ve teşhis araçları hazırlanacaktır.

Hedeflenen gözlemler:
- Mevcut dünya konumu.
- Hız/yön bilgisi.
- Karşılık gelen axial hücre.
- Simülasyon adım sayısı ve delta time bilgisi.
- Hücre sınırı geçişi sırasında konumun kesintisizliği.

Görsel prototip yalnızca hareketi gözlemlemek için kullanılacaktır; nihai render, kamera veya sanat sistemi değildir. Çekirdek testlerin çalışması için Pygame penceresi açılması zorunlu olmayacaktır.

## 5. Önerilen alt çalışma sırası

Aşağıdaki alt çalışmalar uygulama sırasını düzenlemek için önerilmiştir. Kesin modül sınırları, dosya adları ve alt aşama kabul ölçütleri Aşama 4 teknik mimari planında belirlenecektir.

| Alt çalışma | Amaç | Beklenen çıktı |
|---|---|---|
| 4.1 — Konum sözleşmesi | WorldPosition ve hareketli konum verisinin tanımlanması | Sürekli konum veri modeli ve testleri |
| 4.2 — Hareket çekirdeği | Hareket niyeti, yön, hız ve konum güncellemesi | Pygame'den bağımsız hareket modülü |
| 4.3 — Zaman modeli | Simülasyon adımı ve kare hızından bağımsızlık | Seçilmiş ve test edilmiş zaman güncelleme politikası |
| 4.4 — Girdi adaptörü | Klavye durumlarının hareket niyetine çevrilmesi | İnce Pygame input adaptörü |
| 4.5 — Dünya ilişkisi | Konum-hücre eşleşmesi ve sınır geçişleri | World/Geometry entegrasyon testleri |
| 4.6 — Kabul prototipi | Hareket davranışının gözlenmesi ve bütünleşik doğrulama | Minimal hareket sahnesi, test ve ölçüm raporu |

Alt çalışmaların birleştirilmesi veya sırasının değiştirilmesi teknik mimari planında gerekçelendirilebilir; kapsamın genişletilmesi ise ayrıca onay gerektirir.

## 6. Kapsam dışı işler

Aşağıdaki işler Aşama 4'e dahil değildir:

- Hex duvarları, engeller ve çarpışma çözümü.
- Collider/gövde geometrisi, temas çözümü, duvar boyunca kayma ve tünelleme önleme.
- Pathfinding veya NPC karar sistemi.
- Kamera, zoom, pan ve screen-to-world dönüşümü.
- Nihai dünya render'ı, sprite animasyonu, y-sort ve sanat varlıkları.
- Oyuncu/NPC/kaynak için tam Entity/Component mimarisi.
- Çoklu harita otomatik yükleme/tahliye ve offline progression.
- Tam oyun kaydı, oyuncu envanteri veya görev verisi persistence.
- Ana oyuna veya `demo_eldoria` dalına entegrasyon.
- Godot'a geçiş veya motor değişikliği.
- Multiplayer/ağ hareketi ve istemci-sunucu senkronizasyonu.

Bu maddelerden birinin Aşama 4 için zorunlu olduğu ortaya çıkarsa doğrudan eklenmeyecek; etkisi ve gerekçesi kullanıcıya sunulacaktır.

## 7. Mimari ve performans ilkeleri

1. Hareket matematiği saf Python çekirdeğinde tutulmalı; Pygame yalnızca girdi ve gözlem/prototip sınırında kullanılmalıdır.
2. Movement, Rendering veya Camera katmanlarına bağımlı olmamalıdır.
3. Hücre adresi, dünya konumu ve ekran konumu farklı veri tipleri/sorumluluklar olarak kalmalıdır.
4. Geometri dönüşümleri Aşama 2 API'sinden kullanılmalı; kopya hex matematiği yazılmamalıdır.
5. Her simülasyon adımında gereksiz nesne üretimi, harita taraması veya veri kopyalama yapılmamalıdır.
6. Hareket sistemi yalnızca ilgili varlığın konum ve hareket durumunu güncellemelidir.
7. Çok sayıda kayıtlı harita, hareket güncellemesinin maliyetini artırmamalıdır; aktif harita dışındaki haritalar bu aşamada simüle edilmez.
8. Erken optimizasyon yapılmamalı; performans sorunları ölçümle gösterilmelidir.
9. Hareket state'inin tek bir yetkili sahibi olmalı; debug ve render katmanları bu state'i değiştirmemelidir.
10. Yeni bağımlılık eklenmesi gerekiyorsa gerekçesi, alternatifleri ve bakım maliyeti teknik mimari planında açıklanmalıdır.

## 8. Test ve kabul hedefleri

Aşama 4'ün teknik kapanışında aşağıdaki davranışlar kanıtlanmalıdır:

### 8.1 Konum ve geometri

- Konum kesirli değerleri korur; hücre merkezine snap edilmez.
- Pozitif ve negatif dünya koordinatlarında doğru davranır.
- Axial/world eşleşmesi mevcut geometri API'siyle tutarlıdır.
- Hücre sınırının iki tarafında hareket süreklidir.
- Önceki hücre tie-break davranışı mevcut sözleşmeyle çelişmez.

### 8.2 Hareket

- Tek eksenli ve çapraz hareketin hız büyüklüğü eşdeğer kurala uyar.
- Yön değiştirme fiziksel konumda sıçrama oluşturmaz.
- Girdi bırakma ve durma davranışı belirlenen modele uyar.
- Çok küçük ve yüksek hız değerleri test edilir.
- Uzun süreli hareket sırasında sayısal hata/birikim davranışı incelenir.

### 8.3 Zaman tutarlılığı

- Aynı hareket girdisi ve aynı toplam simülasyon süresi, farklı render FPS koşullarında karşılaştırılır.
- En az 30, 60 ve 120 FPS senaryoları değerlendirilir.
- Değişken frame-time ve büyük zaman sıçramaları test edilir.
- Seçilen timestep politikasının hata ve telafi davranışı belgelenir.
- Aynı girdi dizisi tekrarlanabilir sonuç üretir.

### 8.4 Mimari ve regresyon

- Hareket çekirdeği Pygame olmadan import ve test edilebilir.
- Input adaptörü hareket çekirdeğine ters bağımlılık oluşturmaz.
- Aşama 2 geometri testleri korunur.
- Aşama 3 dünya modeli ve persistence testleri gerilemez.
- Laboratuvarın tam test paketi başarılı olur.
- CI Linux ve Windows doğrulamalarını sürdürür.

### 8.5 Performans

- Hareket güncellemesinin maliyeti farklı timestep ve hareketli varlık sayılarında ölçülür.
- Ortalama süre yanında mümkünse P95 güncelleme süresi kaydedilir.
- Gereksiz harita/hücre taraması ve beklenmeyen bellek büyümesi aranır.
- Donanım ve test koşulları raporda belirtilir.
- Ölçülmeyen FPS veya ölçeklenebilirlik garantisi verilmez.

Bu ölçütlerin sayısal toleransları ve test örnekleri teknik mimari planında kesinleştirilecektir.

## 9. Başlıca riskler ve kontrol yaklaşımı

| Risk | Olası sonuç | Kontrol yaklaşımı |
|---|---|---|
| Dünya birimi ve hız ölçeğinin belirsiz kalması | Hız değerlerinin anlamsız veya tutarsız olması | Birim sözleşmesini teknik planda açıkça tanımlamak |
| Hareketin render FPS'e bağlanması | Farklı bilgisayarlarda farklı hareket hızı | Kontrollü timestep deneyleri ve karşılaştırmalı test |
| Büyük delta time | Tek adımda aşırı hareket veya kararsızlık | Zaman sıçraması politikası ve regresyon testleri |
| Çapraz hızın normalize edilmemesi | Çapraz yönde daha hızlı hareket | Vektör büyüklüğü değişmez testleri |
| Konumun hücre merkezine yuvarlanması | Kesintili hareket ve konum kaybı | WorldPosition'ın authoritative kalması |
| Geometri matematiğinin kopyalanması | Hücre tespitinde tutarsızlık | Aşama 2 API'sine bağlılık ve entegrasyon testleri |
| Pygame'in çekirdeğe sızması | Headless test ve yeniden kullanım zorluğu | Saf Python çekirdeği ve bağımlılık kontrolleri |
| Gereğinden erken fizik eklenmesi | Aşama kapsamının karışması | Çarpışma ve engel çözümünü Aşama 5'e bırakmak |
| Gereksiz nesne/hesaplama üretimi | Düşük donanımda performans kaybı | Benchmark ve profil ölçümü |

## 10. Beklenen teslimatlar

Aşama 4 kapanışında aşağıdaki çıktılar beklenir:

- Sürekli dünya konumu ve hareket state sözleşmesi.
- Pygame'den bağımsız hareket çekirdeği.
- Zaman/timestep yaklaşımının gerekçeli kararı ve ilgili ADR (karar gerekiyorsa).
- Klavye girdisi adaptörü.
- Dünya konumu ile axial hücre ilişkisini doğrulayan entegrasyon testleri.
- Hareketi gözlemlemek için minimal prototip/teşhis görünümü.
- Unit, integration, regression ve kabul testleri.
- Performans ölçüm sonuçları.
- Alt çalışma raporları ve Aşama 4 genel kapanış raporu.
- Güncel README ve gerekli mimari belge bağlantıları.

## 11. Uygulama ve onay kapıları

Aşama 4 aşağıdaki sırayla yürütülecektir:

1. **Genel plan:** Bu belgeyle tanımlandı ve kullanıcı tarafından onaylandı.
2. **Teknik mimari plan:** Modüller, dosyalar, veri tipleri, API'ler, bağımlılıklar, alternatifler, riskler, test senaryoları ve kabul ölçütleri ayrıntılandırılacak.
3. **Teknik plan onayı:** Kullanıcı açıkça onaylamadan kod değiştirilmeyecek.
4. **Uygulama:** Yalnızca onaylanan kapsamda ve `experiment/hex-world-laboratory` dalında yapılacak.
5. **Test ve doğrulama:** Hedefli testler, tam regresyon paketi, CI ve gerekli benchmark/görsel kontroller çalıştırılacak.
6. **Kapanış raporu:** Gerçekleşen işler, test kanıtları, ölçümler, commit'ler ve bilinen sınırlar raporlanacak.
7. **Kullanıcı kabulü:** Aşama 4, raporun kullanıcı tarafından incelenip açıkça kabul edilmesiyle kapanacak.

Bir alt çalışmada yeni ve onaylanmamış kapsam ihtiyacı ortaya çıkarsa uygulama durdurulacak; değişiklik gerekçesi ve etkisi sunulacaktır.

## 12. Dal güvenliği ve değişiklik sınırı

- Bütün Aşama 4 planlama ve uygulama belgeleri ile kod değişiklikleri `experiment/hex-world-laboratory` dalında tutulacaktır.
- `main` ve `demo_eldoria` dalları bu aşamada değiştirilmeyecektir.
- Bu genel planın onayı, teknik mimari planını veya kod uygulamasını otomatik olarak onaylamaz.
- Aşama 4'ün tamamlanması, Aşama 5'i otomatik başlatmaz; sonraki aşama için ayrı plan ve onay gerekir.

## 13. Genel planın kabul durumu

Kullanıcı, 16 Kasım 2026 tarihinde Aşama 4 genel planını onaylamıştır. Bu belge, onaylanan genel planın ayrıntılı ve izlenebilir sürümüdür.

**Mevcut aşama durumu:** Genel plan onaylandı. Sıradaki izinli iş Aşama 4 Teknik Mimari Planı'nın hazırlanmasıdır. Kod uygulaması henüz başlamamıştır.
