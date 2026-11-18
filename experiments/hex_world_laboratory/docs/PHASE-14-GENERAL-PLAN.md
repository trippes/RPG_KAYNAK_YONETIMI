# Aşama 14 — İçerik Veri Altyapısı ve ELDORIA CONTENT EDITOR Hazırlığı

> **Belge türü:** Genel aşama planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Ön koşul:** Aşama 13 resmen kapatıldı (18 Kasım 2026)  
> **Durum:** GÜNCELLENMİŞ TASLAK — KULLANICI GENEL PLAN ONAYI BEKLENİYOR  
> **Uygulama durumu:** Başlamadı; bu belge kod değişikliği veya teknik uygulama izni değildir.

## 1. Amaç ve uzun vadeli vizyon

Aşama 13 ile prosedürel nesne üretimi için ortak geometri, canvas, palet, varyasyon, bileşen, profil ve cache altyapısı tamamlandı. Bir sonraki adım hemen görsel bir editör arayüzü yazmak değildir. Önce bu içeriklerin editörlerden bağımsız, güvenli, sürümlenebilir ve yeniden kullanılabilir veri olarak tanımlanmasını sağlayacağız.

Uzun vadeli ürün hedefi, ayrı bir masaüstü uygulaması olan **ELDORIA CONTENT EDITOR**'dür. Bu uygulama ileride en azından şu üretim iş akışlarını destekleyecektir:

- Harita oluşturma, açma ve düzenleme.
- Harita üzerine çevresel nesneler, yapılar ve diğer içerikleri yerleştirme.
- Yapı ve nesneleri çizme, şekillendirme ve görsel olarak düzenleme.
- Yerleştirilmiş içerikleri taşıma, değiştirme, çoğaltma ve kaldırma.
- Harita ve içerik çalışmalarını kaydetme, yeniden açma ve sürümleme.

**Aşama 14 bu masaüstü uygulamasını geliştirmeyecek.** Yalnızca gelecekteki uygulamanın ve oyun runtime'ının ortak kullanabileceği içerik veri sözleşmelerini ve temel içerik altyapısını hazırlayacaktır. Böylece gelecekteki editör, kendi özel veri biçimini veya ikinci bir çizim motorunu üretmek zorunda kalmayacaktır.

## 2. Aşama 14'ün hedefleri

1. Aşama 13 prosedürel profillerini koddan bağımsız, veri odaklı tanımlanabilir hale getirmek.
2. İçerik tanımı ile harita üzerindeki içerik örneğini/yerleşimini kavramsal ve teknik olarak ayırmak.
3. Ağaç, kaya, çalı, çim ve çiçek/bitki profillerinin mevcut davranışını bozmadan veriyle temsil edilebilen alanlarını belirlemek.
4. Gelecekteki yapılar ve diğer yerleştirilebilir içerikler için genişletilebilir tanım ve kimlik yaklaşımını hazırlamak.
5. İçerik dosyaları için kararlı kimlik, şema, sürümleme, serileştirme, yükleme ve doğrulama altyapısı oluşturmak.
6. Harita belgesi ve harita üzerindeki yerleşim verileri için gelecekteki editörün kullanabileceği veri sınırlarını araştırmak ve gerekli temel sözleşmeleri belirlemek.
7. İçerik verisini mevcut procedural renderer'a güvenli biçimde bağlayan adaptör/registry yaklaşımını oluşturmak.
8. Görsel tanımların collider, fizik veya simülasyon state'ini örtük biçimde değiştirmesini engellemek.
9. Gelecekteki ELDORIA CONTENT EDITOR'ün ayrı masaüstü uygulaması olarak geliştirilebilmesini sağlayacak modüler sınırları korumak.

## 3. Kapsam

### 3.1 Dahil olanlar

**A. Mevcut içerik mimarisinin denetimi**
- Aşama 13 geometri, canvas, palette, variation, components, profiles ve cache API'lerini inceleme.
- Mevcut çevresel nesne tanımları, yerleşimler, renderer adaptörleri ve collider ayrımını inceleme.
- Laboratuvardaki dünya/harita temsillerini ve mevcut koordinat sözleşmelerini inceleme.
- Dosya saklama, test, CI, Ruff ve artifact örüntülerini inceleme.
- Gelecekteki ayrı masaüstü editör için bağımlılık ve paket sınırlarını değerlendirme.

**B. İçerik tanım sözleşmesi**
- İçerik tanımı (ör. ağaç profili veya gelecekteki bina tanımı) ile dünyadaki yerleşmiş örneği birbirinden ayırma.
- Kararlı içerik kimliği, tür/kategori, şema sürümü ve gerekli metadata alanlarını belirleme.
- Parametre, bileşen, palet ve deterministik seed alanlarının veri olarak temsil edilebilirliğini belirleme.
- Desteklenmeyen veya yalnızca kodla tanımlanabilen özellikler için açık sınırlar koyma.
- İçerik tanımlarının Python kodu veya çalıştırılabilir betik olarak saklanmasını engelleme.

