# ELDORIA RPG — MASTER ROADMAP V2
## Başlangıç vizyonu, gerçekleşen çalışmalar ve gelecek geliştirme planı

| Alan | Değer |
|---|---|
| Proje | Eldoria — Kaynak Yönetimi RPG |
| Depo | `trippes/RPG_KAYNAK_YONETIMI` |
| Referans dal | `demo_eldoria` |
| Belge sürümü | Master Roadmap V2 |
| Hazırlanma tarihi | 14 Kasım 2026 |
| Referans HEAD | `2c1598f17d43230bfd76329c6f9a402f00478361` |
| Mevcut uygulama sürümü | `3.0.0rc1` |
| Belge durumu | Yeni ana yol haritası — başlangıç ve mevcut durum kaydı; gelecek fazlar plan niteliğindedir |

---

# 1. Bu belgenin amacı ve yetkisi

Master Roadmap V2, Eldoria'nın başlangıçtaki ürün vizyonunu, bugüne kadar gerçekleştirilen teknik ve oynanış çalışmalarını, mevcut mimari sınırları ve gelecekteki geliştirme hedeflerini tek bir ana belgede toplar.

Bu belge, eski yol haritasının satır satır güncellenmiş hâli değildir. Eski yol haritası ve faz belgeleri tarihsel kayıt olarak korunur; V2 ise bugünkü gerçek durumu esas alarak sıfırdan düzenlenmiş ana planı oluşturur.

Bu belgenin üç ana sorusu vardır:

1. Eldoria hangi oyun ve yazılım hedefleriyle yola çıktı?
2. Bu hedeflerin hangileri uygulandı, hangileri testlerle doğrulandı, hangileri değişti veya ertelendi?
3. Eldoria'nın tamamlanmış bir oyun ve içerik üretim ekosistemine dönüşmesi için hangi işler hangi sırayla yapılmalı?

## 1.1. Durum etiketleri

Bu belgede her iş aşağıdaki anlamlarla değerlendirilir:

- **TAMAMLANDI:** Kod veya içerik uygulandı ve ilgili kabul/otomatik doğrulama kanıtı mevcut.
- **UYGULANDI — KISMİ:** Temel teknik altyapı mevcut; hedeflenen nihai ürün kapsamı henüz tamamlanmadı.
- **PLANLANDI:** Gelecek geliştirme hedefidir; uygulanmış özellik olarak kabul edilmez.
- **ERTELENDİ:** Bilinçli olarak sonraki faza bırakıldı.
- **KAPSAM DIŞI:** İlgili fazın hedefi değildir. İleride ayrıca karar verilebilir.
- **DOĞRULANMADI:** Kod veya belge işaretleri bulunsa da hedef davranış için yeterli kabul kanıtı yoktur.

Bir fazın teknik olarak tamamlanması, oyunun bütün ürün hedeflerinin tamamlandığı anlamına gelmez. Test başarısı, görsel kabul, oynanış kabulü ve içerik kapsamı birbirinden ayrı değerlendirilir.

## 1.2. Belge hiyerarşisi

- Bu belge, proje seviyesindeki hedefleri ve faz sırasını tanımlar.
- `docs/architecture/` altındaki teknik sözleşmeler, ilgili sistemlerin nasıl çalışması gerektiğini tanımlar.
- `docs/content/` altındaki belgeler, oyun içeriklerinin veri biçimini ve hazırlanma kurallarını tanımlar.
- `reports/` altındaki raporlar, belirli bir fazın denetim, uygulama, test ve kapanış kanıtlarını saklar.
- Kaynak kodu ve testler, uygulanmış davranışın nihai kanıtıdır.

Master Roadmap V2 teknik sözleşmelerin yerine geçmez. Bir faza başlanırken ilgili mimari belgeler, gerçek kaynak kodu ve testler birlikte incelenir.

---

# 2. Başlangıç vizyonu — Eldoria'dan ne yapmak istiyorduk?

Eldoria'nın temel amacı, yalnızca kaynak toplayıp üretim yaptıran basit bir simülasyon değil; keşif, karakter gelişimi, dünya etkileşimi, ekonomi, üretim, görevler ve savaş sistemlerinin aynı yaşayan dünyada birleştiği, uzun vadede genişletilebilir bir RPG oluşturmaktır.

Oyuncu dünyayı keşfeder; kaynakları toplar; eşyalar ve üretim zincirleriyle ekonomik faaliyet yürütür; NPC'lerle ilişki kurar; görevler alır; karakterini geliştirir ve karşılaştığı tehditlerle mücadele eder. Bu sistemlerin birbirinden kopuk mini oyunlar değil, ortak dünya ve simülasyon kurallarıyla çalışan tek bir oyun olması hedeflenir.

## 2.1. Oyun deneyiminin ana sütunları

### Keşif ve dünya

- Oyuncunun dolaşabildiği, birbirine bağlanan yerel haritalardan oluşan geniş bir dünya.
- Köyler, ormanlar, madenler, doğal alanlar, yapılar, geçitler ve keşfedilebilir bölgeler.
- Harita geçişlerinin yalnızca menü seçimiyle değil, dünyadaki gerçek bağlantılar üzerinden gerçekleşmesi.
- Teknik harita koordinatlarının oyuncuya doğrudan gösterilmediği, doğal ve bütünlüklü bir dünya sunumu.
- Çevre nesneleri, arazi, yapılar, kaynaklar ve NPC'lerin aynı mekânsal kurallara bağlı olması.

### Kaynak yönetimi ve üretim

- Dünyadaki kaynak düğümlerinden kaynak toplama.
- Envanter ve kaynak miktarlarının tutarlı yönetimi.
- Reçeteler, süreli üretim işleri ve çok aşamalı üretim zincirleri.
- Üretim tesisleri, kapasite ve tesis yetenekleri.
- Kaynakların ekonomi ve ticaret sistemleriyle ilişkilendirilmesi.
- Üretim ve kaynak faaliyetlerinin simülasyon zamanı içinde deterministik ilerlemesi.

### Karakter ve RPG sistemleri

- Oyuncunun tek ana karakteri üzerinden ilerleyen oyun yapısı.
- Karakter oluşturma, ırk/sınıf tanımları, nitelikler, ekipman ve gelişim.
- Envanter, eşya, silah, zırh, tüketilebilirler, ganimet ve konteynerler.
- NPC'lerle konuşma, görev alma, karar verme ve sonuçlarla karşılaşma.
- Sıra tabanlı savaş ve karakter yetenekleri.

### Yaşayan dünya ve NPC'ler

- NPC'lerin yalnızca sabit diyalog noktaları değil, dünyada konum ve faaliyet sahibi aktörler olması.
- Kaynak toplama, üretim ve benzeri faaliyetlerin dünya simülasyonuyla ilişkilendirilmesi.
- NPC ilişkileri, fraksiyonlar, itibar ve görev bağlantıları.
- Gelecekte daha kapsamlı karar verme ve günlük faaliyet simülasyonu.

## 2.2. Görsel ve oynanış yönü

Görsel hedef; Diablo II'nin atmosferini ve keşif hissini, Stardew Valley'nin yaşayan dünya ve kaynak döngülerini, Baldur's Gate II'nin RPG derinliğini bir araya getiren özgün bir deneyimdir.

