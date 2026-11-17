# Eldoria Hex World Laboratory — Master Plan

> **Belge türü:** Ana laboratuvar yol haritası ve çalışma sözleşmesi  
> **Proje:** Eldoria — Kaynak Yönetimi RPG  
> **Depo:** `trippes/RPG_KAYNAK_YONETIMI`  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Hedef entegrasyon dalı:** `demo_eldoria`  
> **Durum:** AŞAMA 0–7 TAMAMLANDI VE KABUL EDİLDİ — AŞAMA 8 SIRADAKİ PLANLI AŞAMA  
> **Belge sürümü:** 1.6

---

## 1. Belgenin amacı ve bağlayıcılığı

Bu belge, Eldoria'nın canon altıgen dünya mimarisini bağımsız bir laboratuvarda araştırmak, tasarlamak, prototiplemek, ölçmek ve doğrulamak için izlenecek ana plandır.

Laboratuvarın hedefi yalnızca karakterin altıgen haritada hareket etmesini sağlamak değildir. Hedef; geometri, koordinat sistemleri, dünya modeli, sürekli hareket, fizik, çarpışma, kamera, çizim, mekânsal sorgulama, varlıklar, etkileşimler, simülasyon ve performans katmanlarını birbiriyle tutarlı tek bir mimari altında birleştirmektir. Sonuç, ana oyuna aktarılabilecek kadar belgelenmiş ve test edilmiş bir altıgen dünya altyapısı olmalıdır.

Bu belge, laboratuvardaki sonraki çalışmalar için birincil referanstır. Her yeni görev ve değişiklik bu plana göre değerlendirilir. Planda bulunmayan yeni bir kapsam, mimari değişiklik veya aşama sırası değişikliği doğrudan uygulanmaz; önce gerekçesi yazılır, etkisi değerlendirilir ve kullanıcı onayı alınır.

### 1.1 Öncelik sırası

Çalışma sırasında çelişki oluşursa aşağıdaki sıra izlenir:

1. Kullanıcının bu sohbette verdiği en güncel açık talimat.
2. Bu Master Plan'ın onaylanmış en güncel sürümü.
3. Onaylanmış mimari karar kayıtları (ADR).
4. İlgili aşamanın teknik tasarım ve kabul belgeleri.
5. Laboratuvar kodu ve deney sonuçları.

Kod, belgelendirilmiş mimari kararı sessizce değiştiremez. Deneyler planın varsayımlarından birinin yanlış olduğunu gösterirse önce bulgu raporlanır; ardından plan/ADR güncellenir ve onay alınır.

---

## 2. Çalışma alanı, dallar ve izolasyon

### 2.1 Dal sorumlulukları

- `main`: Korunacak ana dal. Bu laboratuvar çalışması kapsamında değiştirilmeyecek.
- `demo_eldoria`: Mevcut oynanabilir demo dalı. Laboratuvar tamamlanmadan burada değişiklik yapılmayacak.
- `experiment/hex-world-laboratory`: Bu planın ve bütün laboratuvar uygulamalarının tek çalışma dalı.

Laboratuvar dosyaları, deney kodu, testler, raporlar ve mimari belgeler yalnızca laboratuvar dalında tutulur.

### 2.2 Bağımsızlık kuralları

1. Laboratuvar kendi paketine, giriş noktasına, bağımlılık tanımına, testlerine ve çalıştırma talimatlarına sahip olur.
2. Ana oyunun modülleri laboratuvarın çalışma zamanı bağımlılığı yapılmaz.
3. Ana oyunun mevcut davranışını doğrulamak için kaynak dosyalar incelenebilir; ancak laboratuvar deneyi ana oyun dosyalarını değiştirmez.
4. Deney amacıyla ana oyundan kod alınması gerekirse kaynak dosya, sürüm/commit ve lisans/bağımlılık ilişkisi kayda geçirilir. Kopyalama otomatik varsayım değildir.
5. Laboratuvarın kendi `main.py`, `pyproject.toml`, testleri veya diğer kök dosyaları ana oyunun karşılıklarıyla karıştırılmaz.
6. Her commit öncesinde aktif dal ve değişen dosyalar kontrol edilir.
7. Bir işlem yanlış dala yönelmişse yeni değişiklik yapılmaz; durum raporlanır ve güvenli geri dönüş planı hazırlanır.

### 2.3 Entegrasyon sınırı

Laboratuvar tamamlanmadan `demo_eldoria` dalına kod aktarılmaz. Nihai aktarım, ayrı bir entegrasyon planı, dosya eşleştirme tablosu, bağımlılık analizi, test raporu ve kullanıcı onayı gerektirir. Otomatik veya doğrudan toplu birleştirme varsayılmaz.

---

## 3. Ürün hedefi ve kapsam

### 3.1 Ana hedef

Eldoria'nın altıgen haritasını yalnızca görsel bir ızgara olarak değil, dünya topolojisinin ve mekânsal ilişkilerin temelini oluşturan canon dünya modeli olarak ele almak. Oyuncu ve diğer hareketli varlıklar bu dünyada sürekli fiziksel koordinatlarla hareket eder; hücre adresleri, dünya geometrisi ve etkileşim sorguları bu fiziksel konumla tutarlı çalışır.

### 3.2 Laboratuvarın teslim edeceği yetenekler

- Matematiksel olarak tutarlı altıgen koordinat ve geometri çekirdeği.
- Hücre adresi ile sürekli dünya konumu arasında çift yönlü dönüşüm.
- Harita kimliği, boyutları, yönelimi, ölçeği ve koordinat kökeni tanımlı dünya modeli.
- Kesirli konum ve zamandan bağımsız hız parametreleriyle sürekli hareket.
- Gerçek altıgen sınırlarıyla uyumlu çarpışma ve engel çözümleme.
- Kamera dönüşümleri ve ekranda doğru dünya çizimi.
- Varlıkların konum, ayak/zemin ankrajı ve mekânsal sorgu modeli.
- NPC, kaynak ve etkileşim prototiplerinin aynı konum sözleşmesini kullanması.
- Tekrarlanabilir otomatik testler ve görsel kabul senaryoları.
- Performans ölçümleri ve darboğaz raporları.
- Ana oyuna aktarım için mimari ve entegrasyon belgeleri.

### 3.3 Kapsam dışı

Aşağıdakiler bu laboratuvarın birincil hedefi değildir; ayrıca onaylanmadıkça geliştirilmez:

