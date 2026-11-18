# Aşama 11 — Manuel Kabul Kontrol Listesi

> **Durum:** TÜM OTOMATİK VE MANUEL KABUL KONTROLLERİ TAMAMLANDI — AŞAMA 11 KAPATILDI  
> **Çalışma dalı:** `experiment/hex-world-laboratory`  
> **Başlatıcı:** `python -m hex_world_lab`

Bu kontrol listesi, otomatik testlerin yerine geçmez. Kullanıcı tarafından masaüstünde gerçekleştirilecek görsel ve işlevsel kabul adımlarını tanımlar. Uygulama tamamlanmadan maddeler kabul edilmiş sayılmaz.

## A. Başlatma ve temel sahne

- [ ] Laboratuvar, tek resmi komut olan `python -m hex_world_lab` ile açılıyor.
- [ ] Başlangıç sahnesi hatasız yükleniyor.
- [ ] Pencere boyutu değiştirildiğinde dünya ve arayüz çizimi bozulmuyor.
- [ ] Kamera takip/zoom davranışı önceki kabul edilen davranışını koruyor.

## B. Oyuncu hareketi ve simülasyon

- [ ] Oyuncu normal, hızlı ve gizlilik hareket modlarında doğru hareket ediyor.
- [ ] Uzun süreli hareketten sonra oyuncu konumunda görünür sıçrama veya birikimli kayma oluşmuyor.
- [ ] Duvar, engel, köşe ve dar geçit temaslarında oyuncu engelin içine girmiyor.
- [ ] Engel boyunca kayma davranışı korunuyor.
- [ ] Render FPS değişse de aynı süre/tick girdisinde simülasyon sonucu değişmiyor.

## C. Entity ve etkileşim

- [ ] Oyuncu, NPC ve kaynak görselleri doğru yerde çiziliyor.
- [ ] NPC ve kaynaklar test boyunca sabit konumlarında kalıyor.
- [ ] NPC hedef seçimi/etkileşim menzili doğru çalışıyor.
- [ ] FOLLOW, WAIT ve RETURN komutları mevcut ilişki bilgisini güncelliyor; NPC'yi hareket ettirmiyor.
- [ ] Harita yükleme/boşaltma testinden sonra entity görselleri ve etkileşim kayıtları tutarlı kalıyor.

## D. Yoğun harita ve render

- [ ] Büyük haritada kamera hareketi sırasında görünür hücreler doğru çiziliyor.
- [ ] Kamera dışındaki hücrelerin culling davranışı görsel bozulma oluşturmuyor.
- [ ] Entity çizim sırası, foot-anchor ve Y-sort davranışı korunuyor.
- [ ] Zoom ve pencere boyutu değişiminde seçim/hedef işaretlemesi doğru konumda kalıyor.
- [ ] Yoğun engel ve entity sahnelerinde belirgin çizim titremesi, kaybolma veya yanlış katmanlama oluşmuyor.

## E. Stabilite ve gözlem

- [ ] Stres senaryosu çalıştırıldıktan sonra uygulama kontrollü biçimde kapanıyor.
- [ ] Tekrar açılışta önceki testten kalmış bozuk dünya/entity durumu görülmüyor.
- [ ] Görsel hata veya performans düşüşü gözlenirse senaryo adı ve tekrar adımı kaydedildi.
- [ ] Otomatik test raporu ve görsel artifact'ler manuel gözlemle çelişmiyor.

## F. Kabul kaydı

- [x] Laboratuvar testleri başarılı (774/774; 0 failure/error/skip).
- [x] Core Quality Linux başarılı.
- [x] Core Quality Windows başarılı.
- [x] Deterministik stress smoke ve tam stress profilleri raporlandı.
- [x] Benchmark ve bellek raporları incelendi; üç bağımsız oturum kaydedildi.
- [x] Otomatik CI'da kritik/yüksek önem dereceli test failure'ı bulunmadı.
- [x] Kullanıcı masaüstü görsel/işlevsel kabulünü verdi.

**Kullanıcı kabul tarihi:** 18 Kasım 2026

**Kullanıcı notları / gözlemler:**

________________________________________________________________

________________________________________________________________

**Kabul kararı:** KABUL — Aşama 11 kapatıldı


**Otomatik kanıtlar:** [Laboratuvar CI 44275529494](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44274231933) · [Core Quality 44275529498](https://github.com/trippes/RPG_KAYNAK_YONETIMI/actions/runs/44274231885)

**Manuel kabul durumu:** Kullanıcı 18 Kasım 2026 tarihinde A–E bölümlerindeki masaüstü görsel/işlevsel kontrollerin tamamının geçtiğini bildirdi. F bölümündeki kullanıcı kabulü kaydedildi; manuel kabul tamamlandı.