Temel yönelim:

- Üstten görünüm, katmanlı 2.5D sunum.
- Doğal arazi, çevre nesneleri ve derinlik sıralaması.
- Teknik altıgen hücre sisteminin oyuncuya görünmeden hareket ve dünya simülasyonunu yönetmesi.
- Sıra tabanlı savaş.
- Oyuncu tarafında tek ana karakter odağı.
- Pencere tabanlı, sürüklenebilir RPG arayüzü.
- Yalnızca teknik prototip değil, görsel olarak bütünlüklü ve oynanabilir bir dünya.

Bu görsel referanslar doğrudan kopyalama hedefi değildir; atmosfer, sistem derinliği ve oynanış yaklaşımı için yön gösterir.

## 2.3. Erken tasarım notları ve doğrulama durumu

Projenin önceki tasarım görüşmelerinde aşağıdaki simülasyon fikirleri de ele alınmıştır:

- Simülasyon zamanı ile gerçek zamanın kesin biçimde ayrılması.
- 60 tick/saniye tabanlı çalışma fikri.
- 360 günlük oyun yılı.
- Bir oyun gününün yaklaşık 24 gerçek dakika sürmesi.
- Hücre tabanlı mekânsal ölçek ve altıgen harita yaklaşımı.

Bunlar erken tasarım hedefleri/parametreleridir. Bu Master Roadmap, her birinin mevcut oyunda bütünüyle uygulandığını iddia etmez. Takvim, gün/gece, mevsim, hızlandırma ve fiziksel mesafe gibi ürün davranışları ilgili gelecek fazda tek bir güncel tasarım sözleşmesi altında yeniden doğrulanmalıdır.

---

# 3. Teknik başlangıç yaklaşımı ve mimarinin evrimi

## 3.1. İlk teknik yönelim

Proje Python ekosisteminde geliştirilmeye başlandı. Oyun mantığı, kaynak yönetimi, simülasyon ve görsel katmanların erişilebilir ve aşamalı geliştirilebilir olması hedeflendi.

Pygame, oynanabilir prototip ve 2D sunum katmanı olarak kullanıldı. Zaman içinde oyun büyüdükçe yalnızca ekran ve sınıflar eklemek yerine, temel motorun bağımsız ve test edilebilir katmanlara ayrılması gerektiği görüldü.

## 3.2. Core mimarisinin ayrıştırılması

İlk önemli mimari dönüşüm, oyun altyapısının deterministik ve bağımsız bir Core etrafında yeniden düzenlenmesiydi.

Bu dönüşümün hedefleri:

- Domain, application, runtime, UI ve persistence sorumluluklarını ayırmak.
- Entity ve World sahipliğini tek otoriteye bağlamak.
- Simülasyon tick'lerini deterministik hâle getirmek.
- Action, scheduler ve event akışını açık sözleşmelerle yönetmek.
- Runtime nesne grafiğini kalıcı kayıt verisinden ayırmak.
- Eski API'leri bir anda silmek yerine uyumluluk adaptörleriyle kontrollü taşımak.
- Mimari sınırları testlerle korumak.

Core 2.0 Architecture Baseline ve Architecture Freeze sonrasında Core 2.1 kapanışıyla canonical state, world/entity ownership, simulation, event transport, restore ve application sınırları tamamlandı.

Core 2.1 kapanışı gerçek oyun save/load backend'inin veya tüm gameplay sistemlerinin tamamlandığı anlamına gelmez. Bu ayrım korunmalıdır.

## 3.3. Pygame ve Godot değerlendirmesi

Pygame'in görsel sınırları nedeniyle Godot 4 ile hibrit veya alternatif bir görsel motor yaklaşımı değerlendirildi. Ancak mevcut karar, Eldoria'yı şu aşamada Pygame üzerinde geliştirmeye devam etmektir.

Godot geçişi başlatılmış bir iş değildir. Pygame ile hedeflenen 2.5D görsel kaliteye ulaşmak teknik veya üretim açısından sürdürülemez hâle gelirse, ayrı bir mimari değerlendirmeyle tekrar ele alınabilir. Bu karar mevcut oyun kodunu iki motor arasında bölmek için gerekçe oluşturmaz.

---

# 4. Bugüne kadar gerçekleştirilen çalışmalar

Bu bölüm, 14 Kasım 2026 tarihinde `demo_eldoria` dalında bulunan kod, mimari belgeler ve faz kapanış raporlarına göre hazırlanmıştır.

## 4.1. Core ve temel mimari

**Durum: TAMAMLANDI — Core 2.1 kapsamı**

Tamamlanan ana başlıklar:

- Canonical ID, Position ve Tick gibi temel değer nesneleri.
- Entity repository ve world membership sahipliği.
- World domain state ile runtime ayrımı.
- GameSession ve application sınırları.
- Deterministik simulation runtime.
- Callback-free scheduler ve action lifecycle.
- Canonical event transport, dispatcher ve event schema versioning.
- Legacy API uyumluluk ve migration araçları.
- Canonical persistence state ve restore planı.
- Validate → prepare → activate yaklaşımı ve başarısız restore durumunda çalışan oturumun korunması.
- Mimari bağımlılık sınırlarının testlerle güvence altına alınması.

Core katmanı gameplay, UI veya somut persistence backend'inin sahibi değildir. Yeni oyun özellikleri bu sınırları bozmadan application/domain katmanlarında geliştirilmelidir.

## 4.2. Save/load ve persistence

**Durum: UYGULANDI — Kapsamlı application persistence mevcut**

- Core ve gameplay state'ini birleştiren kayıt zarfı.
- Şema sürümü kontrolü ve legacy kayıt migration'ları.
- Candidate runtime oluşturma ve doğrulama.
- Tüm referanslar doğrulanmadan aktif oturumun değiştirilmemesi.
- Save slot, yedek ve güvenli dosya yazma davranışları.
- Kaynak, envanter, üretim, tesis, aktör, sosyal sistem ve diğer uygulama kayıtlarının snapshot/restore entegrasyonları.
- Save/load sonrasında aktif oturumun tutarlı biçimde yeniden kurulması.

**Bilinen sınır:** Bazı runtime-only orkestrasyon nesneleri kalıcı kayıt kapsamına alınmamıştır. Özellikle üretim zinciri orkestrasyonunun tüm devam durumu otomatik restore edilmez. Bir sistemin tekil job kayıtlarının saklanması, o sistemin bütün üst seviye planlama/orkestrasyon durumunun saklandığı anlamına gelmez.

## 4.3. Kaynak, envanter ve üretim

**Durum: UYGULANDI — Temel ve ileri uygulama katmanları mevcut**

- Kaynak türleri, miktarlar ve birimler.
- Dünya kaynak düğümleri.
- Kaynak toplama ve atomik envanter güncellemesi.
- Envanterler arası transfer.
- Reçete tanımları.
- Anında ve tick tabanlı süreli üretim işleri.
- Çok aşamalı üretim zinciri orkestrasyonu.
- Üretim kapasitesi ve slot rezervasyonu.
- Üretim tesisleri, tesis türleri ve yetenekleri.
- Üretim job ve tesis ilişkilerinin persistence entegrasyonu.
- GameplayService üzerinden toplama, üretim, zincir ve durum sorgulama.

