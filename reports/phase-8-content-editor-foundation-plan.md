# ELDORIA RPG — AŞAMA 8
# CONTENT EDITOR İÇİN ALTYAPI HAZIRLIĞI
## Ayrıntılı Teknik Kapsam, Uygulama Planı ve Kabul Sözleşmesi

| Alan | Değer |
|---|---|
| Proje | Eldoria — Kaynak Yönetimi RPG |
| Depo | `trippes/RPG_KAYNAK_YONETIMI` |
| Çalışma dalı | `demo_eldoria` |
| Aşama | 8 — Content Editor Altyapısı |
| Belge türü | Uygulama öncesi teknik kapsam ve yol haritası |
| Hazırlanma tarihi | 13 Kasım 2026 |
| Durum | **PLANLANDI — UYGULAMA HENÜZ BAŞLAMADI** |
| Ana hedef | Gelecekte geliştirilecek Content Editor için güvenilir içerik, varlık, yerleşim, doğrulama ve kayıt altyapısını hazırlamak |

---

## 0. Bu belgenin amacı ve bağlayıcılığı

Bu belge, Aşama 8'in sınırlarını, teknik hedeflerini, alt aşamalarını, beklenen çıktıları, doğrulama ölçütlerini ve korunacak mimari sözleşmeleri tanımlar.

Aşama 8'in amacı bir Content Editor uygulaması üretmek değildir. Amaç, ileride geliştirilecek editörün oyun motorunun iç işleyişine doğrudan ve kontrolsüz biçimde müdahale etmeden içerik oluşturabilmesini sağlayacak veri ve servis altyapısını hazırlamaktır.

Bu nedenle Aşama 8 sonunda kullanıcı harita düzenleyebileceği yeni bir pencere, araç çubuğu veya oyun içi düzenleme modu görmeyecektir. Bunun yerine, editörün ileride çağırabileceği kararlı ve test edilebilir altyapı bileşenleri bulunacaktır.

Bu belge uygulama sırasında teknik referans olarak kullanılacaktır. Aşama 6.1'de gerçek depo kodu yeniden denetlenmeli; burada adı geçen mevcut sınıf, dosya veya sorumlulukların gerçek karşılıkları doğrulanmalıdır. Kod tabanında bulunmayan bir sınıfın var olduğu varsayılmayacak, aynı işi yapan mevcut bileşen varsa ikinci bir paralel sistem oluşturulmayacaktır.

**Önemli karar:** Aşama 8, Content Editor'ün altyapısını hazırlar; Content Editor'ü yazmaz.

## 1. Aşama 7'den devralınan temel kararlar

Aşama 7 kapanış raporu ve `docs/architecture/39-phase-7-natural-world-architecture.md` belgesi, Aşama 8'in başlangıç mimari referanslarıdır.

Aşağıdaki ilkeler korunacaktır:

1. **Simülasyon altıgen, görsel dünya doğaldır.** Hex koordinatları motorun teknik organizasyonudur; oyuncuya gösterilen dünya görünümü hücre ızgarasına dönüştürülmeyecektir.
2. `HexWorldRuntime`, axial koordinatlar, `WorldTransform`, kamera, hareket, yol bulma, çarpışma ve harita geçişleri kendi sorumluluklarında kalacaktır.
3. Kare harita altyapısı korunacak; yeni içerik altyapısı yalnızca hex haritalara özgü varsayımlarla tasarlanmayacaktır.
4. PNG dosyası ile PNG'yi sahnede kullanmak için gereken metadata birbirinden ayrılacaktır.
5. Bir nesnenin görsel boyutu ile fiziksel çarpışma alanı birbirinden bağımsız tanımlanacaktır.
6. Nesnenin `anchor/pivot` noktası, zemin teması ve derinlik sıralaması için anlamlı bir referans olarak kullanılacaktır.
7. Çevre nesnelerinin çizim sırası mevcut depth/Y-sort düzeniyle uyumlu kalacaktır.
8. Gerçek PNG varlıkları nihai içerik olarak kullanılacaktır. Prosedürel siluetler yalnızca eksik içerik ve geliştirme güvenliği için fallback olabilir.
9. Ağaç atlası/rig altyapısı korunabilir; ancak Aşama 7'de kabul edilen doğal tek PNG ağaç çizimi varsayılan davranış olarak kalacaktır.
10. Aşama 8, önceki aşamalarda kabul edilmiş oyun davranışlarını yeniden tasarlama aşaması değildir.

### 1.1. Aşama 7'den gelen mevcut veri örneği

`content/demo_eldoria/presentation_assets.json` dosyasında şu anda `assets` ve `objects` koleksiyonları birlikte bulunmaktadır.

Varlık tanımlarında görülen alanlar:
- `asset_id`
- `path`
- `width`, `height`
- `scale`
- `anchor`
- `collision`
- `placement`
- `depth_offset`

Harita nesnesi yerleşimlerinde görülen alanlar:
- `object_id`
- `asset_id`
- `map_id`
- `q`, `r`
- `offset_x`, `offset_y`
- `footprint`
- `collision_box`
- `layer`
- `kind`

Bu yapı Aşama 8 için başlangıç girdisidir. İlk iş bu alanları körü körüne yeniden adlandırmak değil; mevcut yükleyicilerin, renderer'ın, AssetManager'ın ve testlerin gerçekte hangi alanları nasıl kullandığını ortaya çıkarmaktır.

Özellikle `width` ve `height` değerlerinin sıfır olabildiği mevcut örneklerde boyutların PNG'den mi, metadata'dan mı, yoksa başka bir katmandan mı çözüldüğü tespit edilmelidir. Sıfır değerinin anlamı belgelenmeden yeni şema sözleşmesine taşınmamalıdır.

## 2. Aşama 8'in ana hedefleri

