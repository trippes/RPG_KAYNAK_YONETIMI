# Aşama 4.7 — Hareket Modları Kapanış Raporu

> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** ALT AŞAMA TEKNİK OLARAK KAPALI; AŞAMA 4 GENEL KULLANICI KABULÜ TAMAMLANDI

## 1. Amaç ve kapsam

Aşama 4.7, sürekli hareket çekirdeğine Normal, Koşma ve Gizlilik hız modlarını eklemiş; klavye adaptöründe Shift basılı-tutma ve Alt aç/kapat davranışını tanımlamış; modları hareket demosunda görünür kılmıştır.

Kabul edilen sözleşme:
- Normal: 1.0x.
- Koşma: Shift basılı tutulduğu sürece 1.5x.
- Gizlilik: Alt'a bir kez basıldığında açılır, tekrar basıldığında kapanır; 0.5x.
- Gizlilik, Koşma'ya göre önceliklidir.
- Alt'ın basılı tutulması veya sol/sağ Alt'ın örtüşmesi tekrar tekrar toggle üretmez.
- Gizlilik kapatıldığında Shift hâlâ basılıysa Koşma geri gelir.
- Odak kaybı yönü ve gizlilik toggle durumunu sıfırlar; odak kazanımı sahte Alt basışı üretmez.
- Mod değişimleri fiziksel WorldPoint konumunu sıçratmaz.

## 2. Alt aşama sonuçları

| Alt aşama | Gerçekleşen çıktı | Kanıt |
|---|---|---|
| 4.7.1 — Hareket modu sözleşmesi | MovementMode NORMAL/RUNNING/STEALTH; intent/state mod alanları | `f307ecaaff956cd408d2bab81c01e810845e0d75` |
| 4.7.2 — Hız profilleri | Config tabanlı 1.0x / 1.5x / 0.5x hız profilleri | `322ef007d73e1743652b8a9c2c343ddbb47ffb5a` |
| 4.7.3 — Klavye adaptörü | Shift hold, Alt toggle, sol/sağ modifier birleştirme, odak yaşam döngüsü ve toggle regresyon testleri | `b14e55a020e076ec9e7653e868ba094cefea4dc5`, `9c78402bdd0b12bd457455a068b183856f033bd7`, `0b6dafe4d346c6f61a6fc03282eb81c2fdb68f75` |
| 4.7.4 — Uçtan uca entegrasyon | Mod değişimleri sırasında hücre sınırı sürekliliği, Shift/Alt etkileşimi ve focus lifecycle entegrasyon testleri | `3a4d5944b3b5861637a4948acd18f913df3f755c` |
| 4.7.5 — Teşhis görünümü | Mod, çarpan, teorik mod hızı ve gerçek Velocity ayrımı; salt okunur teşhis | `257524130869156e3b54dc4dc8002276ebeeb85e` |
| 4.7.6 — Son teknik doğrulama | 505 laboratuvar testi, Linux/Windows Core Quality, mimari sınır testi ve hareket benchmark'ı | `dafb5ce674c2356b1e07c4fde1965c7ee67ec611` |

## 3. Son teknik doğrulama

Son commit `dafb5ce674c2356b1e07c4fde1965c7ee67ec611` üzerinde:
- Hex World Laboratory CI: **505 passed**.
- Core Quality Linux: **1.968 passed, 1 warning**.
- Core Quality Windows: **1.968 passed**.
- Map persistence ve runtime persistence benchmark'ları başarılı.
- Hareket + hex hücre takip benchmark'ı 1, 10, 100 ve 1.000 aktör için başarılı ölçüm üretti.
- Geometry/movement/simulation/world paketlerinin Pygame import etmediğini denetleyen mimari test başarılı.

CI kayıtları:
- [Laboratory CI run 43882088050](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43882088050)
- [Core Quality run 43882087966](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43882087966)

Hareket benchmark'ının ayrıntılı ortam ve ölçüm değerleri `bu raporun 7.3. bölüm` içindedir. Ölçümler yalnızca GitHub Linux CI makinesindeki MovementSystem + MovementCellTracker yükünü kapsar; toplam oyun performansı veya hedef bilgisayar için garanti değildir.

## 4. Aşama 4 genel masaüstü kabulü

Aşama 4.7'nin teknik kapanışı sırasında masaüstü kabulü Aşama 4 genel kapanışına ertelenmişti. Kullanıcı, 16 Kasım 2026 tarihinde Aşama 4 bilgisayar kabul kontrolündeki 11 maddenin tamamını başarılı olarak bildirmiştir.

Bu nedenle masaüstü kabulü artık açık değildir. Kullanıcı kabulinin kapsamı ve kayıt biçimi `reports/PHASE-04-CLOSURE-REPORT.md` belgesinde yer alır. Bu kabul, 4.7 alt aşamalarının teknik doğrulama kayıtlarını geriye dönük değiştirmez; Aşama 4'ün genel kapanış kapısını tamamlar.