**C. Yerleşim ve harita verisi için temel sözleşmeler**
- Bir içerik tanımının harita üzerindeki bir veya daha fazla örneğe nasıl referans vereceğini tasarlama.
- Yerleşim kimliği, içerik referansı, konum, yön/ölçek gibi gerekli dönüşüm alanlarını mevcut dünya koordinat mimarisine göre değerlendirme.
- Harita belgesi ile içerik kütüphanesi arasındaki ilişkiyi tanımlama.
- Gelecekte harita üzerine nesne/yapı ekleme, taşıma, düzenleme ve kaldırma işlemlerinin veri düzeyinde desteklenebilmesi için gerekli temel işlemleri belirleme.
- Bu aşamada tam harita editörü veya harita çizim arayüzü geliştirmeme.

**D. Serileştirme, sürümleme ve doğrulama**
- İnsan tarafından okunabilir ve sürüm kontrolüne uygun veri biçimini belirleme.
- İçerik kimliklerinin kararlılığını ve referans bütünlüğünü koruma.
- Şema/sürüm doğrulaması, tür ve aralık kontrolleri, eksik alan ve bilinmeyen alan davranışlarını belirleme.
- Bozuk veya uyumsuz içeriğin güvenli biçimde reddedilmesi.
- Kaydetme/yükleme işlemlerinin mevcut geçerli veriyi yarım yazım veya bozuk dosya nedeniyle kaybetmemesini sağlama.
- İleri/geri sürüm geçişi ihtiyacını ve destek sınırlarını belgeleme.

**E. Runtime adaptasyonu**
- Doğrulanmış içerik verisini mevcut procedural profile üreticilerine bağlayan ince adaptör/registry katmanını oluşturma.
- Mevcut beş profilin runtime görsellerini ve cache davranışını koruma.
- İçerik kütüphanesi ile renderer arasında editör bağımlılığı oluşturmama.
- Görsel profil verisi ile fizik/collider verisini ayrı tutma.

**F. Gelecekteki editör için mimari hazırlık**
- İçerik çekirdeğinin GUI veya masaüstü uygulama çatısına bağımlı olmamasını sağlama.
- Gelecekte ayrı bir masaüstü uygulamasının aynı içerik API'lerini kullanabilmesi için paket sınırlarını belirleme.
- Harita editörü, nesne/yapı çizim araçları, yerleştirme ve düzenleme iş akışları için teknik ön koşulları raporlama.
- ELDORIA CONTENT EDITOR'ün ayrı bir ürün/aşama olarak planlanması gerektiğini belgelemek.

### 3.2 Bu aşamanın dışında kalanlar

- ELDORIA CONTENT EDITOR masaüstü uygulamasının kendisi.
- Görsel profil tarayıcısı, parametre panelleri, renk seçiciler veya interaktif önizleme editörü.
- Harita oluşturma/düzenleme ekranı veya hex hücre boyama aracı.
- Harita üzerinde fareyle yapı/nesne yerleştirme, sürükleme, taşıma, çizme veya silme arayüzü.
- Bina/duvar/kapı gibi bütün yapı ailelerinin görsel tasarımını tamamlamak.
- Piksel tabanlı raster çizim programı, animasyon editörü veya 3B modelleme.
- Collider/fizik düzenleme editörü.
- Oyun içi görev, diyalog, envanter, ekonomi veya savaş editörü.
- NPC AI, yoldaş hareketi, pathfinding veya simülasyon davranış editörü.
- Ana oyun runtime'ına entegrasyon veya `demo_eldoria` dalına aktarım.
- Eklenti mağazası, çevrimiçi paylaşım veya çok kullanıcılı düzenleme.

Bu maddeler gelecekte ELDORIA CONTENT EDITOR ve ilgili dünya üretim aşamalarında ayrıca planlanacaktır.

## 4. Temel mimari ilkeler

