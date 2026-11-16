# Aşama 4.6 — Hareket Kabul Prototipi Genel Planı

> **Belge türü:** Alt aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Durum:** KULLANICI ONAYI BEKLİYOR — teknik mimari planı henüz hazırlanmadı  
> **Tarih:** 16 Kasım 2026  
> **Ön koşul:** Aşama 4.5 kullanıcı tarafından kapatıldı.

---

## 1. Amaç

Aşama 4.6, Aşama 4 Sürekli Hareket Sistemi'nin son alt aşamasıdır. 4.1–4.5 boyunca ayrı ayrı geliştirilen hareket veri sözleşmelerini, sabit tick yürütümünü, klavye adaptörünü ve hex dünya bağlantısını tek bir küçük kabul prototipinde bir araya getirerek uçtan uca doğrulamayı amaçlar.

Bu alt aşamanın temel sorusu şudur:

**Oyuncu klavyeden hareket komutu verdiğinde, aktör 60 TPS simülasyonunda kesintisiz dünya koordinatlarında ilerliyor mu; aynı anda doğru hex hücresi bulunuyor mu; bu davranış farklı render FPS değerlerinde ve harita sınırlarında mevcut sözleşmeleri bozmadan çalışıyor mu?**

Aşama 4.6 yeni bir hareket modeli veya yeni bir dünya sistemi tasarlamayacaktır. Önceki alt aşamaların çıktıları birleştirilecek, gözlemlenebilir hale getirilecek ve kabul testlerinden geçirilecektir.

## 2. Devralınacak ve değiştirilmeyecek sözleşmeler

Aşağıdaki mevcut bileşenler kullanılacaktır:

- `geometry.WorldPoint`: Aktörün kesirli ve authoritative fiziksel konumu.
- `MovementIntent`, `MovementConfig`, `MovementState` ve `MovementIntegrator`: Hareket veri sözleşmeleri ve sabit hızlı hareket hesabı.
- `MovementSystem`: Dışarıdan verilen ardışık simülasyon tick'lerinde hareketi bir kez ilerletir.
- `DemoTickPump`: Laboratuvar demosu için 60 TPS tick üretir; render karesi başına en fazla 8 tick işler ve kalan tick borcunu düşürmeden sonraki kareye taşır.
- `PygameKeyboardAdapter`: WASD ve ok tuşlarını hareket niyetine çevirir; odak kaybında nötr girdi üretir.
- `MovementWorldContext`, `MovementCellResolution` ve `MovementCellTracker`: Tek yüklü harita bağlamında konumdan hücre çözümlemesi yapar ve önceki hücreyi takip eder.
- `HexLayout`, `world_to_axial` ve `HexWorldView`: Geometri ve güncel hücre verisi için mevcut kanonik API'ler.

Aşağıdaki ilkeler korunacaktır:

1. Fiziksel konumun tek doğruluk kaynağı `MovementState.position` olarak kalır.
2. Hücre adresi fiziksel konumdan türetilir; konum hücre merkezine taşınmaz.
3. Hareket çekirdeği Pygame, çizim veya dünya modeline bağımlı hale getirilmez.
4. Hareket kendi saatini, tick sayacını veya bağımsız zaman biriktiricisini oluşturmaz.
5. Harita dışı konum hareketi durdurmaz; çözümleme sonucu hücre verisi yoksa `cell_data=None` olur.
6. Harita otomatik yüklenmez ve başka haritaya otomatik geçiş yapılmaz.
7. Aşama 2 geometri ve Aşama 3 dünya/persistence sözleşmeleri değiştirilmez.

## 3. Kapsam içi işler

### 3.1 Tek haritalı kabul sahnesi

- Laboratuvarın mevcut harita tanımı ve dünya API'leri kullanılarak tek bir deterministik test haritası hazırlanır.
- Harita, açık hücre kümesiyle sınırlı ve tekrarlanabilir olmalıdır; rastgele üretim kullanılmaz.
- Prototip tek bir kayıtlı ve yüklü harita üzerinde çalışır.
- Aktör, haritadaki belirli bir hücrenin merkezinde başlatılır; hareket başladıktan sonra kesirli dünya koordinatlarında ilerler.
- Başlangıç konumu, harita kimliği, layout ve hız değerleri prototip yapılandırmasında açıkça tanımlanır.
- Harita verisi için yeni bir format veya yeni persistence sistemi oluşturulmaz.

### 3.2 Uçtan uca hareket akışı

Her simülasyon tick'inde aşağıdaki sıra gözlemlenebilir ve test edilebilir olmalıdır:

1. Ana Pygame döngüsü olayları işler.
2. Klavye adaptörü güncel tuş durumundan `MovementIntent` üretir.
3. `DemoTickPump` bir veya daha fazla 60 TPS tick'i yürütür.
4. Her tick için `MovementSystem.step()` tam bir kez çağrılır.
5. Yeni `MovementState.position`, `MovementCellTracker.update()` metoduna verilir.
6. Çizim ve teşhis katmanı son state ile son hücre çözümlemesini salt okunur biçimde gösterir.

Bu sıra, render kare sayısı ile simülasyon tick sayısının birbirine karıştırılmasını önlemelidir. Aynı tick içinde hareketin iki kez uygulanmasına izin verilmez.

### 3.3 Minimal Pygame gözlem görünümü

Yalnızca hareketi değerlendirmek için gereken görsel öğeler hazırlanır:

- Sabit ölçekte ve sabit ekranda gösterilen tek hex harita.
- Hücre sınırlarını gösteren sade hex ızgarası.
- Hareketli aktörü temsil eden basit bir işaretçi.
- Aktörün karşılık geldiği hücrenin görsel vurgusu.
- Aktörün fiziksel konumunun hücre merkezine kilitlenmediğini gösterecek kesintisiz hareket.
- Harita dışında veya açık hücre kümesinde bulunmayan konuma ulaşıldığında, aktörün hareketinin kesilmediğini gösterecek davranış.

Bu çizim, prototipe özel basit bir dünya-koordinatı → pencere-koordinatı gösterimidir. Genel amaçlı kamera, zoom, pan veya ana oyun render mimarisi oluşturulmayacaktır. Görsel katman hareket state'ini değiştiremez.

### 3.4 Teşhis paneli

Prototipte en az şu bilgiler gösterilmelidir:

- WorldId ve MapId.
- Kesirli dünya konumu `x, y`.
- Hız vektörü ve hız büyüklüğü.
- Son çözümlenen axial `q, r` koordinatı.
- Hücre verisinin mevcut olup olmadığı.
- Son işlenen simülasyon tick numarası veya toplam tick sayısı.
- Render FPS.
- Tick pump'ın bekleyen tick borcu ve mevcut karede işlenen tick sayısı.

Teşhis değerleri mevcut state ve diagnostics verilerinden okunur. Panel kendi zaman veya hareket hesabını yürütmez. Eksik bir diagnostics alanı gerekiyorsa bunun kaynağı teknik mimari planında belirlenecek; ikinci bir tick sayacı oluşturulmayacaktır.

### 3.5 Otomatik kabul ve regresyon testleri

Prototipin görsel olarak çalışması tek başına yeterli kabul edilmeyecektir. GUI gerektirmeyen otomatik testler aşağıdakileri kanıtlamalıdır:

- Klavye girdisinden hareket state'ine, oradan hücre çözümlemesine kadar uçtan uca akış.
- Tek eksen ve çapraz hareket.
- Tuş bırakıldığında durma; odak kaybında nötr girdiye geçiş.
- Kesirli konumun ve hücre sınırı geçişinin korunması.
- Harita dışı konumda hareketin devam etmesi.
- Hücre çözümleme sonucunun hareket konumunu değiştirmemesi.
- Render FPS değişse de aynı sıralı tick/girdi dizisinin aynı sonucu üretmesi.
- Tick pump'ın kare başına 8 adım sınırını ve kalan tick borcunu koruması.
- Pygame bağımlılığının hareket çekirdeğine sızmaması.

### 3.6 Performans ölçümü

Aşama 4 genel planındaki ölçüm hedefleri doğrultusunda:

- Hareket + hücre çözümleme maliyeti, 1 / 10 / 100 / 1.000 bağımsız aktör state'i için ölçülür.
- Ortalama ve P95 güncelleme süresi kaydedilir.
- Tick pump normal yük ve catch-up durumunda gözlemlenir.
- Harita hücrelerinin topluca taranmadığı, yalnızca gerekli geometri dönüşümü ve doğrudan hücre sorgusunun yapıldığı incelenir.
- Ölçüm ortamı, Python sürümü, işletim sistemi ve commit SHA rapora yazılır.

Bu ölçümler performans profili çıkarmak içindir; bu alt aşamada yeni optimizasyon veya FPS garantisi hedeflenmez. Sorun görülürse önce ölçüm ve etki analizi yapılır; kapsamlı optimizasyon ayrıca onaylanır.

### 3.7 Manuel görsel kabul kontrolü

Gerçek Pygame penceresinde aşağıdaki senaryoların kontrol edilmesi için kısa bir kontrol listesi hazırlanır:

- Prototipin açılması ve hatasız kapanması.
- WASD ve ok tuşlarıyla dört ana yönde hareket.
- Çapraz hareketin tek eksen hareketinden hızlı olmaması.
- Tuş bırakıldığında aktörün durması.
- Pencere odağı kaybolduğunda hareketin sürmemesi.
- Hücre sınırlarının kesintisiz geçilmesi ve aktörün merkezlere sıçramaması.
- Harita kenarının ötesinde hareketin fiziksel olarak kesilmemesi.
- Teşhis panelindeki axial hücre bilgisinin görsel konumla tutarlı olması.

Manuel kontrol, otomatik testlerin yerine geçmez. Bilgisayara erişim olmadığında bu kontrol ertelenir ve raporda tamamlanmamış olarak açıkça belirtilir.

## 4. Önerilen alt iş sırası

| Alt iş | Amaç | Beklenen çıktı |
|---|---|---|
| 4.6.1 — Prototip sahnesi | Tek haritalı, deterministik kabul ortamı | Yüklü test haritası ve başlangıç aktörü |
| 4.6.2 — Uçtan uca orkestrasyon | Klavye → tick pump → movement → cell tracker akışını bağlamak | Çalışan tek aktör simülasyon döngüsü |
| 4.6.3 — Görsel gözlem | Hex ızgarası ve aktör işaretçisi | Minimal Pygame prototipi |
| 4.6.4 — Teşhis paneli | Konum, hız, hücre ve zaman değerlerini görünür kılmak | Salt okunur diagnostics |
| 4.6.5 — Kabul/regresyon testleri | Uçtan uca ve FPS bağımsızlığı kanıtı | Otomatik test paketi |
| 4.6.6 — Performans ve manuel kontrol | Ölçüm ve görsel kontrol | Benchmark ve manuel kontrol raporu |
| 4.6.7 — Kapanış | Tüm kanıtları bir araya getirmek | Aşama 4.6 kapanış raporu ve Aşama 4 genel değerlendirmesi |

Alt işlerin dosya sınırları, test isimleri ve teknik API'leri teknik mimari planında kesinleştirilecektir.

## 5. Kapsam dışı işler

Aşama 4.6'da aşağıdakiler yapılmayacaktır:

- Çarpışma, collider, fizik, duvar/engel çözümü veya yürüme alanı kontrolü.
- Pathfinding veya NPC/çoklu aktör karar sistemi.
- Kamera, zoom, pan, takip kamerası veya genel world-to-screen altyapısı.
- Nihai sanat tasarımı, sprite/karakter animasyonu, y-sort veya oyun HUD'ı.
- Birden fazla harita arasında geçiş veya otomatik harita yükleme/tahliye.
- Hareket state'inin kayıt dosyasına eklenmesi.
- Ana Eldoria oyununa veya `demo_eldoria` dalına entegrasyon.
- Godot veya başka oyun motoruna geçiş.
- Multiplayer/ağ senkronizasyonu.
- Ölçümle gerekçelendirilmemiş optimizasyon veya yeni bağımlılık.

## 6. Test ve kabul ölçütleri

Aşama 4.6'nın kabulü için aşağıdaki kanıtlar gereklidir:

### 6.1 Davranışsal kabul

- Prototip tek bir yüklü haritada başlar ve kontrollü biçimde kapanır.
- Klavye girdisi hareket niyetine doğru çevrilir.
- Hareket her canonical demo tick'inde en fazla bir kez uygulanır.
- Fiziksel konum kesirli kalır ve hücre merkezine snap edilmez.
- Hücre takibi hareketin ardından güncellenir.
- Hücre sınırı tie-break kuralı korunur.
- Eksik hücre veya harita kenarı hareketi durdurmaz.
- Teşhis görünümü simülasyon state'ini değiştirmez.

### 6.2 Zaman ve deterministik kabul

- Aynı başlangıç state'i ve aynı sıralı tick/girdi dizisi aynı sonucu üretir.
- 30, 60 ve 120 render FPS senaryoları aynı toplam simülasyon tick sayısında eşdeğer son konuma ulaşır.
- Catch-up durumunda kare başına en fazla 8 tick yürütülür.
- Kalan tick borcu silinmez veya gizlenmez.
- Render FPS, hareket hızının kaynağı olmaz.

### 6.3 Mimari ve regresyon kabulü

- Hareket çekirdeği Pygame import etmeden test edilebilir.
- Dünya/geometry entegrasyonu yalnızca mevcut API'leri kullanır.
- Aşama 2 geometri testleri ve Aşama 3 world/persistence testleri korunur.
- Laboratuvarın tam pytest paketi başarılı olur.
- Laboratuvar CI ve Core Quality CI Linux/Windows doğrulamaları başarılı olur.
- Ana oyun ve korunan dallarda değişiklik yapılmaz.

### 6.4 Performans kabulü

