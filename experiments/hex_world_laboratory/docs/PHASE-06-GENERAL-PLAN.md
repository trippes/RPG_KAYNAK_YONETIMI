# Aşama 6 — Kamera ve Dünya-Ekran Dönüşümü Genel Planı

> Belge türü: Aşama genel planı  
> Proje: Eldoria — Hex World Laboratory  
> Çalışma dalı: experiment/hex-world-laboratory  
> Durum: ONAYLANDI — 6.1–6.5 TEKNİK UYGULAMA TAMAMLANDI; GÖRSEL KULLANICI KABULÜ BEKLİYOR  
> Tarih: 17 Kasım 2026  
> Ön koşul: Aşama 0–5 tamamlandı ve kabul edildi.

---

## 1. Amaç

Aşama 6'nın amacı, mevcut hex dünya ve sürekli hareket sisteminin üzerine, simülasyonun yetkili dünya koordinatlarını değiştirmeyen bir kamera ve dünya-ekran dönüşüm katmanı eklemektir.

Oyuncu ve dünya nesneleri dünya uzayında konumlanmaya devam eder. Kamera yalnızca bu konumların görüntü alanındaki yerini belirler. Ekran koordinatından dünya konumuna ters dönüşüm yapılabilmeli; fareyle işaretlenen noktanın hangi dünya hücresine karşılık geldiği bulunabilmelidir.

Aşama sonunda laboratuvar demosu, sabit ekran merkezine çizilen harita olmaktan çıkarak takip edilebilir, yakınlaştırılabilir ve farklı viewport boyutlarında doğru çalışan bir dünya görünümüne sahip olacaktır.

## 2. Devralınan mimari sözleşmeler

Aşama 6, aşağıdaki tamamlanmış sistemleri yeniden yazmadan kullanmalıdır:

1. **Geometry:** `WorldPoint`, `AxialCoord`, `HexLayout`, `HexOrientation`, `axial_to_world`, `world_to_axial`, `hex_polygon` ve mevcut geometri toleransları.
2. **World:** `HexWorld`, `HexMapDefinition`, `HexWorldView`, harita kimliği ve yüklenmiş harita bağlamı.
3. **Movement:** `MovementState.position` alanındaki `WorldPoint`, hareket sistemi ve 60 TPS simülasyon sözleşmesi.
4. **Physics:** Aşama 5 gövde/çarpışma sistemleri ve dünya koordinatındaki collider geometrisi.
5. **Application:** Pygame pencere/event loop sahipliği ve `MovementDemo` simülasyon orkestrasyonu.

Koordinatların anlamı korunur:

- `WorldPoint`: matematiksel dünya koordinatı; x sağa, y yukarı.
- `ScreenPoint`: viewport içinde piksel koordinatı; x sağa, y aşağı.
- `AxialCoord`: hex hücre adresi; ekran konumu veya hareketli aktörün sürekli konumu değildir.

Kamera veya renderer, MovementState ya da dünya verisini değiştiremez. Kamera dönüşümü simülasyonun authoritative state'ine geri yazılamaz.

## 3. Kapsam içi işler

### 3.1 Dünya-ekran dönüşüm sözleşmesi

- Dünya koordinatından ekran piksel koordinatına dönüşümü tanımlamak.
- Ekran koordinatından dünya koordinatına ters dönüşümü tanımlamak.
- Her iki dönüşümde viewport boyutu, kamera merkezi/offset'i ve zoom parametrelerinin rolünü kesinleştirmek.
- Dönüşümün round-trip doğruluğunu sayısal toleransla test etmek.
- Y ekseni yön farkını tek bir katmanda ele almak; çizim koduna dağılmış ters çevirmeleri kaldırmak.

### 3.2 Kamera durumu ve viewport

