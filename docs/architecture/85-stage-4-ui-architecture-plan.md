# Aşama 4 — Arayüzün Yeni Mimariye Tam Uyumu

**Durum:** Tamamlandı (2026-11-27) — otomatik CI ve gerçek oyun penceresi manuel kabulü kullanıcı tarafından başarılı olarak doğrulandı  
**Hedef dal:** `experiment/map-cleanup`  
**Çalışma biçimi:** Tek ve bütünleşik aşama. A4.1, A4.2 veya benzeri alt aşamalar oluşturulmayacak.

## 1. Amaç

Mevcut oyun ekranlarını, pencere yönetimini ve kullanıcı girdisi yönlendirmesini Aşama 3'te tamamlanan GameplayService ve merkezi oyuncu bağlamı sözleşmeleriyle tutarlı hâle getirmek. Mevcut oynanış davranışını korurken ekranların birbirinden bağımsız, öngörülebilir ve güvenilir çalışmasını sağlamak.

Bu aşama yeni oynanış özelliği geliştirme veya görsel tasarımı baştan ele alma çalışması değildir.

## 2. Kapsam

### 2.1. Ekranların servis ve kimlik sözleşmesine uyumu

Aşağıdaki mevcut ekranlar aynı mimari kontrol listesinden geçirilecek:

- Karakter ve karakter oluşturma
- Envanter
- Pazar ve para değişimi
- Diyalog
- Görev günlüğü
- Üretim
- Konteyner
- Ticaret
- Savaş

Kontroller:
- Oyuncu/aktör/karakter kimliği merkezi oyuncu bağlamından ve yetkili servis API'lerinden çözülür.
- UI, iş kurallarını yeniden uygulamaz; veri ve komutlar için GameplayService'in public sözleşmesini kullanır.
- Ekranlar birbirlerinin private durumuna veya iç uygulama ayrıntılarına erişmez.
- Snapshot/koleksiyon sırası, ilk eleman veya örtük varsayımlar kimlik seçimi için kullanılmaz.
- Ekran açma, kapatma ve yeniden açma işlemleri eski oturum verisi veya bozuk geçici durum bırakmaz.

### 2.2. Pencere yönetimi ve ekran yaşam döngüsü

WindowManager ve GameWindow birlikte ele alınacak.

- Dünya/oyun görünümü arka planda sürekli görünür kalır.
- Oynanış panelleri mevcut pencere sistemi üzerinden yönetilir.
- Uygun panellerin sürükleme ve boyutlandırma davranışı tutarlı olur.
- Odak ve z-sırası doğru yönetilir.
- Bir pencerenin kapatılması diğer açık pencereleri kapatmaz veya durumlarını bozmaz.
- Pencereler kapatılıp yeniden açıldığında geçerli servis/oturum durumuyla tutarlı biçimde kurulur.
- Fare olayları doğru pencereye yönlendirilir.
- Sürükle-bırak sırasında pointer capture, odak ve hedef pencere davranışı korunur.

### 2.3. Klavye, fare ve menü sözleşmesi

**ESC davranışı — kesin karar:**
- ESC tuşuna basıldığında duraklatma menüsü açılır.
- Açık envanter, karakter, görev günlüğü veya başka bir oyun paneli ESC nedeniyle önce kapatılmaz.
- Bu kural, açık panel bulunup bulunmamasından bağımsızdır.
- Duraklatma menüsü açıkken ESC'ye tekrar basıldığında menü kapanır ve oyun devam eder; açık oyun panelleri korunur.
- Pencere kapatma, ilgili pencerenin kendi kapatma düğmesi/kontrolüyle yapılır; ESC genel pencere kapatma kısayolu değildir.

Diğer girdi kuralları:
- Pencere kısayolları yalnızca hedefledikleri paneli açar/kapatır.
- X ve pencere kapatma kontrolleri yalnızca ilgili pencereyi etkiler.
- WASD ve ok tuşları mevcut hareket girdisi sözleşmesine uygun yönlendirilir; hareket mekaniği veya hızları bu aşamada değiştirilmez.
- Odak dışındaki ekranlara klavye/fare girdisi sızmaz.
- Duraklatma menüsündeki devam et, kaydet, ana menü ve çıkış seçeneklerinin mevcut davranışı korunur ve doğrulanır.

## 3. Test ve regresyon kapsamı