- Tam oyun içeriği, görev hikâyeleri, ekonomi ve ilerleme sisteminin yeniden yazılması.
- Savaş sisteminin veya kullanıcı arayüzünün yeniden tasarlanması.
- Nihai sanat varlıkları, animasyon paketi ve ses sistemi.
- Ağ/multiplayer altyapısı.
- Tam dünya editörü veya genel amaçlı harita üretim aracı.
- Godot'a geçiş. Mevcut karar doğrultusunda Pygame laboratuvar aracı olarak kullanılır; motor değişimi ancak Pygame'in doğrulanmış teknik sınırları hedefleri engellerse ayrı karar süreciyle değerlendirilir.
- Ana oyundaki kare harita prototipini bu laboratuvarda geliştirmeye devam etmek.

Kapsam dışı bir ihtiyaç ortaya çıkarsa önce etkisi ve gerekliliği yazılır; kendiliğinden plana eklenmez.

---

## 4. Temel mimari ilkeler

Bu ilkeler laboratuvarın başlangıç yönünü belirler. Ölçülebilir teknik ayrıntılar ilgili aşamalarda ve ADR kayıtlarında kesinleştirilir.

### 4.1 Canon dünya geometrisi

Altıgen harita, Eldoria'nın hedef dünya geometrisidir. Kare harita mevcut/legacy prototip yaklaşımı olarak kalır; yeni dünya mimarisinin doğruluk kaynağı yapılmaz.

### 4.2 Ayrı koordinat sorumlulukları

- **Axial `(q, r)`:** Altıgen hücrelerin mantıksal adresidir. Komşuluk, hücre mesafesi, hücre verisi ve topolojik sorgular için kullanılır.
- **WorldPosition `(x, y)`:** Dünya uzayındaki sürekli, kesirli fiziksel konumdur. Hareketli varlıkların hareket durumu için temel konum temsilidir.
- **ScreenPosition `(x, y)`:** Kamera dönüşümünden sonra elde edilen ekran piksel koordinatıdır. Dünya simülasyonunda authoritative konum olarak kullanılmaz.

Bu koordinat türleri aynı türmüş gibi birbirine atanamaz. Dönüşümler açık fonksiyonlar ve tanımlı parametrelerle yapılır.

### 4.3 Dünya konumu ve hücre ilişkisi

Hareketli bir varlığın fiziksel konumu `WorldPosition` ile tutulur. Bu konuma karşılık gelen hücre, tanımlanmış hex grid dönüşümüyle bulunur. Hücre merkezine sabitlenmiş statik içerikler hücre adresiyle tanımlanabilir; bunların dünya konumu aynı dönüşümden türetilir.

Hücre adresi, hareketli varlığın sürekli konumunu yuvarlayarak kaybetmesine neden olmamalıdır. Hücre sınırından geçişte fiziksel konum kesintiye uğramaz.

### 4.4 Geometri ve yönelim

Flat-top/pointy-top yönelimi, başlangıç açısı, eksen yönleri, dünya birimi başına hex boyutu ve harita origin'i tek bir koordinat sözleşmesinde tanımlanır. Bu seçimler gelişigüzel kod içine gömülmez; ADR ve testlerle sabitlenir.

### 4.5 Gerçek hex çarpışması

Nihai çarpışma doğruluğu gerçek altıgen polygon/kenar geometrisine dayanır. AABB veya başka basitleştirilmiş şekiller yalnızca broadphase (olası çarpışma adaylarını hızlı seçme) için kullanılabilir; nihai çarpışma kararı yerine geçemez.

### 4.6 Kamera ve render ayrımı

Kamera dünya verisini değiştirmez; yalnızca world-to-screen dönüşümünü uygular. Çizim sistemi simülasyon konumlarını değiştiremez. Render interpolasyonu gerekiyorsa görsel konum ile fiziksel simülasyon durumu ayrı tutulur.

### 4.7 Zaman ve deterministik simülasyon

Hareket hızı kare hızına bağlı olmamalıdır. Simülasyon güncellemesi ile çizim döngüsü sorumlulukları ayrılır. Sabit zaman adımı/fixed timestep ve değişken çizim sıklığı seçenekleri kontrollü testlerle değerlendirilir. Seçilen yöntem, büyük frame-time sıçramalarında ve farklı cihaz hızlarında kararlı olmalıdır.

### 4.8 Veri odaklı ve test edilebilir tasarım

Geometri, dünya, hareket ve fizik mümkün olduğunca Pygame yüzeylerinden bağımsız saf Python katmanlarında tutulur. Pygame; pencere, input ve çizim adaptörü olarak kullanılır. Böylece matematik ve simülasyon testleri grafik penceresi açmadan çalışabilir.

---

## 5. Hedef mimari katmanları

Bu bölüm hedeflenen sorumluluk sınırlarını tanımlar; kesin sınıf ve modül isimleri ilgili aşama tasarımında belirlenebilir.

| Katman | Sorumluluk | Yapmaması gereken |
|---|---|---|
| Geometry | Hex koordinatları, köşeler, kenarlar, mesafe ve dönüşümler | Pygame çizimi veya oyun kuralı |
| World | Harita kimliği, hücreler, dünya sınırları, topoloji ve dünya verisi | Ekran pikseli yönetimi |
| Movement | Girdi niyeti, hız, yön, ivme ve konum entegrasyonu | Kamera veya sprite çizimi |
| Physics | Gövde şekli, çarpışma, engel çözümü ve hareket kısıtları | Görev/NPC kararları |
| Spatial | Yakınlık, aday toplama, mekânsal indeks ve sorgular | Authoritative geometriyi değiştirme |
| Camera | View transform, takip, zoom ve viewport | Dünya simülasyonunu ilerletme |
| Rendering | Hücre/varlık çizimi, katmanlama ve görsel interpolasyon | Fiziksel state değiştirme |
| Entities | Oyuncu, NPC, kaynak ve diğer dünya varlıklarının konum bileşenleri | Hex matematiğini kopya biçimde yeniden uygulama |
| Interaction | Menzil, hedef seçimi, hücre/varlık etkileşimi | Kendi koordinat standardını oluşturma |
| Simulation | Güncelleme sırası, zaman, sistem orkestrasyonu | Katmanların iç işleyişini tek modülde birleştirme |
| Diagnostics | Debug overlay, ölçüm, kayıt ve hata teşhisi | Üretim mantığına gizli yan etki ekleme |

