# Aşama 14 — Content Editor ve Görsel Düzenleme Araçları

> **Belge türü:** Genel aşama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Ön koşul:** Aşama 13 resmen kapatıldı (18 Kasım 2026)  
> **Durum:** TASLAK HAZIR — KULLANICI GENEL PLAN ONAYI BEKLENİYOR  
> **Uygulama durumu:** Başlamadı; bu belge kod değişikliği veya teknik uygulama izni değildir.

## 1. Amaç ve gerekçe

Aşama 13 ile ağaç, kaya, çalı, çim ve çiçek/bitki kümelerini üretebilen ortak, deterministik ve yeniden kullanılabilir prosedürel grafik altyapısı tamamlandı. Ancak bu profillerin görünümünü değiştirmek için kullanıcı hâlâ kod ve parametre tanımlarını doğrudan düzenlemek zorunda.

Aşama 14'ün amacı, mevcut prosedürel grafik altyapısını kullanan, görsel odaklı ve kullanıcı tarafından etkileşimli biçimde kullanılabilen bir **Content Editor** oluşturmaktır. Kullanıcı bir nesne profilini seçebilmeli, önizlemesini görebilmeli, desteklenen parametreleri değiştirebilmeli, sonucu karşılaştırabilmeli ve çalışmasını güvenli, doğrulanabilir bir içerik dosyası olarak kaydedip yeniden açabilmelidir.

Editör, Aşama 13'ün yerine yeni bir çizim motoru yazmayacak; onun sunduğu geometri, bileşen, palet, varyasyon ve profil üretim kabiliyetlerini kullanacaktır.

## 2. Ürün hedefleri

1. Prosedürel nesne profillerini kod düzenlemeden seçip görüntüleyebilmek.
2. Bir profilin görsel önizlemesini düzenleme sırasında güncel tutmak.
3. Profilin desteklediği parametreleri anlaşılır kontrollerle düzenleyebilmek.
4. Ağaç gibi bileşenli nesnelerde desteklenen alt bileşenleri ayrı ayrı düzenleyebilmek.
5. Renk paletlerini ve renk varyasyonlarını görsel olarak inceleyip değiştirebilmek.
6. Seed ve varyasyon ayarlarını kontrol ederek tekrarlanabilir sonuçlar alabilmek.
7. Önceki ve yeni görünümü karşılaştırabilmek; varsayılan değerlere dönebilmek.
8. İçerik çalışmalarını sürümlenebilir, doğrulanabilir bir dosya biçiminde kaydedip yükleyebilmek.
9. Hatalı veya desteklenmeyen verilerin runtime çizim sistemine ulaşmasını engellemek.
10. Editörün ana oyun ve laboratuvar simülasyonundan bağımsız kalmasını sağlamak.

## 3. Kapsam

### 3.1 Dahil olanlar

**A. Editör çalışma alanı**
- Laboratuvarın tek başlatıcısı korunarak editöre ulaşılabilmesi.
- Önizleme alanı ile profil/parametre panellerinin birbirinden anlaşılır biçimde ayrılması.
- Pencere boyutu değiştiğinde kullanılabilir düzenin korunması.
- Fare ve klavye ile temel gezinme ve düzenleme.
- Geçerli çalışma, kaydedilmemiş değişiklik ve hata durumlarının açıkça gösterilmesi.

**B. Profil tarayıcısı**
- Mevcut beş profilin listelenmesi: ağaç, kaya, çalı, çim kümesi ve çiçek/bitki kümesi.
- Profilin adı, kısa açıklaması ve küçük önizlemesinin gösterilmesi.
- Profil seçildiğinde ilgili düzenleme alanlarının açılması.
- Yeni profil ailelerinin ileride eklenebilmesine uygun bir içerik keşif yaklaşımı.

**C. Görsel önizleme**
- Seçili profilin izole önizlemesi.
- Gerekli olduğunda profilin farklı arka plan/zemin kontrastlarında incelenmesi.
- Ölçek ve görünüm kontrolleri.
- Parametre değişikliklerinin önizlemeye kontrollü biçimde yansıması.
- Aynı seed ile aynı çıktının korunması; farklı seed ile desteklenen görsel varyasyonun gözlemlenmesi.

**D. Parametre ve bileşen düzenleme**
- Profilin izin verdiği boyut, şekil, yoğunluk, dağılım ve benzeri parametrelerin düzenlenmesi.
- Bileşenli profillerde desteklenen alt bileşenlerin ayrı ayrı seçilip düzenlenmesi. Örneğin ağaçta gövde, dal ve yaprak kümeleri.
- Parametre sınırlarının ve varsayılan değerlerin kullanıcıya anlaşılır biçimde sunulması.
- Bir parametre değişikliğinin yalnızca ilgili görsel çıktıyı etkilemesi.