- Her ekran için açma, kapatma ve yeniden açma.
- Aynı anda birden fazla pencere açıkken bağımsız yaşam döngüsü.
- Odak, z-sırası, sürükleme ve boyutlandırma.
- ESC'nin açık panel varken ve panel yokken duraklatma menüsünü açması.
- Duraklatma menüsü açıkken ESC'nin tekrar kullanımı.
- X ve pencere kapatma kontrolünün yalnızca hedef pencereyi kapatması.
- Klavye/fare olaylarının doğru ekrana yönlendirilmesi.
- Envanter-konteyner sürükle-bırak akışı.
- Pencereyi kapatıp yeniden açma ve kayıt yükleme sonrasında durum tutarlılığı.
- Merkezi oyuncu kimliği ve GameplayService sınırlarının UI genelinde korunması.
- Pygame headless smoke, ilgili hedefli testler, tam test paketi ve kalite kapıları.

Testler mevcut davranışı kanıtlamalı; yapılmayan manuel kabul veya çalıştırılmayan CI başarılı olarak raporlanmamalıdır.

## 4. Manuel kabul

Manuel kabul gerçek Pygame oyun penceresinde, kullanıcının mevcut oyun kaydı ve mevcut içerikle yapılacaktır. Her kontrol sonucu **Geçti / Başarısız / Uygulanamadı** olarak kaydedilecek; uygulanamayan akışlar başarılı sayılmayacaktır.

### 4.1. Ekran açma, kapatma ve odak

- Karakter (C), envanter (I) ve görev günlüğü (J) pencerelerini ayrı ayrı açıp kapat.
- İki veya daha fazla pencereyi aynı anda açık tut; her birine tıklayarak odağı değiştir.
- Pencere başlığından sürükle; uygun kenar/köşelerden boyutlandır.
- Bir pencerenin kapatma düğmesine bas. Yalnızca hedef pencerenin kapandığını, diğer pencerelerin açık kaldığını doğrula.
- Kapatılan pencereyi yeniden aç. İçerik, seçili öğe ve servis verisinin tutarlı olduğunu kontrol et.

### 4.2. Pazar ve para değişimi

- Mevcut diyalog akışından pazar ekranını aç.
- Pazar penceresindeki para değişimi kontrolünü kullan.
- Para değişimi penceresinin açıldığını, pazar penceresinin beklenmedik biçimde kapanmadığını doğrula.
- Para değişimi penceresini kapat; pazar penceresinin kullanılabilir kaldığını kontrol et.
- Mevcut bakiyelerle izin verilen bir dönüşüm yap ve bakiyelerin güncellendiğini doğrula.

### 4.3. Üretim ve tesis bağlamı

- Üretim kısayoluyla üretim ekranını aç.
- Mevcut bir tesis etkileşiminden üretim ekranına geçişi dene.
- Tarif seçimi, uygun tesis ve kaynak durumunun doğru gösterildiğini kontrol et.
- Pencereyi kapatıp yeniden aç; geçerli tesis bağlamının bozulmadığını doğrula.

### 4.4. Konteyner ve sürükle-bırak

- Mevcut dünyadaki bir konteyneri aç.
- Envanter penceresini de aç ve bir eşyayı diğer pencereye sürükleyerek aktar.
- Aktarımın doğru miktar ve doğru envanterler arasında gerçekleştiğini kontrol et.
- Sürükleme sürerken kaynak pencereyi kapat; takılı kalan sürükleme imleci veya sonraki fare girdilerinde kilitlenme olmadığını doğrula.
- Konteyneri kapatıp yeniden aç; içerik ve pencere durumu tutarlılığını kontrol et.

### 4.5. Diyalog, görev günlüğü ve savaş

- Mevcut NPC ile diyalog başlat; geçmiş panelini aç/kapat ve seçenek seçimini dene.
- Mevcut içerik izin veriyorsa diyalogdan pazar geçişini doğrula.
- Görev günlüğünde kategori değiştirme, liste kaydırma ve ayrıntı görüntülemeyi dene.
- Mevcut savaş akışını açıp ekrandaki mevcut komutların çalıştığını doğrula; savaş mekaniğini değiştirme.
- Görev veren NPC bulunmadığından gerçek görev alma/teslim etme akışı bu manuel kabulde ertelenmiş olarak kalır.

### 4.6. ESC ve duraklatma menüsü