Bağımlılık yönü mümkün olduğunca aşağıdan yukarıya tek yönlü olmalıdır. Örneğin Geometry, Pygame'e; Movement, Rendering'e; Camera, Entity davranışlarına bağımlı olmamalıdır. Döngüsel import ve aynı kuralın birden fazla katmanda kopyalanması mimari kusur kabul edilir.

---

## 6. Aşamalı uygulama yol haritası

Her aşama için ayrı teknik görev listesi, dosya değişiklik listesi, test planı ve kapanış raporu hazırlanır. Aşağıdaki aşamalar ana sıradır. Bir aşama kabul edilmeden sonraki aşamaya geçilmez.

### Aşama 0 — Plan, sözleşme ve laboratuvar yönetişimi

**Amaç:** Ne inşa edileceğini, nasıl karar alınacağını ve başarı ölçütlerini sabitlemek.

İşler:
- Master Plan'ı onaylamak ve sürümlemek.
- Mimari katmanları ve izolasyon sınırlarını tanımlamak.
- ADR kayıtlarının biçimini belirlemek.
- Aşama kapanış şablonunu ve test kanıtı standardını belirlemek.
- Açık teknik soruları ve riskleri kayda geçirmek.

Çıktılar:
- Bu Master Plan.
- Mimari sözleşme taslağı.
- Geliştirme kuralları ve test/kabul yaklaşımı.
- ADR kayıtları için şablon.

Kabul koşulları:
- Kullanıcı planı onaylamış olmalı.
- Dal ve dosya izolasyonu doğrulanmış olmalı.
- Uygulamaya geçiş için gerekli belirsizlikler listelenmiş olmalı.

### Aşama 1 — Bağımsız çalışma ve test altyapısı

**Amaç:** Laboratuvarı ana oyundan bağımsız, tekrar kurulabilir ve kolay test edilebilir hale getirmek.

İşler:
- Python sürüm aralığını ve paketleme yaklaşımını doğrulamak.
- İzole sanal ortam ve bağımlılık kurulumunu sağlamak.
- Laboratuvar paketini ve bağımsız giriş noktasını oluşturmak.
- Pygame pencere açılışı, kapanışı ve temel event loop'u doğrulamak.
- pytest yapılandırmasını, test etiketlerini ve temel CI/yerel komutları tanımlamak.
- Grafik arayüz gerektirmeyen testleri pencere açmadan çalıştırmak.

Çıktılar:
- Kurulum ve çalıştırma yönergesi.
- Minimal açılış/kapanış uygulaması.
- Boş testin çalıştığını kanıtlayan test altyapısı.

Kabul koşulları:
- Temiz sanal ortamda kurulum başarılı.
- Laboratuvar tek belgelenmiş komutla açılabiliyor.
- Pencere normal biçimde kapanıyor.
- Test komutu beklenen sonucu veriyor.
- Ana oyunun bağımlılıklarına veya giriş noktasına ihtiyaç duyulmuyor.

### Aşama 2 — Hex geometri çekirdeği

**Amaç:** Harita sisteminin matematiksel temelini oluşturmak.

İşler:
- Hex koordinat konvansiyonunu seçmek: axial `(q,r)`, buna karşılık gelen cube dönüşümü ve yön indeksleri.
- Flat-top/pointy-top, başlangıç açısı ve eksen yönlerini belirlemek.
- Hex boyutu ve ölçü birimini tanımlamak.
- Axial-to-world ve world-to-axial dönüşümlerini tanımlamak.
- Hex merkezleri, altı köşe, altı kenar ve komşu merkezlerini hesaplamak.
- Hex mesafesi ve hücre komşuluğunu hesaplamak.
- Hücre sınırı ve noktanın hangi hücrede olduğu kurallarını belirlemek.
- Eşit uzaklıkta/sınır üzerinde kalan noktalar için deterministik tie-break kuralı belirlemek.
- Negatif koordinatlar, büyük koordinatlar ve sınır durumlarını test etmek.

Çıktılar:
- Pygame'den bağımsız geometri modülü.
- Koordinat sözleşmesi ve diyagramlar.
- Birim testleri ve sayısal tolerans politikası.

Kabul koşulları:
- Axial → world → axial dönüşümleri test toleransı içinde tutarlı.
- Komşuluk ve mesafe bilinen matematiksel sonuçlarla uyumlu.
- Altıgen köşeleri/kenarları aynı merkez ve ölçüden türetiliyor.
- Negatif ve pozitif koordinatlarda tutarlı davranış.
- Sınır noktalarının hücre ataması tekrarlanabilir.
- Rastgele örnekli/property-based testlerde dönüşüm hatası yok.

### Aşama 3 — Hex dünya veri modeli ve runtime

**Amaç:** Geometriyi gerçek bir harita/dünya yapısına dönüştürmek.

İşler:
- Dünya kimliği ve harita kimliği kavramlarını ayırmak.
- Harita origin'i, boyutları, yönelimi, hex boyutu ve sınır politikasını tanımlamak.
- Hücre verisi ile geometrik hücre adresini ayırmak.
- Hücre var/yok, geçilebilirlik, arazi türü ve engel verisinin sorumluluğunu belirlemek.
- Dünya sınırları ve harita dışı koordinat davranışını tanımlamak.
- HexWorld, HexWorldView ve HexWorldRuntime sorumluluklarını kesinleştirmek.
- Dünya verisinin salt okunur görünüm ve değiştirilebilir runtime erişimini ayırmak.
- Basit test haritası üretmek ve yüklemek.

Çıktılar:
- Hex dünya veri modeli.
- Runtime ve view sınırları.
- Test haritaları ve dünya bütünlüğü testleri.

Kabul koşulları:
- Hücre kimliği harita kimliğiyle çakışmıyor.
- Aynı axial koordinat farklı haritalarda farklı adreslenebiliyor.
- Harita dışı sorgu davranışı açık ve testli.
- Dünya verisi ile ekran çizimi birbirinden bağımsız.
- Runtime güncellemesi geometri kurallarını bozmuyor.

**Aşama 3 uygulama ve kabul kaydı:** Dünya veri modeli, runtime ve persistence kapsamı tamamlandı ve kabul edildi. Bütünleşik kanıtlar laboratuvar raporları dizinindeki `PHASE-03-WORLD-REPORT.md` dosyasındadır. Aşama 3 kapanışından sonra Aşama 4 (sürekli hareket) ve Aşama 5 (gövde, çarpışma ve fizik) ayrı onaylı planları doğrultusunda tamamlanmış ve kabul edilmiştir. Güncel genel durum Bölüm 14'te tutulur.