Aşama sonunda aşağıdaki yetenekler kod seviyesinde ve otomatik testlerle kullanılabilir olmalıdır:

- Varlık tanımlarının tek ve merkezi bir katalog sözleşmesi üzerinden okunması.
- Görsel dosya ile varlık metadata'sının birbirinden bağımsız yönetilmesi.
- Harita yerleşimlerinin varlık kataloğundan ayrı bir veri kümesi olarak okunabilmesi.
- Asset kimliklerinin kararlı, benzersiz ve doğrulanabilir olması.
- Anchor, pivot, scale, depth, layer, collision ve footprint değerlerinin açık ve tutarlı anlamlara sahip olması.
- PNG yolu, dosya varlığı, dosya türü ve görsel boyutlarının doğrulanabilmesi.
- İçerik verisinin yükleme öncesinde şema ve referans kontrollerinden geçirilebilmesi.
- Hatalı bir içerik dosyasının geçerli mevcut içeriğin üzerine yazılmasının engellenmesi.
- İçerik paketlerinin sürüm bilgisinin ve gelecekteki şema geçişlerinin yönetilebilmesi.
- Oyun runtime'ının içerik verisini editörün varlığından bağımsız olarak yükleyebilmesi.
- Gelecekteki Content Editor'ün kullanabileceği UI bağımsız servis/API sınırlarının tanımlanması.
- Eski içeriklerin ve kare/hex harita davranışlarının geriye dönük uyumluluk testleriyle korunması.

## 3. Aşama kapsamı ve kapsam dışı işler

### 3.1. Kapsam dahilinde

- Mevcut içerik/asset/placement kodunun denetlenmesi.
- Asset Catalog veri sözleşmesinin netleştirilmesi ve gerekli altyapının düzenlenmesi.
- Asset metadata ile harita yerleşimlerinin ayrıştırılması.
- Kimlik, yol, boyut, ölçek, anchor, pivot, depth, layer, collision ve footprint sözleşmelerinin standartlaştırılması.
- İçerik yükleme ve doğrulama sınırlarının belirginleştirilmesi.
- Güvenli kayıt ve şema sürümleme altyapısı.
- Gelecekteki editörün kullanacağı UI bağımsız uygulama servisleri.
- Birim, entegrasyon ve regresyon testleri.
- Mimari belgeler ve Aşama 8 kapanış raporu.

### 3.2. Kesinlikle kapsam dışında

- Content Editor penceresi, paneli, menüsü veya araç çubuğu geliştirmek.
- Fareyle harita üzerinde nesne seçme, sürükleme, bırakma veya yerleştirme arayüzü yapmak.
- Harita önizleme/asset önizleme penceresi oluşturmak.
- Oyun içine düzenleme modu veya editör kısayolu eklemek.
- Oyuncunun normal oyun arayüzünü değiştirmek.
- Yeni ağaç, kaya, çalı, çiçek veya bina sanat varlıkları üretmek.
- Mevcut PNG'leri yeniden çizmek veya görsel tasarımlarını değiştirmek.
- Ağaç rig/atlas animasyonunu varsayılan olarak etkinleştirmek.
- Su, ateş, duman, yaprak parçacıkları veya ileri çevre animasyonları geliştirmek.
- Hex geometri, axial koordinat, hareket, kamera, çarpışma veya pathfinding sistemini yeniden yazmak.
- Kare harita sistemini kaldırmak veya hex sisteme dönüştürmek.
- Godot/3B motor geçişi yapmak.
- NPC, görev, savaş, ekonomi veya envanter sistemlerine yeni özellik eklemek.
- Bu aşama için ihtiyaç doğmadıkça büyük ölçekli performans optimizasyonu yapmak.

Kapsam dışı bir ihtiyaç tespit edilirse doğrudan eklenmeyecek; gerekçesi ve etkisi raporlanıp ayrı karar alınacaktır.

## 4. Mimari hedef: editörden bağımsız içerik altyapısı

Aşama 8'in tasarımında dört ayrı sorumluluk alanı bulunmalıdır.

### 4.1. Asset dosyaları

PNG ve ileride desteklenebilecek diğer görsel dosyalarıdır. Dosyanın kendisi; oyun içindeki konum, çarpışma veya harita kimliği gibi sahne verilerini taşımaz.

Örnek sorumluluklar:
- Dosyanın depoda bulunması.
- Dosya yolunun güvenli ve göreli olması.
- Dosya formatının doğrulanması.
- PNG'nin açılabilir olması.
- Genişlik/yükseklik gibi kaynak özelliklerinin okunması.

### 4.2. Asset metadata / katalog

Bir görselin oyun motorunda nasıl yorumlanacağını tanımlar.

Örnek sorumluluklar:
- Benzersiz `asset_id`.
- Dosya yolu.
- Görsel ölçü veya ölçünün kaynaktan okunma kuralı.
- Ölçek.
- Anchor/pivot.
- Varsayılan depth/layer davranışı.
- Collision tanımı veya collision bulunmadığını açıkça belirtme.
- Varlık kategorisi/türü gibi editörün ileride filtreleme yapmasına yarayacak tanımlayıcı bilgiler.

Katalog, harita üzerindeki tekil konumları saklamamalıdır.

### 4.3. Harita yerleşim verisi

Bir varlığın belirli bir haritada nerede ve hangi yerel ayarlarla kullanılacağını tanımlar.

Örnek sorumluluklar:
- Benzersiz `object_id`.
- Referans verilen `asset_id`.
- `map_id`.
- Harita koordinatı veya mevcut harita modelinin gerektirdiği konum.
- Hücreye göre yerel piksel ofseti.
- Gerekirse örnek bazlı ölçek/anchor/depth düzeltmesi.
- Footprint ve instance collision override.
- Layer/kind gibi mevcut renderer'ın gerektirdiği sunum verileri.