- 1 / 10 / 100 / 1.000 aktör senaryolarının ölçüm sonuçları raporlanır.
- Ortalama ve P95 süreler kaydedilir.
- Benchmark koşulları ve commit SHA raporda yer alır.
- Ölçüm olmadan performans veya ölçeklenebilirlik garantisi verilmez.
- Ölçüm sırasında ciddi bir darboğaz görülürse çözüm otomatik olarak bu aşamaya eklenmez; ayrı etki analizi sunulur.

### 6.5 Görsel kabul

- Manuel kontrol listesi gerçek Pygame penceresinde uygulanır.
- Görsel kontrol yapılamadıysa bu durum açıkça raporlanır; CI sonucu manuel görsel kabul yerine yazılmaz.

## 7. Başlıca riskler ve kontroller

| Risk | Olası sonuç | Kontrol |
|---|---|---|
| Prototipin yeni oyun mimarisine dönüşmesi | Aşama kapsamının büyümesi | Tek harita, tek aktör ve basit gösterim sınırı |
| Render döngüsünün hareket state'ini değiştirmesi | Zaman ve state tutarsızlığı | Simülasyon/çizim ayrımı ve salt okunur diagnostics |
| Tick pump'ın kalan zamanı düşürmesi | Simülasyon zamanı kaybı | Mevcut backlog koruma sözleşmesini değiştirmemek |
| Hücre takibinin konumu düzeltmesi | Hücre merkezine sıçrama | Tracker yalnızca çözümleme yapar |
| Pygame bağımlılığının core'a taşınması | Headless testlerin bozulması | Mimari import testi |
| Görsel testlerin CI'da pencere gerektirmesi | Platforma bağlı CI hatası | Otomatik testleri headless, görsel kontrolü manuel tutmak |
| Benchmark sonuçlarının yanlış yorumlanması | Gerçek dışı performans iddiası | Donanım ve çalışma koşullarını raporlamak |

## 8. Beklenen teslimatlar

1. Tek haritalı deterministik hareket kabul sahnesi.
2. Klavye → DemoTickPump → MovementSystem → MovementCellTracker uçtan uca bağlantısı.
3. Minimal Pygame hex ızgara ve aktör görünümü.
4. Salt okunur hareket ve zaman teşhis paneli.
5. Uçtan uca, FPS eşdeğerliği ve mimari regresyon testleri.
6. 1 / 10 / 100 / 1.000 aktör performans ölçüm raporu.
7. Manuel görsel kabul kontrol listesi ve sonucu.
8. `reports/PHASE-04.6-CLOSURE-REPORT.md`.
9. Aşama 4 tamamlandığında, 4.1–4.6 sonuçlarını birleştiren `reports/PHASE-04-MOVEMENT-REPORT.md` genel kapanış raporu için kanıt seti.

## 9. Uygulama, onay ve kapanış kapıları

1. Bu genel plan kullanıcıya sunulur ve onayı beklenir.
2. Onaydan sonra mevcut dosya ağacı ve 4.1–4.5 uygulaması tekrar incelenerek 4.6 teknik mimari planı hazırlanır.
3. Teknik mimari planı kullanıcı tarafından ayrıca onaylanır.
4. Yalnızca onaylanan kapsam `experiment/hex-world-laboratory` dalında uygulanır.
5. Hedefli testler, tam pytest, laboratuvar CI ve Core Quality CI çalıştırılır.
6. Bilgisayara erişim olduğunda manuel görsel kontrol yapılır; erişim yoksa açık takip maddesi olarak raporlanır.
7. Kapanış raporu gerçek test, CI, benchmark ve commit kanıtlarıyla oluşturulur ve GitHub'dan tekrar okunarak doğrulanır.
8. Kullanıcı 4.6 kapanışını kabul ettikten sonra Aşama 4 genel kapanış raporu hazırlanır ve Aşama 4 kapatılır.

Bu genel planın onayı teknik planı veya kod uygulamasını otomatik olarak onaylamaz.

## 10. Dal güvenliği

- Planlama ve uygulama belgeleri yalnızca `experiment/hex-world-laboratory` dalında tutulur.
- `main` ve `demo_eldoria` dallarına yazma, merge, cherry-pick, rebase veya reset yapılmaz.
- Aşama 4.6, Aşama 4'ün son alt aşamasıdır; tamamlanması Aşama 5'i otomatik başlatmaz.
- Aşama 5 için ayrı genel plan ve kullanıcı onayı gerekir.

## 11. Genel planın kabul durumu

Bu belge, Aşama 4 genel planındaki 4.6 kabul prototipi hedefini ve 4.1–4.5 boyunca kesinleşen gerçek mimari sözleşmeleri esas alır.

**Mevcut durum:** Aşama 4.6 genel planı hazırlandı ve laboratuvar dalına eklendi. Kullanıcı onayı beklenmektedir. Teknik plan ve kod uygulaması henüz başlatılmamıştır.