### Aşama 4 — Sürekli hareket sistemi

**Amaç:** Oyuncu ve hareketli varlıkların hücre adımları yerine kesintisiz dünya koordinatlarında hareket etmesini sağlamak.

İşler:
- WorldPosition veri tipini ve world-unit tanımını kesinleştirmek.
- Hız, yön, ivme, maksimum hız ve hareket niyeti modelini belirlemek.
- Klavye/joystick benzeri input'u hareket niyetine dönüştürmek.
- Çapraz hareketin normalize edilmesini sağlamak.
- Delta time/fixed timestep yaklaşımını deneyerek seçmek.
- Hareketin harita koordinatından bağımsız, dünya uzayında gerçekleşmesini sağlamak.
- Hücre sınırı geçişinde konumun ve hızın kesilmediğini doğrulamak.
- Durma, yön değiştirme, hız değişimi ve büyük frame-time senaryolarını test etmek.

Çıktılar:
- Pygame'den bağımsız hareket çekirdeği.
- Input adaptörü.
- Hareket debug görünümü ve test senaryoları.

Kabul koşulları:
- Aynı simülasyon süresinde farklı render FPS değerlerinde benzer fiziksel mesafe.
- Çapraz hareketin eksen hareketinden hızlı olmaması.
- Kesirli konum korunuyor; her frame hücre merkezine snap edilmiyor.
- Hücre geçişlerinde ani sıçrama veya koordinat kaybı yok.
- Hareket testleri otomatik ve tekrarlanabilir.

### Aşama 5 — Gövde modeli, çarpışma ve fizik

**Amaç:** Sürekli hareketin hex dünya engelleriyle fiziksel olarak tutarlı etkileşmesini sağlamak.

İşler:
- Oyuncu/NPC çarpışma gövdesi temsilini seçmek (daire, capsule veya başka uygun şekil).
- Görsel sprite ile fiziksel gövdeyi ayırmak.
- Foot-anchor/zemin temas noktasını ve gövde yüksekliği kavramını tanımlamak.
- Hex hücre polygonları ve kenarları üzerinden engel sınırlarını üretmek.
- Broadphase aday toplama ve narrowphase gerçek çarpışma testini ayırmak.
- Kayma, duvar boyunca hareket, köşe sıkışması ve birden çok temas çözümünü tasarlamak.
- Harita sınırları, dar geçitler, bitişik engeller ve tek hücre engellerini test etmek.
- Tünelleme ve yüksek hızda engel geçme riskini değerlendirmek; gerekirse swept collision kullanmak.

Çıktılar:
- Çarpışma/physics çekirdeği.
- Engel örnek haritaları.
- Debug collider çizimleri ve çarpışma raporu.

Kabul koşulları:
- Gerçek hex kenarları nihai çarpışma doğruluğunu belirliyor.
- AABB kullanılıyorsa yalnızca aday bulma/broadphase rolünde.
- Karakter engellerin içinden geçmiyor.
- Duvar kenarında hareket doğal ve kararlı.
- Köşelerde titreme, takılma ve sonsuz çözüm döngüsü yok.
- Farklı hız ve frame-time koşullarında tünelleme testleri geçiyor.

### Aşama 6 — Kamera ve dünya-ekran dönüşümü

**Amaç:** Dünya simülasyonunu değiştirmeden doğru ve kullanılabilir kamera sunmak.

İşler:
- World-to-screen ve screen-to-world dönüşüm sözleşmesini tanımlamak.
- Kamera origin/offset, viewport ve zoom modelini kurmak.
- Oyuncu takibi, kamera sınırları ve harita kenarı davranışını belirlemek.
- Fare ile dünya noktasına erişim ve hücre seçimini doğrulamak.
- Zoom sırasında koordinat dönüşümünün kararlı kalmasını sağlamak.
- Farklı pencere boyutları ve çözünürlükleri test etmek.

Çıktılar:
- Kamera modülü.
- Pygame render adaptörü.
- Kamera debug overlay ve dönüşüm testleri.

Kabul koşulları:
- Ekran koordinatından dünya koordinatına dönüş ve geri dönüş tolerans içinde tutarlı.
- Kamera hareketi fiziksel konumu değiştirmiyor.
- Zoom ve viewport değişiminde seçim hatası yok.
- Oyuncu takibi ve harita sınırları kararlı.

### Aşama 7 — Render ve görsel doğrulama

**Durum:** 7.1–7.8 kodlama, otomatik testler, benchmark ve görsel test sahneleri tamamlandı. Kullanıcı masaüstü görsel kabulü bekleniyor; bu aşama henüz kapatılmadı.

**Belgeler:** [Genel Plan](PHASE-07-GENERAL-PLAN.md) · [Teknik Plan](PHASE-07-TECHNICAL-PLAN.md) · [Manuel Görsel Kabul](PHASE-07-MANUAL-ACCEPTANCE-CHECKLIST.md) · [Uygulama ve Doğrulama Raporu](../reports/PHASE-07-IMPLEMENTATION-VALIDATION-REPORT.md)

**Amaç:** Hex dünya topolojisini, varlık konumlarını ve derinlik ilişkilerini görsel olarak doğru sunmak.

İşler:
- Hex hücre çizim sırasını ve görünür alan culling yaklaşımını belirlemek.
- Hücre sınırları, merkezler, koordinat etiketleri ve debug katmanlarını göstermek.
- Sprite foot-anchor ile dünya konumunu eşlemek.
- Y-sort/depth sıralamasını araştırmak.
- Kamera hareketinde çizim titremesi ve subpixel davranışını incelemek.
- Dünya görünümü ile fiziksel collider debug görünümünü karşılaştırmak.
- Performans için gereksiz çizimlerin elenmesini sağlamak.

Çıktılar:
- Render pipeline prototipi.
- Görsel test sahneleri ve ekran görüntüsü kanıtları.
- Görsel doğruluk raporu.

Kabul koşulları:
- Hex çizimi geometri çekirdeğiyle aynı parametreleri kullanıyor.
- Sprite zemine doğru noktadan oturuyor.
- Render katmanı simülasyon state'ini değiştirmiyor.
- Kamera kayarken belirgin titreme/konum sapması yok.
- Görünür alan çizimi büyük haritalarda ölçülebilir fayda sağlıyor veya gereksizliği kanıtlanıyor.

### Aşama 8 — Mekânsal indeksleme ve performans karşılaştırması