- Kamera dünya merkezini ve görünür viewport boyutunu temsil etmek.
- Pencere/viewport yeniden boyutlandırıldığında dönüşümün güncel ölçülerle çalışmasını sağlamak.
- Geçersiz, sıfır veya negatif zoom ve viewport değerlerini reddetmek.
- Kamera verisini Pygame Surface veya display nesnesine bağımlı olmayan bir çekirdekte tutmak.

### 3.3 Zoom

- Kamera zoom seviyesini tanımlamak ve güvenli alt/üst sınırlarını belirlemek.
- Zoom değişiminde dünya koordinatlarının kararlı kalmasını sağlamak.
- Zoom'un fiziksel collider boyutlarını, hareket hızını veya dünya geometrisini değiştirmediğini doğrulamak.
- Fare tekerleği/zoom girdisinin uygulama adaptöründe nasıl ele alınacağını teknik tasarımda kesinleştirmek.

### 3.4 Oyuncu takibi ve kamera sınırları

- Kamera hedefini hareketli aktörün dünya konumuna bağlamak.
- Takip davranışını render güncellemesinden ayırmak; seçilen yumuşatma yaklaşımının frame-rate bağımsız olmasını sağlamak.
- Kamera sınırlarını harita geometrisi ve viewport boyutlarıyla ilişkilendirmek.
- Harita sınır politikası (OPEN/BLOCKED) ile kamera sınır politikasını birbirine karıştırmamak.
- Viewport haritadan büyük olduğunda ve harita düzensiz hücre kümesi içerdiğinde davranışı tanımlamak.
- Sınırlandırmanın kapatılabildiği veya uygulanmadığı açık dünya senaryosunu desteklemek.

### 3.5 Ekran girdisi ve hücre seçimi

- Fare ekran noktasını dünya noktasına dönüştürmek.
- Dünya noktasını mevcut `world_to_axial` sözleşmesiyle hücre adresine dönüştürmek.
- Hex kenarı/eşit uzaklık durumlarında mevcut deterministik tie-break davranışını korumak.
- Ekran koordinatı, dünya koordinatı ve hücre adresini ayrı tipler/katmanlar olarak tutmak.
- Kamera hareketi ve zoom sonrasında fareyle seçilen hücrenin doğru kalmasını doğrulamak.

### 3.6 Pygame render adaptasyonu

- `MovementDemo` içindeki sabit ekran merkezine dayalı çizim dönüşümünü kamera tabanlı hale getirmek.
- Dünya çizimi ile kamera dönüşümünü ayırmak.
- Hex hücreleri, engeller, ev iskeleti, collider tanıları ve oyuncunun aynı dönüşüm sözleşmesini kullanmasını sağlamak.
- Kamera çekirdeğini Pygame'den bağımsız tutmak; Pygame yalnızca pencere, event, Surface ve çizim adaptörü olarak kalmalıdır.
- Render işleminin fiziksel simülasyon durumunu değiştirmediğini test etmek.

## 4. Alt aşamalar ve sıralama

| Alt aşama | Başlık | Ana çıktı |
|---|---|---|
| 6.1 | Koordinat ve viewport sözleşmesi | ScreenPoint/viewport tanımı, dönüşüm matematiği ve round-trip testleri |
| 6.2 | Kamera çekirdeği ve zoom | Pygame bağımsız kamera durumu, zoom sınırları ve dönüşüm API'si |
| 6.3 | Takip ve kamera sınırları | Hedef takip davranışı, harita bounds hesabı ve açık dünya politikası |
| 6.4 | Render ve fare girdisi entegrasyonu | Kamera kullanan Pygame renderer, mouse-to-world ve hex picking |
| 6.5 | Bütünleşik doğrulama ve kabul hazırlığı | Regresyon, performans, manuel kabul listesi ve kapanış girdileri |

Alt aşamaların kesin dosya kapsamı, sınıf/fonksiyon API'leri ve bağımlılık sırası ayrıntılı teknik mimari belgesinde belirlenecektir. Her alt aşama kendi test kapısını geçmeden sonraki alt aşamaya başlanmayacaktır.