- Hiçbir oyun penceresi açık değilken ESC'ye bas; duraklatma menüsü açılmalı.
- Envanter veya karakter gibi bir pencere açıkken ESC'ye bas; pencere kapanmadan duraklatma menüsü açılmalı.
- Duraklatma menüsü açıkken seçimi başka bir öğeye taşı ve ESC'ye tekrar bas; menü kapanmalı, oyun panelleri açık kalmalı.
- Devam et seçeneğini kullan; oyun ve açık pencereler beklenen durumla devam etmeli.
- Kaydet ve ana menüye dön seçeneklerini mevcut kayıtla doğrula.

### 4.7. Ekran boyutu ve kayıt yükleme

- Pencere boyutunu değiştir veya tam ekranı aç/kapat; pencerelerin görünür alan içinde kaldığını ve fare hedeflerinin doğru çalıştığını kontrol et.
- Birden fazla pencere açıkken kayıt yükle; eski oturuma ait pencere/drag durumu kalmadığını ve yeni ekranların güncel servis bağlamını kullandığını doğrula.
- Oyun dünyasının pencere panellerinin arkasında görünür kaldığını kontrol et.

**Ertelenmiş genel oyun kabul maddeleri:**
- Görev veren NPC bulunmadığından gerçek görev alma/teslim etme akışı, uygun içerik mevcut olduğunda doğrulanacaktır. Bu aşama için yeni NPC veya görev içeriği eklenmeyecektir.
- Ticaret ekranının gerçek oyun içi manuel kabulü, hancı NPC eklemeden, tüm geliştirme aşamalarının sonundaki genel oyun kabulüne ertelenmiştir. Bu aşamada sırf test amacıyla hancı/NPC eklenmeyecektir.

## 5. Açıkça kapsam dışı

- Yeni oyun mekaniği, görev, NPC veya içerik eklemek.
- Savaş kurallarını veya savaş mekaniğini yeniden tasarlamak.
- Harita, hareket, çarpışma, pathfinding veya kamera değişiklikleri.
- Karakter rig'i, animasyon veya render değişiklikleri.
- Yeni görsel tasarım projesi veya kapsamlı UI yeniden tasarımı.
- Kayıt sistemini baştan yazmak.
- Aşama 3'te tamamlanan servis/kimlik sözleşmelerini gerekçe olmadan yeniden açmak.
- Bu aşamanın dışında kalan mimari temizliğe yönelmek.

## 6. Tamamlanma ölçütleri

Aşama 4 ancak aşağıdaki koşullar birlikte sağlandığında tamamlanır:

1. Kapsamdaki ekranlar merkezi oyuncu kimliği ve GameplayService public API sözleşmelerine uygundur.
2. Pencere açma-kapama, yeniden açma, odak, z-sırası ve fare yönlendirmesi tutarlıdır.
3. ESC duraklatma menüsünü açıp kapatır; kapatma sırasında açık oyun panelleri korunur.
4. Hedefli regresyon testleri, tam test paketi ve kalite kapıları başarılıdır.
5. Gerçek oyun penceresindeki Aşama 4 kapsamındaki manuel kabul akışları kullanıcı tarafından başarılı olarak doğrulanmıştır.
6. Ertelenmiş görev ve ticaret kabul maddeleri tamamlanmış gibi gösterilmez.
7. Değişiklikler yalnızca bu aşamanın kapsamındadır; roadmap ve teknik notlar kanıtlarla güncellenmiştir.

## 7. Uygulama ilkesi

Önce mevcut ekran, pencere yöneticisi, GameWindow ve test davranışları ayrıntılı incelenecek; ardından tek bütünleşik Aşama 4 kapsamında gerekli değişiklikler yapılacaktır. İç çalışma sırasında mantıksal commit'ler kullanılabilse de alt aşama tanımlanmayacak ve aşama tamamlanmadan ara alt-aşama kapanışları ilan edilmeyecektir.

**Kapanış kaydı (2026-11-27):** Aşama 4 kapsamındaki otomatik doğrulamalar son commit `578556d01aab34f33af3b3516599dd191e3bd3a3` üzerinde Eldoria CI (`45988005961`, 5/5 iş) ve Core Quality (`45988005662`, 2/2 iş) ile başarılıdır. Gerçek oyun penceresindeki manuel testlerin de başarılı olduğu kullanıcı tarafından doğrulanmıştır. Böylece Aşama 4 tamamlanmıştır. Görev alma/teslim etme, görev veren NPC bulunmadığı için; ticaret ekranının gerçek oyun içi kabulü ise hancı/NPC eklenmeden genel oyun kabulüne ertelenmiştir. Bu iki ertelenmiş madde Aşama 4 kapsamında test edilmiş veya başarılı sayılmamıştır.