Yerleşim verisi PNG dosyasını veya görselin tüm metadata'sını kopyalamamalı; katalogdaki varlığa referans vermelidir.

### 4.4. Runtime ve servis katmanı

Runtime, içerik dosyalarını doğrudan farklı ekranlardan veya editör kodundan okumamalıdır. Mevcut yükleme mimarisi denetlenerek tek sorumlu erişim sınırı oluşturulmalıdır.

Hedef sorumluluklar:
- Asset metadata yükleme.
- Harita yerleşimi yükleme.
- Asset ID referanslarını çözümleme.
- İçerik doğrulama.
- Runtime için hazır, doğrulanmış içerik modeli sunma.
- Güvenli kayıt ve şema geçişi işlemleri.

Bu sınır UI teknolojisine bağımlı olmamalıdır. İleride Pygame içinden, ayrı bir masaüstü editörden veya başka bir araçtan kullanılabilmelidir.

## 5. Önerilen veri sözleşmeleri

Bu bölüm nihai sınıf adlarını zorunlu kılmaz. Aşama 6.1'de mevcut uygulama incelendikten sonra, gerçek kod tabanına en az müdahale eden karşılık seçilecektir. Buradaki alanlar anlamsal sözleşmedir.

### 5.1. Asset tanımı

Bir asset kaydı aşağıdaki kavramları açık biçimde temsil etmelidir:

| Alan | Anlam | Kural |
|---|---|---|
| `asset_id` | Kalıcı varlık kimliği | Benzersiz, boş olmayan, kararlı |
| `path` | Görsel dosya yolu | İçerik köküne göre göreli, güvenli |
| `category` | İçerik kategorisi | Kontrollü veya doğrulanabilir değer |
| `source_size` | Kaynak PNG boyutu | Dosyadan okunabilir; metadata ile çelişmemeli |
| `scale` | Varsayılan çizim ölçeği | Sonlu ve pozitif |
| `anchor` | Normalize zemin/pivot referansı | İki bileşenli, tanımlı aralık |
| `depth_offset` | Derinlikte ince ayar | Sonlu sayısal değer |
| `layer` | Varsayılan çizim katmanı | Renderer'ın tanıdığı katman |
| `collision` | Varsayılan çarpışma verisi | Açıkça yok veya geçerli geometri |
| `placement` | Yerleşim davranışı | Mevcut yerleştirme modeline uygun |

Notlar:
- Kaynak görselin gerçek boyutu ile ekranda çizilecek boyut karıştırılmamalıdır.
- Ölçek, PNG dosyasını fiziksel olarak yeniden boyutlandıran bir işlem değildir; renderer'ın çizim ölçeğidir.
- Anchor, çarpışma kutusu değildir.
- Anchor'ın normalize koordinat mı, piksel koordinatı mı olduğu tek bir sözleşmeyle belirlenmelidir. Mevcut kodun kullandığı anlam denetlenmeden değiştirilmemelidir.
- `collision: null` ile collision alanının hiç bulunmaması aynı anlama geliyorsa bu davranış belgelenmeli; farklı anlama geliyorsa ikisi ayrıştırılmalıdır.

### 5.2. Harita nesnesi / placement tanımı

| Alan | Anlam | Kural |
|---|---|---|
| `object_id` | Tekil yerleşim kimliği | Harita içinde veya paket genelinde benzersizliği açık |
| `asset_id` | Asset Catalog referansı | Var olan asset'e bağlanmalı |
| `map_id` | Hedef harita | Mevcut harita kimliğiyle eşleşmeli |
| `position` | Harita koordinatı | Harita tipine uygun biçimde temsil edilmeli |
| `offset` | Hücre/konum merkezine göre yerel fark | Sonlu sayısal değer |
| `scale_override` | İsteğe bağlı örnek ölçeği | Yoksa asset varsayılanı |
| `anchor_override` | İsteğe bağlı örnek anchor | Yoksa asset varsayılanı |
| `depth_offset` | Örnek bazlı derinlik farkı | Yoksa asset varsayılanı |
| `footprint` | Simülasyon/yerleşim kapladığı alan | Mevcut harita modeline uygun |
| `collision_override` | Örnek bazlı çarpışma farkı | Açık ve doğrulanabilir |
| `layer` | Çizim katmanı | Mevcut renderer ile uyumlu |
| `kind` | Nesnenin semantik türü | Kontrollü veya belgelenmiş |

Hex yerleşimlerde mevcut `q/r` alanları korunabilir; kare harita yerleşimlerinde ise mevcut kare koordinat modeli kullanılmalıdır. Tek bir koordinat biçimini tüm harita türlerine zorla uygulamak yasaktır.

Aynı metadata hem katalogda hem placement içinde gereksiz yere çoğaltılmamalıdır. Override alanları yalnızca tek bir yerleşimin asset varsayılanından ayrılması gerektiğinde kullanılmalıdır.

### 5.3. Şema sürümleme

İçerik dosyaları açık bir şema sürümü taşımalıdır. Mevcut `schema_version: 1` alanı başlangıç noktasıdır.

Kurallar:
- Şema sürümü eksikse mevcut içeriklerin nasıl ele alınacağı belgelenmelidir.
- Desteklenmeyen gelecek sürümler sessizce yüklenmemelidir.
- Eski sürümden yeni sürüme geçiş açık ve test edilebilir olmalıdır.
- Migration işlemi kaynak dosyayı doğrudan ve geri döndürülemez biçimde ezmemelidir.
- Şema geçişi ile oyun içeriğinin anlamsal değişikliği birbirinden ayrılmalıdır.
- Her migration için eski sürüm girdisi, yeni sürüm çıktısı ve doğrulama testi bulunmalıdır.

## 6. Alt aşamalar ve ayrıntılı iş planı

## 6.1 — Mevcut içerik altyapısının teknik denetimi