1. **Önce veri, sonra arayüz:** Editör arayüzü geliştirmeden önce editörün kullanacağı içerik sözleşmeleri kurulmalıdır.
2. **İçerik tanımı ve yerleşim ayrımı:** Bir ağacın/yapının tanımı ile haritadaki belirli ağaç/yapı örneği aynı veri nesnesi olmamalıdır.
3. **Editör bağımsız çekirdek:** İçerik modeli, doğrulama ve serileştirme GUI/Pygame penceresine bağımlı olmamalıdır.
4. **Runtime güvenliği:** Runtime yalnızca doğrulanmış içerik verisini kabul etmelidir.
5. **Mevcut üretim altyapısını kullan:** Aşama 13'ün geometri, bileşen, palet, varyasyon, profil ve cache sistemleri temel alınmalıdır.
6. **Görsel/fiziksel ayrım:** Görsel içerik verisi collider veya fizik davranışını örtük biçimde değiştirmemelidir.
7. **Deterministik sonuç:** Seed ve parametreler aynı kaldığında üretim sonucu tekrarlanabilir olmalıdır.
8. **Veri güvenliği:** Hatalı dosya yükleme veya kaydetme mevcut geçerli içeriği bozmamalıdır.
9. **Genişletilebilirlik:** Gelecekte yeni nesne ve yapı türleri, mevcut içerik dosyalarını kırmadan eklenebilmelidir.
10. **Tek laboratuvar başlatıcısı:** `python -m hex_world_lab` korunmalıdır; Aşama 14 için editör launcher'ı oluşturulmayacaktır.

## 5. Önerilen iş paketleri

### 14.1 — Depo ve mimari denetimi
- Procedural profil API'leri, çevresel içerik tanımları, yerleşim ve collider ayrımını denetleme.
- Mevcut harita/dünya koordinatları ile map lifecycle sözleşmelerini inceleme.
- Serileştirme ve dosya yönetimi örüntülerini inceleme.
- Gelecekteki masaüstü uygulama için bağımlılık ve paket sınırlarını inceleme.
- Bulguları denetim raporuna kaydetme.

### 14.2 — İçerik modeli ve veri sözleşmeleri
- İçerik tanımı, içerik örneği/yerleşimi ve harita belgesi kavramlarını ayırma.
- Kimlik, tür, metadata, parametre, bileşen, palet ve seed alanlarını tanımlama.
- Mevcut beş procedural profilin hangi alanlarının veriyle ifade edilebileceğini belirleme.
- Gelecekteki yapı ve yerleştirilebilir nesne tanımlarının genişletilme yolunu belirleme.
- Şema ve uyumluluk ilkelerini belgeleme.

### 14.3 — İçerik serileştirme ve sürümleme
- Onaylanan veri biçimini ve şema sürümünü uygulama.
- İçerik tanımlarını güvenli biçimde kaydetme/yükleme.
- Kararlı kimlik ve referans bütünlüğü kontrollerini ekleme.
- Bozuk, eksik, bilinmeyen ve uyumsuz veri senaryolarını test etme.

### 14.4 — Doğrulama ve içerik registry/kütüphanesi
- İçerik türü ve profil parametreleri için merkezi doğrulama kuralları.
- İçerik tanımlarını kimlikleriyle bulup çözümleyen registry/kütüphane katmanı.
- Hatalı verinin renderer'a ulaşmasını engelleyen güvenli sınır.
- İçerik tanımı ile harita yerleşimi referanslarının doğrulanması.

### 14.5 — Runtime adaptörü ve mevcut profil uyumluluğu
- Doğrulanmış veriyi Aşama 13 procedural profile API'lerine bağlama.
- Beş mevcut profilin veri tabanlı tanımlarını ve varsayılanlarını uyarlama.
- Mevcut görsel sonuç, deterministik varyasyon ve cache davranışını koruma.
- Collider/fizik verisinin ayrı kalmasını doğrulama.

### 14.6 — Harita ve yerleşim altyapısı hazırlığı
- Denetim ve 14.2 sözleşmelerine göre harita belgesi ile yerleşim kayıtlarının temel veri yapısını uygulama.
- İçerik referansı, yerleşim kimliği ve dünya/harita koordinatı ilişkisini doğrulama.
- Yerleşim ekleme, güncelleme ve kaldırma işlemlerinin veri/API düzeyindeki kurallarını belirleme.
- Henüz görsel harita editörü, fareyle yerleştirme veya çizim arayüzü geliştirmeme.

### 14.7 — Bütünleşme, regresyon ve editör hazırlık raporu
- İçerik çekirdeği, registry, doğrulama, serileştirme ve runtime adaptörünü bütünleştirme.
- Mevcut dünya demosu ve beş procedural profil üzerinde regresyon testleri.
- Gelecekteki ELDORIA CONTENT EDITOR için tamamlanan ön koşulları ve açık kalan işleri raporlama.
- Teknik borç ve sonraki aşama önerilerini belgeleme.

