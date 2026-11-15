# Aşama 2 — Hex Geometri Çekirdeği Uygulama Raporu

- Proje: Eldoria — Kaynak Yönetimi RPG
- Depo: trippes/RPG_KAYNAK_YONETIMI
- Dal: experiment/hex-world-laboratory
- Tarih: 15 Kasım 2026
- Durum: UYGULANDI — SON SINIR DAVRANIŞI DEĞİŞİKLİĞİNDEN SONRA TEST TEKRARI BEKLENİYOR
- Başlangıç HEAD: a36ea81b7defb8d307fd62015367a142996587f3
- İlk geometri uygulama commit'i: 32c0ab33cf1b10b8dfe5d8f75aa76c5d446dec69

## 1. Hedef
Pygame'den bağımsız saf Python hex koordinat ve geometri çekirdeği. Dünya modeli, hareket, fizik, kamera ve render kapsam dışıdır.

## 2. Onaylanan tercihler
- Flat-top ve pointy-top desteklenir.
- Dünya eksenleri matematiksel: X sağa, Y yukarı.
- Hex boyutu circumradius.
- Axial (0,0) hücresinin merkezi layout origin'idir.
- Nihai görsel yönelim bu aşamada seçilmemiştir.

## 3. Uygulanan modüller
- coordinates.py: AxialCoord, CubeCoord, WorldPoint.
- orientation.py: Flat-top ve pointy-top.
- layout.py: yönelim, circumradius ve origin.
- transforms.py: axial/cube, axial/world, fractional axial ve cube rounding.
- polygon.py: altı köşe, kenar ve hücre polygon'u.
- neighbors.py: altı axial komşu yönü.
- distance.py: hex mesafesi.
- tolerance.py: merkezi mutlak/göreli tolerans.
- geometry/__init__.py: geometri API dışa aktarımı.

## 4. ADR kayıtları
- ADR-001: İki yönelimi destekleme — kullanıcı tercihiyle kabul edildi.
- ADR-002: Matematiksel eksen, origin ve circumradius — kullanıcı tercihiyle kabul edildi.
- ADR-003: Eşit mesafede önceki hücreyi koruma, sınır geçilince en yakın hücreye geçme ve deterministik yedek seçim — kullanıcı kararıyla kabul edildi ve uygulandı.

## 5. Test kapsamı
Axial/cube invariant, dönüşüm döngüsü, iki yönelim, farklı radius/origin, polygon köşe/kenar eşitliği, komşuluk simetrisi, mesafe, negatif koordinat, paylaşılan kenar davranışı, tolerans ve Pygame'siz import. Son güncellemede iki parametrik sınır testi eklendi: her iki yönelimde sınırın tam ortasında önceki hücreyi koruma ve sınır geçildikten sonra yeni hücreyi seçme.

## 6. Test kanıtı

### Önceki kod revizyonu — kullanıcı ortamı
- İşletim sistemi: Windows
- Python: 3.12.10
- Komut: `python -m pytest -q`
- Kullanıcının teyit ettiği sonuç: **49 passed**

Bu 49 test, son önceki-hücre sınır davranışı değişikliğinden önceki revizyona aittir. Son değişiklikle iki parametrik test (Flat-top ve Pointy-top için toplam dört test durumu) eklendi. Dolayısıyla son revizyon için yeniden test gerekir; beklenen toplam 53 testtir.

## 7. Açık konular
- Nihai görsel yönelim kamera/render aşamasında seçilecek.
- Çok büyük koordinatlarda floating-point hassasiyeti ayrıca stres testine tabi tutulmalı.
- WorldPosition, dünya hücre verisi, hareket, fizik, kamera ve render bu aşamanın dışındadır.

## 8. Kabul durumu
**ADR-003 KULLANICI KARARIYLA KABUL EDİLDİ VE UYGULANDI. SON KOD REVİZYONUNUN TEST DOĞRULAMASI BEKLENİYOR.**

Bu rapor Aşama 3 uygulama izni değildir.