**Amaç:** Dünya büyüdükçe yakınlık ve çarpışma adaylarını verimli bulmak; kare yardımcı ızgaranın gerçek faydasını ölçmek.

İşler:
- Basit doğrudan hex komşuluk taramasını referans çözüm olarak kurmak.
- Hex tabanlı komşu hücre sorgusunu ölçmek.
- Spatial hash/grid tabanlı yardımcı indeks prototipi geliştirmek.
- Kare alt bölümlere ayırma yaklaşımını yalnızca yardımcı indeks olarak karşılaştırmak.
- Aday bulma doğruluğunu brute-force referansıyla karşılaştırmak.
- Farklı harita büyüklüğü, varlık yoğunluğu ve hareket yoğunluğu testleri yapmak.
- Bellek, sorgu süresi, güncelleme maliyeti ve karmaşıklığı ölçmek.

Çıktılar:
- En az iki indeksleme yaklaşımı için benchmark.
- Doğruluk ve performans karşılaştırma raporu.
- Seçilen yöntemin gerekçesi.

Kabul koşulları:
- Optimizasyon sonucu hiçbir geçerli aday atlanmıyor.
- Broadphase sonucu yalnızca aday kümesini daraltıyor; nihai karar geometri/fizik katmanında.
- Ölçüm tekrarlanabilir ve aynı koşullarda karşılaştırılabilir.
- Optimizasyon ancak ölçülebilir fayda sağlıyorsa varsayılan mimariye alınır.
- Basit yaklaşım yeterliyse gereksiz karmaşıklık eklenmez.

### Aşama 9 — Varlıklar ve etkileşimler

**Amaç:** Oyuncu, NPC ve kaynak nesnelerinin aynı dünya konum sözleşmesini kullanmasını sağlamak.

İşler:
- Entity kimliği ve transform/position bileşenlerini belirlemek.
- Hareketli ve hücreye sabit nesne konumlarını ayırmak.
- Foot-anchor ve görsel boyut/çarpışma gövdesi ilişkisini kurmak.
- Etkileşim menzili için dünya mesafesi ve/veya hex mesafesi kullanım kurallarını belirlemek.
- Fareyle hedef seçimi ve yakın hedef bulma sorgularını kurmak.
- NPC ve kaynakların mekânsal indeksle uyumunu sağlamak.
- Harita değişiminde entity konumlarının taşınma/yeniden bağlanma politikasını belirlemek.

Çıktılar:
- Entity prototipleri.
- Etkileşim sorgu sistemi.
- Oyuncu, NPC ve kaynak içeren test sahnesi.

Kabul koşulları:
- Tüm varlıklar aynı WorldPosition/Hex adres sözleşmesini kullanıyor.
- Görsel sprite merkezi ile fiziksel temas noktası karıştırılmıyor.
- Etkileşim menzili harita ölçeği ve kamera zoom'undan bağımsız.
- Harita kimliği dışındaki varlık sorguları yanlış sonuç vermiyor.

### Aşama 10 — Simülasyon orkestrasyonu ve dünya bütünlüğü

**Amaç:** Ayrı sistemleri tutarlı bir güncelleme sırasıyla birlikte çalıştırmak.

İşler:
- Simülasyon tick sırasını tanımlamak.
- Input, hareket, fizik, mekânsal indeks, etkileşim ve render sınırlarını netleştirmek.
- NPC basit hareket prototipini eklemek.
- Kaynak nesnelerinin konum ve etkileşim davranışını doğrulamak.
- Harita geçişi, dünya yeniden yükleme ve konum eşleme senaryolarını test etmek.
- Simülasyon state'i ile görsel state arasındaki ilişkiyi belgelemek.
- Hata/diagnostic kayıtlarını standartlaştırmak.

Çıktılar:
- Birleşik simülasyon döngüsü.
- Oyuncu + NPC + kaynak test sahnesi.
- Dünya bütünlüğü ve uzun süreli çalışma raporu.

Kabul koşulları:
- Güncelleme sırası deterministik ve belgeli.
- Sistemler birbirlerinin sorumluluğunu üstlenmiyor.
- Uzun süreli çalışmada konum/indeks tutarsızlığı birikmiyor.
- Harita geçişinde eski dünya referansları sızmıyor.
- Testler tekrar çalıştırıldığında aynı girdiler aynı beklenen sonucu üretiyor.

### Aşama 11 — Sağlamlık, regresyon ve performans doğrulaması

**Amaç:** Mimariyi yalnızca küçük demo sahnesinde değil, hedeflenen yük koşullarında da sınamak.

İşler:
- Büyük harita, yüksek entity sayısı ve yoğun engel senaryoları kurmak.
- Farklı FPS ve frame-time dalgalanması senaryolarını çalıştırmak.
- Uzun süreli simülasyon ve rastgele hareket testleri yapmak.
- Bellek kullanımı, CPU zamanı, frame time ve sorgu maliyetini ölçmek.
- Geometri ve çarpışma regresyon testlerini çalıştırmak.
- Hata durumlarında diagnostic kayıtlarını doğrulamak.
- Bilinen sınırlamaları ve çözülmemiş sorunları listelemek.

Çıktılar:
- Benchmark sonuçları.
- Regresyon raporu.
- Bilinen sorunlar ve risk listesi.

Kabul koşulları:
- Kritik testlerin tamamı geçiyor.
- Önceden tanımlanmış performans hedefleri karşılanıyor veya sapmalar gerekçeli olarak kabul ediliyor.
- Kritik konum, çarpışma veya kamera hatası açık kalmıyor.
- Bilinen sınırlamalar yazılı ve entegrasyon kararına dahil.

### Aşama 12 — Nihai mimari, dokümantasyon ve entegrasyon hazırlığı

**Amaç:** Laboratuvarda kanıtlanmış sistemi ana oyuna taşınabilir bir teknik pakete dönüştürmek.

İşler:
- Gerçekleşen mimariyi hedef mimariyle karşılaştırmak.
- Tüm ADR kararlarını sonuçlarıyla güncellemek.
- Modül/API sözleşmelerini ve veri akışını belgelemek.
- Laboratuvar dosyalarını ana oyun dosyalarıyla eşleştirmek.
- Bağımlılık, lisans, paketleme ve veri uyumluluğu analizini yapmak.
- Ana oyunda değişecek, eklenecek ve kaldırılacak dosyaları listelemek.
- Entegrasyon sırasını, geri dönüş stratejisini ve test matrisini hazırlamak.
- Aktarım öncesi kullanıcı onayı almak.

