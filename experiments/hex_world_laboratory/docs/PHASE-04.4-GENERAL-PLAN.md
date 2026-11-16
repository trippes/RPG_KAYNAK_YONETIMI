# Aşama 4.4 — Pygame Klavye Adaptörü Genel Planı

> **Belge türü:** Alt aşama genel planı  
> **Proje:** Eldoria — Hex World Laboratory  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** GENEL PLAN TASLAĞI — KULLANICI ONAYI BEKLİYOR  
> **Ön koşullar:** Aşama 4.1, 4.2 ve 4.3 tamamlandı; Aşama 4 genel planı ve revize edilmiş teknik mimari planı onaylandı.

---

## 1. Amaç

Aşama 4.4'ün amacı, fiziksel klavye girdisini mevcut hareket veri sözleşmesine uygun `MovementIntent` nesnelerine dönüştüren ince ve Pygame'e özel bir adaptör oluşturmaktır.

Bu aşamanın sonunda laboratuvar uygulaması, klavyede basılı tutulan yön tuşlarını okuyabilecek ve her simülasyon tick'inde hareket sistemine açık bir hareket niyeti sağlayabilecektir. Hareket matematiği, hız hesabı ve konum güncellemesi mevcut saf Python hareket çekirdeğinde kalacaktır.

Aşama 4.4, tek başına görsel hareket demosu veya dünya/hex entegrasyonu değildir. Yalnızca klavye ile hareket çekirdeği arasındaki girdi sınırını kurar.

## 2. Devralınan mimari sözleşmeler

Aşağıdaki mevcut kararlar korunacaktır:

1. `MovementIntent` girdi cihazından bağımsızdır ve yönü `Vector2` ile taşır.
2. Sıfır yön vektörü durma niyetidir.
3. `MovementIntegrator` yönü normalize eder; çapraz hareket tek eksenli hareketten hızlı olmaz.
4. `MovementSystem.step(tick_number, intent)` dışarıdan sağlanan ardışık tick başına bir kez çağrılır.
5. Canonical simülasyon hızı 60 TPS, hareket adımı ise `1/60` saniyedir.
6. `DemoTickPump` gerçek zamanı tick'lere dönüştürür; bir karede en fazla 8 tick işler ve kalan zaman borcunu korur.
7. Hareket çekirdeği Pygame import etmez. Pygame yalnızca input/application sınırında bulunabilir.
8. Dünya konumu `WorldPoint` olarak kalır; bu aşamada world/hex çözümlemesi yapılmaz.
9. Laboratuvar bağımsız paket olma niteliğini korur; ana oyun modüllerine bağımlılık eklenmez.

## 3. Hedeflenen klavye davranışı

İlk sürüm için önerilen kontrol şeması:

| Hareket | Tuşlar | Üretilen yön |
|---|---|---|
| Yukarı | W veya ↑ | (0, +1) |
| Aşağı | S veya ↓ | (0, -1) |
| Sol | A veya ← | (-1, 0) |
| Sağ | D veya → | (+1, 0) |

Davranış kuralları:

- WASD ve ok tuşları birlikte desteklenir.
- Aynı yönün iki eşdeğer tuşu birlikte basılırsa eksen değeri iki katına çıkmaz.
- Aynı eksendeki zıt yönler birlikte basılırsa birbirini götürür; sonuç o eksende sıfırdır.
- Yatay ve dikey yön aynı anda basılırsa adaptör ham çapraz vektörü üretir. Normalizasyon mevcut hareket çekirdeğinin sorumluluğudur.
- Hiçbir yön tuşu basılı değilse sıfır vektörlü `MovementIntent` üretilir; karakter durur.
- Tuş basılı tutulduğu sürece her simülasyon tick'inde güncel niyet yeniden okunur.
- Tuş bırakma veya yön değiştirme bir sonraki hareket tick'ine yansır.
- Klavye tekrarı (key repeat) üzerinden hareket üretilmez; basılı tuş durumu esas alınır.
- Pencere odağının kaybolması durumunda takılı kalmış hareket girdisi oluşmaması için odak kaybı davranışı teknik planda açıkça tanımlanıp test edilir.

Eksen sözleşmesi mevcut matematiksel dünya koordinatlarıyla uyumludur: +X sağ, +Y yukarıdır. Pygame ekran koordinatlarının aşağı doğru artması, hareket yönü sözleşmesini tersine çevirmemelidir.

## 4. Sorumluluk ve bağımlılık sınırı

Önerilen veri akışı:

```text
Pygame event pump / keyboard state
              |
              v
PygameKeyboardAdapter
              |
              | MovementIntent
              v
MovementSystem.step(tick_number, intent)
              |
              v
MovementIntegrator
              |
              v
Immutable MovementState
```