**Amaç:** Yeni bir sistem yazmadan önce gerçek kod tabanındaki varlık, dosya yükleme, yerleşim ve doğrulama akışını çıkarmak.

İncelenecek alanlar:
1. `AssetCatalog` veya aynı sorumluluğu üstlenen mevcut sınıf/modül.
2. `AssetManager` veya görsel yükleme/cache sorumluluğu.
3. `presentation_assets.json` yükleme ve parse akışı.
4. PNG dosya yollarının nasıl çözüldüğü.
5. Asset metadata ile renderer arasındaki veri akışı.
6. Anchor/pivot değerlerinin koordinat dönüşümünde nasıl kullanıldığı.
7. Scale değerinin hangi aşamada uygulandığı.
8. Depth sort anahtarının hangi alanlardan üretildiği.
9. Collision/collision_box değerlerinin hangi sistem tarafından tüketildiği.
10. Footprint ve harita yerleşim koordinatlarının anlamı.
11. Hex ve kare haritaların içerik verisiyle ilişkisi.
12. Ağaç atlası/rig dosyalarının ana asset yükleme hattından bağımsızlığı.
13. Mevcut testlerin içerik dosyası bozulması, eksik PNG ve geçersiz referansları ne ölçüde kapsadığı.

Yapılacak işler:
- Gerçek dosya/sınıf/modül envanteri çıkarılacak.
- Bir PNG'nin dosyadan ekrana kadar izlediği yükleme zinciri belgelenecek.
- Bir harita nesnesinin JSON kaydından renderer'a kadar izlediği placement zinciri belgelenecek.
- Mevcut veri alanlarının tüketicileri ve varsayılanları listelenecek.
- Çakışan sorumluluklar ve eksik doğrulama noktaları tespit edilecek.
- Gereksiz ikinci bir Asset Catalog veya AssetManager oluşturulması önlenecek.

Teslimatlar:
- `docs/architecture/44-content-pipeline-audit.md` benzeri bir denetim belgesi (mevcut numaralandırma kontrol edilerek uygun ad verilecek).
- Mevcut akış diyagramı.
- Alan/kullanıcı (consumer) matrisi.
- Aşama 8'in geri kalanında uygulanacak kesin dosya/sınıf listesi.

Kabul ölçütleri:
- Hiçbir temel içerik akışı varsayıma dayanmamalı.
- Her kritik metadata alanının nerede üretildiği ve nerede tüketildiği bilinmeli.
- Hex ve kare harita ayrımları belgelenmeli.
- Denetim tamamlanmadan veri şeması veya yükleyici yeniden yazılmamalı.

## 6.2 — Asset Catalog sözleşmesinin sağlamlaştırılması

**Amaç:** PNG varlıklarının tekil, kararlı ve doğrulanabilir tanımlara sahip olmasını sağlamak.

Yapılacak işler:
- Mevcut katalog yapısı denetim sonuçlarına göre düzenlenecek.
- Asset kimliklerinin benzersizliği doğrulanacak.
- Katalogdan asset ID ile güvenilir erişim sağlanacak.
- Aynı asset'in birden fazla haritada kullanılabilmesi korunacak.
- Asset kaydı ile harita yerleşim kaydı ayrılacak.
- Kategori/tür bilgisinin anlamı ve izin verilen değerleri belirlenecek.
- PNG yolu için içerik köküne göre çözümleme kuralı belirlenecek.
- Mutlak dosya yolu, üst dizine kaçış (`..`) ve içerik kökü dışına çıkış engellenecek.
- Kaynak PNG'nin varlığı, okunabilirliği ve formatı kontrol edilecek.
- Gerçek kaynak boyutu ile metadata boyutunun uyuşması denetlenecek.
- Mevcut cache/AssetManager davranışı korunacak; katalog her sorguda PNG'yi yeniden yüklememeli.
- Eksik PNG durumunda mevcut deterministik fallback davranışı korunmalı ve hata/uyarı görünür olmalı.

Beklenen servis davranışları:
- Asset ID ile tanım sorgulama.
- Tüm asset tanımlarını listeleme.
- Kategoriye göre filtreleme için UI bağımsız veri sunma.
- Asset kaydının doğruluğunu kontrol etme.
- Katalog verisini kontrollü biçimde yeniden yükleme (mevcut mimari uygunsa).

Bu aşamada kategori listesi bir editör arayüzü değildir; gelecekte editörün listeleme/filtreleme yapabilmesi için veri sözleşmesidir.

Kabul ölçütleri:
- Yinelenen asset ID reddedilir.
- Bulunmayan asset ID açık hata üretir.
- Güvenli olmayan dosya yolu reddedilir.
- Eksik veya bozuk PNG oyunu beklenmedik biçimde çökertmez; fallback ve tanımlı hata davranışı korunur.
- Aynı PNG/asset tekrar kullanıldığında mevcut cache politikası bozulmaz.

## 6.3 — Metadata ve yerleşim verilerinin ayrıştırılması

**Amaç:** Bir görsel varlığın tanımıyla o varlığın harita üzerindeki örneklerini birbirinden ayırmak.

Yapılacak işler:
- Asset katalog verisi ve map placement verisi ayrı sorumluluklara ayrılacak.
- Dosyaların fiziksel olarak ayrılması, 6.1 denetiminden sonra en düşük riskli biçimde kararlaştırılacak.
- `presentation_assets.json` geriye dönük uyumluluk planı olmadan bir anda kaldırılmayacak.
- Yeni placement verileri asset ID referansı kullanacak.
- Harita nesnesi, PNG yolunu kendi içinde tekrar taşımayacak.
- Asset varsayılanları ile placement override değerleri arasındaki öncelik sırası tanımlanacak.
- Bir asset'in birden çok haritada kullanılabilmesi test edilecek.
- Bir asset'in farklı örneklerinin farklı offset/depth/collision override kullanabilmesi sağlanacak.
- Harita tipine göre koordinat alanları korunacak; hex q/r ile kare x/y birbirine karıştırılmayacak.