Çıktılar:
- Nihai mimari raporu.
- Entegrasyon/migrasyon planı.
- Dosya eşleştirme tablosu.
- Kabul ve regresyon kanıtları.

Kabul koşulları:
- Laboratuvar testleri tamamlanmış.
- Kritik mimari kararlar belgelenmiş.
- Entegrasyon kapsamı dosya bazında açık.
- Ana oyun için geriye dönük uyumluluk ve veri etkileri değerlendirilmiş.
- Kullanıcı entegrasyon planını ayrıca onaylamış.

### Aşama 13 — Kontrollü demo entegrasyonu

**Amaç:** Onaylanmış laboratuvar mimarisini kontrollü ve geri alınabilir şekilde `demo_eldoria` dalına taşımak.

Bu aşama, laboratuvarın tamamlanmasıyla otomatik başlamaz. Ayrı açık onay gerektirir.

İşler:
- Entegrasyon öncesi `demo_eldoria` güncel durumu ve hedef commit'i doğrulamak.
- Laboratuvarın onaylanmış commit'ini sabitlemek.
- Dosya bazında aktarım veya uyarlama yapmak; körlemesine tüm klasörü kopyalamamak.
- Eski kare dünya sisteminin kullanım yerlerini ve geçiş stratejisini belirlemek.
- Ana oyunun testlerini ve laboratuvar kabul senaryolarını çalıştırmak.
- Görsel ve oynanış regresyonlarını değerlendirmek.
- Sorun halinde geri dönüş adımlarını uygulamaya hazır tutmak.

Çıktılar:
- Demo entegrasyon commit/commit'leri.
- Entegrasyon test raporu.
- Değişen dosyalar ve bilinen etkiler listesi.

Kabul koşulları:
- Yalnızca onaylanmış hedef dalda işlem yapılmış.
- Laboratuvarın kritik davranışları demo içinde korunmuş.
- Ana oyun testleri geçiyor.
- Oynanabilir demo temel işlevlerini kaybetmemiş.
- Kullanıcı entegrasyonu kabul etmiş.

---

## 7. Test stratejisi ve kanıt standardı

Testler yalnızca “çalışıyor gibi görünüyor” değerlendirmesine dayanamaz. Her önemli iddia uygun test türüyle desteklenmelidir.

### 7.1 Test seviyeleri

1. **Unit test:** Tek fonksiyon/sınıf; özellikle geometri, dönüşüm, hareket ve çarpışma matematiği.
2. **Property-based test:** Çok sayıda koordinat ve parametre üzerinde değişmezlerin doğrulanması.
3. **Integration test:** Geometry + World, Movement + Physics, Camera + Rendering gibi katman birleşimleri.
4. **Acceptance test:** Kullanıcının gözlemleyebileceği davranışlar; örneğin karakterin hex sınırını kesintisiz geçmesi.
5. **Visual test:** Hex hizası, foot-anchor, kamera, katman sıralaması ve collider overlay.
6. **Performance benchmark:** FPS, frame time, sorgu süresi, bellek ve entity sayısı.
7. **Regression test:** Önceden çözülen hataların tekrar ortaya çıkmadığının kontrolü.

### 7.2 Zorunlu test senaryoları

- Origin hücresi ve çevresindeki altı komşu.
- Pozitif ve negatif axial koordinatlar.
- Harita merkezinden uzak hücreler.
- Hex köşesi ve kenarı üzerindeki noktalar.
- Axial ↔ world dönüşüm döngüsü.
- Hücre sınırını çok yavaş ve yüksek hızla geçiş.
- 30, 60, 120 FPS ve değişken frame-time koşulları.
- Çapraz hareket ve yön değişimi.
- Tek engel, bitişik engel, dar koridor ve köşe teması.
- Kamera pan/zoom sırasında fareyle hücre seçimi.
- Sprite foot-anchor ve collider hizası.
- Harita dışı konum ve harita geçişi.
- Çok sayıda entity için mekânsal sorgu doğruluğu.
- Uzun süreli simülasyonda konum/indeks tutarlılığı.

### 7.3 Kanıt standardı

Her aşama kapanışında aşağıdakiler raporlanır:

- Test komutu ve çalıştırma ortamı.
- Toplam test, geçen, kalan/başarısız sayıları.
- Başarısız testlerin açıklaması.
- Görsel aşamalarda ekran görüntüsü veya kısa kayıt.
- Performans aşamalarında test koşulları ve ham ölçüm özeti.
- Değişen dosyalar ve commit SHA.
- Açık riskler ve sonraki aşamaya etkileri.

Bir test çalıştırılmadıysa “geçti” denmez. Görsel olarak kontrol edilmediyse görsel kabul tamamlandı denmez. Ölçülmediyse performans iyileşti iddiası kurulmaz.

---

## 8. Performans ve kalite hedeflerinin belirlenmesi

Sayılarla hedef belirlemek gereklidir; ancak donanım ve sahne yükü doğrulanmadan rastgele FPS veya entity sayısı taahhüt edilmez.

Aşama 1'de laboratuvarın test ortamı kaydedilir. Aşama 8 ve 11'de ölçülebilir başlangıç değerleri oluşturulur. Ardından aşağıdaki ölçütler için kabul eşikleri kullanıcıyla kararlaştırılır:

- Hedef çözünürlük ve pencere boyutu.
- Referans donanım profili.
- Hedef entity ve engel sayısı.
- Ortalama ve yüzde 95 frame time.
- Hareket/çarpışma güncelleme maliyeti.
- Mekânsal sorgu gecikmesi.
- Bellek tüketimi.
- Uzun süreli çalışma kararlılığı.

Optimizasyon hedefi okunabilirlik ve mimari sadelik pahasına gereksiz karmaşıklık yaratmak değildir. Önce doğru çalışan referans çözüm, sonra ölçüm, sonra gerekçeli optimizasyon yapılır.

---

## 9. Mimari karar kayıtları (ADR)

Önemli kararlar kısa ve izlenebilir ADR belgeleriyle kayıt altına alınır. Her ADR şu alanları içerir:

- Kimlik ve başlık.
- Durum: öneri / kabul edildi / reddedildi / yerini başka karar aldı.
- Bağlam ve çözülmek istenen problem.
- Değerlendirilen alternatifler.
- Karar ve gerekçesi.
- Sonuçlar, ödünleşimler ve riskler.
- İlgili test/benchmark kanıtı.
- Kararı onaylayan ve tarih.