Adaptörün sorumlulukları:
- Pygame klavye durumunu okumak.
- Tuşları matematiksel X/Y yön bileşenlerine çevirmek.
- Her çağrıda yeni veya eşdeğer değişmez `MovementIntent` döndürmek.
- Girdi yokluğunu açık sıfır yön niyeti olarak bildirmek.
- Pygame'e özgü veri tiplerini ve sabitlerini adaptör sınırında tutmak.

Adaptörün sorumluluğu olmayan işler:
- Hız veya konum hesaplamak.
- Vektör normalizasyonu yapmak.
- Tick üretmek veya zaman biriktirmek.
- `MovementSystem` state'ini doğrudan değiştirmek.
- Hücre/harita sorgulamak.
- Çarpışma veya engel çözmek.
- Kamera, animasyon veya render yapmak.

## 5. Önerilen uygulama yaklaşımı

Teknik mimari planında kesinleştirilmek üzere önerilen yaklaşım:

- Yeni `input` paketi altında Pygame klavye adaptörü oluşturmak.
- Adaptörü mevcut `MovementIntent` ve `Vector2` tiplerine bağlamak.
- Adaptörün klavye durumunu doğrudan Pygame'den okumasını, test edilebilirlik için klavye durumu sağlayıcısının enjekte edilebilmesini değerlendirmek.
- Uygulama katmanında `DemoTickPump` callback'inin her tick için adaptörden güncel intent almasını sağlamak; adaptörün tick veya zaman yönetmesini önlemek.
- Mevcut `LabApplication` kabuğunu yalnızca bu girdi akışını test etmek için gereken en küçük ölçüde genişletmek. Tam hareket sahnesi ve görsel prototip Aşama 4.6'ya bırakılacaktır.
- Pygame event kuyruğunun her render karesinde işlenmesini sürdürmek; klavye niyetini simülasyon tick'inde örneklemek.
- Odak kaybı ve pencere kapatma davranışlarını uygulama yaşam döngüsüyle uyumlu tutmak.

Dosya adları, sınıf API'si, input sağlayıcısının biçimi ve uygulama kabuğuna yapılacak değişiklikler teknik mimari planında belirlenecektir.

## 6. Test ve kabul hedefleri

### 6.1 Tuş eşlemesi
- W/A/S/D tuşlarının her biri doğru eksen ve işaret üretir.
- Dört ok tuşunun her biri doğru eksen ve işaret üretir.
- WASD ve ok tuşları aynı anda kullanılabilir.
- Eşdeğer iki tuşun aynı yönde basılması değeri iki katına çıkarmaz.

### 6.2 Tuş kombinasyonları
- Dört çapraz kombinasyon doğru ham vektörü üretir.
- Aynı eksendeki zıt tuşlar birbirini götürür.
- Birden fazla eşdeğer tuş ve karşıt tuş birlikte basıldığında sonuç deterministiktir.
- Hiçbir tuş basılı değilken sıfır hareket niyeti üretilir.

### 6.3 Girdi yaşam döngüsü
- Tuş basılıyken aynı yön niyeti tekrar okunabilir.
- Tuş bırakılınca sonraki okumada sıfır veya kalan diğer tuşların yönü üretilir.
- Yön değiştirme bir sonraki örneklemede doğru yansır.
- Pencere odağı kaybında hareket girdisi takılı kalmaz.
- Klavye tekrarı hareket hızını artırmaz.

### 6.4 Mimari ve entegrasyon
- Hareket çekirdeği ve `MovementSystem` Pygame import etmez.
- Pygame bağımlılığı yalnızca input/application sınırında kalır.
- Adaptör yalnızca `MovementIntent` üretir; hareket state'ini değiştirmez.
- Aynı tick'te adaptörden alınan niyet `MovementSystem` üzerinden mevcut integratöre iletilebilir.
- Headless testler SDL dummy ayarlarıyla CI ortamında çalışır.
- Mevcut laboratuvar test paketi, geometri ve world testleri gerilemez.
- Linux ve Windows CI başarılı olur.

## 7. Performans ve kaynak kullanımı

- Klavye durumu yalnızca gerektiği anda örneklenir; her tick'te tüm harita veya dünya verisi taranmaz.
- Adaptör küçük bir yön vektörü ve hareket niyeti dışında gereksiz veri üretmez.
- Girdi örneklemesi sabit zaman veya ayrı thread oluşturmaz.
- Her render karesinde event kuyruğu normal Pygame yaşam döngüsü içinde işlenir.
- Performans iddiası ölçüm olmadan verilmez; bu aşama için pahalı benchmark beklenmez.

## 8. Kapsam dışı

Aşama 4.4'te aşağıdakiler yapılmayacaktır:

- Gamepad/joystick veya yeniden tuş atama arayüzü.
- Tuş konfigürasyonunu dosyaya kaydetme.
- Fare ile tıklayarak hareket.
- Yürüme/koşma, sprint, hız modu veya farklı hareket hızları.
- İvme, sürtünme, atalet veya fizik.
- Çarpışma, duvar, engel ve harita sınırında durma.
- WorldPoint → axial → CellAddress entegrasyonu (Aşama 4.5).
- Kamera, animasyon, sprite veya nihai görsel prototip (Aşama 4.6).
- NPC/AI girdi üretimi.
- Ana oyuna, `main` veya `demo_eldoria` dallarına entegrasyon.
- Laboratuvarın bağımsızlığını bozacak ana proje bağımlılığı.

## 9. Riskler ve kontrol yaklaşımı

| Risk | Olası sonuç | Kontrol |
|---|---|---|
| Ekran Y ekseninin matematiksel Y ile karıştırılması | Yukarı/aşağı ters hareket | Açık işaret sözleşmesi ve yön testleri |
| WASD ile ok tuşlarının iki kez sayılması | İstenmeyen hız/vektör büyüklüğü | Boolean yön birleştirme; toplama yerine eksen işareti |
| Zıt tuş kombinasyonunun belirsizliği | Tutarsız hareket | Aynı eksende cebirsel iptal |
| Keydown olaylarına dayalı hareket | Tuş bırakma veya tekrar sorunları | Basılı tuş durumunu örnekleme |
| Pygame'in çekirdeğe sızması | Headless test ve bağımsızlık kaybı | Adaptörü ayrı input katmanında tutma |
| Tick başına güncel girdinin alınmaması | Gecikmiş durma/yön değişimi | Her hareket tick'inde intent örnekleme |
| Pencere odağı kaybı | Tuşun takılı kalması | Odak kaybında nötr girdi ve test |
| Demo kapsamının büyümesi | 4.6 prototip işlerinin erkenden başlaması | Uygulama kabuğunda minimum entegrasyon |

## 10. Alt aşama iş sırası

1. Güncel laboratuvar dalı ve Pygame uygulama yaşam döngüsünü doğrula.
2. Input adaptörünün public API ve test edilebilir klavye sağlayıcısı sözleşmesini belirle.
3. WASD/ok tuşu eşlemesini ve kombinasyon kurallarını uygula.
4. Odak kaybı ve boş girdi davranışını tanımla.
5. Adaptör unit testlerini ekle.
6. `DemoTickPump` → input adapter → `MovementSystem` akışını headless entegrasyon testiyle doğrula.
7. Gerekli en küçük uygulama kabuğu bağlantısını yap; tam hareket prototipini bu aşamaya taşıma.
8. Tam laboratuvar test paketi ve Linux/Windows CI doğrulamasını çalıştır.
9. Sonuçları Aşama 4.4 kapanış raporunda belgele.

## 11. Aşama 4.4 kabul kapısı

Aşama 4.4 ancak aşağıdaki koşulların tamamı karşılandığında tamamlanmış sayılır:

- [ ] WASD ve ok tuşları doğru yönleri üretir.
- [ ] Eşdeğer tuşlar aynı yön değerini iki katına çıkarmaz.
- [ ] Zıt tuşlar aynı eksende birbirini götürür.
- [ ] Çapraz hareket niyeti doğru ham vektörü üretir ve normalizasyon core'da kalır.
- [ ] Tuş bırakma durma niyetini doğru üretir.
- [ ] Tuş basılı tutma, key repeat'e bağlı olmadan sürekli niyet üretir.
- [ ] Odak kaybı takılı hareket girdisi bırakmaz.
- [ ] Pygame bağımlılığı input/application sınırını aşmaz.
- [ ] Tick başına güncel intent ile MovementSystem entegrasyonu test edilir.
- [ ] Headless testler, tam regresyon ve Linux/Windows CI başarılıdır.
- [ ] Kapanış raporu laboratuvar dalına eklenip doğrulanır.

## 12. Onay ve değişiklik kontrolü

Bu belge Aşama 4.4 genel planıdır; teknik dosya/API tasarımını veya kod uygulamasını tek başına onaylamaz.

Kullanıcı genel planı onayladıktan sonra:
1. Aşama 4.4 teknik mimari planı hazırlanır.
2. Dosyalar, sınıf/API sözleşmeleri, input örnekleme zamanlaması, odak kaybı davranışı ve test senaryoları kesinleştirilir.
3. Teknik plan kullanıcı onayına sunulur.
4. Açık teknik plan onayı olmadan kod veya test değişikliği yapılmaz.

Bütün planlama ve uygulama yalnızca `experiment/hex-world-laboratory` dalında tutulacaktır. `main` ve `demo_eldoria` dallarına yazılmayacak, merge veya geçmiş değiştirme işlemi yapılmayacaktır.

**Mevcut durum:** Aşama 4.4 genel planı onay bekliyor. Kod uygulaması başlamamıştır.
