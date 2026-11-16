# Aşama 4.7.5 — Teknik Kapanış Raporu

> **Proje:** Eldoria — Hex World Laboratory  
> **Dal:** `experiment/hex-world-laboratory`  
> **Tarih:** 16 Kasım 2026  
> **Durum:** TEKNİK DOĞRULAMA TAMAMLANDI — KAPATILDI  
> **Teknik plan:** `docs/PHASE-04.7.5-TECHNICAL-PLAN.md`  
> **Teknik plan güncelleme commit'i:** `1d97fe6531cc94279fb2c20095f0ec2dad6ad675`

## 1. Amaç ve kapsam

Aşama 4.7.5, hareket demosunun salt okunur teşhis panelinde seçili hareket modunu, mod hız çarpanını ve teorik mod hızını görünür kılmayı; bu değerleri gerçek anlık hızdan ayrı tutmayı kapsar. Ayrıca Alt tuşunun basılı tutma yerine kenar tetiklemeli aç/kapat (toggle) davranışını ve Shift ile öncelik etkileşimini güvenceye alır.

## 2. Uygulama denetimi

Mevcut kod incelendi; yeni üretim kodu değişikliği gerekmedi.

- `MovementDemo`, tek bir `MovementConfig` örneğini hem `MovementSystem` hem teşhis hesabı için kullanır.
- Panel `NORMAL`, `RUNNING`, `STEALTH` mod adlarını gösterir.
- Çarpan `MovementConfig.speed_multiplier_for(mode)` üzerinden okunur.
- Teorik mod hızı `max_speed × multiplier` olarak hesaplanır; sabit 60 dünya birimi/saniye varsayımı yoktur.
- Gerçek `Velocity` vektörü ve büyüklüğü ayrı satırda gösterilir. Aktör dururken teorik mod hızı görünür kalırken gerçek hız sıfırdır.
- Render/teşhis çizimi simülasyon tick'i ilerletmez ve hareket durumunu değiştirmez.
- Panel genişliği satır uzunluğuna, yüksekliği satır sayısına göre hesaplanır.

## 3. Otomatik test kapsamı

`tests/integration/test_movement_demo_render.py` içindeki teşhis testleri:

1. Normal, koşma ve gizlilik modlarında doğru mod adı ve çarpanın gösterilmesi.
2. Temel hız 40 iken teorik hızların sırasıyla 40.0, 60.0 ve 20.0 hesaplanması.
3. Aktör hareketsizken gerçek Velocity hızının 0.00 kalması.
4. Hareket sırasında gerçek Velocity hızının teorik mod hızıyla karıştırılmaması.

Bunlara ek olarak hareket modu geçişleri, Alt toggle davranışı, sol/sağ Alt örtüşmesi, Shift önceliği, odak kaybı/geri kazanımı ve render değişmezliği testleri aynı tam laboratuvar test paketinde yer alır.

## 4. CI ve teknik doğrulama kanıtları

Aşama 4.7.5 testlerini içeren ve daha sonraki 4.7.4 entegrasyon testlerini de kapsayan tam laboratuvar CI:

- **Hex World Laboratory CI:** Başarılı — **504 passed**.
- **Map persistence benchmark:** Başarılı.
- **Runtime persistence benchmark:** Başarılı.
- **Core Quality Linux:** Başarılı.
- **Core Quality Windows:** Başarılı.

Kanıtlar:
- Laboratory CI run: `43879093003`, commit `3a4d5944b3b5861637a4948acd18f913df3f755c`.
- Core Quality run: `43879093008`, aynı commit; Linux ve Windows işleri başarılı.
- Sonraki branch HEAD doğrulaması: Laboratory CI run `43880187020` ve Core Quality run `43880186960`, commit `51f525a3c2d943c365c8b2a9ee9037038d9c3210`; tam laboratuvar paketi yeniden **504 passed** ve her iki Core Quality işi başarılı.

Bu sonuçlar GitHub Actions ortamına aittir. Kullanıcının yerel bilgisayarında test veya masaüstü kabulü yapıldığı anlamına gelmez.

## 5. Manuel masaüstü kabulü

Kullanıcının açık kararıyla gerçek Pygame penceresindeki mod/teşhis kontrolleri Aşama 4.7.5 kapanış şartından çıkarılmış ve Aşama 4 genel kapanışına taşınmıştır.

Aşağıdaki kontroller `docs/MANUAL-MOVEMENT-DEMO-CHECKLIST.md` içinde açık kalır:

- Normal, Shift ile koşma ve Alt toggle ile gizlilik modlarının gerçek pencerede gözlenmesi.
- Alt basılı tutma, sol/sağ Alt örtüşmesi ve Shift önceliği.
- Mod adı, çarpan, teorik hız ve gerçek Velocity satırlarının görsel kontrolü.
- Temel hız değişikliğinin teşhis paneline yansıması.
- Pencere odağı kaybı/geri kazanımı.
- Pencere boyutu ve teşhis panelinin taşma yapmaması.

Headless CI bu manuel görsel kabulün yerine geçmez.

## 6. Değişiklik sınırı ve dal güvenliği

- Çalışma dalı yalnızca `experiment/hex-world-laboratory` olmuştur.
- Bu kapanış için üretim kodu değiştirilmemiştir; teknik planın kapanış koşulları güncellenmiş ve bu rapor eklenmiştir.
- `main` ve `demo_eldoria` dallarına yazma veya merge yapılmamıştır.

## 7. Sonuç

Teşhis paneli, mod/hız ayrımı ve Alt toggle davranışının otomatik test kanıtları mevcuttur. Tam laboratuvar test paketi ile Linux/Windows Core Quality doğrulamaları başarılıdır. Açık kalan tek kabul grubu, kullanıcının kararıyla Aşama 4 genel kapanışına ertelenen gerçek masaüstü kontrolleridir.

**Karar: Aşama 4.7.5 teknik doğrulama kapsamında kapatılmıştır.**