## 5. Mimari sınırlar

Aşama 6 boyunca aşağıdaki sınırlar korunacaktır:

- Geometry, World, Movement ve Physics katmanları Camera veya Rendering katmanına bağımlı hâle gelmez.
- Camera çekirdeği Pygame import etmez ve Surface tutmaz.
- Rendering, Camera dönüşümünü kullanır; dünya/simülasyon state'ini değiştiremez.
- Input adaptörü ekran olaylarını alabilir; koordinat dönüşümü için Camera API'sini kullanır.
- Hex hücre seçimi mevcut Geometry dönüşümünü kullanır; ikinci bir hex matematiği uygulanmaz.
- Kamera hareketi, zoom veya pencere boyutu değişimi fizik simülasyonuna yeni bir hareket adımı eklemez.
- 60 TPS simülasyon zamanlaması değiştirilmez.
- Aşama 5 collider ve çarpışma doğruluğu kamera ölçeğinden etkilenmez.

## 6. Test ve doğrulama yöntemi

### 6.1 Birim testleri

- Dünya-ekran ve ekran-dünya dönüşüm round-trip testleri.
- Kamera merkezi, viewport merkezi ve zoom için bilinen koordinat örnekleri.
- Zoom alt/üst sınırları ve geçersiz değerler.
- Viewport yeniden boyutlandırma davranışı.
- Kamera takip fonksiyonunun zaman adımı/elapsed time değişimlerine göre deterministikliği.
- Harita bounds ve viewport büyük/küçük durumları.
- OPEN/BLOCKED dünya sınırı ile kamera sınırının bağımsızlığı.
- Fare noktasından dünya noktasına ve hex hücresine seçim.
- Flat-top ve pointy-top harita yönelimleri.

### 6.2 Entegrasyon ve regresyon testleri

- Kamera hareket ederken oyuncunun fiziksel WorldPoint konumu değişmemeli.
- Zoom değişirken collider dünya boyutu ve hareket hızı değişmemeli.
- Kamera takibi hareket sisteminin tick sayısını etkilememeli.
- Hex, nesne ve ev collider çizimleri aynı kamera dönüşümünü kullanmalı.
- Kamera hareketi ve zoom sonrasında mouse picking doğru hücreyi bulmalı.
- Pencere kapanışı ve mevcut Pygame event loop davranışı korunmalı.
- Aşama 0–5 testleri regresyona karşı çalıştırılmalı.

### 6.3 Masaüstü kabul kontrolleri

Nihai kabul aşamasında kullanıcı bilgisayarında en az şu kontroller yapılacaktır:

1. Laboratuvar penceresinin normal açılması ve kapanması.
2. Oyuncunun hareketi sırasında kameranın hedefi doğru takip etmesi.
3. Kamera hareketinin oyuncuyu ekranda görünür tutması.
4. Yakınlaştırma ve uzaklaştırmanın doğru çalışması.
5. Zoom değişiminde hücre geometrisinin bozulmaması.
6. Kamera farklı konumdayken fareyle işaretlenen hex hücresinin doğru seçilmesi.
7. Kamera sınırına yaklaşırken tanımlanan sınır politikasının doğru uygulanması.
8. OPEN senaryoda kamera sınırı ile fiziksel dünya sınırının karıştırılmaması.
9. Pencere boyutu değişince görüntünün ve dönüşümlerin güncellenmesi.
10. Ağaç, kaya, duvar, ev ve oyuncu çizimlerinin aynı kamera dönüşümünde hizalı kalması.
11. Kamera/zoom işlemlerinin hareket, çarpışma ve 60 TPS davranışını bozmaması.

Kesin test adımları ve beklenen görsel sonuçlar teknik planda kabul listesine dönüştürülecektir.

## 7. Kapsam dışı işler

Ayrıca onaylanmadıkça Aşama 6 kapsamında geliştirilmez:

