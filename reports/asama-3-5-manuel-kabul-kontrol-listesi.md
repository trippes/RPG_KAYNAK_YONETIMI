# Eldoria RPG — Aşama 3.5 Manuel Oynanış Kabul Kontrol Listesi

**Çalışma dalı:** `experiment/map-cleanup`  
**Hazırlanma tarihi:** 21 Kasım 2026  
**Durum:** Kullanıcı tarafından gerçek Pygame oturumunda uygulanmayı bekliyor  
**Amaç:** Otomatik testlerin kapsayamadığı gerçek zamanlı klavye, fare, kamera/oyun yüzeyi, fizik ve hareket hissi davranışlarını doğrulamak.

## 1. Test ortamını başlatma

Proje kök dizininde PowerShell aç:

```powershell
python main.py --play --content-package content/movement_test
```

Bu komut yalnızca mekanik test paketini açar; `content/active_package.json` veya varsayılan aktif paket seçimini değiştirmez. Test sahası ve kontrol açıklamaları için `content/movement_test/README.md` referans alınır.

## 2. Kontrol listesi

Her satırı gerçekten oyunda denedikten sonra işaretle. Bir adım başarısızsa not alanına gözlenen davranışı yaz; başarısız adımı geçilmiş sayma.

| # | Kontrol | Uygulama | Beklenen sonuç | Sonuç |
|---:|---|---|---|---|
| 1 | Oyun açılışı | Komutu çalıştır ve yeni oyun oturumuna gir. | Pygame penceresi açılır; test sahası yüklenir; uygulama hata vermeden kullanılabilir. | Bekliyor |
| 2 | Normal hareket | WASD ve yön tuşlarıyla dört ana yönde ve çapraz yönde hareket et. | Hareket kesintisizdir; tuşa basma/bırakma anında ani hücre teleportu olmaz. | Bekliyor |
| 3 | Yön değiştirme | Hareket hâlindeyken yönü art arda değiştir. | Karakter yeni yönü kontrollü biçimde izler; konumda sıçrama veya takılma olmaz. | Bekliyor |
| 4 | Koşma | Shift basılıyken normal hareketle aynı mesafeyi karşılaştır. | Hızlanma sonrasında koşma normal hızdan belirgin biçimde hızlıdır; hedef çarpanı 1,5'tir. | Bekliyor |
| 5 | Gizlilik | Alt tuşuna basıp bırak; tekrar basarak modu kapat. | Gizlilik modu açılıp kapanır; hedef hız normal hızın 0,5 katıdır. | Bekliyor |
| 6 | Statik engel | Haritanın kuzeyindeki su/taş engel kümesine doğru yürü. | Karakter engelin içinden geçmez ve ince engeli tünelleyerek aşmaz. | Bekliyor |
| 7 | Duvar kayması | Engel yüzeyine çapraz açıyla ilerle; engel boyunca hareket girdisini koru. | Engele dik hareket bileşeni engellenir; yüzeye paralel bileşen devam eder. Karakter duvarda tamamen kilitlenmez. | Bekliyor |
| 8 | NPC itişi | Başlangıç alanının batısındaki Etkileşim Görevlisi'ne fiziksel olarak yürü. | NPC çarpışma sonucunda fiziksel olarak yer değiştirir; oyuncu ve NPC birbirinin içinden geçmez. | Bekliyor |
| 9 | NPC/engel etkileşimi | NPC'yi yakındaki statik engel yönüne doğru itmeye çalış. | NPC statik engelin içine girmez; hareket alanı kalmadığında oyuncu/NPC çakışması çözülür. | Bekliyor |
| 10 | Hücre sınırı | Birkaç hücre boyunca kesintisiz hareket et. | Görsel/continuous konum ile hücre occupancy geçişi senkron kalır; karakter hücre merkezine zorla sıçramaz. | Bekliyor |
| 11 | Click-to-move | Açık bir zemin noktasına tıkla; hedefe yaklaşırken hareketi gözlemle. | Rota fiziksel engelleri ihlal etmez; hedefe yaklaşırken frenleme/varış kontrollüdür; hedef noktasına teleport olmaz. | Bekliyor |
| 12 | Dolu hedef / engellenen hareket | Doğudaki Çarpışma Hedefi'ne ve engelli hücrelere doğru ilerle. | Hareket engellenir veya fiziksel çarpışma ile çözülür; karakter engelin içine geçmez ve oyun oturumu çökmez. | Bekliyor |
| 13 | Uzun hareket oturumu | En az 2 dakika hareket, durma, yön değiştirme ve çarpışma dene. | Birikmiş hız, eski yön girdisi, occupancy kayması, titreme veya beklenmeyen konum sıçraması görülmez. | Bekliyor |
| 14 | Hata sonrası devam | Engel/NPC çarpışmasından sonra başka yöne hareket et. | Çarpışma sonrasında hareket kontrolü çalışmaya devam eder; karakter kilitli kalmaz. | Bekliyor |

## 3. Test sonucu kaydı

- Test tarihi/saat:
- Test edilen commit:
- İşletim sistemi:
- Python sürümü:
- Ekran çözünürlüğü:
- Geçen adımlar:
- Başarısız adımlar:
- Gözlenen hata / tekrar üretme adımları:

## 4. Kabul ölçütü

Aşama 3.5 manuel kabulü ancak tüm zorunlu kontroller gerçek Pygame oturumunda başarıyla tamamlandığında verilir. Başarısız adım varsa ilgili hata düzeltilip aynı adım yeniden uygulanmalıdır.

GitHub Actions'taki unittest/pytest, Ruff, release-candidate ve Pygame headless smoke testleri otomatik doğrulamadır; gerçek pencerede klavye/fare kullanımı, hareket hissi, görsel kayma ve oyuncu gözlemi yerine geçmez.

**Not:** Bu kontrol listesi çalışma dalına eklenmiştir; yerel bilgisayarda oyun çalıştırıldığı veya manuel testlerin tamamlandığı anlamına gelmez.
