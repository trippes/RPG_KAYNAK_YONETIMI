# Aşama 6 — Masaüstü Görsel Kabul Kontrol Listesi

> Durum: **KULLANICI TARAFINDAN KABUL EDİLDİ — 17 Kasım 2026.**  
> Çalışma dalı: `experiment/hex-world-laboratory`  
> Giriş noktası: `python -m hex_world_lab`

Bu liste yalnızca son masaüstü/görsel kabul içindir. Otomatik testler GitHub Actions üzerinde yürütülmüştür; kullanıcıdan tekrar test komutu çalıştırması istenmez. Kullanıcı, listedeki kontrollerin tamamını kendi bilgisayarında gerçekleştirdiğini ve hepsinin başarılı olduğunu 17 Kasım 2026 tarihinde bildirdi. Aşama 6 görsel kabul kapısı kapanmıştır.

## 1. Hazırlık

- [x] Depoda `experiment/hex-world-laboratory` dalına geçildi ve son değişiklikler alındı.
- [ ] Laboratuvar sanal ortamı etkinleştirildi.
- [ ] Terminal laboratuvar dizininde açıldı: `experiments/hex_world_laboratory`.
- [ ] `python -m hex_world_lab` komutuyla pencere açıldı.

## 2. Kamera ve zoom

- [ ] Oyun açıldığında karakter ve harita doğru konumda görünüyor.
- [ ] Karakter hareket ettiğinde kamera onu yumuşak biçimde takip ediyor.
- [ ] Fare tekerleği yukarı çevrildiğinde kamera yakınlaşıyor.
- [ ] Fare tekerleği aşağı çevrildiğinde kamera uzaklaşıyor.
- [ ] Zoom en yakın ve en uzak seviyede sınırda kalıyor; görüntü bozulmuyor.
- [ ] Zoom sırasında karakterin dünya içindeki fiziksel konumu veya hareket hızı değişmiyor.

## 3. Harita çizimi ve hizalama

- [ ] Altıgen hücreler kamera hareketi sırasında birbirine göre kaymıyor.
- [ ] Ağaç, kaya, duvar ve ev iskeleti hücrelerle hizalı kalıyor.
- [ ] Karakter, hücreler ve bütün engeller aynı kamera hareketini izliyor.
- [ ] Yakınlaştırma/uzaklaştırmada dünya nesneleri birlikte ölçekleniyor.
- [ ] Tanı paneli ekran üzerinde sabit kalıyor; zoom ile büyüyüp küçülmüyor.

## 4. Fareyle hücre seçimi

- [ ] Bir hex hücresine tıklandığında doğru hücre vurgulanıyor.
- [ ] Kamera hareket ettirildikten sonra da tıklama doğru hücreyi seçiyor.
- [ ] Zoom yaptıktan sonra da tıklama doğru hücreyi seçiyor.
- [ ] Harita dışındaki boş alana tıklanınca geçerli hücre seçili kalmıyor.

## 5. Pencere boyutu ve açık dünya davranışı

- [ ] Pencereyi büyütüp küçültünce görüntü yeni viewport'a uyum sağlıyor.
- [ ] Pencere boyutu değişince kamera merkezi ve zoom beklenmedik biçimde sıfırlanmıyor.
- [ ] Harita sınırının ötesine hareket edildiğinde açık dünya hareket davranışı korunuyor.
- [ ] Kamera karakteri takip etmeye devam ediyor; karakter ekranın dışına kaçmıyor.

## 6. Hareket ve fizik regresyonu

- [ ] WASD hareketi çalışıyor.
- [ ] Shift ile koşma ve Alt ile gizlilik modu önceki davranışını koruyor.
- [ ] Ağaç, kaya, duvar ve ev collider'ları karakteri engelliyor.
- [ ] Kamera/zoom işlemi çarpışma mesafesini veya karakter collider boyutunu değiştirmiyor.
- [ ] Kamera hareketi simülasyon hızında veya 60 TPS davranışında gözle görülür bozulma oluşturmuyor.
- [ ] Pencere normal biçimde kapatılabiliyor.

## 7. Sonuç kaydı

Her madde için başarılı/başarısız işaretleyin. Başarısız maddelerde mümkünse ekran görüntüsü ve kısa açıklama ekleyin.

- Genel sonuç: **KABUL**
- Bulunan görsel sorunlar:
- Tekrarlanma adımları:
- Ekran görüntüsü veya ek not:

**Kabul kaydı:** Kullanıcı 17 Kasım 2026 tarihinde tüm masaüstü/görsel kontrollerin başarılı olduğunu bildirmiştir. Aşama 6 kapanış koşulu sağlanmıştır.