**Henüz tamamlanmış sayılmayanlar:** Otomatik tesis seçimi, üretim kuyrukları ve önceliklendirme, tam çalışan/iş gücü simülasyonu, enerji üretim/dağıtım ekonomisi, bakım, verimlilik ve kalite modeli. Üretim zinciri orkestrasyon state'inin save/load devamlılığı da ayrı bir karardır.

## 4.4. Ekonomi ve ticaret

**Durum: UYGULANDI — İlk ekonomik döngü mevcut**

- Para birimi ve ledger tabanlı bakiye yönetimi.
- Fiyat/teklif ve pazar kayıtları.
- NPC/merchant ile ticaret.
- Atomik alım-satım ve stok rezervasyonu.
- Konuma bağlı pazar erişimi.
- Oyun günü takvimine göre stok yenileme ve arz-talep temelli fiyat davranışları için mevcut altyapı.
- Para birimleri arasında tanımlı sabit dönüşüm hizmeti ve kullanıcı arayüzü.

Tam kapsamlı ekonomik simülasyon, bütün dünya pazarlarının dengelenmesi ve ekonomik içeriklerin kapsamlı biçimde üretilmesi gelecek işidir.

## 4.5. NPC, diyalog ve görev sistemleri

**Durum: UYGULANDI — Oynanabilir ilk dikey dilim ve genişletilebilir veri sözleşmeleri mevcut**

- NPC kimlikleri ve tanımları içerik paketlerinden yükleniyor.
- NPC konum, fraksiyon ve ilişki verileri ayrıştırılmış durumda.
- Diyalog ve NPC etkileşimi için application servisleri mevcut.
- Görev tanımları, hedefler ve ödüller içerik verisiyle yönetiliyor.
- Görev ilerlemesi kaynak toplama, konuşma ve diğer oyun olaylarına bağlanabiliyor.
- Görev zinciri ve dallanma grafiği için genel veri modeli mevcut.
- Alternatif görev yolları, ön koşul ifadeleri ve dal seçimleri destekleniyor.
- Görev ilerlemesi ve oyuncu dal tercihleri save/load kapsamına alınmış durumda.
- Görev günlüğü, görev veren NPC ve hedef bilgilerini genel veriden çözüyor.

Yeni görev veya NPC eklemek için demo kimliklerine özel kod yazılmaması temel mimari kuraldır. Yeni bir oyun mekaniği gerektiğinde genel mekanik bir kez geliştirilir; bu mekaniği kullanan içerikler veriyle tanımlanır.

## 4.6. Combat, karakter ve eşya sistemleri

**Durum: UYGULANDI — İlk teknik combat altyapısı; nihai RPG kapsamı tamamlanmadı**

- Karakter oluşturma ve karakter tanımları.
- Karakter ile world actor arasındaki bağlantı.
- Karakter istatistiklerinin okunması.
- Combatant runtime, saldırı, HP, durum etkileri ve persistence için ilk teknik prototip.
- Envanter, konteyner, ganimet ve eşya etkileşimleri için altyapı.
- Kilit ve anahtar domain'i, kilit açma/lockpicking ve zorla açma kuralları için teknik temel.
- Oyun ekranlarında karakter, envanter, görev ve diğer pencerelerin ilk uygulamaları.

Bu maddeler tam kapsamlı karakter gelişimi, yetenek ağacı, dengelenmiş savaş, eşya üretim/loot kataloğu veya nihai kullanıcı deneyiminin tamamlandığı anlamına gelmez. Savaş sistemi özellikle daha fazla oynanış tasarımı ve UI çalışması gerektirir.

## 4.7. Pygame oynanabilir dikey dilimi ve arayüz

**Durum: UYGULANDI — İlk oynanabilir uygulama mevcut**

- Pygame oyun döngüsü ve uygulama başlatma.
- Ana menü ve oyun oturumu.
- Karakter oluşturma ve açılış diyaloğu.
- Ana dünya/harita görünümü.
- Envanter, karakter, görev, pazar, ticaret ve diğer oyun pencereleri.
- Pencere yöneticisi, pencere odaklama, sürükleme, kapatma ve input yönlendirme.
- Klavye ve fare etkileşimi.
- Save/load akışı.
- Gerçek GameplayService işlemlerine bağlı oynanış akışları.

Oyuncunun tek ana karakteriyle dünyada ilerlediği temel dikey dilim vardır. Ancak tüm planlanan ekranların, görsel varlıkların ve oyun sistemlerinin nihai ürün kalitesine ulaştığı söylenemez.

## 4.8. Altıgen dünya ve harita mimarisi

**Durum: TEMEL HEX MİMARİSİ VE DEMO RUNTIME TAMAMLANDI; KARE HARİTA UYUMLULUĞU KORUNUYOR**

Altıgen dünya çalışmasının ana kazanımları:

- Immutable axial `HexCoord(q, r)` geometri modeli.
- Altı yön, karşı yön, komşuluk ve altıgen mesafe.
- Pointy-top geometri ve piksel/axial dönüşümleri.
- `LocalHexPosition` ve masked `HexMapDefinition` veri modeli.
- Hex haritalar için schema-v2 JSON yükleme.
- Kare ve altıgen harita kataloglarının aynı content package içinde ayrı tutulması.
- `WorldHexPosition`, axial dünya haritası ve yerel harita yerleşimleri.
- Yönlü ve karşılıklı dünya geçişlerinin doğrulanması.
- Altı komşulu hareket ve A* pathfinding.
- Occupancy, movement blocking ve atomik konum güncellemesi.
- Oyuncu/NPC/taşınabilir nesne hareket profilleri.
- Haritalar arası geçiş runtime'ı.
- Pygame pointy-top sunum, kamera, zoom, fare seçimi ve hareket interpolasyonu.
- Zemin, çevre nesnesi, asset ve depth-sorting sunum altyapısı.
- Oyuncuya normal keşif sırasında hücre ızgarası göstermeyen doğal sunum yaklaşımı.

Demo altıgen dünya gerçek yerel harita örnekleri ve bağlantılarıyla çalışır. Bu, eski dokuz schema-v1 kare haritanın tamamının altıgene dönüştürüldüğü anlamına gelmez. Kare harita sistemi ayrı model ve runtime olarak korunur.

### Hex sisteminin açık sınırları

- Eski dokuz kare harita, mevcut kare harita sözleşmesiyle korunur; toplu axial dönüşüm yapılmış değildir.
- Yeni sunum placement sözleşmesi axial q/r temellidir; kare haritalar için eşdeğer yeni editör yerleşim akışı ayrıca tasarlanmalıdır.
- Runtime hareket ve occupancy hücre tabanlıdır. Asset metadata içindeki collision AABB değerleri piksel hassasiyetli fiziksel çarpışma motoru değildir.
- Footprint metadata'sının bulunması, her çok hücreli nesnenin tam occupancy rezervasyonu yaptığı anlamına gelmez.
- Ağaç atlası/rig altyapısı denenmiştir; doğal görünüm bozulduğu için varsayılan parçalı animasyon kapatılmış, tek PNG çizimi korunmuştur.
- Gerçek 3B geometri veya 3B motor geçişi yapılmamıştır.

## 4.9. Aşama 7 — Doğal dünya görselleştirmesi