Önerilen öncelik kuralı:
1. Placement üzerinde açıkça belirtilmiş geçerli override.
2. Asset katalog varsayılanı.
3. Mevcut renderer'ın belgelenmiş güvenli varsayılanı.

Bu öncelik yalnızca ilgili alan için uygulanır; örneğin placement collision override içermiyorsa asset collision tanımı kullanılır. Collision tanımı da yoksa mevcut oyun davranışının açıkça belirlenmiş karşılığı devreye girer.

Kabul ölçütleri:
- Placement'ın referans verdiği asset mevcut olmalı.
- Placement haritası mevcut bir map ID ile eşleşmeli.
- Aynı asset farklı placement kayıtlarında tekrar kullanılabilmeli.
- Override bulunmayan alanlar asset varsayılanından çözülmeli.
- Mevcut demo haritalarının nesne görünümü ve konumları değişmemeli.
- Kare harita içerik akışı regresyona uğramamalı.

## 6.4 — Konum, anchor, pivot, scale, depth ve collision standartları

**Amaç:** İleride editörün göstereceği ve düzenleteceği değerlerin teknik anlamlarını belirsizlikten kurtarmak.

### Anchor ve pivot
- Anchor'ın hangi koordinat uzayında tanımlandığı belgelenmeli.
- Normalize (0–1) değerler ile piksel değerleri karıştırılmamalı.
- Görselin zeminle temas noktası ile sprite dönüşüm pivot'u aynı değilse ayrı kavramlar olarak modellenmeli.
- Mevcut sistem tek bir anchor kullanıyorsa bu aşamada ayrıştırma ancak gerçek ihtiyaç ve geriye dönük uyumluluk testiyle yapılmalı.
- Anchor değişikliğinin depth sort ve çizim konumuna etkisi test edilmeli.

### Scale ve kaynak boyutu
- PNG'nin kaynak genişlik/yüksekliği değiştirilmeden korunmalı.
- Draw scale sonlu ve pozitif olmalı.
- Aşırı küçük/büyük değerler için makul teknik sınır belirlenmeli.
- Kaynak boyut, ölçekli çizim boyutu ve collision boyutu birbirinden ayrılmalı.
- Cache anahtarı mevcut sistemin ihtiyaçlarına göre kaynak kimliği ve ölçek gibi girdileri güvenli biçimde dikkate almalı.

### Depth ve layer
- Depth sort için ana referansın anchor/zemin noktası mı yoksa başka bir mevcut nokta mı olduğu denetimle kesinleştirilmeli.
- `depth_offset` ince ayar olarak kalmalı; ana sıralama anahtarının yerini almamalı.
- Layer değerleri tanımlı ve belgelenmiş olmalı.
- Aynı derinlikte kalan nesneler için stabil ikincil sıralama anahtarı korunmalı.
- Oyuncu–ağaç ön/arka kabul davranışı değişmemeli.

### Collision ve footprint
- Görsel bounding box, collision box ve harita footprint'i ayrı kavramlardır.
- Collision alanı anchor'a göre hangi koordinat uzayında ifade ediliyorsa belgelenmeli.
- Negatif genişlik/yükseklik, sıfır alan veya geçersiz koordinatlar doğrulanmalı.
- Collision bulunmaması geçerli bir seçenek olabilir; açık biçimde ifade edilmelidir.
- Footprint, hex/kare simülasyonun hücre doluluk kurallarıyla uyumlu kalmalıdır.
- Aşama 7'de gözlenen ağaca yaklaşma mesafesi konusu not edilmeli; ancak bu aşamada hareket/çarpışma motoru yeniden yazılmamalıdır. Gerekirse metadata sözleşmesinin hassasiyeti ölçülür ve ayrı bir sonraki aşamaya öneri hazırlanır.

Kabul ölçütleri:
- Her alanın birimi ve koordinat uzayı belgelenmiş olmalı.
- Geçersiz sayısal değerler doğrulamadan geçmemeli.
- Görsel boyut değişimi collision alanını kendiliğinden ve kontrolsüz biçimde değiştirmemeli.
- Derinlik sıralaması ve mevcut hareket davranışı korunmalı.

## 6.5 — İçerik doğrulama ve güvenli yükleme

**Amaç:** Hatalı içerik verisinin oyunun çalışma anında belirsiz davranışlara veya veri kaybına yol açmasını önlemek.

Doğrulama katmanları:

1. **Dosya doğrulaması:** Dosya bulunuyor mu, okunabiliyor mu, beklenen formatta mı?
2. **JSON doğrulaması:** Dosya sözdizimi geçerli mi, kök veri tipi doğru mu?
3. **Şema doğrulaması:** Zorunlu alanlar, türler ve sürüm kuralları sağlanıyor mu?
4. **Kimlik doğrulaması:** Asset/object/map ID değerleri boş veya yinelenmiş mi?
5. **Referans doğrulaması:** Placement asset ve map referansları geçerli mi?
6. **Geometri doğrulaması:** Anchor, scale, offset, collision, footprint ve koordinatlar geçerli mi?
7. **Runtime uyumluluğu:** Renderer ve harita sisteminin desteklediği değerler mi?
8. **Paket bütünlüğü:** İçerik paketi tutarlı bir bütün olarak yüklenebiliyor mu?

Hata davranışı:
- Hata mesajı dosya yolunu ve mümkünse alan/nesne kimliğini belirtmeli.
- Sessizce hatalı değerleri başka değerlere dönüştürmekten kaçınılmalı.
- Güvenli fallback yalnızca mevcut mimarinin tanımlı olduğu durumlarda kullanılmalı.
- Kritik içerik hatasında yarım yüklenmiş katalog/placement seti runtime'a sunulmamalı.
- Bir dosyanın geçerli eski sürümü, yeni ve geçersiz veriyle ezilmemeli.
- Geliştirici/test ortamında teşhis edilebilir hata; normal oyun ortamında kontrollü hata davranışı ayrıştırılmalı.