**E. Palet ve renk düzenleme**
- Profilin renk paletinin görüntülenmesi.
- Desteklenen renk alanlarının değiştirilmesi.
- Renk rampalarının ve ton geçişlerinin önizlenmesi.
- Geçersiz renk değerlerinin kayda veya çizime ulaşmadan reddedilmesi.

**F. Varyasyon ve karşılaştırma**
- Seed değerinin görüntülenmesi ve düzenlenmesi.
- Kontrollü varyasyon üretimi.
- Önceki görünüm ile güncel önizlemenin karşılaştırılması.
- Profilin varsayılan parametre ve paletine geri dönme.
- Düzenleme geçmişi/geri al-yinele davranışının kullanıcı deneyimi açısından değerlendirilmesi ve uygun görülürse kapsama alınması.

**G. İçerik kaydetme ve yükleme**
- Kullanıcı düzenlemelerinin sürüm bilgisi taşıyan, metin tabanlı ve doğrulanabilir bir içerik biçiminde saklanması.
- Kaydedilmiş içeriğin yeniden açılabilmesi.
- Dosya adı, içerik kimliği ve profil türü gibi gerekli tanımlayıcıların korunması.
- Bozuk, eksik, uyumsuz veya desteklenmeyen içerik dosyaları için anlaşılır hata mesajları.
- Kaydedilmemiş değişiklikler varken çıkış veya başka profile geçişte kullanıcıyı uyarma.
- Runtime'ın yalnızca doğrulamadan geçmiş içerikleri kullanması.

### 3.2 Aşama 14'ün dışında kalanlar

- Genel amaçlı harita/dünya editörü veya hex hücre düzenleme aracı.
- Oyun içi görev, diyalog, envanter, ekonomi veya savaş editörü.
- Piksel piksel raster boyama uygulaması veya tam kapsamlı 2B sanat paketi.
- Animasyon zaman çizelgesi, iskelet animasyonu veya parçacık editörü.
- 3B modelleme, rigging veya Godot geçişi.
- NPC AI, yoldaş hareketi, pathfinding veya simülasyon davranış düzenleyicisi.
- Ana oyunun runtime'ına doğrudan entegrasyon veya `demo_eldoria` dalına aktarım.
- Kullanıcı tarafından yüklenen harici görsel dosyalarını otomatik olarak prosedürel profile dönüştürme.
- Eklenti mağazası, çevrimiçi paylaşım veya çok kullanıcılı düzenleme.

Kapsam genişletme ihtiyacı ortaya çıkarsa ayrıca gerekçelendirilip kullanıcı onayına sunulur.

## 4. Temel tasarım ilkeleri

1. **Mevcut üretim altyapısını kullan:** Yeni bir çizim motoru oluşturma; Aşama 13 profil ve bileşen API'lerini temel al.
2. **Önizleme ile runtime ayrımı:** Editörün geçici düzenleme durumu oyun dünyasının authoritative state'ini değiştirmesin.
3. **Veri odaklı içerik:** Kullanıcı çalışmaları çalıştırılabilir Python kodu olarak değil, şeması doğrulanabilen veri olarak saklansın.
4. **Görsel/fiziksel ayrım:** Palet, geometri veya görsel parametre düzenlemesi collider'ı otomatik değiştirmesin. Fizik tanımı ayrı ve açık bir iş akışına sahip olsun; Aşama 14'te collider düzenleme ancak ayrıca onaylanırsa ele alınsın.
5. **Deterministik sonuç:** Seed ve parametreler kaydedildiğinde aynı profil tekrar üretilebilsin.
6. **Güvenli dosya işlemleri:** Yükleme sırasında şema, veri türü, aralık ve sürüm doğrulaması yapılsın; hatalı dosya mevcut çalışmanın üzerine yazılmasın.
7. **Geriye uyum:** Ağaç, kaya, çalı, çim ve çiçek profillerinin mevcut runtime çıktıları, editör geliştirmesi nedeniyle bozulmasın.
8. **Bağımlılık disiplini:** Yeni GUI kütüphanesi eklemek zorunlu varsayılmasın. Mevcut Pygame yaklaşımı ile olası UI kütüphaneleri; bakım, lisans, paket boyutu, bellek, etkileşim kalitesi ve mevcut event loop uyumu bakımından teknik denetimde karşılaştırılsın.
9. **Küçük ekran ve düşük donanım:** Editör, laboratuvarın hedeflenen mütevazı donanım koşullarında kullanılabilir ve kararlı olmalı.
10. **Tek başlatıcı:** `python -m hex_world_lab` korunmalı; aşamaya özel ikinci launcher oluşturulmamalı.