**Durum: TAMAMLANDI — 13 Kasım 2026 kapanışı**

- İç hex çizgilerinin normal oyun görünümünde gizlenmesi.
- Sürekli taban dolgusu ve daha organik arazi sunumu.
- Doğal hedef göstergesi ve dünya görünümü.
- Çevre nesnelerinin asset/placement tabanlı çizimi.
- Kamera, zoom ve derinlik sıralamasının korunması.
- Ağaç PNG entegrasyonu.
- Ağaç iskeleti ve F3 geliştirici kılavuzları.
- Parçalı ağaç atlası/rig denemesi; doğal görsel kalite nedeniyle varsayılan kullanımın kapatılması.
- Oyuncu–ağaç ön/arka sıralaması, altı yönlü geçişler ve kare harita regresyonu için kullanıcı manuel kabulü.
- Linux/Windows CI ve Pygame headless smoke doğrulaması.

Aşama 7'nin sonucu, tamamlanmış sanat varlığı paketi değildir. Doğal dünya sunumunun teknik temeli ve demo kabulü tamamlanmıştır; kapsamlı biyom ve sanat içeriği üretimi gelecek işidir.

## 4.10. Aşama 8 — Content Editor altyapısının hazırlanması

**Durum: TAMAMLANDI — 14 Kasım 2026 kapanışı**

Aşama 8'in hedefi editör arayüzünü yapmak değil, bağımsız içerik üretim aracının kullanacağı oyun tarafı altyapısını hazırlamaktı.

Tamamlanan alt başlıklar:

- 8.1 — Mevcut içerik hattının teknik denetimi.
- 8.2 — Asset Catalog sağlamlaştırma.
- 8.3 — Asset tanımları ile harita placement kayıtlarının ayrılması.
- 8.4 — Presentation geometry metadata sözleşmesi.
- 8.5 — İçerik doğrulama ve güvenli yükleme.
- 8.6 — Güvenli içerik kaydı, yedekleme ve legacy migration.
- 8.7 — UI bağımsız Presentation Content Service API.
- 8.8 — Entegrasyon, regresyon ve kapanış.

Hazırlanan temel parçalar:

- `asset_catalog.json` ve harita bazlı placement kaynakları.
- Immutable asset ve placement katalog modelleri.
- Map ID, asset ID ve geçerli axial hücre doğrulaması.
- Güvenli paket-relative path kuralları.
- Hatalı metadata'nın runtime'a yayınlanmadan reddedilmesi.
- Eksik/bozuk görsel dosyaları için kontrollü diagnostic ve mevcut fallback yaklaşımı.
- Validation-before-write, staging, atomic replace, backup ve rollback.
- Legacy birleşik presentation dosyasından split kaynaklara açık migration.
- `PresentationContentStore` ve `PresentationContentService`.
- Pygame/UI bağımsız okuma, doğrulama, kaydetme ve migration API'leri.

Aşama 8 sonunda **Content Editor kullanıcı arayüzü yapılmış değildir**. Editör ekranı, önizleme, harita boyama/yerleştirme araçları ve diğer authoring modülleri ayrı projede geliştirilecektir.

Kullanıcının kararıyla Aşama 8 kapanışı için manuel oyun içi görsel kabul zorunlu koşul yapılmamıştır. Bu, raporda açıkça belirtilen kapsam kararıdır; yapılmamış bir manuel test başarılı gösterilmemelidir.

## 4.11. Test, CI ve dağıtım altyapısı

**Durum: UYGULANDI — Otomatik kalite kapıları mevcut**

- Unit, integration, architecture ve regression test paketleri.
- Determinism, persistence, migration ve failure-injection testleri.
- Linux ve Windows GitHub Actions doğrulaması.
- Pygame headless smoke testi.
- Wheel build, izole kurulum ve packaged content kontrolü.
- Release-candidate doğrulama script'i.
- Runtime ve test/release bağımlılıklarının ayrılması.

Aşama 7 ve 8 raporlarında farklı commit ve CI koşularına ait test sayıları bulunur. Bunlar tek bir güncel test sayısıymış gibi birleştirilmemelidir. Aşama 8 kapanış raporunda Eldoria CI için platform başına 1.459 test; Core Quality doğrulamasında platform başına 1.463 test ve 237 subtest raporlanmıştır. Bu sayılar ilgili tarihsel workflow kanıtlarıdır; V2 yazılırken testler yeniden çalıştırılmış değildir.

---

# 5. 14 Kasım 2026 itibarıyla gerçek proje fotoğrafı

## 5.1. Proje ve dal

- Ana geliştirme referansı: `demo_eldoria`.
- V2 hazırlanırken doğrulanan HEAD: `2c1598f17d43230bfd76329c6f9a402f00478361`.
- Son commit mesajı: `docs: polish phase 8 completion report status`.
- Paket sürümü: `3.0.0rc1`.
- Ana oynanabilir giriş: `python main.py --play`.

## 5.2. Tamamlanmış ana teknik temel

| Alan | Durum |
|---|---|
| Core 2.0/2.1 mimarisi | TAMAMLANDI |
| Deterministik simulation ve event altyapısı | TAMAMLANDI |
| Canonical ownership ve restore sözleşmesi | TAMAMLANDI |
| Application save/load | UYGULANDI |
| Kaynak ve envanter | UYGULANDI |
| Üretim işleri, zincir, kapasite ve tesis | UYGULANDI |
| Ekonomi ve ticaret | UYGULANDI |
| NPC, diyalog ve görev dikey dilimi | UYGULANDI |
| Quest graph ve dallanma | UYGULANDI |
| Combat teknik prototipi | UYGULANDI — KISMİ |
| Pygame oynanabilir dikey dilimi | UYGULANDI |
| Altıgen dünya temel mimarisi | TAMAMLANDI |
| Hex Pygame sunum altyapısı | TAMAMLANDI |
| Doğal çevre sunum aşaması | TAMAMLANDI |
| Content Core hazırlığı / Phase 8 | TAMAMLANDI |
| Eldoria Content Editor UI | PLANLANDI |
| Tam kapsamlı oyun içeriği ve sanat paketi | PLANLANDI |
| Nihai oyun dengesi ve yayın | PLANLANDI |

## 5.3. Bilinen teknik ve ürün sınırları

Bu sınırlar açıkça korunmalı; yeni yol haritasında tamamlanmış gibi gösterilmemelidir:

1. Content Editor henüz yoktur. Mevcut Presentation Content Service, editörün kendisi değildir.
2. Dokuz eski kare haritanın axial dönüşümü yapılmamıştır. Kare ve hex sistemleri birlikte yaşar.
3. Hücre tabanlı hareket/occupancy vardır; serbest piksel düzeyinde collision/fizik sistemi yoktur.
4. Ağaç rig altyapısı mevcut olsa da varsayılan doğal ağaç görünümü tek PNG'dir.
5. Mevcut asset/placement altyapısı bütün oyun içerik kategorilerinin editör üzerinden oluşturulabildiği anlamına gelmez.
6. Combat teknik altyapısı, tamamlanmış ve dengelenmiş sıra tabanlı savaş deneyimi değildir.
7. NPC aktör ve faaliyet altyapısı, kapsamlı günlük yaşam/karar verme simülasyonu değildir.
8. Üretim tesisleri ve kapasite vardır; otomatik tesis seçimi, kuyruk ve kapsamlı iş gücü/enerji simülasyonu yoktur.
9. Üretim zinciri orkestrasyonunun tam save/load devamlılığı mevcut değildir.
10. Tam kapsamlı sanat, animasyon, ses ve biyom içerik paketi henüz üretilmiş değildir.