Başlangıçta ele alınacak ADR konuları:

- Hex dünya canon yaklaşımı.
- Axial ve cube koordinat sözleşmesi.
- Flat-top/pointy-top yönelimi ve ölçü birimi.
- WorldPosition ve hücre adresi ilişkisi.
- World origin ve map identity.
- Foot-anchor ve varlık gövdesi.
- Hex polygon çarpışması ve broadphase ayrımı.
- Zaman adımı ve simülasyon güncellemesi.
- Kamera dönüşümü.
- Mekânsal indeksleme yöntemi.
- Render/depth sıralaması.

Bu başlıkların listelenmiş olması, teknik ayrıntılarının peşinen kesinleştiği anlamına gelmez. Kararlar ilgili aşamadaki analiz ve testle kabul edilir.

---

## 10. Riskler ve önleyici tedbirler

| Risk | Etki | Önleyici yaklaşım |
|---|---|---|
| Koordinat sözleşmesinin belirsiz kalması | Tüm sistemlerde konum sapması | Geometri aşamasında tek sözleşme ve dönüşüm testleri |
| Hücre adresinin fiziksel konum yerine kullanılması | Hareketin hücreye kilitlenmesi | WorldPosition'ı hareket state'i olarak korumak |
| Hex ve ekran koordinatlarının karışması | Kamera ve seçim hataları | Ayrı veri tipleri ve açık dönüşüm fonksiyonları |
| AABB'nin nihai çarpışma sayılması | Hex kenarlarında hatalı temas | Gerçek polygon narrowphase |
| FPS'e bağlı hareket | Cihazlar arasında farklı hız | Zaman adımı testleri |
| Kamera kodunun simülasyonu değiştirmesi | Konum ve fizik tutarsızlığı | Katman sınırı ve test |
| Erken optimizasyon | Gereksiz karmaşıklık | Önce referans çözüm, sonra benchmark |
| Pygame bağımlılığının çekirdeğe yayılması | Test ve entegrasyon zorluğu | Saf Python çekirdek, Pygame adaptörü |
| Laboratuvarın ana oyunla karışması | İstenmeyen regresyon | Dal ve paket izolasyonu |
| Çok büyük aşamaların kontrolsüz büyümesi | Hata ayıklama güçlüğü | Küçük görevler ve aşama kapıları |
| Görsel testlerin atlanması | Matematik doğruyken yanlış sunum | Görsel kabul kanıtı |
| Entegrasyonun erken yapılması | Demo istikrarının bozulması | Ayrı onay ve geri dönüş planı |

---

## 11. Geliştirme ve değişiklik yönetimi

Her görev şu sırayla yürütülür:

1. **İnceleme:** İlgili mevcut dosyalar, belgeler ve branch HEAD incelenir.
2. **Problem tanımı:** Hangi sorunun çözüldüğü ve neden gerekli olduğu yazılır.
3. **Öneri:** Dosya bazında değişiklik listesi, tasarım ve test yaklaşımı hazırlanır.
4. **Onay:** Kullanıcıdan açık onay alınır.
5. **Uygulama:** Yalnızca onaylanan kapsamda değişiklik yapılır.
6. **Doğrulama:** Testler ve gerekiyorsa görsel/performance kontrolleri çalıştırılır.
7. **Raporlama:** Sonuçlar ve kanıtlar sunulur.
8. **Commit:** Değişiklikler anlamlı ve küçük commit'lerle kaydedilir.
9. **Aşama kararı:** Kabul, düzeltme veya bekletme kararı verilir.

Kullanıcı “planla” dediğinde uygulamaya geçilmez. “İncele” talebi tek başına dosya değiştirme yetkisi vermez. “Uygula” talebi de yalnızca açıkça onaylanan kapsam için geçerlidir. Kapsam genişletme ihtiyacı ortaya çıkarsa durulur ve yeni onay istenir.

### 11.1 Commit ilkeleri

- Commit mesajları yapılan işi açıkça anlatır.
- Her commit tek bir mantıksal değişiklik kümesini kapsar.
- Test edilmemiş kod, test edilmiş gibi sunulmaz.
- Commit öncesi aktif branch ve diff kontrol edilir.
- Commit sonrası yeni HEAD ve değişen dosyalar doğrulanır.
- Laboratuvar commit'leri demo/main dallarına taşınmaz.

### 11.2 Aşama kapanış raporu

Her aşama sonunda `reports/` altında şu başlıkları içeren rapor oluşturulur:

- Aşama ve hedef.
- Yapılan işler.
- Değişen dosyalar.
- Mimari kararlar.
- Testler ve sonuçları.
- Görsel/performans kanıtları.
- Commit SHA.
- Açık sorunlar ve riskler.
- Kabul durumu.
- Sonraki aşamaya geçiş önerisi.

---

## 12. Dosya ve belge yönetimi

Laboratuvarın mevcut iskeleti korunur. Yeni belgeler mevcut `experiments/hex_world_laboratory/docs/` dizinine eklenir.

Önerilen belge düzeni:

```text
experiments/hex_world_laboratory/
├── README.md
├── pyproject.toml
├── src/hex_world_lab/
├── tests/
├── scenarios/
├── scripts/
├── assets/
├── docs/
│   ├── HEX_WORLD_LAB_MASTER_PLAN.md
│   ├── ARCHITECTURE_SPECIFICATION.md
│   ├── DEVELOPMENT_RULES.md
│   ├── TESTING_AND_ACCEPTANCE_CRITERIA.md
│   └── INTEGRATION_AND_MIGRATION_PLAN.md
│   └── decisions/
│       ├── ADR-001-HEX-WORLD-AS-CANON.md
│       ├── ADR-002-AXIAL-COORDINATES.md
│       ├── ADR-003-CONTINUOUS-WORLD-POSITION.md
│       ├── ADR-004-HEX-COLLISION-GEOMETRY.md
│       └── ADR-005-SPATIAL-INDEXING-STRATEGY.md
├── reports/
└── benchmarks/
```

Belgeler ihtiyaç doğdukça ve ilgili aşama öncesinde hazırlanır. Sırf ağaçta görünsün diye içeriği belirsiz belgeler oluşturulmaz. Bu Master Plan diğer belgelerin üst referansıdır.

---

## 13. Tamamlanma tanımı (Definition of Done)

Laboratuvar ancak aşağıdaki koşulların tamamı sağlandığında tamamlanmış sayılır:

- [ ] Altıgen geometri ve koordinat sözleşmesi belgeli ve testli.
- [ ] Hex dünya modeli ve runtime bağımsız çalışıyor.
- [ ] Sürekli hareket sistemi farklı zaman adımlarında kararlı.
- [ ] Gerçek hex geometrisine dayalı çarpışma doğrulanmış.
- [ ] Kamera ve world/screen dönüşümleri testli.
- [ ] Render ve foot-anchor hizası görsel olarak kabul edilmiş.
- [ ] Mekânsal sorgu yaklaşımı ölçülmüş ve gerekçeli seçilmiş.
- [ ] Oyuncu, NPC ve kaynak prototipleri aynı dünya sözleşmesini kullanıyor.
- [ ] Simülasyon güncelleme sırası belgeli ve tekrarlanabilir.
- [ ] Kritik unit, integration, acceptance ve regression testleri geçiyor.
- [ ] Performans ve sağlamlık raporları mevcut.
- [ ] ADR'ler güncel ve kararların gerekçeleri kayıtlı.
- [ ] Bilinen sorunlar ve sınırlamalar açıkça listelenmiş.
- [ ] Entegrasyon/migrasyon planı hazırlanmış.
- [ ] Kullanıcı laboratuvar tamamlanmasını ve entegrasyon planını kabul etmiş.

Bu liste tamamlanmadan laboratuvarın ana oyuna aktarılmaya hazır olduğu söylenemez.

---

## 14. Şu anki durum ve bir sonraki izinli adım

### Mevcut durum — 17 Kasım 2026

| Aşama | Kapsam | Durum |
|---|---|---|
| 0 | Plan, sözleşme ve laboratuvar yönetişimi | Tamamlandı |
| 1 | Bağımsız çalışma ve test altyapısı | Tamamlandı |
| 2 | Hex geometri çekirdeği | Tamamlandı |
| 3 | Hex dünya veri modeli ve runtime | Tamamlandı |
| 4 | Sürekli hareket sistemi | Tamamlandı |
| 5 | Gövde modeli, çarpışma ve fizik | Tamamlandı; kullanıcı kabulü alındı |
| 6.1 | Koordinat ve viewport sözleşmesi | Teknik olarak tamamlandı; CI başarılı |
| 6.2 | Kamera çekirdeği ve zoom | Teknik olarak tamamlandı; CI başarılı |
| 6.3 | Takip ve kamera sınırları | Teknik olarak tamamlandı; CI başarılı |
| 6.4 | Render ve fare girdisi entegrasyonu | Teknik olarak tamamlandı; CI başarılı |
| 6.5 | Bütünleşik doğrulama ve kabul | 681/681 test, benchmark, Linux/Windows CI ve kullanıcı görsel kabulü başarılı; Aşama 6 kapatıldı |
| 7 | Render ve görsel doğrulama | 7.1–7.8 tamamlandı; 703/703 test, Linux/Windows CI, benchmark ve kullanıcı görsel kabulü başarılı; 17 Kasım 2026 tarihinde kapatıldı |
| 8–13 | Spatial, entities, interaction, simulation, robustness ve entegrasyon hazırlığı | Aşama 7 kapanışından sonra kendi teknik planlarıyla sırayla ele alınacak |

- Çalışma dalı: `experiment/hex-world-laboratory`.
- Aşama 6 son otomatik test kapısında Laboratuvar CI 681/681 testle başarılıdır.
- Aynı commit için Core Quality Linux ve Windows job'ları başarılıdır; laboratuvar benchmark adımları da başarılı tamamlanmıştır.
- Aşama 6 alt aşama commit'leri, CI run kimlikleri ve teknik kanıtlar `experiments/hex_world_laboratory/reports/PHASE-06-VALIDATION-LOG.md` içindedir.
- Kullanıcının son masaüstü/görsel kabul adımları `experiments/hex_world_laboratory/docs/PHASE-06-MANUAL-ACCEPTANCE-CHECKLIST.md` içindedir.
- Kullanıcı 17 Kasım 2026 tarihinde masaüstü kontrol listesindeki tüm maddeleri kendi bilgisayarında doğruladığını ve hepsinin başarılı olduğunu bildirmiştir. Aşama 6 teknik, otomatik ve görsel kabul kapılarının tamamı geçilerek kapatılmıştır.
- Korunan `main` ve `demo_eldoria` dallarına bu çalışma kapsamında yazılmamıştır.

### Bir sonraki izinli adım

Aşama 7, 17 Kasım 2026 tarihinde teknik, otomatik ve kullanıcı görsel kabul kapılarının tamamı geçilerek kapatılmıştır. Bir sonraki sıradaki aşama Aşama 8 — Mekânsal indeksleme ve performans karşılaştırmasıdır. Aşama 8 için önce genel plan ve ayrıntılı teknik plan hazırlanır; uygulama, onaylı kapsam doğrultusunda başlatılır.

Dünya görsel zenginleştirmesi (arazi dokuları, bitki örtüsü, ağaç/kaya/çevre varlıkları, ışık ve atmosfer) Aşama 7'nin geriye dönük eksik işi değildir. Kullanıcı kararı doğrultusunda ihtiyaç duyulan ileriki aşamalarda ayrı kapsam olarak ele alınacaktır.

**Her aşama ve kapsam değişikliği ayrıca onaylanır. Korunan `main` ve `demo_eldoria` dallarına bu laboratuvar çalışması kapsamında yazılmaz.**

---

## 15. Değişiklik geçmişi

| Sürüm | Durum | Açıklama |
|---|---|---|
| 1.0 | İlk taslak | Hex World Laboratory için kapsamlı aşamalı yol haritası ve çalışma sözleşmesi |
| 1.1 | Önceki sürüm | Aşamalı laboratuvar planı |
| 1.2 | Önceki sürüm | Aşama 0–5 kapanış durumu ve Aşama 6 izinli aşama |\n| 1.3 | Önceki sürüm | Aşama 6.1–6.5 teknik uygulama, 681 test ve Linux/Windows CI; görsel kabul bekleniyordu |\n| 1.4 | Güncellendi — 17 Kasım 2026 | Kullanıcı tüm masaüstü/görsel kontrolleri başarılı bildirdi; Aşama 6 resmen kapatıldı |
| 1.6 | Güncellendi — 17 Kasım 2026 | Aşama 7.1–7.8 otomatik ve manuel kabulü tamamlandı; Aşama 7 kapatıldı, Aşama 8 sıradaki aşama olarak işaretlendi |