- Nihai sanat varlıkları, sprite animasyonları ve karakter animasyon sistemi.
- Y-sort, katmanlı derinlik/örtüşme ve gelişmiş 2.5D render sistemi.
- Işık, gölge, shader, parçacık ve post-processing.
- Harita editörü veya genel amaçlı dünya editörü.
- NPC, kaynak ve etkileşim sistemlerinin uygulanması.
- Pathfinding veya simülasyon orkestrasyonunun yeniden tasarlanması.
- Kamera rotasyonu; yalnızca ayrıca gerekçelendirilip onaylanırsa değerlendirilir.
- Ana oyuna veya `demo_eldoria` dalına entegrasyon.
- Godot'a geçiş.

Bu aşama kamera ve koordinat dönüşüm altyapısını kurar; nihai görsel kalite/derinlik sistemi için ön koşulları hazırlar ancak o sistemi tamamlamayı hedeflemez.

## 8. Aşama kapanış koşulları

Aşama 6 ancak aşağıdakilerin tamamı sağlandığında kapatılabilir:

1. 6.1–6.5 alt aşamaları tamamlanmış ve belgelenmiş olmalıdır.
2. Dünya-ekran dönüşümleri ve ters dönüşümler tanımlı toleranslarda tutarlı olmalıdır.
3. Kamera ve renderer simülasyonun authoritative state'ini değiştirmemelidir.
4. Zoom, takip, viewport ve kamera sınır senaryoları otomatik testlerle doğrulanmalıdır.
5. Mouse picking flat-top ve pointy-top yönelimlerinde doğrulanmalıdır.
6. Aşama 0–5 regresyon testleri başarılı olmalıdır.
7. Linux ve Windows CI / Core Quality doğrulamaları başarılı olmalıdır.
8. Performans ve bilinen sınırlamalar raporlanmalıdır.
9. Kullanıcı bilgisayarında nihai masaüstü kabulü tamamlanmalıdır.
10. `experiments/hex_world_laboratory/reports/PHASE-06-CLOSURE-REPORT.md` oluşturulmalı ve test/CI/manual kanıtlarını içermelidir.
11. Master Plan ve README aşama durumuyla tutarlı biçimde güncellenmelidir.
12. Kullanıcı nihai sonucu kabul etmelidir.

## 9. Dal ve değişiklik güvenliği

- Bütün çalışmalar yalnızca `experiment/hex-world-laboratory` dalında yapılır.
- `main` ve `demo_eldoria` dallarına ayrı ve açık kullanıcı onayı olmadan yazılmaz, merge veya cherry-pick yapılmaz.
- Bu genel planın kabulünden sonra ayrıntılı teknik mimari ve uygulama planı hazırlanır.
- Teknik mimari kullanıcı tarafından onaylanmadan kod değişikliği yapılmaz.
- Her alt aşamadan önce gerçek dosya ağacı ve API yeniden incelenir.
- Her yazma öncesi aktif dal HEAD'i, hedef dosyanın mevcut SHA'sı/oluşturulmamış olması ve korunan dalların HEAD'leri doğrulanır.
- Her commit sonrasında commit, branch HEAD ve değişen dosyalar doğrulanır.
- Plan dışı kapsam veya mimari değişiklik gerekirse önce gerekçe ve etki analizi sunulur.

---

Bu genel plan kullanıcı tarafından onaylanmış, ayrıntılı teknik mimari de uygulama öncesinde kabul edilmiştir. 6.1–6.5 alt aşamalarının teknik uygulaması ve otomatik CI doğrulamaları tamamlanmıştır. Son durum ve CI kanıtları `../reports/PHASE-06-CLOSURE-REPORT.md` belgesinde; masaüstü görsel kabul adımları `PHASE-06-MANUAL-ACCEPTANCE-CHECKLIST.md` belgesindedir. Aşama 6, kullanıcı görsel kabulü bildirilene kadar tamamen kapanmış sayılmaz.