---

# 6. Gelecek için mimari ilkeler

Gelecek fazlar aşağıdaki değişmez ilkelerle yürütülür:

1. **Core freeze korunur.** Yeni gameplay davranışı gerekmedikçe Core katmanı genişletilmez.
2. **Oyun kuralları ile içerik verisi ayrıdır.** JSON veya başka bir içerik dosyası keyfî Python kodu çalıştırmaz.
3. **İçerik üretimi Content Editor üzerinden yürütülür.** Oyunun bütün içerik kategorileri için editör araçları oluşturulur.
4. **Editör oyundan bağımsızdır.** Editör Pygame oyun ekranlarının içinde çalışan bir mod değildir.
5. **Ortak Content Core kullanılır.** Editör ve oyun paralel/çelişkili asset, placement, validation veya persistence modelleri üretmez.
6. **Oyun içerik paketlerini tüketir.** Editörün ürettiği paketler oyun tarafından doğrulanabilir ve yüklenebilir olmalıdır.
7. **Kararlı ID ve referans bütünlüğü korunur.** NPC, görev, eşya, harita, kaynak ve diğer içerikler kimliklerle bağlanır.
8. **İçerik tanımı ile oyuncu ilerlemesi ayrıdır.** İçerik güncellemeleri oyuncu kayıtlarını sessizce bozamaz.
9. **Görsel sunum simülasyon state'ini değiştirmez.** Kamera, animasyon ve renderer authoritative world state'in sahibi değildir.
10. **Kare harita uyumluluğu açık karar olmadan kırılmaz.**
11. **Her faz küçük, denetlenebilir commit'ler ve test kapılarıyla ilerler.**
12. **Başarısız test düzeltilmeden faz kapatılmaz.** Çalıştırılmayan test başarılı kabul edilmez.
13. **Manuel görsel kabul ile otomatik CI birbirinin yerine geçmez.**
14. **Oyuncu sürümü geliştirici editörünü içermez.** Editör, geliştirme araç zincirinin parçasıdır.

---

# 7. Gelecek ana yol haritası

Aşağıdaki fazlar, V2'nin gelecek geliştirme planıdır. Bu fazların tamamı henüz başlatılmış veya onaylanmış uygulamalar değildir. Her faz açılırken kapsamı, teknik sözleşmeleri, test stratejisi ve kabul kriterleri ayrı belgelenir.

## Faz 9 — Eldoria Content Editor: Proje ayrıştırma ve mimari tasarım

**Durum: PLANLANDI — Bir sonraki ana geliştirme odağı**

Amaç: Eldoria'nın bütün oyun içeriklerini üreteceğimiz bağımsız Content Editor projesinin mimarisini kesinleştirmek.

Ana hedefler:

- Editörün ayrı geliştirme dalında geliştirilmesi.
- Oyun runtime'ından ve Pygame oyun pencerelerinden bağımsız çalışması.
- Mevcut Content Core ve `PresentationContentService` sözleşmelerini kullanması.
- Editörün kendi uygulama katmanı, UI katmanı, authoring modelleri ve proje dosya düzeninin belirlenmesi.
- Oyun ile editör arasında veri alışverişinin açık sözleşmeye bağlanması.
- Editörün oyun kaynak koduna gereksiz bağımlılık oluşturmaması.
- Editörün ürettiği içeriklerin oyun tarafından aynı canonical loader/validator ile doğrulanması.

Tasarım kapsamı:

- Uygulama başlangıcı ve proje/paket açma.
- Content package seçimi ve yönetimi.
- Asset kütüphanesi.
- Harita ve dünya çalışma alanı.
- İçerik kategorileri için ortak kayıt/form altyapısı.
- Önizleme ve doğrulama.
- Kaydetme, yedekleme ve migration.
- Oyun sürümü ile editör sürümü arasındaki uyumluluk politikası.
- Ayrı dalda geliştirme, kontrollü entegrasyon ve geri dönüş stratejisi.

**Çıkış kriteri:** Editörün mimari tasarım belgesi, bağımlılık kuralları, proje yapısı, veri akışı, entegrasyon sözleşmesi ve ilk MVP kapsamı onaylanmış olmalıdır.

Not: UI framework ve masaüstü teknoloji seçimi bu V2 belgesiyle peşinen kesinleştirilmez; Faz 9 teknik değerlendirmesinde karara bağlanır.

## Faz 10 — Content Editor çekirdeği ve harita çalışma alanı

**Durum: PLANLANDI**

Amaç: Editörün kullanılabilir ilk sürümünü oluşturmak ve ilk gerçek içerik üretim akışını tamamlamak.

Hedefler:

- Editör uygulamasının açılması ve proje/paket yüklemesi.
- Asset kütüphanesinde görsel ekleme, metadata düzenleme ve arama.
- Hex dünya haritasının görsel çalışma alanında gösterilmesi.
- Yerel hex haritaların açılması ve düzenlenmesi.
- Geçerli hücre maskesi, arazi türü ve engelli hücre düzenleme.
- Haritalar arası bağlantı ve giriş/çıkış hücresi düzenleme.
- Asset'leri haritaya yerleştirme, taşıma, döndürme/ölçekleme gibi desteklenen metadata işlemleri.
- Placement katmanı, anchor, depth ve footprint bilgilerinin düzenlenmesi.
- Undo/redo ve güvenli kaydetme.
- Harita/placement doğrulama ve hatalı kayıtların açıklanması.
- Oyun runtime'ı olmadan editör içinde önizleme.

**Çıkış kriteri:** Bir geliştirici Content Editor ile yeni bir hex harita oluşturabilmeli, arazi ve nesne yerleşimlerini düzenleyebilmeli, paketi kaydedip oyunun canonical loader'ı ile doğrulayabilmelidir.

## Faz 11 — Bütün oyun içerik kategorileri için authoring araçları

**Durum: PLANLANDI**

Amaç: İçerik üretiminin yalnızca harita ve görsellerle sınırlı kalmamasını sağlamak.

Editör modülleri:

### Dünya ve çevre
- Dünya haritası ve yerel haritalar.
- Biyomlar, arazi türleri ve çevresel özellikler.
- Landmark, yapı, kapı, köprü ve etkileşimli nesneler.
- Kaynak düğümleri ve yenilenme tanımları.
- Asset/placement kütüphanesi.

### Karakter, NPC ve sosyal sistemler
- Oyuncu karakteri için ırk, sınıf ve başlangıç tanımları.
- NPC tanımları, roller, fraksiyonlar ve ilişkiler.
- NPC konumları ve harita bağlantıları.
- Diyalog ağları, seçenekler ve güvenli genel eylemler.
- NPC görev ilişkileri ve pazar profilleri.

### Görev ve hikâye
- Görev tanımları ve hedefler.
- Görev zincirleri ve DAG bağlantıları.
- Ön koşul ifadeleri.
- Alternatif dallar ve oyuncu seçimi kuralları.
- Ödüller, itibar ve görev veren ilişkileri.
- Diyalog ile görev ilerlemesi bağlantıları.