## 5. Dal güvenliği

- Bütün çalışmalar `experiment/hex-world-laboratory` dalında tutuldu.
- `main` HEAD `9d39afe21158a036ae3c5a7a00f552369b340f51` olarak kaldı.
- `demo_eldoria` HEAD `7d53d431d5c3639fd95d273de9043b64483a5125` olarak kaldı.
- Merge, cherry-pick veya ana oyun entegrasyonu yapılmadı.

## 6. Sonuç

**Aşama 4.7 teknik uygulama ve otomatik doğrulama bakımından tamamlanmıştır.** Aşama 4 genel masaüstü kabulü kullanıcı tarafından 11/11 başarılı olarak bildirilmiş ve Aşama 4, `reports/PHASE-04-CLOSURE-REPORT.md` ile kapatılmıştır. Bu rapor, sonraki aşamaya otomatik uygulama izni vermez.


## 7. Alt aşama teknik doğrulama kayıtları

Aşağıdaki alt aşama kapanış belgeleri bu rapora birleştirilmiştir. Her alt aşamanın teknik planı `docs/` altında korunur; burada uygulama ve kabul kanıtlarının tek kronolojik özeti tutulur.

### 7.1 — Uçtan uca entegrasyon testleri (4.7.4)

Üretim kodu değiştirilmeden `tests/integration/test_movement_demo_flow.py` genişletildi. Normal/koşma/gizlilik modları arasında hex sınırı geçişinde WorldPoint sürekliliği, Shift + Alt önceliği ve focus lost/gained yaşam döngüsü doğrulandı. İlk CI denemesinde hatalı seçilmiş flat-top sınır beklentisi düzeltildi; üretim kodunda kusur bulunmadı.

- Uygulama commit'i: `04eb0d36af004c3b77e58e8b6dc340bfb3d38dd2`.
- Test düzeltme commit'i: `3a4d5944b3b5861637a4948acd18f913df3f755c`.
- Laboratory CI: [43879093003](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43879093003), 504 test başarılı.
- Core Quality: [43879093008](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43879093008), Linux ve Windows başarılı.
- Yerel masaüstü kontrolü alt aşamadan çıkarılarak Aşama 4 genel kabulüne taşındı.

### 7.2 — Teşhis paneli (4.7.5)

Teşhis panelinde NORMAL/RUNNING/STEALTH modu, `MovementConfig.speed_multiplier_for(mode)`, teorik hız (`max_speed × multiplier`) ve gerçek Velocity ayrı gösterildi. Aynı `MovementConfig` örneği MovementSystem ve panel tarafından kullanıldı; render/diagnostics simülasyon tick'ini veya hareket state'ini değiştirmedi. Üretim kodunda yeni değişiklik gerekmemiş, mevcut entegrasyon testleri kullanılmıştır.

- 504 test başarılı; Laboratory CI [43879093003](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43879093003).
- Core Quality [43879093008](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43879093008), Linux/Windows başarılı.
- Sonraki branch doğrulaması: Laboratory CI [43880187020](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43880187020), Core Quality [43880186960](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43880186960); 504 test ve iki platform başarılı.
- Gerçek Pygame penceresi kabulü Aşama 4 genel kabulüne ertelendi ve 16 Kasım 2026'da 11/11 maddeyle tamamlandı.

### 7.3 — Son teknik doğrulama (4.7.6)

Hareket modları, klavye odak yaşam döngüsü, tick/FPS eşdeğerliği, WorldPoint–hex takibi, render'ın salt okunurluğu ve mimari bağımlılık sınırları tek kapıda doğrulandı. `tests/unit/test_architecture_boundaries.py` Geometry, Movement, Simulation ve World paketlerinde Pygame import'unu AST üzerinden denetledi.

- Son doğrulama commit'i: `dafb5ce674c2356b1e07c4fde1965c7ee67ec611`.
- Laboratory CI: [43882088050](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43882088050), **505 passed**.
- Core Quality: [43882087966](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/43882087966), Linux **1.968 passed, 1 warning**, Windows **1.968 passed**.
- Map persistence, runtime persistence, movement + hex tracking benchmarkları başarılı.

Hareket benchmark'ı yalnızca MovementSystem adımı ve MovementCellTracker çözümlemesini kapsar; render ve diğer oyun sistemleri dahil değildir:

| Aktör | Ortalama 10-tick parti (ms) | P95 parti (ms) | Ortalama aktör-tick (µs) |
|---:|---:|---:|---:|
| 1 | 0.1548 | 0.1756 | 15.4797 |
| 10 | 1.5196 | 1.5367 | 15.1961 |
| 100 | 15.1547 | 15.3680 | 15.1547 |
| 1.000 | 153.4378 | 156.1921 | 15.3438 |

Ölçümler Linux CI koşucusuna aittir; hedef donanım veya toplam oyun performansı garantisi değildir.