Kabul ölçütleri:
- Bozuk JSON testleri.
- Eksik PNG testleri.
- Yinelenen ID testleri.
- Bilinmeyen asset/map referansı testleri.
- Geçersiz scale/anchor/collision/footprint testleri.
- Desteklenmeyen schema version testleri.
- Hatalı veri nedeniyle geçerli dosyanın kaybolmadığını gösteren güvenli kayıt testleri.

## 6.6 — Güvenli kayıt ve şema geçişi altyapısı

**Amaç:** Gelecekte editörün üreteceği içerik dosyalarının kontrollü ve kurtarılabilir biçimde yazılabilmesini sağlamak.

Bu aşamada editörün Save düğmesi yapılmayacaktır. Bunun yerine UI bağımsız kayıt servisinin güvenilirliği hazırlanacaktır.

Hedef davranış:
- Kaydedilecek veri önce bellekte doğrulanır.
- Şema sürümü ve referans bütünlüğü kontrol edilir.
- JSON deterministik ve okunabilir biçimde serileştirilir.
- Geçici dosyaya yazma ve mümkün olan platformlarda atomik değiştirme yaklaşımı değerlendirilir.
- Başarısız yazımda orijinal dosya korunur.
- Gerekli görülürse önceki dosya için yedek/geri dönüş stratejisi belirlenir.
- Yazma işlemi tamamlanmadan runtime'ın kısmi dosya görmesi engellenir.
- Dosya yolu içerik kökü dışına çıkamaz.
- Dosya kodlaması açıkça UTF-8 olarak belirlenir.
- Birden fazla dosyaya yayılan katalog/placement kaydında tutarlılık ve hata sonrası davranış belgelenir.

Migration davranışı:
- Kaynak sürüm tanınır.
- Migration fonksiyonu girdiyi kontrollü biçimde yeni veri modeline dönüştürür.
- Sonuç yeni şemaya göre doğrulanır.
- Migration başarısızsa kaynak dosya değişmeden kalır.
- Migration tekrar çalıştırıldığında aynı veriyi bozmamalıdır (idempotent davranış hedeflenir).
- Eski içerik dosyaları için otomatik migration mı, açık komut mu kullanılacağı mevcut proje iş akışına göre belirlenir.

Kabul ölçütleri:
- Başarılı kayıtta dosya yeniden yüklenebilir.
- Başarısız kayıtta önceki geçerli dosya korunur.
- Migration testleri eski örnekleri yeni şemaya doğru taşır.
- Aynı migration'ın tekrar uygulanması veri bozulmasına yol açmaz.
- Dosya yolu güvenliği test edilir.

## 6.7 — Content Editor için UI bağımsız servis/API sözleşmesi

**Amaç:** İleride yazılacak editörün doğrudan JSON dosyalarını veya renderer iç yapılarını yönetmesini önlemek.

Bu aşamada görsel arayüz yoktur. Sadece editörün ileride kullanacağı uygulama sınırları hazırlanır.

Servislerin kavramsal sorumlulukları:
- Asset katalog verisini okuma ve sorgulama.
- Asset kimliğini çözümleme.
- Bir haritanın placement kayıtlarını okuma.
- İçerik paketi doğrulama.
- Asset/placement verisinin bellek içi taslağını doğrulama.
- Kayıt öncesi değişiklikleri kontrol etme.
- Geçerli veriyi güvenli biçimde diske yazma.
- Şema sürümünü ve migration durumunu bildirme.

Sözleşme ilkeleri:
- Servisler Pygame ekran sınıflarına bağımlı olmamalı.
- Servisler mouse/keyboard event almamalı.
- Servisler doğrudan çizim yapmamalı.
- Runtime için gerekli veri modelleri UI tipleri taşımamalı.
- Okuma işlemleri ile kalıcı kayıt işlemleri ayrılmalı.
- Doğrulama sonucu mümkün olduğunca yapılandırılmış olmalı; yalnızca kullanıcı arayüzüne özel metinlerden oluşmamalı.
- Editör henüz bulunmadığından bu servisler küçük, gerçek ihtiyaçla sınırlı tutulmalı; genel amaçlı aşırı soyutlama yapılmamalı.

Kavramsal API işlemleri:
- `load_asset_catalog(content_root)`
- `get_asset(asset_id)`
- `load_map_placements(map_id)`
- `validate_content_package(package)`
- `validate_placement(placement, catalog, map_definition)`
- `save_asset_catalog(draft)`
- `save_map_placements(map_id, draft)`
- `migrate_content(source_version, data)`

Bunlar zorunlu fonksiyon adları değildir; gerçek projedeki isimlendirme ve mimari standarda uyarlanmalıdır.

Kabul ölçütleri:
- Servisler UI başlatılmadan test edilebilmeli.
- Geçerli içerik servis üzerinden okunup doğrulanabilmeli.
- Hatalı taslak kayıt işleminden önce reddedilmeli.
- Runtime aynı içerik sözleşmesini kullanmaya devam etmeli.
- Editör UI'si yazılmadan servis sözleşmeleri otomatik testlerle doğrulanmalı.

## 6.8 — Entegrasyon, regresyon ve kapanış

**Amaç:** Yeni altyapının var olan oyun deneyimini değiştirmediğini ve gelecekte editörün güvenle üzerine kurulabileceğini doğrulamak.