### Eşya ve ekipman
- Eşya tanımları ve kategorileri.
- Silah, zırh, aksesuar ve tüketilebilirler.
- Nitelik etkileri ve kullanım koşulları.
- Nadirlik, ganimet tabloları ve düşme kuralları.
- Konteyner/loot içerikleri.

### Kaynak, tarif ve üretim
- Kaynak türleri ve miktar/birim tanımları.
- Reçeteler ve üretim süreleri.
- Tesis türleri, tesisler ve capability gereksinimleri.
- Üretim zinciri aşamaları.
- İş gücü/enerji/yakıt gibi kaynak girdileri.
- Kapasite ve üretim kısıtları.

### Combat ve karşılaşmalar
- Düşman/yaratık tanımları.
- Combatant istatistikleri.
- Saldırı, savunma ve durum etkisi tanımları.
- Karşılaşma ve ganimet tanımları.
- Savaş alanı/başlangıç yerleşimi ve encounter içeriği.

### Ekonomi
- Para birimleri ve fiyat tanımları.
- Pazarlar, merchant profilleri ve başlangıç stokları.
- Arz-talep ve stok yenileme parametreleri.
- Ticaret/ekonomi içerik konfigürasyonları.

**Çıkış kriteri:** Mevcut oyun veri sözleşmeleriyle uyumlu temel içerik kategorileri editör üzerinden oluşturulup düzenlenebilmeli; yeni içerik eklemek için demo kimliğine özel Python kodu gerekmemelidir. Yeni mekanik ihtiyacı doğarsa bu, içerik kaydı değil ayrı motor geliştirmesi olarak ele alınır.

## Faz 12 — Content package üretimi, doğrulama ve oyun entegrasyonu

**Durum: PLANLANDI**

Amaç: Editörün oluşturduğu içeriklerin güvenilir, sürümlü ve dağıtılabilir oyun paketlerine dönüşmesini sağlamak.

Hedefler:

- Paket manifesti ve bağımlılık yönetimi.
- Paket kimliği, sürümü ve schema uyumluluğu.
- Asset dosyalarının paketlenmesi ve referans kontrolü.
- NPC, görev, harita, kaynak, eşya ve diğer kayıtlar arasında referans doğrulaması.
- Editör içi tam paket doğrulaması.
- Hata/uyarı raporları ve kaynak dosyaya yönlendirme.
- Paket karşılaştırma ve değişiklik özeti.
- Güvenli migration ve geri dönüş.
- Oyun sürümüyle uyumsuz paketlerin yüklenmesinin engellenmesi.
- Oyun içinde seçili paketin yüklenmesi ve başlangıç akışının doğrulanması.
- Oyuncu kayıtlarının içerik güncellemelerinden etkilenmemesi için migration politikası.

**Çıkış kriteri:** Editör tarafından üretilen bir paket, ayrı doğrulama adımından geçerek oyunda açılabilmeli; hatalı paket mevcut çalışan oyunun veya önceki içeriğin üzerine yazılmamalıdır.

## Faz 13 — Eldoria dünya ve içerik üretimi

**Durum: PLANLANDI**

Amaç: Editörün teknik kabiliyetini gerçek oyun dünyası ve oynanabilir içerikle doldurmak.

Hedefler:

- Ana dünya haritası ve bölge bağlantıları.
- Köy, orman, maden ve diğer başlangıç bölgelerinin içerik üretimi.
- Yeni biyomlar ve keşif alanları.
- Doğal arazi kompozisyonları ve geçişler.
- Yapılar, iç mekânlar ve etkileşimli nesneler.
- Kaynak dağılımı ve ekonomik lokasyonlar.
- NPC nüfusu, roller, fraksiyonlar ve ilişkiler.
- Ana görev ve yan görev zincirleri.
- Diyaloglar, hikâye olayları ve alternatif yollar.
- Eşya, tarif, ganimet ve üretim içerikleri.
- Düşmanlar ve karşılaşma paketleri.
- İçeriklerin görsel ve oynanış açısından kabul edilmesi.

Bu fazda harita/asset authoring aracı tamamlanmış kabul edilmeden büyük ölçekli manuel içerik üretimine başlanmamalıdır. Böylece içeriklerin doğrudan kod ve dağınık JSON düzenlemeleriyle üretilmesi önlenir.

## Faz 14 — RPG oynanış sistemlerinin tamamlanması

**Durum: PLANLANDI — Mevcut prototiplerin ürün seviyesine taşınması**

Amaç: Teknik dikey dilimi bütünlüklü RPG oynanışına dönüştürmek.

Hedef başlıklar:

- Sıra tabanlı combat kurallarının ve tur akışının tamamlanması.
- Karakter nitelikleri, seviye ilerlemesi ve gelişim.
- Yetenek, beceri ve karakter sınıfı sistemleri.
- Silah, zırh, aksesuar ve eşya etkileşimlerinin tamamlanması.
- Envanter, konteyner, ganimet ve ekipman akışlarının tutarlı hâle getirilmesi.
- Kilit, anahtar, lockpicking ve engel etkileşimlerinin oynanışa bağlanması.
- NPC ve düşman karşılaşmalarının içerik sistemiyle entegrasyonu.
- Görev, diyalog, itibar ve combat sonuçlarının tek oyun döngüsünde birleşmesi.
- Oyuncu kararlarının dünyaya ve NPC ilişkilerine etkisi.

Her mekanik kendi domain/application sözleşmesini, UI akışını, save/load davranışını ve testlerini taşımalıdır.

## Faz 15 — Görsel kalite, animasyon ve kullanıcı deneyimi

**Durum: PLANLANDI — Mevcut sunum altyapısının sanat üretimiyle doldurulması**

Amaç: Teknik renderer'ı tutarlı bir oyun sanat yönetimiyle birleştirmek.

Hedefler:

- Karakter ve NPC sprite/animasyon setleri.
- Biyomlara uygun zemin ve çevre varlıkları.
- Ağaç, bitki, kaya, su, yapı ve doğal nesne çeşitliliği.
- Oyuncu ve NPC hareket animasyonları.
- Combat, etkileşim ve üretim animasyonları.
- Katmanlı çevre ve derinlik sıralaması.
- Işık, hava durumu ve çevresel efektler.
- Kullanıcı arayüzü görsel bütünlüğü ve ölçeklenebilirliği.
- Ses efektleri, ortam sesleri ve müzik için ayrı içerik hattı.
- Performans ve bellek kullanımı.

Gerçek 3B dönüşüm bu fazın varsayılan hedefi değildir. 2.5D hedefinin Pygame üzerinde karşılanıp karşılanamadığı teknik ölçütlerle değerlendirilir.

## Faz 16 — Yaşayan dünya, NPC faaliyetleri ve simülasyon derinliği

**Durum: PLANLANDI — Mevcut actor/activity altyapısının genişletilmesi**

Amaç: Dünyanın yalnızca oyuncu etkileşimi sırasında değil, kendi kuralları içinde de yaşayan bir yapı kazanması.

Hedefler:

- NPC günlük rutinleri ve zaman çizelgeleri.
- NPC ihtiyaçları, hedefleri ve faaliyet seçimi.
- Kaynak toplama, üretim, taşıma ve ticaret faaliyetlerinin aktörlere bağlanması.
- NPC'lerin lokasyonlar arasında hareket etmesi ve rota kullanması.
- Fraksiyon, ilişki, itibar ve dünya olaylarının etkileşimi.
- Kaynakların yenilenmesi, tüketilmesi ve bölgesel ekonomiyle ilişkisi.
- Dünya olayları ve zaman tabanlı gelişmeler.
- Performanslı simülasyon güncelleme stratejisi.
- Oyuncu uzaktayken dünya simülasyonunun hangi ayrıntı seviyesinde ilerleyeceği.

Bu fazda gerçek zamanlı çok oyuncululuk veya çok iş parçacıklı simülasyon varsayılmaz. Deterministik tek oyunculu simülasyon temel alınır.

## Faz 17 — Dengeleme, bütünleşik test ve performans

**Durum: PLANLANDI**

Amaç: Bütün sistemleri birlikte çalışan, uzun süreli oyun oturumlarında tutarlı bir ürüne dönüştürmek.

Hedefler:

- Kaynak bolluğu ve tüketim dengesi.
- Üretim süresi, kapasite ve ekonomik fiyat dengesi.
- NPC ve görev ödüllerinin oyun ekonomisine etkisi.
- Combat zorluk eğrisi ve karakter gelişim dengesi.
- Görev zincirlerinin tamamlanabilirliği ve dallanma testleri.
- Uzun süreli simulation determinism testleri.
- Save/load, içerik güncellemesi ve migration regresyonları.
- Büyük harita ve çok sayıda aktör için performans testleri.
- Bellek, asset cache ve yükleme sürelerinin ölçülmesi.
- Kullanılabilirlik, erişilebilirlik ve hata geri bildirimi.
- Windows temiz kurulum ve paketlenmiş sürüm doğrulaması.

**Çıkış kriteri:** Kritik oynanış akışları yeni oyundan sonuca kadar tekrarlanabilir; kayıtlar güvenle yüklenebilir; içerik paketleri doğrulanabilir; bilinen kritik hata kalmamış olmalıdır.

## Faz 18 — Yayın hazırlığı ve dağıtım

**Durum: PLANLANDI**

Amaç: Eldoria'yı geliştirici ortamından bağımsız kurulabilen ve oynanabilen bir sürüme dönüştürmek.

Hedefler:

- Sürüm ve içerik paketi uyumluluk politikası.
- Temiz kurulum ve paketlenmiş uygulama.
- Oyuncu kayıtlarının güvenli konumu ve yedekleme.
- Log, hata raporu ve kurtarma davranışı.
- İlk açılış ve ayar yapılandırması.
- Lisans ve üçüncü taraf varlık envanteri.
- Kullanıcı kılavuzu ve sürüm notları.
- Release-candidate testleri.
- Son manuel oynanış kabulü.
- Dağıtım paketi ve güncelleme stratejisi.

---

# 8. Content Editor ile oyun arasındaki kesin ilişki

Eldoria Content Editor, oyunun içine gömülmüş bir geliştirme menüsü değildir. Kendi geliştirme dalında ilerleyen, oyun runtime'ından bağımsız içerik üretim uygulamasıdır.

Temel veri akışı:

```text
Eldoria Content Editor
        |
        | içerik oluşturma / düzenleme
        v
Ortak Content Core sözleşmeleri
        |
        | validate / save / migrate
        v
Sürümlü Content Package
        |
        | oyunun canonical loader'ı
        v
Eldoria RPG Runtime
        |
        v
Oyuncunun oynadığı dünya
```

## 8.1. Sorumluluk ayrımı

**Content Editor:**
- İçerik üretir, düzenler ve önizler.
- İçerik paketlerini yönetir.
- Kullanıcıya doğrulama hatalarını gösterir.
- İçeriği ortak servisler üzerinden güvenli biçimde kaydeder.

**Content Core:**
- Veri sözleşmelerini ve canonical modelleri sağlar.
- İçerik doğrulama, yükleme, kayıt ve migration sınırlarını korur.
- Editör ile oyunun aynı veriyi farklı yorumlamasını önler.

**Eldoria RPG:**
- İçerik paketini yükler.
- Oyun kurallarını ve simülasyonu çalıştırır.
- İçeriği oyuncuya sunar.
- Oyuncu ilerlemesini içerik tanımlarından ayrı kaydeder.

## 8.2. İçerik ile mekanik arasındaki sınır

Yeni bir NPC, görev, eşya, kaynak, harita, yapı, tarif veya diyalog eklemek mümkün olduğunca editörde yeni veri oluşturmakla yapılmalıdır.

Ancak yeni bir davranış veya oyun mekaniği gerekiyorsa, örneğin daha önce bulunmayan bir savaş kuralı ya da yeni bir etkileşim türü, bu önce oyun motorunda genel bir özellik olarak geliştirilir. Sonrasında Content Editor bu özelliği kullanan içerikleri üretir.

Hedef, hiçbir zaman oyun koduna ihtiyaç duyulmayacağı iddiası değildir. Hedef, her yeni içerik kaydı için özel kod yazma zorunluluğunu ortadan kaldırmak ve mekanikleri tekrar kullanılabilir hâle getirmektir.

## 8.3. Dal ve entegrasyon politikası

- Ana oyun geliştirmesi `demo_eldoria` üzerinde korunur.
- Content Editor ayrı geliştirme dalında yürütülür.
- Editörün hangi ortak sözleşmelere bağımlı olduğu açıkça belgelenir.
- Ortak veri sözleşmelerindeki değişiklikler iki taraf için uyumluluk denetiminden geçer.
- Editör kodu oyun runtime'ına gelişigüzel taşınmaz.
- Oyun tarafındaki entegrasyon kontrollü commit/PR ve test kapılarıyla yapılır.
- Editörün oyuncu dağıtımına dahil edilmesi hedeflenmez.

Dal adı, uygulama teknolojisi ve kesin proje dizin yapısı Faz 9'da teknik karar olarak sabitlenecektir.

---

# 9. Sürekli kalite ve faz yönetimi

Her gelecek faz aşağıdaki standart akışla yürütülür:

1. **Başlangıç denetimi:** İlgili kaynak kodu, mimari belgeler, testler ve mevcut dal HEAD'i incelenir.
2. **Kapsam sözleşmesi:** Yapılacaklar, yapılmayacaklar ve bağımlılıklar yazılır.
3. **Uygulama planı:** Alt aşamalar küçük ve doğrulanabilir işlere bölünür.
4. **Kod ve test:** Her değişiklikle birlikte ilgili testler eklenir veya güncellenir.
5. **Regresyon:** İlgili alt sistemler ve tam test paketi çalıştırılır.
6. **CI:** Desteklenen platformlarda otomatik doğrulama yapılır.
7. **Manuel kabul:** Görsel veya etkileşimli davranış söz konusuysa gerçek oyun/editör oturumu test edilir.
8. **Rapor:** Gerçek commit, test sayısı, workflow sonucu, bilinen sınırlamalar ve kalan işler kaydedilir.
9. **Kapanış:** Kabul kriterleri karşılanmadan faz kapatılmaz.

## 9.1. Test kanıtı kuralları

