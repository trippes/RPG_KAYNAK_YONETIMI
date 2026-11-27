# Aşama 4 — Arayüzün Yeni Mimariye Tam Uyumu

**Durum:** Plan revize edildi; uygulama henüz başlamadı  
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
- ESC tuşuna her basıldığında duraklatma menüsü açılır.
- Açık envanter, karakter, görev günlüğü veya başka bir oyun paneli ESC nedeniyle önce kapatılmaz. ESC'nin görevi duraklatma menüsünü açmaktır.
- Bu kural, açık panel bulunup bulunmamasından bağımsızdır.
- Duraklatma menüsü zaten açıkken ESC'ye tekrar basılmasının mevcut menü durumuyla etkileşimi incelenir; oyun yanlışlıkla devam ettirilmez ve menü beklenmedik biçimde kapatılmaz. Nihai tekrar-basım davranışı mevcut menü sözleşmesi ve testlerle açıkça tanımlanır.
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

Mevcut oyun penceresinde en az şu akışlar doğrulanacak:
- Karakter ve envanter ekranları.
- Pazar, para değişimi ve üretim ekranları.
- Diyalog ve görev günlüğü ekranları.
- Konteyner açma ve eşya aktarımı.
- Mevcut savaş ekranı akışı.
- Birden fazla pencerenin birlikte kullanımı, odak ve pencere yaşam döngüsü.
- ESC'nin açık panel olsun veya olmasın duraklatma menüsünü açması.
- Duraklatma menüsünden devam etme ve ana menüye dönüş.

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
3. ESC her durumda duraklatma menüsünü açar; açık panelleri kapatma davranışına dönüşmez.
4. Hedefli regresyon testleri, tam test paketi ve kalite kapıları başarılıdır.
5. Gerçek oyun penceresindeki manuel kabul akışları kullanıcı tarafından doğrulanmıştır.
6. Ertelenmiş görev ve ticaret kabul maddeleri tamamlanmış gibi gösterilmez.
7. Değişiklikler yalnızca bu aşamanın kapsamındadır; roadmap ve teknik notlar kanıtlarla güncellenmiştir.

## 7. Uygulama ilkesi

Önce mevcut ekran, pencere yöneticisi, GameWindow ve test davranışları ayrıntılı incelenecek; ardından tek bütünleşik Aşama 4 kapsamında gerekli değişiklikler yapılacaktır. İç çalışma sırasında mantıksal commit'ler kullanılabilse de alt aşama tanımlanmayacak ve aşama tamamlanmadan ara alt-aşama kapanışları ilan edilmeyecektir.

Bu belge planı tanımlar; kod değişikliği, test çalıştırması veya manuel kabul yapıldığı anlamına gelmez.