### 14.8 — Bütünleşik doğrulama ve kabul
- Tam Pytest paketi ve yeni içerik/harita veri testleri.
- Ruff lint/format ve Laboratuvar/Core Quality GitHub Actions.
- Serileştirme round-trip, sürüm, bozuk dosya, referans bütünlüğü ve deterministik üretim testleri.
- Gerekli performans/bellek benchmarkları.
- Runtime görsel regresyon kanıtları ve artifact'ler.
- Kullanıcı masaüstü uygulama testi yerine, laboratuvarın mevcut demo ve içerik çıktılarının kabul kontrolü.
- Kapanış raporu ve Master Plan güncellemesi.

## 6. Kalite ve kabul hedefleri

Aşama 14 ancak aşağıdaki koşulların tamamı sağlandığında kapatılabilir:

- Beş mevcut procedural profilin tanımları kararlı ve doğrulanabilir veri olarak temsil edilebilir.
- İçerik tanımı ile harita üzerindeki yerleşim örneği birbirinden ayrılmıştır.
- İçerik kimlikleri, referanslar ve şema sürümleri doğrulanır.
- İçerik verisi kaydedilip yeniden yüklendiğinde kayıpsız round-trip sağlar.
- Bozuk/uyumsuz içerik güvenli biçimde reddedilir; geçerli veri korunur.
- Registry yalnızca doğrulanmış içerik sunar.
- Runtime adaptörü mevcut beş profilin görsel ve deterministik davranışını korur.
- Görsel içerik verisi collider/fizik state'ini örtük biçimde değiştirmez.
- Harita/yerleşim veri sözleşmeleri gelecekte içerik ekleme, güncelleme ve kaldırma işlemlerini destekleyecek biçimde belgelenmiş ve test edilmiştir.
- İçerik çekirdeği GUI veya masaüstü uygulama bağımlılığı taşımaz.
- Pytest, Ruff, Laboratuvar CI ve Core Quality kontrolleri başarılıdır.
- Benchmark ve regresyon kanıtları üretilmiştir.
- Kapanış raporu değişen dosyaları, commit SHA'lerini, test/CI kanıtlarını ve bilinen sınırlamaları kaydeder.

## 7. Kullanıcı kabul yaklaşımı

Bu aşamada kullanıcıdan bir editör arayüzünü test etmesi istenmeyecektir; çünkü böyle bir arayüz geliştirilmeyecektir. Kullanıcı kabulü mevcut laboratuvar demosunun açılması, beş procedural profilin görsel olarak bozulmadığının kontrolü ve içerik altyapısının mevcut dünya davranışını etkilemediğinin doğrulanması üzerine kurulacaktır.

Gelecekte ELDORIA CONTENT EDITOR geliştirildiğinde ayrı masaüstü kabul süreci hazırlanacaktır. Bu süreç harita açma/kaydetme, içerik yerleştirme, çizme, düzenleme, taşıma ve kaldırma gibi gerçek editör iş akışlarını kapsayacaktır.

## 8. Dal, güvenlik ve çalışma yöntemi

- Tüm denetim, plan, uygulama, test ve raporlama yalnızca `experiment/hex-world-laboratory` dalında yürütülür.
- `main` ve `demo_eldoria` dallarına yazılmaz ve merge yapılmaz.
- Laboratuvarın tek başlatıcısı `python -m hex_world_lab` olarak korunur.
- Kullanıcı genel planı onaylamadan teknik plan kesinleştirilmiş sayılmaz.
- Teknik plan ayrıca onaylanmadan kod değişikliği yapılmaz.
- Her GitHub yazma işleminden önce dal HEAD'i ve hedef dosya SHA/varlık durumu doğrulanır; işlem sonrası yeni HEAD ve korunan dallar tekrar kontrol edilir.
- Kapsam dışı yeni ihtiyaçlar kullanıcı onayı olmadan eklenmez.

## 9. Onay kapıları ve sıradaki adım

1. **Genel plan onayı:** Kullanıcı bu güncellenmiş belgeyi ve kapsam sınırlarını inceler.
2. **Ayrıntılı denetim:** Genel plan onayından sonra 14.1 denetimi tamamlanır.
3. **Teknik plan:** Gerçek depo bulgularına göre modüller, API'ler, veri şemaları, dosya değişiklik listesi, test matrisi ve kabul adımları hazırlanır.
4. **Teknik plan onayı:** Kullanıcı teknik planı ayrıca onaylar.
5. **Uygulama:** Yalnızca onaylanmış iş paketleri uygulanır.
6. **Otomatik doğrulama:** Pytest, Ruff, GitHub Actions ve benchmarklar tamamlanır.
7. **Kullanıcı kabulü:** Mevcut demo ve görsel regresyon kontrolleri yapılır.
8. **Kapanış:** Rapor hazırlanır ve Master Plan güncellenir.

**Bu belge yalnızca Aşama 14 Genel Planı'dır. Onay verilmeden teknik plan veya kod uygulaması başlatılmaz.**