- Test komutu ve gerçek sonucu rapora yazılır.
- Test sayıları farklı workflow koşularından gelişigüzel toplanmaz.
- CI başarılı olması, manuel görsel kabulün yapıldığı anlamına gelmez.
- Manuel kabul, test çıktısı gibi gösterilmez; kullanıcı bildirimi olarak kaydedilir.
- Çalıştırılmayan test başarılı sayılmaz.
- Kod değişikliği yapılmayan dokümantasyon denetimi, yeni kod doğrulaması gibi sunulmaz.
- Bir fazın kapanış raporu o fazın gerçek kapsamını ve ertelenen işleri açıkça belirtir.

---

# 10. V2 ile birlikte yapılacak dokümantasyon düzeni

Master Roadmap V2, eski ana yol haritasının yerine proje seviyesinde yeni referans olacaktır.

Önerilen dokümantasyon düzeni:

- `docs/architecture/50-master-roadmap-v2.md`: Projenin yeni ana yol haritası.
- `docs/architecture/30-master-roadmap.md`: V1 tarihsel belge olarak korunur; başına V2 tarafından superseded edildiğini belirten not eklenmesi sonraki dokümantasyon işidir.
- `docs/architecture/00–49`: Mevcut teknik sözleşmeler ve tarihsel faz belgeleri korunur.
- `reports/phase-*`: Faz uygulama, denetim ve kapanış kanıtları olarak korunur.
- Yeni fazlar için kapsam/plan ve kapanış raporları ayrı dosyalarda tutulur.

V2, eski belgeleri silme veya yeniden yazma izni vermez. Tarihsel kararların izlenebilirliği korunmalıdır.

---

# 11. Açık kararlar ve risk kayıtları

Aşağıdaki konular V2 ile kendiliğinden çözülmüş sayılmaz:

1. Content Editor'ın masaüstü UI framework ve teknoloji seçimi.
2. Editörün ayrı dal adı ve ortak kod/sözleşme paylaşımının tam Git stratejisi.
3. Kare haritaların gelecekte dönüştürülüp dönüştürülmeyeceği.
4. Kare harita için yeni authoring ve placement modelinin gerekip gerekmediği.
5. Hücre tabanlı occupancy'nin hangi nesnelerde alt-hücre hassasiyetli collision'a yükseltileceği.
6. Üretim zinciri orchestration state'inin save/load kapsamına alınıp alınmayacağı.
7. NPC günlük rutinleri ve karar verme sisteminin simülasyon maliyeti.
8. Combat'ın nihai tur, aksiyon, beceri ve denge kuralları.
9. Takvim, mevsim, hava durumu ve gerçek zaman/simülasyon zamanı ilişkisinin son tasarımı.
10. Pygame 2.5D sunumunun uzun vadeli görsel kalite ve performans hedeflerini karşılayıp karşılamadığı.
11. Tam sanat ve ses varlıklarının üretim/dağıtım biçimi.
12. Oyuncu sürümünün hedef platformları ve dağıtım yöntemi.

Bu kararlar ihtiyaç duyulan fazda, ilgili teknik kanıt ve ürün hedefleriyle birlikte alınmalıdır.

---

# 12. V2'nin başlangıç noktası ve ilk sonraki adım

Master Roadmap V2'nin referans aldığı proje durumu:

- Core 2.1 mimari kapanışı tamamlanmıştır.
- Kaynak, üretim, ekonomi, aktör, NPC, görev, diyalog ve ilk combat altyapıları mevcuttur.
- Pygame ile oynanabilir bir dikey dilim vardır.
- Altıgen dünya geometri, harita, hareket, geçiş ve sunum altyapısı tamamlanmıştır.
- Aşama 7 doğal çevre sunum çalışması kapanmıştır.
- Aşama 8 Content Editor altyapı hazırlığı kapanmıştır.
- Content Editor uygulaması ve tüm içerik authoring ekranları henüz geliştirilmemiştir.
- Oyunun tam içerik üretimi, nihai görsel kalite, oynanış derinliği, dengeleme ve yayın hedefleri gelecektedir.

**Bir sonraki ana geliştirme odağı Faz 9 — Eldoria Content Editor proje ayrıştırması ve mimari tasarımıdır.**

Faz 9 başlamadan önce bu V2 belgesi ile ilgili teknik sözleşmeler birlikte referans alınmalı; mevcut tamamlanmış altyapı yeniden tasarlanmadan editörün bağımsız mimarisi oluşturulmalıdır.

---

# 13. Kaynak belgeler

Bu yol haritasının hazırlanmasında `demo_eldoria` dalındaki aşağıdaki temel belgeler esas alınmıştır:

## Proje ve ana mimari
- `README.md`
- `pyproject.toml`
- `docs/architecture/00-core-2.0-baseline.md`
- `docs/architecture/01-package-layout.md`
- `docs/architecture/02-dependency-rules.md`
- `docs/architecture/12-implementation-plan.md`
- `docs/architecture/22-core-2.0-freeze.md`
- `docs/architecture/23-core-2.1-closure.md`
- `docs/architecture/30-master-roadmap.md`

## Gameplay ve içerik
- `docs/architecture/24-content-driven-npc-quest-rules.md`
- `docs/architecture/25-economy-production-roadmap.md`
- `docs/architecture/26-production-chain-orchestration.md`
- `docs/architecture/27-core15-production-economy.md`
- `docs/architecture/28-core16-playable-gameplay-loop.md`
- `docs/architecture/29-core17-world-actors-activities.md`
- `docs/architecture/34-content-data-contract.md`
- `docs/content/map-authoring.md`

## Altıgen dünya ve sunum
- `docs/architecture/35-hexagonal-world-architecture.md`
- `docs/architecture/36-hexagonal-world-migration-plan.md`
- `docs/architecture/37-hexagonal-world-dependency-inventory.md`
- `docs/architecture/38-hex-geometry-stage1.md`
- `docs/architecture/39-hex-local-map-data-model.md`
- `docs/architecture/40-hex-world-map-stage3.md`
- `docs/architecture/41-hex-movement-stage4.md`
- `docs/architecture/42-main-screen-hex-runtime-integration.md`
- `docs/architecture/43-pygame-hex-presentation-stage6.md`
- `docs/architecture/38-phase-7-visual-baseline.md`
- `docs/architecture/39-phase-7-natural-world-architecture.md`
- `docs/architecture/40-tree-skeleton-contract.md`
- `docs/architecture/43-articulated-tree-sprite-rig.md`

## Content Editor altyapısı
- `docs/architecture/44-content-pipeline-audit.md`
- `docs/architecture/45-presentation-content-separation.md`
- `docs/architecture/46-presentation-geometry-contract.md`
- `docs/architecture/47-content-validation-and-safe-loading.md`
- `docs/architecture/48-presentation-content-safe-persistence.md`
- `docs/architecture/49-presentation-content-service-api.md`
- `reports/phase-7-completion-report.md`
- `reports/phase-8-content-editor-foundation-plan.md`
- `reports/phase-8-completion-report.md`

Bu kaynak listesi, V2'nin dayandığı temel belge envanteridir. İlgili faza başlanırken kaynak kodu ve testler ayrıca denetlenmelidir.

---

**Belge sonu — Eldoria RPG Master Roadmap V2**
