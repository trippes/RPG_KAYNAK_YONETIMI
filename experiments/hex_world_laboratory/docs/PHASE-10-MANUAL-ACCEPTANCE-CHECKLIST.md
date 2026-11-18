# Aşama 10 — Manuel Kabul Kontrol Listesi

> **İlgili belgeler:** [Genel Plan](PHASE-10-GENERAL-PLAN.md) · [Teknik Mimari Planı](PHASE-10-TECHNICAL-PLAN.md)  
> **Durum:** UYGULAMA SONRASI KULLANICI TESTİ İÇİN TASLAK  
> **Launcher:** `python -m hex_world_lab`

Bu kontrol listesi kodlama tamamlanmadan kabul edilmiş sayılmaz. Her madde kullanıcı tarafından gerçek laboratuvar çalıştırmasında doğrulanacaktır.

## 1. Başlatma ve genel sahne
- [ ] Laboratuvar yalnızca `python -m hex_world_lab` komutuyla açılıyor.
- [ ] Oyuncu, iki NPC ve iki kaynak nesnesi sahnede görünüyor.
- [ ] Başlangıçta NPC veya kaynak kendiliğinden hareket etmiyor.

## 2. Oyuncu hareketi ve dünya eşitlemesi
- [ ] Oyuncu önceki aşamalardaki gibi hareket ediyor.
- [ ] Duvar/engel çarpışması ve kenar kayması bozulmamış.
- [ ] Oyuncu hareket ederken hücre/hex çözümü tutarlı kalıyor.
- [ ] Oyuncu hareketi tamamlandığında entity/spatial eşitlemesi aynı tick içinde gerçekleşiyor.
- [ ] Kamera takip ve zoom işlemleri oyuncunun fiziksel konumunu değiştirmiyor.

## 3. NPC, kaynak ve yoldaş sınırı
- [ ] NPC'ler yerlerinde sabit duruyor.
- [ ] Kaynak nesneleri yerlerinde sabit duruyor.
- [ ] NPC sağ tık menüsü açılıyor.
- [ ] Yoldaş olarak alma ve FOLLOW/WAIT/RETURN komutları mevcut ilişki kaydını güncelliyor.
- [ ] Bu komutların hiçbiri NPC'yi hareket ettirmiyor.
- [ ] Yoldaşlıktan çıkarma ilişkiyi kaldırıyor; NPC'yi silmiyor.

## 4. Render ve etkileşim
- [ ] Sol tık hedef seçimi çalışıyor.
- [ ] NPC sağ tık menüsü doğru hedefte açılıyor.
- [ ] Kamera zoom değişiminden sonra hedef seçimi doğru kalıyor.
- [ ] Birden fazla render frame'i simülasyon tick'i üretmiyor.
- [ ] Render sırasında oyuncu entity konumu veya spatial index güncellenmiyor; bu madde otomatik render-saflığı testleriyle de doğrulanmış olmalı.
- [ ] Pencere yeniden boyutlandırıldığında çizim ve seçim bozulmuyor.

## 5. Son kabul
- [ ] Otomatik testler ve Linux/Windows kalite kontrolleri başarılı.
- [ ] Benchmark ve görsel kanıt üretimi başarılı.
- [ ] Bilinen hata veya kapsam dışı davranışlar kapanış raporunda açıkça belirtilmiş.
- [ ] Kullanıcı manuel kabulü tamamlandı.