Otomatik doğrulama:
- Asset Catalog yükleme testleri.
- PNG yolu ve kaynak boyutu testleri.
- Asset ID benzersizlik testleri.
- Placement referans testleri.
- Şema sürümleme ve migration testleri.
- Anchor/scale/depth/layer/collision/footprint testleri.
- Güvenli kayıt ve bozuk dosya testleri.
- Eksik asset fallback testleri.
- Cache davranışı regresyon testleri.
- Hex map içerik yükleme regresyonu.
- Kare map içerik yükleme regresyonu.
- Ağaç PNG çizimi ve mevcut derinlik sıralaması regresyonu.
- Ağaç atlası/rig varsayılan kapalı davranışı regresyonu.

Manuel kabul:
- Eldoria demo haritası normal biçimde açılmalı.
- Ağaç, kaya, çalı ve çiçek gibi mevcut nesneler eski konumlarında görünmeli.
- Oyuncu–ağaç ön/arka sıralaması değişmemeli.
- Kamera hareketi ve zoom sırasında nesneler dünya konumuna bağlı kalmalı.
- Altı yönlü harita geçişleri çalışmalı.
- Kare harita sistemi açılmalı ve çalışmalı.
- Normal oyun arayüzüne editör veya düzenleme modu eklenmemiş olmalı.

Kapanış teslimatları:
- Tamamlanan teknik değişikliklerin listesi.
- Değişen/eklenen dosyalar.
- Şema ve servis sözleşmelerinin son hâli.
- Otomatik test ve CI sonuçları.
- Kullanıcı tarafından yapılan manuel kabul sonuçları.
- Bilinçli olarak ertelenen işler.
- `reports/phase-8-completion-report.md` dosyasında ayrıntılı kapanış raporu.

## 7. Aşama boyunca korunacak mimari sınırlar

Aşağıdaki sistemler Aşama 8'in doğrudan hedefi değildir ve açık teknik gerekçe/ayrı onay olmadan değiştirilmemelidir:

- Hex geometri ve axial koordinat hesapları.
- `HexWorldRuntime`.
- `WorldTransform`.
- Kamera takip, zoom ve kenar kaydırma davranışı.
- Altı yönlü hareket ve harita geçişleri.
- Occupancy, collision ve pathfinding motoru.
- Harita bağlantıları ve kaynak/hedef hücre eşlemeleri.
- Kare harita sistemi.
- Karakter, envanter ve diğer mevcut oyun pencereleri.
- Ağaç PNG'sinin kabul edilen doğal çizimi.
- Ağaç atlası/rig'in varsayılan kapalı davranışı.
- Normal oyun HUD ve oyuncu etkileşimleri.

İçerik verisinin okunması ve doğrulanması için gereken en küçük entegrasyon değişiklikleri yapılabilir. Ancak veri altyapısı bahanesiyle simülasyon veya dünya sunum mimarisi yeniden yazılmayacaktır.

## 8. Test stratejisi ve kalite kapıları

Her alt aşama kendi testleriyle kapanmalıdır. Büyük bir değişiklik tek seferde yapılıp yalnızca en sonda test edilmeyecektir.

### 8.1. Birim testleri
- ID ve alan doğrulama.
- Dosya yolu çözümleme.
- Şema doğrulama.
- Anchor ve scale sınırları.
- Collision/footprint geometri doğrulama.
- Referans çözümleme.
- Migration fonksiyonları.

### 8.2. Entegrasyon testleri
- Asset Catalog + AssetManager.
- Catalog + placement referansları.
- Placement + map definition.
- İçerik doğrulama + güvenli kayıt.
- Yeniden yükleme sonrası veri eşitliği.

### 8.3. Regresyon testleri
- Mevcut demo içeriklerinin yüklenmesi.
- Hex harita görünümü.
- Kare harita görünümü.
- Oyuncu–ağaç depth sort.
- Kamera/zoom.
- PNG fallback ve cache.
- Altı yönlü geçişler.

### 8.4. Kalite kapıları
- Test başarısızsa sonraki alt aşamaya geçilmez.
- CI sonucu görülmeden “başarılı” denmez.
- Kullanıcı manuel kabulü gerektiren görsel davranışlar otomatik test sonucu gibi sunulmaz.
- Test sayıları gerçek CI çıktısından alınır.
- Eski içerik dosyaları değiştirilmişse önce/sonra uyumluluk kanıtı bulunur.

## 9. Riskler ve önleyici kararlar

| Risk | Olası sonuç | Önlem |
|---|---|---|
| Mevcut Asset Catalog'ın yeniden yazılması | Çalışan yükleme hattının bozulması | Önce 6.1 denetimi, mevcut sınıfı genişletme |
| Asset ve placement verisinin karışık kalması | Editörün aynı bilgiyi farklı yerlerde değiştirmesi | Ayrı veri sorumlulukları ve tekil referans |
| Anchor biriminin belirsizliği | Nesnelerin yanlış konumlanması/depth sort | Koordinat uzayını belgelemek ve fixture testleri |
| Collision ile görsel boyutun karışması | Oyuncunun nesneye yaklaşamaması veya içinden geçmesi | Ayrı geometri sözleşmeleri |
| Mutlak dosya yolları | Farklı makinelerde içerik yüklenmemesi | İçerik köküne göre güvenli göreli yollar |
| Şema değişiminde eski verinin kaybı | Demo haritalarının bozulması | Migration, yedek ve başarısız kayıtta kaynak koruma |
| Geçersiz referansın runtime'a ulaşması | Eksik nesne veya çalışma zamanı hatası | Paket yüklemeden önce bütünlük doğrulaması |
| Fazla soyutlama | Küçük altyapı işinin gereksiz büyümesi | Yalnızca editörün gerçek ihtiyaç duyacağı servisler |
| Editör UI'sine erken başlanması | Aşama kapsamının büyümesi | UI ve mouse etkileşimini açıkça kapsam dışı tutmak |
| Hex varsayımlarının kare haritaya sızması | Kare harita regresyonu | Koordinat tipini harita tanımına göre çözmek |

