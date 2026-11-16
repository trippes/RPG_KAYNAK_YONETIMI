# Aşama 4.7 — Hareket Modları Kapanış Raporu

> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** TEKNİK UYGULAMA VE OTOMATİK DOĞRULAMA TAMAMLANDI; MASAÜSTÜ KABULİ AÇIK

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

Hareket benchmark'ının ayrıntılı ortam ve ölçüm değerleri `reports/PHASE-04.7.6-CLOSURE-REPORT.md` içindedir. Ölçümler yalnızca GitHub Linux CI makinesindeki MovementSystem + MovementCellTracker yükünü kapsar; toplam oyun performansı veya hedef bilgisayar için garanti değildir.

## 4. Açık masaüstü kabulü

Kullanıcı, bilgisayar başındaki manuel kontrollerin Aşama 4'ün en sonunda toplu yapılmasını istedi. Bu karar doğrultusunda Aşama 4.7 alt aşamalarının teknik kapanışı masaüstü testlerine bağlanmamıştır.

Aşağıdaki liste henüz kullanıcı bilgisayarında doğrulanmamıştır ve açık kalır:
- Uygulama açılışı ve 61 hücreli haritanın görünmesi.
- WASD/ok yönleri, durma, zıt yön ve çapraz hareket.
- Shift basılı tutma ile koşma.
- Alt toggle ile gizlilik, sol/sağ Alt örtüşmesi ve Shift önceliği.
- Mod geçişi sırasında hücre sınırı sürekliliği.
- Odak kaybı/geri kazanımı ve takılı modifier davranışı.
- Teşhis panelinin gerçek pencerede doğru görünmesi.
- Normal pencere kapanışı.

Kontrol listesi: `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md`. Maddeler kullanıcı gerçek masaüstü testini yapana kadar PASS olarak işaretlenmemelidir.

## 5. Dal güvenliği

- Bütün çalışmalar `experiment/hex-world-laboratory` dalında tutuldu.
- `main` HEAD `9d39afe21158a036ae3c5a7a00f552369b340f51` olarak kaldı.
- `demo_eldoria` HEAD `7d53d431d5c3639fd95d273de9043b64483a5125` olarak kaldı.
- Merge, cherry-pick veya ana oyun entegrasyonu yapılmadı.

## 6. Sonuç

**Aşama 4.7 teknik uygulama ve otomatik doğrulama bakımından tamamlanmıştır.** Gerçek masaüstü kabulü Aşama 4 genel kapanışında yapılacaktır. Bu rapor Aşama 4'ün tamamlandığını veya Aşama 5'e geçiş izni verildiğini ifade etmez.