## 5. Önerilen iş paketleri

Bu bölüm genel aşama sırasını tanımlar. Kesin sınıflar, dosya listesi, API'ler ve veri şeması teknik planda belirlenecektir.

### 14.1 — Depo ve mimari denetimi
- Aşama 13 profil, bileşen, palet, varyasyon ve cache API'lerini inceleme.
- Mevcut laboratuvar giriş noktası, event loop, renderer ve pencere davranışını inceleme.
- Mevcut dosya/JSON şema ve persistence örüntülerini inceleme.
- GUI kütüphanesi seçeneklerini, bağımlılık ve lisans etkilerini karşılaştırma.
- Mevcut test, CI, Ruff ve artifact üretim düzenini inceleme.
- Bulguları denetim raporuna kaydetme.

### 14.2 — Editör deneyimi ve içerik sözleşmesi
- Kullanıcı akışlarını ve ekran/panel sorumluluklarını tanımlama.
- Profil, düzenleme oturumu, geçici önizleme ve kaydedilmiş içerik kavramlarını ayırma.
- Parametrelerin kullanıcıya sunulma ve doğrulanma ilkelerini belirleme.
- İçerik dosyası biçimi ve sürümleme gereksinimlerini belirleme.
- UI teknolojisi ve bağımlılık kararını teknik plana girdi olacak şekilde netleştirme.

### 14.3 — Editör kabuğu ve önizleme alanı
- Editör çalışma alanı, profil seçimi ve önizleme alanını oluşturma.
- Fare/klavye etkileşimlerini ve pencere boyutu değişimini ele alma.
- Önizlemeyi mevcut procedural profile üreticileriyle bağlama.
- Runtime dünya/simülasyon durumundan izolasyonu doğrulama.

### 14.4 — Profil ve bileşen düzenleme
- Profil tarayıcısını ve profil seçimini uygulama.
- Her profil için desteklenen parametre kontrollerini sunma.
- Bileşenli profillerde ilgili alt bileşenleri seçilebilir hale getirme.
- Parametre değişikliklerini önizlemeye yansıtma.

### 14.5 — Palet, seed ve görsel varyasyon araçları
- Renk paleti düzenleme ve önizleme.
- Seed ve deterministik varyasyon kontrolleri.
- Önceki/güncel görünüm karşılaştırması ve varsayılana dönme.
- Düzenleme geçmişi/geri al-yinele kapsamını teknik plan kararına göre uygulama.

### 14.6 — İçerik kaydetme, yükleme ve doğrulama
- Sürümlü içerik dosyası biçimini uygulama.
- Kaydetme/yükleme ve dosya doğrulama akışlarını ekleme.
- Bozuk/uyumsuz dosya ve kaydedilmemiş değişiklik senaryolarını ele alma.
- Yüklenen içeriğin runtime profil üretimine güvenli adaptasyonunu sağlama.

### 14.7 — Bütünleşme, kullanılabilirlik ve regresyon iyileştirmeleri
- Editörün tek laboratuvar başlatıcısı içindeki akışını tamamlamak.
- Profil üretimi/cache ve önizleme yenileme davranışını doğrulamak.
- Klavye/fare etkileşimi, hata mesajları ve pencere düzenini iyileştirmek.
- Mevcut dünya demosu ve Aşama 12–13 görsel çıktıları üzerinde regresyon kontrolü yapmak.

### 14.8 — Bütünleşik doğrulama ve kabul
- Tam Pytest paketi ve yeni editör testleri.
- Ruff lint/format ve laboratuvar/Core Quality GitHub Actions.
- İçerik dosyası doğrulama, bozuk dosya, sürüm uyumsuzluğu ve deterministik tekrar testleri.
- Profil üretimi, önizleme yenileme ve cache davranışı benchmarkları.
- Editör ekranları ve düzenleme akışları için görsel kanıt artifact'leri.
- Kullanıcı masaüstü görsel/işlevsel kabul kontrol listesi.
- Resmî kapanış raporu ve Master Plan güncellemesi.

## 6. Kalite ve kabul hedefleri

Aşama 14 ancak aşağıdaki koşulların tamamı sağlandığında kapatılabilir:

- Beş mevcut profil editörde seçilip önizlenebilir.
- Desteklenen parametreler kod değişikliği olmadan düzenlenebilir.
- Bileşenli profilin desteklenen alt parçaları ayrı düzenlenebilir.
- Palet ve seed değişiklikleri anlaşılır ve tekrarlanabilir sonuç verir.
- Aynı içerik verisi aynı görsel sonucu üretir.
- Kaydedilen içerik kapatılıp yeniden açıldığında kayıpsız geri yüklenir.
- Geçersiz/bozuk içerik reddedilir ve mevcut geçerli çalışma korunur.
- Görsel düzenlemeler collider veya dünya simülasyonu state'ini gizlice değiştirmez.
- Mevcut beş profilin kabul edilmiş runtime görsellerinde regresyon oluşmaz.
- Pencere yeniden boyutlandırma, temel fare/klavye kullanımı ve kaydedilmemiş değişiklik akışları çalışır.
- Pytest, Ruff, laboratuvar CI ve Core Quality kontrolleri başarılıdır.
- Benchmark ve görsel kanıt artifact'leri üretilmiştir.
- Kullanıcı masaüstü kabulünü tamamlamıştır.
- Kapanış raporu değişen dosyaları, commit SHA'lerini, test/CI kanıtlarını ve bilinen sınırlamaları kaydeder.

## 7. Kullanıcı kabul yaklaşımı

Kullanıcıdan teknik kod incelemesi değil, editörün gerçek kullanımını doğrulaması istenir. Kabul kontrol listesi teknik plan sonrasında hazırlanacaktır. Genel olarak kullanıcı:

- Editörü tek laboratuvar başlatıcısından açar.
- Beş profil arasında geçiş yapar.
- Birkaç parametreyi ve palet rengini değiştirerek önizlemeyi inceler.
- Seed değiştirerek varyasyon farkını ve aynı seed ile tekrarlanabilirliği kontrol eder.
- Çalışmayı kaydeder, editörü kapatıp tekrar açar ve dosyayı yükler.
- Hatalı dosya/parametre uyarılarını ve kaydedilmemiş değişiklik korumasını dener.
- Pencere boyutu, fare/klavye etkileşimi ve genel kararlılığı kontrol eder.

Kesin adımlar, ekran görüntüsü beklentileri ve hata raporlama yöntemi teknik plan onayından sonra hazırlanacak manuel kabul kontrol listesinde yer alır.

## 8. Dal, güvenlik ve çalışma yöntemi

- Tüm denetim, plan, uygulama, test ve raporlama yalnızca `experiment/hex-world-laboratory` dalında yürütülür.
- `main` ve `demo_eldoria` dallarına yazılmaz ve merge yapılmaz.
- Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak korunur.
- Kullanıcı genel planı onaylamadan teknik plan kesinleştirilmiş sayılmaz.
- Teknik plan ayrıca onaylanmadan kod değişikliği yapılmaz.
- Her GitHub yazma işleminden önce dal HEAD'i ve hedef dosya SHA/varlık durumu doğrulanır; işlem sonrası yeni HEAD ve korunan dallar tekrar kontrol edilir.
- Kapsam dışı yeni ihtiyaçlar kullanıcı onayı olmadan eklenmez.

## 9. Onay kapıları ve sıradaki adım

1. **Genel plan onayı:** Kullanıcı bu belgeyi ve kapsam sınırlarını inceler.
2. **Ayrıntılı denetim:** Genel plan onayından sonra 14.1 denetimi tamamlanır; gerçek depo, event loop, profil API'leri, veri saklama ve UI bağımlılıkları doğrulanır.
3. **Teknik plan:** Denetim bulgularına göre modüller, API'ler, veri şeması, dosya değişiklik listesi, test matrisi, benchmark ve manuel kabul adımları hazırlanır.
4. **Teknik plan onayı:** Kullanıcı teknik planı ayrıca onaylar.
5. **Uygulama:** Yalnızca onaylanmış iş paketleri uygulanır.
6. **Ara ve bütünleşik doğrulama:** Pytest, Ruff, GitHub Actions, benchmark ve görsel artifact kontrolleri tamamlanır.
7. **Manuel kabul:** Kullanıcı masaüstünde editörün gerçek kullanımını doğrular.
8. **Kapanış:** Rapor hazırlanır ve Master Plan güncellenir.

**Bu belge yalnızca Aşama 14 Genel Planı'dır. Onay verilmeden teknik plan veya kod uygulaması başlatılmaz.**