## 10. Uygulama sırası ve karar kapıları

Önerilen sıra:

1. 6.1 — Denetim ve envanter.
2. 6.2 — Asset Catalog sözleşmesi.
3. 6.3 — Asset/placement ayrımı.
4. 6.4 — Metadata alanlarının standartlaştırılması.
5. 6.5 — Doğrulama ve güvenli yükleme.
6. 6.6 — Güvenli kayıt ve migration.
7. 6.7 — UI bağımsız servis/API.
8. 6.8 — Entegrasyon, regresyon, CI, manuel kabul ve kapanış raporu.

Karar kapıları:
- 6.1 tamamlanmadan veri modeli değiştirilmeyecek.
- 6.2 ve 6.3 tamamlanmadan yeni editör odaklı servisler genişletilmeyecek.
- 6.4 sözleşmeleri belgelenmeden anchor/collision/depth alanları topluca dönüştürülmeyecek.
- 6.5 doğrulaması olmadan kayıt servisi geçerli içerik dosyalarını değiştirmeyecek.
- 6.6 güvenli kayıt testleri geçmeden migration mevcut içerik dosyalarına uygulanmayacak.
- 6.7 servisleri UI bağımsız test edilmeden editör geliştirmeye hazır olduğu iddia edilmeyecek.

## 11. Aşama 8 tamamlanma ölçütleri

Aşama 8 ancak aşağıdaki koşulların tümü karşılandığında tamamlanmış sayılır:

- [ ] Mevcut içerik ve asset yükleme mimarisi gerçek kod üzerinden belgelenmiş.
- [ ] Tekil asset kimliği ve katalog sözleşmesi doğrulanıyor.
- [ ] Asset dosyası ile metadata sorumluluğu ayrılmış.
- [ ] Harita placement kayıtları asset ID üzerinden referans veriyor.
- [ ] Hex ve kare harita koordinat modelleri korunmuş.
- [ ] Anchor/pivot/scale/depth/layer/collision/footprint anlamları belgelenmiş.
- [ ] Geçersiz dosya yolu ve eksik PNG güvenli biçimde ele alınıyor.
- [ ] Şema sürümü ve migration yaklaşımı test edilmiş.
- [ ] Hatalı kayıt mevcut geçerli dosyayı bozmuyor.
- [ ] UI bağımsız içerik servisleri mevcut.
- [ ] Otomatik birim, entegrasyon ve regresyon testleri başarılı.
- [ ] CI doğrulaması başarılı.
- [ ] Kullanıcı manuel kabul kontrollerini tamamlamış.
- [ ] Normal oyun görünümüne Content Editor arayüzü eklenmemiş.
- [ ] `main` dalında değişiklik yapılmamış.
- [ ] Ayrıntılı kapanış raporu `reports` klasörüne eklenmiş.

## 12. Aşama sonunda beklenen mimari sonuç

Aşama 8 sonunda Eldoria'nın içerik üretim hattı aşağıdaki kavramsal akışa sahip olmalıdır:

```text
PNG / Görsel Dosyaları
        |
        v
Asset Metadata / Catalog
        |
        +----------------------+
        |                      |
        v                      v
Asset Validation         Asset Lookup
        |                      |
        +----------+-----------+
                   |
                   v
          Content Services
                   |
          +--------+--------+
          |                 |
          v                 v
   Map Placements      Safe Persistence
          |
          v
   Validated World Content
          |
          v
   Existing Game Runtime
          |
          v
   Existing Renderer
```

Gelecekteki Content Editor bu altyapının üstünde ayrı bir istemci olarak yer alacaktır:

```text
Future Content Editor UI (NOT PART OF PHASE 8)
                   |
                   v
          Content Services
                   |
          Catalog / Placement / Validation / Persistence
```

Editör arayüzünün runtime, renderer veya JSON dosyalarına doğrudan bağımlı olması hedeflenmez. Servis sözleşmesi üzerinden çalışması hedeflenir.

## 13. Aşama 8 dışında bırakılan gelecek işler

Aşağıdaki işler, altyapı tamamlandıktan sonra ayrı bir aşama olarak planlanabilir:

- Content Editor kullanıcı arayüzü.
- Asset kütüphanesi görsel önizlemesi.
- Harita seçimi ve harita üzerinde nesne yerleştirme.
- Sürükle-bırak, taşıma, çoğaltma ve silme araçları.
- Anchor/pivot ve collision alanı görsel düzenleme.
- Katman/depth sırası için görsel yardımcılar.
- Undo/redo ve değişiklik geçmişi.
- Çoklu seçim ve toplu düzenleme.
- İçerik paketi içe/dışa aktarma.
- Gelişmiş asset etiketleme ve arama.
- Profesyonel sanat varlığı üretim/ithalat iş akışı.

Bu maddeler Aşama 8'in gizli hedefi değildir ve bu aşama sırasında uygulanmayacaktır.

## 14. Nihai kapsam kararı

**Aşama 8'in adı: Content Editor İçin Altyapı Hazırlığı.**

Aşamanın başarı ölçütü bir editör penceresinin açılması değil; gelecekteki editörün güvenle kullanabileceği veri modellerinin, asset kataloğunun, harita yerleşim sözleşmesinin, doğrulama ve güvenli kayıt servislerinin hazır olmasıdır.

Aşama 8 boyunca oyun normal şekilde oynanabilir kalmalıdır. Var olan doğal dünya sunumu ve kabul edilmiş simülasyon davranışları korunmalıdır.

Aşama 8 tamamlandığında Content Editor geliştirmesi ayrı bir aşama olarak başlatılabilecek; editörün temel dosya formatı, servis sınırları ve doğrulama kuralları önceden belirlenmiş olacaktır.

**Bu belge uygulama izni veya tamamlanma raporu değildir. Uygulama öncesi kapsam ve teknik yol haritasıdır.**
